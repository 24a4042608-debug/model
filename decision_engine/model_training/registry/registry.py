import os
import pickle
import json
from datetime import datetime

REGISTRY_DIR = os.path.dirname(__file__)
STORAGE_DIR = os.path.join(REGISTRY_DIR, "storage")
METADATA_FILE = os.path.join(STORAGE_DIR, "metadata.json")

def init_registry():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "active_version": None,
                "models": []
            }, f, ensure_ascii=False, indent=2)

def get_next_version(algorithm: str) -> str:
    init_registry()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        models = data.get("models", [])
        if not models:
            return "1.0.0"
        
        # Parse major.minor.patch
        versions = []
        for m in models:
            v_str = m.get("version", "1.0.0")
            parts = v_str.split(".")
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                versions.append(tuple(map(int, parts)))
        if not versions:
            return "1.0.0"
        
        max_v = max(versions)
        # Increment patch version
        return f"{max_v[0]}.{max_v[1]}.{max_v[2] + 1}"
    except Exception:
        return "1.0.0"

def register_model(models_dict: dict, algorithm: str, accuracy: float, dataset_size: int) -> dict:
    """
    Saves a trained models dictionary (profit, gmv, roas) and registers it in metadata.json.
    """
    init_registry()
    version = get_next_version(algorithm)
    
    model_version_dir = os.path.join(STORAGE_DIR, f"version_{version}")
    os.makedirs(model_version_dir, exist_ok=True)
    
    # Save the target models
    for target, model in models_dict.items():
        filepath = os.path.join(model_version_dir, f"{target}_model.pkl")
        with open(filepath, "wb") as f:
            pickle.dump(model, f)
            
    # Update metadata
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        registry_data = json.load(f)
        
    new_model_entry = {
        "algorithm": algorithm,
        "version": version,
        "accuracy": round(float(accuracy), 4),
        "dataset_size": int(dataset_size),
        "train_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "path": f"version_{version}"
    }
    
    registry_data["models"].append(new_model_entry)
    registry_data["active_version"] = version
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, ensure_ascii=False, indent=2)
        
    return new_model_entry

def load_active_models() -> tuple[dict, dict]:
    """
    Loads and returns (models_dict, metadata_dict) for the active model version.
    """
    init_registry()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        active_version = data.get("active_version")
        if not active_version:
            return None, None
            
        metadata = None
        for m in data.get("models", []):
            if m.get("version") == active_version:
                metadata = m
                break
                
        if not metadata:
            return None, None
            
        model_version_dir = os.path.join(STORAGE_DIR, metadata["path"])
        
        models_dict = {}
        for target in ["profit", "gmv", "roas"]:
            filepath = os.path.join(model_version_dir, f"{target}_model.pkl")
            if not os.path.exists(filepath):
                return None, None
            with open(filepath, "rb") as f:
                models_dict[target] = pickle.load(f)
                
        return models_dict, metadata
    except Exception as e:
        print(f"Error loading active model: {e}")
        return None, None

def get_registry_info() -> dict:
    init_registry()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active_version": None, "models": []}
