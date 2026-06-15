import os
import json
import logging
from typing import List, Optional
from datetime import datetime

from supabase import create_client, Client
from backend.database.models import (
    VitalsRecord, AlertRecord, PatientHistoryRecord,
    MedicationRecord, LabResultRecord, ImageRecord, VideoRecord, RiskRecord
)

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Fallback to avoid crashing locally if keys aren't set during startup
# In production, these should be verified
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

class DatabaseManager:
    @staticmethod
    def _execute_insert(table: str, data: dict):
        if not supabase:
            logger.warning(f"Supabase not configured. Mocking insert to {table}: {data}")
            return 1
        response = supabase.table(table).insert(data).execute()
        if response.data:
            return response.data[0].get('id', 1)
        return None

    @staticmethod
    def _execute_select(table: str, match_cols: dict, order_col: str, limit: int = None, desc: bool = True):
        if not supabase:
            logger.warning(f"Supabase not configured. Mocking select from {table}")
            return []
        
        query = supabase.table(table).select("*").match(match_cols)
        if order_col:
            query = query.order(order_col, desc=desc)
        if limit is not None:
            query = query.limit(limit)
            
        response = query.execute()
        return response.data

    @staticmethod
    def insert_vitals(record: VitalsRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('vitals_history', data)

    @staticmethod
    def get_vitals_history(patient_id: str, limit: int = 10) -> List[VitalsRecord]:
        data = DatabaseManager._execute_select('vitals_history', {'patient_id': patient_id}, 'timestamp', limit)
        return [VitalsRecord(**row) for row in reversed(data)]

    @staticmethod
    def insert_alert(record: AlertRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('alerts', data)

    @staticmethod
    def get_alerts(patient_id: str, limit: int = 10) -> List[AlertRecord]:
        data = DatabaseManager._execute_select('alerts', {'patient_id': patient_id}, 'timestamp', limit)
        return [AlertRecord.from_db(row) for row in data]

    @staticmethod
    def insert_history(record: PatientHistoryRecord) -> int:
        # Instead of multiple tables, we map this to timeline_events if preferred, 
        # but sticking to current model structure 'patient_history' mapping for now.
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        # Convert list to json-serializable format for Supabase if needed, but supabase-py handles dict/list as JSONB
        return DatabaseManager._execute_insert('patient_history', data)

    @staticmethod
    def get_patient_history(patient_id: str, limit: int = 100) -> List[PatientHistoryRecord]:
        data = DatabaseManager._execute_select('patient_history', {'patient_id': patient_id}, 'timestamp', limit, desc=False)
        return [PatientHistoryRecord.from_db(row) for row in data]

    @staticmethod
    def insert_medication(record: MedicationRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('medications', data)

    @staticmethod
    def get_medications(patient_id: str) -> List[MedicationRecord]:
        data = DatabaseManager._execute_select('medications', {'patient_id': patient_id}, 'timestamp', None)
        return [MedicationRecord(**row) for row in data]

    @staticmethod
    def insert_lab_result(record: LabResultRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('lab_results', data)

    @staticmethod
    def get_lab_results(patient_id: str) -> List[LabResultRecord]:
        data = DatabaseManager._execute_select('lab_results', {'patient_id': patient_id}, 'timestamp', None)
        return [LabResultRecord(**row) for row in data]

    @staticmethod
    def insert_image(record: ImageRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('medical_images', data)

    @staticmethod
    def get_images(patient_id: str) -> List[ImageRecord]:
        data = DatabaseManager._execute_select('medical_images', {'patient_id': patient_id}, 'timestamp', None)
        return [ImageRecord(**row) for row in data]

    @staticmethod
    def insert_video(record: VideoRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('videos', data)

    @staticmethod
    def get_videos(patient_id: str) -> List[VideoRecord]:
        data = DatabaseManager._execute_select('videos', {'patient_id': patient_id}, 'timestamp', None)
        return [VideoRecord(**row) for row in data]

    @staticmethod
    def insert_risk(record: RiskRecord) -> int:
        data = record.model_dump(exclude={"id"}, exclude_none=True)
        return DatabaseManager._execute_insert('risk_history', data)

    @staticmethod
    def get_risk_history(patient_id: str, limit: int = 100) -> List[RiskRecord]:
        data = DatabaseManager._execute_select('risk_history', {'patient_id': patient_id}, 'timestamp', limit)
        return [RiskRecord.from_db(row) for row in reversed(data)]
