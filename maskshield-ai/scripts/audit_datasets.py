import os
import json
from pathlib import Path

def get_dir_stats(path: Path):
    num_images = len(list(path.rglob("*.jpg"))) + len(list(path.rglob("*.png")))
    num_xml = len(list(path.rglob("*.xml")))
    num_txt = len(list(path.rglob("*.txt")))
    
    subdirs = [d for d in path.iterdir() if d.is_dir()]
    num_identities = len([d for d in subdirs if len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) > 0])
    
    return {
        "images": num_images,
        "xml_annotations": num_xml,
        "txt_annotations": num_txt,
        "identities": num_identities
    }

def analyze_datasets():
    datasets_dir = Path(__file__).resolve().parent.parent / "datasets"
    
    report = {}
    for folder_name in ["lfw", "mask", "IMFD", "CMFD"]:
        folder = datasets_dir / folder_name
        if folder.exists():
            report[folder_name] = get_dir_stats(folder)
        else:
            report[folder_name] = "NOT FOUND"
            
    print(json.dumps(report, indent=4))

if __name__ == "__main__":
    analyze_datasets()
