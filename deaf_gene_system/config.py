#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
RESOURCES_DIR = BASE_DIR / "resources"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
RESOURCES_DIR.mkdir(exist_ok=True)

SOFTWARE_INFO = {
    "name": "爱湾医学耳聋基因检测系统",
    "version": "1.0.0",
    "company": "深圳爱湾医学检验实验室",
    "copyright": "© 2026 深圳爱湾医学检验实验室 版权所有",
    "description": "专业的耳聋基因检测与分析系统",
    "contact": "0755-86708123"
}

DATABASE_CONFIG = {
    "type": "sqlite",
    "path": DATA_DIR / "deaf_gene_system.db",
    "backup_dir": DATA_DIR / "backups"
}

USER_ROLES = {
    "admin": "管理员",
    "doctor": "医师", 
    "technician": "实验员"
}

PERMISSIONS = {
    "admin": [
        "dashboard", "sample_management", "gene_analysis",
        "report_generation", "report_review", "statistics", "system_settings"
    ],
    "doctor": [
        "dashboard", "sample_management", "gene_analysis",
        "report_generation", "report_review", "statistics"
    ],
    "technician": [
        "dashboard", "sample_management", "gene_analysis", "report_generation"
    ]
}

UI_MODULES = {
    "dashboard": {"name": "主控台", "icon": "📊"},
    "sample_management": {"name": "样本管理", "icon": "📋"},
    "gene_analysis": {"name": "数据解析", "icon": "🧬"},
    "report_generation": {"name": "报告生成", "icon": "📄"},
    "report_review": {"name": "审核中心", "icon": "✅"},
    "statistics": {"name": "统计查询", "icon": "📈"},
    "system_settings": {"name": "系统设置", "icon": "⚙️"}
}

REPORT_TEMPLATES = {
    "clinical": "临床诊断报告",
    "newborn": "新生儿筛查报告", 
    "genetic": "遗传咨询报告"
}

GENE_CONFIG = {
    "genes": ["GJB2", "GJB3", "SLC26A4", "MT-RNR1"],
    "supported_formats": [".xlsx", ".xls", ".csv"],
    "mutation_db": "resources/mutations.json"
}

SECURITY_CONFIG = {
    "password_min_length": 6,
    "session_timeout": 3600,
    "max_login_attempts": 5,
    "password_complexity": True
}

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": DATA_DIR / "system.log",
    "max_bytes": 10 * 1024 * 1024,
    "backup_count": 5
}

DEFAULT_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "real_name": "系统管理员"
    },
    {
        "username": "doctor",
        "password": "doctor123", 
        "role": "doctor",
        "real_name": "张医师"
    },
    {
        "username": "tech",
        "password": "tech123",
        "role": "technician",
        "real_name": "李实验员"
    }
]

SAMPLE_STATUS = {
    "pending": "待检测",
    "analyzing": "分析中",
    "completed": "已完成",
    "failed": "失败"
}

REPORT_STATUS = {
    "pending": "待审核",
    "approved": "已通过",
    "rejected": "已驳回",
    "archived": "已归档"
}