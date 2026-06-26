#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import os
import csv

from config import DATABASE_CONFIG, DEFAULT_USERS

# import pymysql  # 之前想换成MySQL，后来还是用SQLite了


class DatabaseError(Exception):
    pass


class DuplicateRecordError(DatabaseError):
    pass


class RecordNotFoundError(DatabaseError):
    pass


class DeafGeneDbManager:
    def __init__(self, db_path: Path = None):
        # 数据库路径，默认从配置里取，也可以手动指定
        self.db_path = db_path or DATABASE_CONFIG["path"]
        # 确保数据目录存在，之前忘了建目录导致报错
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self._debug_mode = True  # 调试模式，上线记得关掉
        
        # 临时记录查询次数，之前遇到过性能问题，靠这个排查出来的
        self._query_count = 0
        self._last_query_time = None
        
        self.connect()
        self.init_database()
        
    def connect(self):
        try:
            print(f"连接数据库: {self.db_path}", file=sys.stderr)
            
            # 连接数据库，row_factory设为Row，这样查出来是字典格式，方便用
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            print(f"数据库连接成功", file=sys.stderr)
        except sqlite3.Error as e:
            print(f"数据库连接失败: {str(e)}", file=sys.stderr)
            raise DatabaseError(f"数据库连接失败: {str(e)}")
        
    def close(self):
        if self.connection:
            self.connection.close()
            
    def execute_query(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        # 计数加一，方便统计查询次数
        self._query_count += 1
        
        # 调试模式下打印SQL，方便排查问题
        if self._debug_mode:
            print(f"SQL: {query}", file=sys.stderr)
            if params:
                print(f"参数: {params}", file=sys.stderr)
        
        cursor = self.connection.cursor()
        try:
            # 带参数的查询更安全，防止SQL注入
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.Error as e:
            print(f"SQL执行失败: {str(e)}", file=sys.stderr)
            raise DatabaseError(f"SQL执行失败: {str(e)}")
        
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        # 查询单条记录，查不到返回None
        cursor = self.execute_query(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        # 查询多条记录，返回列表
        cursor = self.execute_query(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        if self._debug_mode:
            print(f"[DEBUG] 查询结果: {len(results)}条", file=sys.stderr)
        
        return results
        
    def commit(self):
        # 提交事务，之前忘了commit导致数据没保存
        self.connection.commit()
        
    def rollback(self):
        # 回滚事务，出错时用
        self.connection.rollback()
        
    def init_database(self):
        print(f"初始化数据库表...", file=sys.stderr)
        
        # 创建所有表，顺序不能乱，后面的表依赖前面的
        self._create_users_table()
        self._create_samples_table()
        self._create_gene_data_table()
        self._create_reports_table()
        self._create_audit_logs_table()
        self._create_templates_table()
        
        self.commit()
        # 创建默认用户，第一次用的时候至少有个admin可以登录
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
        # 样本表 - 存储耳聋基因检测样本的基本信息
        # 注意：sample_no必须唯一，这是样本的唯一标识
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
        # 基因数据表 - 存储每个样本的基因检测结果
        # 一个样本可能有多个位点数据，所以这里是一对多关系
        # 关键字段：sample_id关联样本，gene_name基因名称，mutation_site突变位点
        # genotype基因型，pathogenicity致病性评级（参考ACMG标准）
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
        # 报告表 - 存储生成的检测报告
        # status字段：pending待审核，approved已审核，rejected已拒绝
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
    
    def _create_templates_table(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS report_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_code TEXT UNIQUE NOT NULL,
                template_name TEXT NOT NULL,
                hospital_name TEXT,
                header_content TEXT,
                footer_content TEXT,
                normal_interpretation TEXT,
                abnormal_interpretation TEXT,
                clinical_suggestions TEXT,
                tester_signature TEXT,
                reviewer_signature TEXT,
                seal_image TEXT,
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self._add_template_signature_columns()
    
    def _add_template_signature_columns(self):
        columns_to_add = [
            ('tester_signature', 'TEXT'),
            ('reviewer_signature', 'TEXT'),
            ('seal_image', 'TEXT')
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                self.execute_query(f"ALTER TABLE report_templates ADD COLUMN {col_name} {col_type}")
            except DatabaseError:
                pass
    
    def init_default_users(self):
        print(f"检查默认用户...", file=sys.stderr)
        
        created_count = 0
        skipped_count = 0
        failed_users = []
        
        idx = 0
        while idx < len(DEFAULT_USERS):
            user = DEFAULT_USERS[idx]
            username = user["username"]
            
            if not username or username.strip() == "":
                idx += 1
                continue
            
            existing_user = self.get_user_by_username(username)
            
            if not existing_user:
                try:
                    self.create_user(
                        username=username,
                        password=user["password"],
                        role=user["role"],
                        real_name=user["real_name"]
                    )
                    print(f"创建默认用户: {username}", file=sys.stderr)
                    created_count += 1
                except DuplicateRecordError:
                    skipped_count += 1
                except Exception as e:
                    failed_users.append(f"{username}: {str(e)}")
                    print(f"创建用户失败: {username} - {str(e)}", file=sys.stderr)
            else:
                print(f"用户已存在: {username}", file=sys.stderr)
                skipped_count += 1
            
            idx += 1
        
        print(f"默认用户初始化完成: 创建{created_count}个, 跳过{skipped_count}个, 失败{len(failed_users)}个", file=sys.stderr)
    
    def hash_password(self, password: str) -> str:
        # 密码哈希，用SHA256，虽然简单但够用了
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
        # 简单查询，不加异常捕获，调用方自己处理
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
        # 之前用的是直接传所有字段，现在改成逐字段提取，更清晰
        # 不过这样写有点啰嗦，后面优化的时候再改
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
        conditions = []
        
        # 临时变量：记录应用的过滤条件数量
        applied_filter_count = 0
        
        if filters:
            # 多种判断形式混合
            status_filter = filters.get("status")
            # 判断形式1：字符串非空
            if status_filter != "" and status_filter is not None:
                conditions.append("status = ?")
                params.append(status_filter)
                applied_filter_count += 1
            
            hospital_filter = filters.get("hospital")
            # 判断形式2：长度大于0
            if len(hospital_filter or "") > 0:
                conditions.append("hospital LIKE ?")
                params.append(f"%{hospital_filter}%")
                applied_filter_count += 1
            
            sample_no_filter = filters.get("sample_no")
            # 判断形式3：直接判断（隐式转换）
            if sample_no_filter:
                conditions.append("sample_no LIKE ?")
                params.append(f"%{sample_no_filter}%")
                applied_filter_count += 1
            
            patient_name_filter = filters.get("patient_name")
            # 判断形式4：is not None
            if patient_name_filter is not None:
                conditions.append("patient_name LIKE ?")
                params.append(f"%{patient_name_filter}%")
                applied_filter_count += 1
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        cursor = self.execute_query(query, tuple(params))
        results = [dict(row) for row in cursor.fetchall()]
        
        # 调试信息：打印查询结果和应用的过滤条件
        if self._debug_mode and applied_filter_count > 0:
            print(f"[DEBUG] 查询样本: 应用{applied_filter_count}个过滤条件, 返回{len(results)}条", file=sys.stderr)
        
        return results
    
    def create_gene_data(self, gene_data: Dict) -> int:
        # 基因数据插入 - 需要验证关键字段
        # 临时变量：保存验证后的字段值
        validated_sample_id = gene_data.get("sample_id")
        validated_gene_name = gene_data.get("gene_name")
        validated_mutation_site = gene_data.get("mutation_site")
        
        # 验证sample_id，不能为空
        if validated_sample_id is None or validated_sample_id == "":
            raise ValueError("样本ID不能为空")
        
        # 验证gene_name，为空则用默认值
        if not validated_gene_name or validated_gene_name.strip() == "":
            validated_gene_name = "GJB2"
        
        # 验证mutation_site，为空则用默认值（手动兜底赋值）
        if not validated_mutation_site or validated_mutation_site.strip() == "":
            validated_mutation_site = "未知位点"
            print(f"[WARN] 基因数据位点为空，使用默认值: sample_id={validated_sample_id}", file=sys.stderr)
        
        # 临时变量：整理插入数据
        insert_data = (
            validated_sample_id,
            validated_gene_name,
            validated_mutation_site,
            gene_data.get("genotype"),
            gene_data.get("pathogenicity"),
            gene_data.get("reference")
        )
        
        try:
            cursor = self.execute_query("""
                INSERT INTO gene_data (
                    sample_id, gene_name, mutation_site, genotype, pathogenicity, reference
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, insert_data)
            self.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            # 外键约束错误，样本不存在
            print(f"[ERROR] 基因数据插入失败：样本ID {validated_sample_id} 不存在", file=sys.stderr)
            raise DatabaseError(f"样本不存在，无法插入基因数据")
        except sqlite3.Error as e:
            # 其他数据库错误
            with open("deaf_gene_errors.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 基因数据插入失败: sample_id={validated_sample_id}, gene={validated_gene_name}, error={str(e)}\n")
            raise DatabaseError(f"基因数据插入失败: {str(e)}")
    
    def get_gene_data_by_sample(self, sample_id: int) -> List[Dict]:
        # 根据样本ID查询基因数据
        # 这个函数后面会频繁用到，所以不加try-except，让上层处理
        cursor = self.execute_query(
            "SELECT * FROM gene_data WHERE sample_id = ? ORDER BY gene_name",
            (sample_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def create_report(self, report_data: Dict) -> int:
        # 报告生成异常单独处理，和其他操作区分开
        try:
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
        except sqlite3.IntegrityError as e:
            # 报告编号重复，这是常见错误，单独处理
            print(f"[ERROR] 报告编号重复: {report_data['report_no']}", file=sys.stderr)
            raise DatabaseError(f"报告编号 '{report_data['report_no']}' 已存在")
        except sqlite3.Error as e:
            # 其他数据库错误
            print(f"[ERROR] 报告生成失败: {str(e)}", file=sys.stderr)
            raise DatabaseError(f"报告生成失败: {str(e)}")
    
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
        # 仪表盘统计数据 - 多个查询组合
        stats = {}
        
        # 临时变量：记录每个统计项的查询结果
        today_sample_count = 0
        pending_review_count = 0
        completed_report_count = 0
        abnormal_mutation_count = 0
        
        # 查询今日样本数
        try:
            cursor = self.execute_query("""
                SELECT COUNT(*) as count FROM samples 
                WHERE DATE(created_at) = DATE('now')
            """)
            today_sample_count = cursor.fetchone()["count"]
        except Exception as e:
            print(f"[WARN] 查询今日样本数失败: {str(e)}", file=sys.stderr)
            today_sample_count = 0
        
        # 查询待审核报告数
        try:
            cursor = self.execute_query("""
                SELECT COUNT(*) as count FROM reports WHERE status = 'pending'
            """)
            pending_review_count = cursor.fetchone()["count"]
        except Exception as e:
            print(f"[WARN] 查询待审核报告数失败: {str(e)}", file=sys.stderr)
            pending_review_count = 0
        
        # 查询已完成报告数
        try:
            cursor = self.execute_query("""
                SELECT COUNT(*) as count FROM reports WHERE status = 'approved'
            """)
            completed_report_count = cursor.fetchone()["count"]
        except Exception as e:
            print(f"[WARN] 查询已完成报告数失败: {str(e)}", file=sys.stderr)
            completed_report_count = 0
        
        # 查询异常位点数量
        try:
            cursor = self.execute_query("""
                SELECT COUNT(*) as count FROM gene_data WHERE pathogenicity = 'pathogenic'
            """)
            abnormal_mutation_count = cursor.fetchone()["count"]
        except Exception as e:
            print(f"[WARN] 查询异常位点数量失败: {str(e)}", file=sys.stderr)
            abnormal_mutation_count = 0
        
        # 临时变量：计算总样本数（用于验证数据一致性）
        total_samples = today_sample_count
        
        # 组装结果
        stats["today_samples"] = today_sample_count
        stats["pending_reviews"] = pending_review_count
        stats["completed_reports"] = completed_report_count
        stats["abnormal_mutations"] = abnormal_mutation_count
        
        # 调试信息：如果异常位点数量大于今日样本数，可能数据有问题
        if abnormal_mutation_count > total_samples and total_samples > 0:
            print(f"[WARN] 异常位点数量({abnormal_mutation_count})大于今日样本数({total_samples})", file=sys.stderr)
        
        return stats
    
    def log_audit(self, user_id: int, action: str, table_name: str, record_id: int, 
                  old_values: str = None, new_values: str = None):
        # 审计日志，简单操作不加异常捕获
        self.execute_query("""
            INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, table_name, record_id, old_values, new_values))
        self.commit()
    
    def get_deaf_gene_report_by_sample(self, sample_id: int):
        # 查询样本对应的报告 - 简单查询，不加try-except
        return self.fetch_one(
            "SELECT * FROM reports WHERE sample_id = ? ORDER BY created_at DESC",
            (sample_id,)
        )
    
    def create_report_template(self, template_data: Dict) -> int:
        try:
            if template_data.get('is_default'):
                self.execute_query("UPDATE report_templates SET is_default = 0")
            
            cursor = self.execute_query("""
                INSERT INTO report_templates (
                    template_code, template_name, hospital_name, header_content,
                    footer_content, normal_interpretation, abnormal_interpretation,
                    clinical_suggestions, tester_signature, reviewer_signature,
                    seal_image, is_default, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_data["template_code"],
                template_data["template_name"],
                template_data.get("hospital_name"),
                template_data.get("header_content"),
                template_data.get("footer_content"),
                template_data.get("normal_interpretation"),
                template_data.get("abnormal_interpretation"),
                template_data.get("clinical_suggestions"),
                template_data.get("tester_signature"),
                template_data.get("reviewer_signature"),
                template_data.get("seal_image"),
                template_data.get("is_default", 0),
                template_data.get("is_active", 1)
            ))
            self.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise DuplicateRecordError(f"模板编码 '{template_data['template_code']}' 已存在")
    
    def get_report_template_by_code(self, template_code: str) -> Optional[Dict]:
        return self.fetch_one(
            "SELECT * FROM report_templates WHERE template_code = ? AND is_active = 1",
            (template_code,)
        )
    
    def get_all_report_templates(self) -> List[Dict]:
        return self.fetch_all(
            "SELECT * FROM report_templates WHERE is_active = 1 ORDER BY is_default DESC, created_at DESC"
        )
    
    def update_report_template(self, template_code: str, template_data: Dict):
        if template_data.get('is_default'):
            self.execute_query("UPDATE report_templates SET is_default = 0")
        
        set_clauses = []
        params = []
        
        if 'template_name' in template_data:
            set_clauses.append("template_name = ?")
            params.append(template_data['template_name'])
        if 'hospital_name' in template_data:
            set_clauses.append("hospital_name = ?")
            params.append(template_data['hospital_name'])
        if 'header_content' in template_data:
            set_clauses.append("header_content = ?")
            params.append(template_data['header_content'])
        if 'footer_content' in template_data:
            set_clauses.append("footer_content = ?")
            params.append(template_data['footer_content'])
        if 'normal_interpretation' in template_data:
            set_clauses.append("normal_interpretation = ?")
            params.append(template_data['normal_interpretation'])
        if 'abnormal_interpretation' in template_data:
            set_clauses.append("abnormal_interpretation = ?")
            params.append(template_data['abnormal_interpretation'])
        if 'clinical_suggestions' in template_data:
            set_clauses.append("clinical_suggestions = ?")
            params.append(template_data['clinical_suggestions'])
        if 'tester_signature' in template_data:
            set_clauses.append("tester_signature = ?")
            params.append(template_data['tester_signature'])
        if 'reviewer_signature' in template_data:
            set_clauses.append("reviewer_signature = ?")
            params.append(template_data['reviewer_signature'])
        if 'seal_image' in template_data:
            set_clauses.append("seal_image = ?")
            params.append(template_data['seal_image'])
        if 'is_default' in template_data:
            set_clauses.append("is_default = ?")
            params.append(template_data['is_default'])
        
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(template_code)
        
        if set_clauses:
            self.execute_query(
                "UPDATE report_templates SET " + ", ".join(set_clauses) + " WHERE template_code = ?",
                tuple(params)
            )
            self.commit()
    
    def delete_report_template(self, template_code: str):
        self.execute_query(
            "UPDATE report_templates SET is_active = 0 WHERE template_code = ?",
            (template_code,)
        )
        self.commit()
    
    def get_default_template(self) -> Optional[Dict]:
        return self.fetch_one(
            "SELECT * FROM report_templates WHERE is_default = 1 AND is_active = 1"
        )


db = DeafGeneDbManager()

# 兼容旧代码，之前用的是DatabaseManager，后来改成DeafGeneDbManager了
# 暂时保留别名，避免其他模块导入报错
DatabaseManager = DeafGeneDbManager

print(f"[DEBUG] 数据库初始化完成，查询次数: {db._query_count}", file=sys.stderr)

