import time
import asyncio
from backend.modules.alerts_engine import evaluate_alerts

# Shared state
latest_alert = None
last_alert_signature = None
last_alert_time = 0

ALERT_COOLDOWN_SEC = 10

async def alert_loop():
    global latest_alert, last_alert_signature, last_alert_time
    
    while True:
        try:
            alert = evaluate_alerts()
            
            if alert:
                signature = (
                    alert["type"],
                    alert.get("source"),
                )
                
                now = time.time()
                
                # Deduplicate and Cool down
                if (
                    signature != last_alert_signature
                    or (now - last_alert_time) > ALERT_COOLDOWN_SEC
                ):
                    latest_alert = alert
                    last_alert_signature = signature
                    last_alert_time = now
                    
                    print("ALERT!: ", alert)
        except Exception as e:
            print("Alert Loop Error: ", e)
        
        await asyncio.sleep(1)