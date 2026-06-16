#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI模块初始化
"""

from .login_dialog import LoginDialog
from .main_window import MainWindow
from .dashboard import Dashboard
from .sample_management import SampleManagement
from .gene_analysis import GeneAnalysis
from .report_preview import ReportPreview
from .report_review import ReportReview
from .statistics import Statistics
from .system_settings import SystemSettings

__all__ = [
    'LoginDialog', 'MainWindow', 'Dashboard', 'SampleManagement',
    'GeneAnalysis', 'ReportPreview', 'ReportReview', 'Statistics', 'SystemSettings'
]