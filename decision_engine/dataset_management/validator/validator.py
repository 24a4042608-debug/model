import re
from sqlalchemy.orm import Session
from automation.database.models import TrainingDataset

def validate_record(record: dict, db: Session = None) -> tuple[bool, str]:
    """
    Validates a single dataset record before importing.
    """
    required_fields = ["product_id", "date", "ctr", "cvr", "cpc", "cpa", "roas", "refund", "gmv", "profit"]
    
    # 1. Missing Values check
    for field in required_fields:
        if field not in record or record[field] is None:
            return False, f"Missing required field: '{field}'"

    # 2. Data Types check
    try:
        record["product_id"] = str(record["product_id"])
        record["date"] = str(record["date"])
        record["ctr"] = float(record["ctr"])
        record["cvr"] = float(record["cvr"])
        record["cpc"] = float(record["cpc"])
        record["cpa"] = float(record["cpa"])
        record["roas"] = float(record["roas"])
        record["refund"] = float(record["refund"])
        record["gmv"] = float(record["gmv"])
        record["profit"] = float(record["profit"])
    except (ValueError, TypeError) as e:
        return False, f"Invalid data type: {str(e)}"

    # 3. Date format validation (YYYY-MM-DD)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", record["date"]):
        return False, f"Date '{record['date']}' must be in YYYY-MM-DD format."

    # 4. Outliers / Domain validations
    if record["ctr"] < 0 or record["ctr"] > 100:
        return False, f"CTR ({record['ctr']}%) must be between 0 and 100."
    
    if record["cvr"] < 0 or record["cvr"] > 100:
        return False, f"CVR ({record['cvr']}%) must be between 0 and 100."
        
    if record["refund"] < 0 or record["refund"] > 100:
        return False, f"Refund Rate ({record['refund']}%) must be between 0 and 100."

    if record["cpc"] < 0:
        return False, f"CPC ({record['cpc']}) cannot be negative."
        
    if record["cpa"] < 0:
        return False, f"CPA ({record['cpa']}) cannot be negative."

    if record["roas"] < 0:
        return False, f"ROAS ({record['roas']}) cannot be negative."

    if record["gmv"] < 0:
        return False, f"GMV ({record['gmv']}) cannot be negative."

    # 5. Duplicate check (if db is provided)
    if db:
        exists = db.query(TrainingDataset).filter(
            TrainingDataset.product_id == record["product_id"],
            TrainingDataset.date == record["date"]
        ).first()
        if exists:
            return False, f"Duplicate record for product_id '{record['product_id']}' on date '{record['date']}'."

    return True, ""

def validate_batch(records: list[dict], db: Session = None) -> tuple[list[dict], list[str]]:
    """
    Validates a batch of records. Returns (valid_records, error_messages).
    """
    valid_records = []
    errors = []
    
    # Track duplicates inside the batch itself
    seen = set()
    
    for i, record in enumerate(records):
        pk = (record.get("product_id"), record.get("date"))
        if None in pk:
            errors.append(f"Row {i}: Missing product_id or date.")
            continue
            
        if pk in seen:
            errors.append(f"Row {i}: Duplicate product_id/date combination within this batch.")
            continue
            
        success, msg = validate_record(record, db)
        if success:
            seen.add(pk)
            valid_records.append(record)
        else:
            errors.append(f"Row {i} (Product {pk[0]} on {pk[1]}): {msg}")
            
    return valid_records, errors
