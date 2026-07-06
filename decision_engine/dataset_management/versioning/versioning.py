import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from automation.database.models import TrainingDataset

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
REGISTRY_FILE = os.path.join(STORAGE_DIR, "versions_registry.json")

def init_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def save_version(db: Session, version_name: str) -> dict:
    """
    Saves a snapshot of all current database training records to a JSON file.
    """
    init_storage()
    
    # Query all training records
    records = db.query(TrainingDataset).all()
    
    # Convert records to JSON serializable structures
    serializable_records = []
    for r in records:
        serializable_records.append({
            "product_id": r.product_id,
            "date": r.date,
            "ctr": float(r.ctr),
            "cvr": float(r.cvr),
            "cpc": float(r.cpc),
            "cpa": float(r.cpa),
            "roas": float(r.roas),
            "refund": float(r.refund),
            "gmv": float(r.gmv),
            "profit": float(r.profit)
        })
        
    version_filename = f"{version_name}.json"
    filepath = os.path.join(STORAGE_DIR, version_filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable_records, f, ensure_ascii=False, indent=2)
        
    # Update registry
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    # Remove if version already exists in registry
    registry = [v for v in registry if v["version"] != version_name]
    
    new_entry = {
        "version": version_name,
        "filename": version_filename,
        "record_count": len(serializable_records),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    registry.append(new_entry)
    
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
        
    return new_entry

def rollback_version(db: Session, version_name: str) -> bool:
    """
    Clears the database table and restores it to a previous version snapshot.
    """
    init_storage()
    filepath = os.path.join(STORAGE_DIR, f"{version_name}.json")
    if not os.path.exists(filepath):
        return False
        
    with open(filepath, "r", encoding="utf-8") as f:
        saved_records = json.load(f)
        
    try:
        # 1. Clear current database table
        db.query(TrainingDataset).delete()
        db.commit()
        
        # 2. Re-insert saved records
        for item in saved_records:
            record = TrainingDataset(
                product_id=item["product_id"],
                date=item["date"],
                ctr=item["ctr"],
                cvr=item["cvr"],
                cpc=item["cpc"],
                cpa=item["cpa"],
                roas=item["roas"],
                refund=item["refund"],
                gmv=item["gmv"],
                profit=item["profit"]
            )
            db.add(record)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error during rollback: {e}")
        return False

def list_versions() -> list[dict]:
    init_storage()
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
