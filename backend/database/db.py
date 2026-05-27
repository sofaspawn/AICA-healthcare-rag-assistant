import sqlite3
import json
from typing import List
from pathlib import Path
from backend.database.models import VitalsRecord, AlertRecord, PatientHistoryRecord

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
        # Return in chronological order (oldest to newest) for trend analysis
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
