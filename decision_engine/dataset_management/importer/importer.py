from sqlalchemy.orm import Session
from automation.database.models import TrainingDataset
from ..validator.validator import validate_batch
from ..versioning.versioning import save_version

def import_dataset_records(db: Session, records: list[dict], version_name: str = None) -> tuple[int, list[str]]:
    """
    Validates and imports a batch of records. Creates a version snapshot if version_name is provided.
    Returns (imported_count, errors_list).
    """
    # 1. Validate the batch
    valid_records, errors = validate_batch(records, db)
    
    if not valid_records:
        return 0, errors + ["No valid records to import."]
        
    try:
        # 2. Insert valid records into database
        for item in valid_records:
            db_record = TrainingDataset(
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
            db.add(db_record)
        db.commit()
        
        # 3. Create version snapshot if requested
        if version_name:
            save_version(db, version_name)
            
        return len(valid_records), errors
        
    except Exception as e:
        db.rollback()
        return 0, errors + [f"Database write error: {str(e)}"]
