#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

from config import DATABASE_CONFIG, DEFAULT_USERS


class DatabaseError(Exception):
    pass


class DuplicateRecordError(DatabaseError):
    pass


class RecordNotFoundError(DatabaseError):
    pass


class DatabaseManager:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DATABASE_CONFIG["path"]
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.connect()
        self.init_database()
        
    def connect(self):
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise DatabaseError(f"数据库连接失败: {str(e)}")
        
    def close(self):
        if self.connection:
            self.connection.close()
            
    def execute_query(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor
        
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        cursor = self.execute_query(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        cursor = self.execute_query(query, params)
        return [dict(row) for row in cursor.fetchall()]
        
    def commit(self):
        self.connection.commit()
        
    def rollback(self):
        self.connection.rollback()
        
    def init_database(self):
        self._create_users_table()
        self._create_samples_table()
        self._create_gene_data_table()
        self._create_reports_table()
        self._create_audit_logs_table()
        
        self.commit()
        self.init_default_users()
    
    def _create_users_table(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
    
    def _create_samples_table(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_no TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                gender TEXT,
                age TEXT,
                clinical_diagnosis TEXT,
                hospital TEXT,
                test_project TEXT,
                status TEXT DEFAULT 'pending',
                family_history TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
    
    def _create_gene_data_table(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS gene_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id INTEGER NOT NULL,
                gene_name TEXT NOT NULL,
                mutation_site TEXT NOT NULL,
                genotype TEXT,
                pathogenicity TEXT,
                reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sample_id) REFERENCES samples(id)
            )
        """)
    
    def _create_reports_table(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id INTEGER NOT NULL,
                report_no TEXT UNIQUE NOT NULL,
                template_type TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                reviewer_id INTEGER,
                review_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (sample_id) REFERENCES samples(id),
                FOREIGN KEY (reviewer_id) REFERENCES users(id)
            )
        """)
    
    def _create_audit_logs_table(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
    def init_default_users(self):
        for user in DEFAULT_USERS:
            if not self.get_user_by_username(user["username"]):
                self.create_user(
                    username=user["username"],
                    password=user["password"],
                    role=user["role"],
                    real_name=user["real_name"]
                )
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, role: str, real_name: str = None) -> int:
        try:
            hashed_password = self.hash_password(password)
            cursor = self.execute_query(
                "INSERT INTO users (username, password, role, real_name) VALUES (?, ?, ?, ?)",
                (username, hashed_password, role, real_name)
            )
            self.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise DuplicateRecordError(f"用户名 '{username}' 已存在")
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        cursor = self.execute_query(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        user = self.get_user_by_username(username)
        if user and user["password"] == self.hash_password(password):
            self.execute_query(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user["id"])
            )
            self.commit()
            return user
        return None
    
    def create_sample(self, sample_data: Dict) -> int:
        cursor = self.execute_query("""
            INSERT INTO samples (
                sample_no, patient_name, gender, age, clinical_diagnosis,
                hospital, test_project, family_history, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_data["sample_no"],
            sample_data["patient_name"],
            sample_data.get("gender"),
            sample_data.get("age"),
            sample_data.get("clinical_diagnosis"),
            sample_data.get("hospital"),
            sample_data.get("test_project"),
            sample_data.get("family_history"),
            sample_data.get("notes"),
            sample_data.get("created_by")
        ))
        self.commit()
        return cursor.lastrowid
    
    def get_samples(self, filters: Dict = None) -> List[Dict]:
        query = "SELECT * FROM samples"
        params = []
        
        if filters:
            conditions = []
            if filters.get("status"):
                conditions.append("status = ?")
                params.append(filters["status"])
            if filters.get("hospital"):
                conditions.append("hospital LIKE ?")
                params.append(f"%{filters['hospital']}%")
            if filters.get("sample_no"):
                conditions.append("sample_no LIKE ?")
                params.append(f"%{filters['sample_no']}%")
            if filters.get("patient_name"):
                conditions.append("patient_name LIKE ?")
                params.append(f"%{filters['patient_name']}%")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        cursor = self.execute_query(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    
    def create_gene_data(self, gene_data: Dict) -> int:
        cursor = self.execute_query("""
            INSERT INTO gene_data (
                sample_id, gene_name, mutation_site, genotype, pathogenicity, reference
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            gene_data["sample_id"],
            gene_data["gene_name"],
            gene_data["mutation_site"],
            gene_data.get("genotype"),
            gene_data.get("pathogenicity"),
            gene_data.get("reference")
        ))
        self.commit()
        return cursor.lastrowid
    
    def create_report(self, report_data: Dict) -> int:
        cursor = self.execute_query("""
            INSERT INTO reports (
                sample_id, report_no, template_type, content, status
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            report_data["sample_id"],
            report_data["report_no"],
            report_data.get("template_type"),
            report_data.get("content"),
            report_data.get("status", "pending")
        ))
        self.commit()
        return cursor.lastrowid
    
    def update_report_status(self, report_id: int, status: str, reviewer_id: int = None, comment: str = None):
        query = """
            UPDATE reports 
            SET status = ?, reviewed_at = ?
        """
        params = [status, datetime.now().isoformat()]
        
        if reviewer_id:
            query += ", reviewer_id = ?"
            params.append(reviewer_id)
        if comment:
            query += ", review_comment = ?"
            params.append(comment)
            
        query += " WHERE id = ?"
        params.append(report_id)
        
        self.execute_query(query, tuple(params))
        self.commit()
    
    def get_dashboard_stats(self) -> Dict:
        stats = {}
        
        cursor = self.execute_query("""
            SELECT COUNT(*) as count FROM samples 
            WHERE DATE(created_at) = DATE('now')
        """)
        stats["today_samples"] = cursor.fetchone()["count"]
        
        cursor = self.execute_query("""
            SELECT COUNT(*) as count FROM reports WHERE status = 'pending'
        """)
        stats["pending_reviews"] = cursor.fetchone()["count"]
        
        cursor = self.execute_query("""
            SELECT COUNT(*) as count FROM reports WHERE status = 'approved'
        """)
        stats["completed_reports"] = cursor.fetchone()["count"]
        
        cursor = self.execute_query("""
            SELECT COUNT(*) as count FROM gene_data WHERE pathogenicity = 'pathogenic'
        """)
        stats["abnormal_mutations"] = cursor.fetchone()["count"]
        
        return stats
    
    def log_audit(self, user_id: int, action: str, table_name: str, record_id: int, 
                  old_values: str = None, new_values: str = None):
        self.execute_query("""
            INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, table_name, record_id, old_values, new_values))
        self.commit()


# 全局数据库实例
db = DatabaseManager()