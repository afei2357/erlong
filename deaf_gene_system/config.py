#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
耳聋基因检测系统 - 配置文件
"""

import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
RESOURCES_DIR = BASE_DIR / "resources"

# 创建必要的目录
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
RESOURCES_DIR.mkdir(exist_ok=True)

# 软件信息
SOFTWARE_INFO = {
    "name": "耳聋基因检测系统",
    "version": "1.0.0",
    "company": "医学检验中心",
    "copyright": "© 2024 医学检验中心 版权所有"
}

# 数据库配置
DATABASE_CONFIG = {
    "type": "sqlite",
    "path": DATA_DIR / "deaf_gene_system.db",
    "backup_dir": DATA_DIR / "backups"
}

# 用户权限
USER_ROLES = {
    "admin": "管理员",
    "doctor": "医师", 
    "technician": "实验员"
}

# 权限配置
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

# 界面模块
UI_MODULES = {
    "dashboard": {"name": "主控台", "icon": "📊"},
    "sample_management": {"name": "样本管理", "icon": "📋"},
    "gene_analysis": {"name": "数据解析", "icon": "🧬"},
    "report_generation": {"name": "报告生成", "icon": "📄"},
    "report_review": {"name": "审核中心", "icon": "✅"},
    "statistics": {"name": "统计查询", "icon": "📈"},
    "system_settings": {"name": "系统设置", "icon": "⚙️"}
}

# 报告模板
REPORT_TEMPLATES = {
    "clinical": "临床诊断报告",
    "newborn": "新生儿筛查报告", 
    "genetic": "遗传咨询报告"
}

# 基因检测配置
GENE_CONFIG = {
    "genes": ["GJB2", "GJB3", "SLC26A4", "MT-RNR1"],
    "supported_formats": [".xlsx", ".xls", ".csv"],
    "mutation_db": "resources/mutations.json"
}

# 安全配置
SECURITY_CONFIG = {
    "password_min_length": 6,
    "session_timeout": 3600,
    "max_login_attempts": 5,
    "password_complexity": True
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": DATA_DIR / "system.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# 默认用户
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

# 样本状态
SAMPLE_STATUS = {
    "pending": "待检测",
    "analyzing": "分析中",
    "completed": "已完成",
    "failed": "失败"
}

# 报告状态
REPORT_STATUS = {
    "pending": "待审核",
    "approved": "已通过",
    "rejected": "已驳回",
    "archived": "已归档"
}