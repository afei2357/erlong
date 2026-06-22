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

# 这些目录后面可能会用到，先预留着
TEMP_DIR = BASE_DIR / "temp"
BACKUP_DIR = DATA_DIR / "backups"
TEMP_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

SOFTWARE_INFO = {
    "name": "耳聋基因检测系统",
    "version": "1.3.9",  # 版本号改来改去的，先记在这里
    "company": "深圳爱湾医学检验实验室",
    "copyright": "© 2026 深圳爱湾医学检验实验室 版权所有",
    "description": "专业的耳聋基因检测与分析系统",
    "contact": "0755-xxxx",
    "build_date": "2026-06-17"  # 上次打包的日期，记一下
}

DATABASE_CONFIG = {
    "type": "sqlite",
    "path": DATA_DIR / "deaf_gene_system.db",
    "backup_dir": DATA_DIR / "backups",
    "debug_queries": True  # 调试时打开，可以看到所有SQL语句
}

USER_ROLES = {
    "admin": "管理员",
    "doctor": "医师", 
    "technician": "实验员"
    # "auditor": "审核员"  # 这个角色还没做，先注释掉
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
    "mutation_db": "resources/mutations.json",
    "default_gene": "GJB2"  # 默认显示的基因，方便测试
}

SECURITY_CONFIG = {
    "password_min_length": 6,
    "session_timeout": 3600,
    "max_login_attempts": 5,
    "password_complexity": True
    # "two_factor_auth": False  # 双因素认证还没做
}

LOGGING_CONFIG = {
    "level": "DEBUG",  # 开发阶段用DEBUG，上线改成INFO
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

# 开发调试用的临时配置，上线前要清理掉
DEBUG_CONFIG = {
    "show_sql_logs": True,
    "enable_auto_reload": False,  # 热重载还没搞
    "test_sample_count": 10,
    "skip_permission_check": False  # 测试时可以临时设为True跳过权限检查
}