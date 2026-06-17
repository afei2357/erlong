#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
耳聋基因检测系统 - 项目结构设计
"""

# 项目目录结构
"""
deaf_gene_system/
├── main.py                          # 主程序入口
├── config.py                        # 配置文件
├── requirements.txt                 # 依赖包
├── resources/                       # 资源文件
│   ├── images/                      # 图片资源
│   │   ├── logo.png                 # 软件logo
│   │   ├── dna_icon.png             # DNA图标
│   │   ├── background.png           # 背景图
│   │   └── icons/                   # 各种图标
│   ├── templates/                   # 报告模板
│   │   ├── clinical_report.docx     # 临床诊断报告模板
│   │   ├── newborn_report.docx      # 新生儿筛查报告模板
│   │   └── genetic_report.docx      # 遗传咨询报告模板
│   ├── fonts/                       # 字体文件
│   └── styles/                      # 样式文件
│       ├── main.qss                 # 主样式
│       └── login.qss                # 登录样式
├── core/                            # 核心功能模块
│   ├── __init__.py
│   ├── auth.py                      # 用户认证和权限管理
│   ├── database.py                  # 数据库操作
│   ├── report_generator.py          # 报告生成（集成现有功能）
│   ├── gene_analyzer.py             # 基因数据分析
│   └── config_manager.py            # 配置管理
├── ui/                              # 用户界面模块
│   ├── __init__.py
│   ├── main_window.py               # 主窗口
│   ├── login_dialog.py              # 登录对话框
│   ├── dashboard.py                 # 主控台/首页
│   ├── sample_management.py         # 样本信息管理
│   ├── gene_analysis.py             # 基因数据解析
│   ├── report_preview.py            # 报告生成与预览
│   ├── report_review.py             # 报告审核
│   ├── statistics.py                # 统计查询
│   └── system_settings.py           # 系统设置
├── models/                          # 数据模型
│   ├── __init__.py
│   ├── user.py                      # 用户模型
│   ├── sample.py                    # 样本模型
│   ├── report.py                    # 报告模型
│   └── gene_data.py                 # 基因数据模型
├── utils/                           # 工具函数
│   ├── __init__.py
│   ├── logger.py                    # 日志工具
│   ├── validator.py                 # 数据验证
│   ├── file_handler.py              # 文件处理
│   └── date_utils.py                # 日期工具
└── tests/                           # 测试文件
    ├── __init__.py
    ├── test_auth.py
    └── test_report_generator.py
"""

# 用户权限定义
USER_ROLES = {
    "admin": "管理员",
    "doctor": "医师",
    "technician": "实验员"
}

# 权限配置
PERMISSIONS = {
    "admin": [
        "sample_management", "gene_analysis", "report_generation",
        "report_review", "statistics", "system_settings"
    ],
    "doctor": [
        "sample_management", "gene_analysis", "report_generation",
        "report_review", "statistics"
    ],
    "technician": [
        "sample_management", "gene_analysis", "report_generation"
    ]
}

# 界面模块配置
UI_MODULES = {
    "dashboard": "主控台",
    "sample_management": "样本管理",
    "gene_analysis": "数据解析",
    "report_preview": "报告生成",
    "report_review": "审核中心",
    "statistics": "统计查询",
    "system_settings": "系统设置"
}

# 数据库表结构
DATABASE_SCHEMA = {
    "users": """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            real_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """,
    "samples": """
        CREATE TABLE samples (
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
    """,
    "gene_data": """
        CREATE TABLE gene_data (
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
    """,
    "reports": """
        CREATE TABLE reports (
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
    """,
    "audit_logs": """
        CREATE TABLE audit_logs (
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
    """
}

# 软件配置
SOFTWARE_CONFIG = {
    "name": "爱湾医学耳聋基因检测系统",
    "version": "1.0.0",
    "company": "爱湾医学检验实验室",
    "description": "专业的耳聋基因检测与分析系统",
    "database": {
        "type": "sqlite",
        "path": "data/deaf_gene_system.db"
    },
    "report": {
        "output_dir": "reports",
        "template_dir": "resources/templates",
        "pdf_generator": "tools/word2pdf.jar"
    },
    "security": {
        "password_min_length": 6,
        "session_timeout": 3600,  # 1小时
        "max_login_attempts": 5
    }
}