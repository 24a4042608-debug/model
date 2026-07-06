from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from automation.database.models import get_db, TrainingDataset
from ..dataset_management.importer.importer import import_dataset_records
from ..dataset_management.versioning.versioning import list_versions, rollback_version
from ..model_training.trainer import train_decision_model
from ..model_training.registry.registry import get_registry_info
from ..prediction_analysis.predictor.predictor import predict_kpis
from ..prediction_analysis.simulator.simulator import run_whatif_simulation
from ..prediction_analysis.sensitivity.sensitivity import analyze_sensitivity
from ..prediction_analysis.explainer.explainer import explain_simulation_impact
from ..recommendation.planner.planner import generate_recommendations

router = APIRouter(prefix="/api/decision-engine", tags=["AI Decision Engine"])

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class DatasetRecord(BaseModel):
    product_id: str
    date: str
    ctr: float
    cvr: float
    cpc: float
    cpa: float
    roas: float
    refund: float
    gmv: float
    profit: float

class ImportRequest(BaseModel):
    records: List[DatasetRecord]
    version_name: Optional[str] = None

class RollbackRequest(BaseModel):
    version_name: str

class TrainRequest(BaseModel):
    algorithm: Optional[str] = "XGBoost"

class PredictRequest(BaseModel):
    ctr: float
    cvr: float
    cpa: float
    refund: float

class SimulateRequest(BaseModel):
    baseline: PredictRequest
    modified: PredictRequest

class RecommendRequest(BaseModel):
    target_profit: Optional[float] = 5000000
    target_roas: Optional[float] = 4.5
    max_refund: Optional[float] = 3.0
    current_inputs: PredictRequest

# ==========================================
# DATASET MANAGEMENT ENDPOINTS
# ==========================================

@router.get("/dataset")
def get_dataset(db: Session = Depends(get_db)):
    records = db.query(TrainingDataset).order_by(TrainingDataset.date.desc()).all()
    return records

@router.post("/dataset/import")
def import_dataset(req: ImportRequest, db: Session = Depends(get_db)):
    raw_records = [r.dict() for r in req.records]
    imported, errors = import_dataset_records(db, raw_records, req.version_name)
    if imported == 0:
        raise HTTPException(status_code=400, detail={"message": "Failed to import records", "errors": errors})
    return {"message": f"Successfully imported {imported} records.", "errors": errors}

@router.get("/dataset/versions")
def get_versions():
    return list_versions()

@router.post("/dataset/rollback")
def rollback(req: RollbackRequest, db: Session = Depends(get_db)):
    success = rollback_version(db, req.version_name)
    if not success:
        raise HTTPException(status_code=400, detail="Rollback failed or version snapshot not found.")
    return {"message": f"Successfully rolled back dataset to version {req.version_name}."}

@router.put("/dataset/{record_id}")
def update_dataset_record(record_id: int, req: DatasetRecord, db: Session = Depends(get_db)):
    record = db.query(TrainingDataset).filter(TrainingDataset.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    record.product_id = req.product_id
    record.date = req.date
    record.ctr = req.ctr
    record.cvr = req.cvr
    record.cpc = req.cpc
    record.cpa = req.cpa
    record.roas = req.roas
    record.refund = req.refund
    record.gmv = req.gmv
    record.profit = req.profit
    
    db.commit()
    db.refresh(record)
    return {"message": f"Successfully updated record {record_id}."}

@router.delete("/dataset/{record_id}")
def delete_dataset_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(TrainingDataset).filter(TrainingDataset.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    db.delete(record)
    db.commit()
    return {"message": f"Successfully deleted record {record_id}."}

# ==========================================
# MODEL TRAINING ENDPOINTS
# ==========================================

@router.post("/train")
def trigger_train(req: TrainRequest, db: Session = Depends(get_db)):
    try:
        metadata = train_decision_model(db, req.algorithm)
        return {"status": "success", "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@router.get("/train/registry")
def get_registry():
    return get_registry_info()

# ==========================================
# PREDICTION & WHAT-IF ENDPOINTS
# ==========================================

@router.post("/predict")
def run_prediction(req: PredictRequest, db: Session = Depends(get_db)):
    try:
        preds = predict_kpis(db, req.dict())
        return preds
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evaluate")
def evaluate_model(db: Session = Depends(get_db)):
    try:
        records = db.query(TrainingDataset).order_by(TrainingDataset.date.desc()).limit(30).all()
        evaluation_list = []
        actual_roas_list = []
        pred_roas_list = []
        
        for r in records:
            inputs = {
                "ctr": float(r.ctr),
                "cvr": float(r.cvr),
                "cpa": float(r.cpa),
                "refund": float(r.refund)
            }
            preds = predict_kpis(db, inputs)
            
            actual_roas_list.append(float(r.roas))
            pred_roas_list.append(preds["roas"])
            
            evaluation_list.append({
                "date": r.date,
                "actual_roas": float(r.roas),
                "predicted_roas": round(preds["roas"], 2),
                "actual_gmv": float(r.gmv),
                "predicted_gmv": round(preds["gmv"], 0),
                "actual_profit": float(r.profit),
                "predicted_profit": round(preds["profit"], 0),
                "error_pct": round(abs(float(r.roas) - preds["roas"]) / float(r.roas) * 100, 1) if r.roas > 0 else 0
            })
            
        mae = sum(abs(a - p) for a, p in zip(actual_roas_list, pred_roas_list)) / len(actual_roas_list) if actual_roas_list else 0.0
        
        return {
            "metrics": {
                "mae_roas": round(mae, 2),
                "sample_size": len(evaluation_list)
            },
            "evaluations": evaluation_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate")
def run_simulation(req: SimulateRequest, db: Session = Depends(get_db)):
    try:
        sim_data = run_whatif_simulation(db, req.baseline.dict(), req.modified.dict())
        sensitivity = analyze_sensitivity()
        explanation = explain_simulation_impact(sim_data, sensitivity)
        
        # Merge sensitivity and explanations into outputs
        return {
            "simulation": sim_data,
            "sensitivity": sensitivity,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# RECOMMENDATION ENDPOINTS
# ==========================================

@router.post("/recommend")
def get_recommendations(req: RecommendRequest, db: Session = Depends(get_db)):
    try:
        rules = {
            "target_profit": req.target_profit,
            "target_roas": req.target_roas,
            "max_refund": req.max_refund
        }
        recs = generate_recommendations(db, rules, req.current_inputs.dict())
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
