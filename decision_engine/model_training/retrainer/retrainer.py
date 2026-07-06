from sqlalchemy.orm import Session
from ..trainer.trainer import train_decision_model
from ..registry.registry import get_registry_info

def check_and_trigger_retrain(db: Session, force: bool = False, algorithm: str = "XGBoost") -> dict:
    """
    Checks if model accuracy or updates require retraining.
    """
    registry = get_registry_info()
    models = registry.get("models", [])
    
    should_retrain = force or not models
    
    # Check if latest model accuracy is below threshold
    if not should_retrain and models:
        latest = models[-1]
        if latest.get("accuracy", 1.0) < 0.70:
            should_retrain = True
            
    if should_retrain:
        print(f"[Retrainer] Triggering retrain using {algorithm}...")
        return train_decision_model(db, algorithm)
        
    return models[-1] if models else {}
