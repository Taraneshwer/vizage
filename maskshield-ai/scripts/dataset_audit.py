import os
import json
from pathlib import Path

def run_audit(data_root: str):
    root = Path(data_root)
    audit = {
        "datasets": {},
        "totals": {
            "images": 0,
            "identities": 0
        }
    }
    
    datasets_to_check = ["IMFD", "CMFD", "lfw", "mask"]
    for ds_name in datasets_to_check:
        ds_path = root / ds_name
        if not ds_path.exists():
            audit["datasets"][ds_name] = {"status": "missing"}
            continue
            
        images = list(ds_path.rglob("*.jpg")) + list(ds_path.rglob("*.png")) + list(ds_path.rglob("*.jpeg"))
        
                                                  
        identities = len([d for d in ds_path.iterdir() if d.is_dir()])
        
        audit["datasets"][ds_name] = {
            "status": "present",
            "image_count": len(images),
            "identity_count": identities
        }
        
        audit["totals"]["images"] += len(images)
        audit["totals"]["identities"] += identities
        
                
    with open("dataset_audit.json", "w") as f:
        json.dump(audit, f, indent=4)
        
              
    with open("dataset_audit.md", "w") as f:
        f.write("# Dataset Audit Report\n\n")
        f.write(f"**Total Images**: {audit['totals']['images']}\n")
        f.write(f"**Total Identities**: {audit['totals']['identities']}\n\n")
        for k, v in audit["datasets"].items():
            f.write(f"### {k}\n")
            if v["status"] == "missing":
                f.write("- **Status**: Missing\n")
            else:
                f.write(f"- **Images**: {v['image_count']}\n")
                f.write(f"- **Identities (Folders)**: {v['identity_count']}\n")

if __name__ == "__main__":
    datasets_dir = Path(__file__).resolve().parent.parent / "datasets"
    run_audit(str(datasets_dir))
