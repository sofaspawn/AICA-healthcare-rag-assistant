import sqlite3
import json
from typing import List
from pathlib import Path
from backend.database.models import (
    VitalsRecord, AlertRecord, PatientHistoryRecord,
    MedicationRecord, LabResultRecord, ImageRecord, VideoRecord, RiskRecord
)

DB_PATH = Path(__file__).parent.parent.parent / "healthcare_rag.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create patient_vitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            spo2 REAL,
            heart_rate REAL,
            temperature REAL,
            respiratory_rate REAL,
            systolic_bp REAL,
            diastolic_bp REAL
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            severity TEXT,
            score INTEGER,
            alerts TEXT
        )
    ''')
    
    # Create patient_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            interaction_text TEXT,
            extracted_symptoms TEXT,
            risk_score INTEGER,
            severity TEXT
        )
    ''')
    
    # Create medications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            medicine TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            source_file TEXT
        )
    ''')

    # Create lab_results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            test TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            reference_range TEXT,
            source_file TEXT
        )
    ''')

    # Create medical_images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            image_type TEXT NOT NULL,
            observation TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')

    # Create videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            video_path TEXT NOT NULL,
            summary TEXT NOT NULL,
            observations TEXT NOT NULL
        )
    ''')

    # Create risk_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            reasons TEXT NOT NULL,
            severity TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# Initialize on import
init_db()

class DatabaseManager:
    @staticmethod
    def insert_vitals(record: VitalsRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patient_vitals (patient_id, timestamp, spo2, heart_rate, temperature, respiratory_rate, systolic_bp, diastolic_bp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.spo2, record.heart_rate, record.temperature, record.respiratory_rate, record.systolic_bp, record.diastolic_bp))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_vitals_history(patient_id: str, limit: int = 10) -> List[VitalsRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM patient_vitals 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC LIMIT ?
        ''', (patient_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [VitalsRecord(**dict(row)) for row in reversed(rows)]

    @staticmethod
    def insert_alert(record: AlertRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        alerts_json = json.dumps(record.alerts)
        cursor.execute('''
            INSERT INTO alerts (patient_id, timestamp, severity, score, alerts)
            VALUES (?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.severity, record.score, alerts_json))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_alerts(patient_id: str, limit: int = 10) -> List[AlertRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC LIMIT ?
        ''', (patient_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [AlertRecord.from_db(row) for row in rows]

    @staticmethod
    def insert_history(record: PatientHistoryRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        symptoms_json = json.dumps(record.extracted_symptoms)
        cursor.execute('''
            INSERT INTO patient_history (patient_id, timestamp, interaction_text, extracted_symptoms, risk_score, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.interaction_text, symptoms_json, record.risk_score, record.severity))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_patient_history(patient_id: str, limit: int = 100) -> List[PatientHistoryRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM patient_history 
            WHERE patient_id = ? 
            ORDER BY timestamp ASC LIMIT ?
        ''', (patient_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [PatientHistoryRecord.from_db(row) for row in rows]

    @staticmethod
    def insert_medication(record: MedicationRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO medications (patient_id, timestamp, medicine, dosage, frequency, source_file)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.medicine, record.dosage, record.frequency, record.source_file))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_medications(patient_id: str) -> List[MedicationRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM medications 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [MedicationRecord(**dict(row)) for row in rows]

    @staticmethod
    def insert_lab_result(record: LabResultRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO lab_results (patient_id, timestamp, test, value, unit, reference_range, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.test, record.value, record.unit, record.reference_range, record.source_file))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_lab_results(patient_id: str) -> List[LabResultRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM lab_results 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [LabResultRecord(**dict(row)) for row in rows]

    @staticmethod
    def insert_image(record: ImageRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO medical_images (patient_id, timestamp, image_type, observation, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.image_type, record.observation, record.image_path))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_images(patient_id: str) -> List[ImageRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM medical_images 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [ImageRecord(**dict(row)) for row in rows]

    @staticmethod
    def insert_video(record: VideoRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (patient_id, timestamp, video_path, summary, observations)
            VALUES (?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.video_path, record.summary, record.observations))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_videos(patient_id: str) -> List[VideoRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM videos 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [VideoRecord(**dict(row)) for row in rows]

    @staticmethod
    def insert_risk(record: RiskRecord) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        reasons_json = json.dumps(record.reasons)
        cursor.execute('''
            INSERT INTO risk_history (patient_id, timestamp, risk_score, reasons, severity)
            VALUES (?, ?, ?, ?, ?)
        ''', (record.patient_id, record.timestamp, record.risk_score, reasons_json, record.severity))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def get_risk_history(patient_id: str, limit: int = 100) -> List[RiskRecord]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM risk_history 
            WHERE patient_id = ? 
            ORDER BY timestamp DESC LIMIT ?
        ''', (patient_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [RiskRecord.from_db(row) for row in reversed(rows)]

