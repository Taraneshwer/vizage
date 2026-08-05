import os
import argparse
import logging
from pathlib import Path
import math

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms
    import torchvision.models as models
except ImportError:
    torch = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock IR50 (ResNet50 based for demonstration) 
# In a full implementation, you would use the exact AdaFace IR50/IR100 architecture
class FaceModel(nn.Module):
    def __init__(self, embedding_size=512):
        super(FaceModel, self).__init__()
        # Use standard resnet50 as a backbone
        self.backbone = models.resnet50(pretrained=True)
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, embedding_size)
        self.bn = nn.BatchNorm1d(embedding_size)

    def forward(self, x):
        x = self.backbone(x)
        x = self.bn(x)
        return x

# ArcFace / AdaFace Margin Loss (Simplified ArcFace implementation)
class ArcFaceMargin(nn.Module):
    def __init__(self, in_features, out_features, s=64.0, m=0.50):
        super(ArcFaceMargin, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_uniform_(self.weight)
        
        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.th = math.cos(math.pi - m)
        self.mm = math.sin(math.pi - m) * m

    def forward(self, input, label):
        cosine = torch.nn.functional.linear(torch.nn.functional.normalize(input), torch.nn.functional.normalize(self.weight))
        sine = torch.sqrt(1.0 - torch.pow(cosine, 2))
        phi = cosine * self.cos_m - sine * self.sin_m
        phi = torch.where(cosine > self.th, phi, cosine - self.mm)
        
        one_hot = torch.zeros(cosine.size(), device=input.device)
        one_hot.scatter_(1, label.view(-1, 1).long(), 1)
        
        output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
        output *= self.s
        return output

def train_adaface(data_dir: str, epochs: int = 20, batch_size: int = 64, lr: float = 0.01, device: str = 'cuda', save_dir: str = 'runs/adaface'):
    if torch is None:
        logger.error("PyTorch is not installed.")
        return
        
    device = torch.device(device if torch.cuda.is_available() else 'cpu')
    logger.info(f"Training AdaFace on {device}. Data: {data_dir}")
    
    transform = transforms.Compose([
        transforms.Resize((112, 112)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.125, contrast=0.125, saturation=0.125),
        transforms.ToTensor(),
        transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    ])
    
    train_path = Path(data_dir) / 'train'
    if not train_path.exists():
        logger.error(f"Training data not found at {train_path}")
        return
        
    train_dataset = datasets.ImageFolder(train_path, transform=transform)
    num_classes = len(train_dataset.classes)
    
    logger.info(f"Found {len(train_dataset)} images belonging to {num_classes} classes.")
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4, pin_memory=True)
    
    model = FaceModel(embedding_size=512).to(device)
    margin = ArcFaceMargin(in_features=512, out_features=num_classes).to(device)
    
    criterion = nn.CrossEntropyLoss()
    # Optimizer includes both model and margin parameters
    optimizer = optim.SGD([{'params': model.parameters()}, {'params': margin.parameters()}], lr=lr, momentum=0.9, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    start_epoch = 0
    best_loss = float('inf')
    
    # Auto-resume
    last_ckpt = Path(save_dir) / 'last_adaface.pth'
    if last_ckpt.exists():
        logger.info(f"Found checkpoint at {last_ckpt}. Resuming...")
        checkpoint = torch.load(last_ckpt)
        model.load_state_dict(checkpoint['model_state_dict'])
        margin.load_state_dict(checkpoint['margin_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_loss = checkpoint['best_loss']
        logger.info(f"Resumed from epoch {start_epoch}")
    
    scaler = torch.amp.GradScaler('cuda') if device.type == 'cuda' else None
    
    try:
        for epoch in range(start_epoch, epochs):
            model.train()
            margin.train()
            total_loss = 0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(device), target.to(device)
                
                optimizer.zero_grad()
                
                if scaler:
                    with torch.amp.autocast('cuda'):
                        features = model(data)
                        output = margin(features, target)
                        loss = criterion(output, target)
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    features = model(data)
                    output = margin(features, target)
                    loss = criterion(output, target)
                    loss.backward()
                    optimizer.step()
                    
                total_loss += loss.item()
                
                if batch_idx % 50 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} [{batch_idx}/{len(train_loader)}] Loss: {loss.item():.4f}")
                    
            scheduler.step()
            avg_loss = total_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1} Average Loss: {avg_loss:.4f}")
            
            # Save best model
            if avg_loss < best_loss:
                best_loss = avg_loss
                torch.save(model.state_dict(), Path(save_dir) / 'best_adaface.pth')
                logger.info("Saved best model.")
                
            # Save last model (checkpoint)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'margin_state_dict': margin.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'best_loss': best_loss
            }, last_ckpt)
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user. Gracefully shutting down...")
        
    # Export to ONNX
    logger.info("Exporting to ONNX...")
    model.eval()
    dummy_input = torch.randn(1, 3, 112, 112, device=device)
    onnx_path = Path(save_dir) / 'best_adaface.onnx'
    torch.onnx.export(model, dummy_input, onnx_path, 
                      input_names=['input'], output_names=['output'], 
                      dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
    logger.info(f"Exported to {onnx_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AdaFace model.")
    parser.add_argument('--data', type=str, default='../datasets/processed/arcface', help='Path to arcface formatted dataset')
    parser.add_argument('--epochs', type=int, default=20, help='Number of epochs')
    parser.add_argument('--batch', type=int, default=64, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.01, help='Learning rate')
    parser.add_argument('--save_dir', type=str, default='runs/adaface', help='Directory to save model')
    
    args = parser.parse_args()
    
    data_path = Path(args.data).absolute()
    train_adaface(str(data_path), args.epochs, args.batch, args.lr, save_dir=args.save_dir)
