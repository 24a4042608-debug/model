import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Computes accuracy metrics (R2 score, MAE, MAPE).
    """
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    
    # Calculate Mean Absolute Percentage Error (MAPE)
    # Avoid division by zero
    non_zero = y_true != 0
    if np.sum(non_zero) > 0:
        mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100
    else:
        mape = 0.0
        
    return {
        "r2_score": float(r2),
        "mae": float(mae),
        "mape": float(mape)
    }
