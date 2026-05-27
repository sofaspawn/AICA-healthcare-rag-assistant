from typing import List
from backend.database.models import AlertRecord
from backend.database.db import DatabaseManager

class AlertEngine:
    @staticmethod
    def process_alerts(patient_id: str, severity: str, score: int, alerts: List[str]):
        """
        Triggers and persists alerts if severity is HIGH or CRITICAL.
        """
        if severity in ["HIGH", "CRITICAL"]:
            # Persist to DB
            record = AlertRecord(
                patient_id=patient_id,
                severity=severity,
                score=score,
                alerts=alerts
            )
            DatabaseManager.insert_alert(record)
            
            # Here we would integrate Slack/Email/Twilio webhooks
            AlertEngine.dispatch_external_alerts(record)
            
    @staticmethod
    def dispatch_external_alerts(record: AlertRecord):
        """
        Mock function to dispatch external alerts.
        """
        # print(f"DISPATCHING ALERT for Patient {record.patient_id}: {record.severity} Severity. Details: {record.alerts}")
        pass
