from fastapi import APIRouter
from backend.modules.alert_loop import latest_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/latest")
def get_latest():
    """
    Returns most recent alert (if any)
    """
    return latest_alert or {"status": "NO_ALERT"}
