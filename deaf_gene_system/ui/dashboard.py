#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主控台/首页界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QFrame, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.database import db
from config import SAMPLE_STATUS, REPORT_STATUS


class Dashboard(QWidget):
    """主控台界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 欢迎信息
        welcome_widget = self.create_welcome_widget()
        layout.addWidget(welcome_widget)
        
        # 数据看板
        stats_widget = self.create_stats_widget()
        layout.addWidget(stats_widget)
        
        # 快捷入口
        shortcuts_widget = self.create_shortcuts_widget()
        layout.addWidget(shortcuts_widget)
        
        # 最近活动
        recent_widget = self.create_recent_activity_widget()
        layout.addWidget(recent_widget)
        
        layout.addStretch()
        
    def create_welcome_widget(self):
        """创建欢迎信息"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        title_label = QLabel("欢迎使用耳聋基因检测系统")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("专业的基因检测与分析平台，为临床诊断提供精准支持")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
            }
        """)
        layout.addWidget(subtitle_label)
        
        return widget
        
    def create_stats_widget(self):
        """创建数据看板"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        title_label = QLabel("数据概览")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(title_label)
        
        # 统计卡片
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        self.stats_cards = {}
        
        # 今日样本数
        today_sample_card = self.create_stat_card(
            "今日样本数", "0", "#0078d4", "📋"
        )
        stats_layout.addWidget(today_sample_card, 0, 0)
        self.stats_cards['today_samples'] = today_sample_card
        
        # 待审核报告数
        pending_review_card = self.create_stat_card(
            "待审核报告", "0", "#ff9800", "⏳"
        )
        stats_layout.addWidget(pending_review_card, 0, 1)
        self.stats_cards['pending_reviews'] = pending_review_card
        
        # 已完成报告数
        completed_report_card = self.create_stat_card(
            "已完成报告", "0", "#4caf50", "✅"
        )
        stats_layout.addWidget(completed_report_card, 0, 2)
        self.stats_cards['completed_reports'] = completed_report_card
        
        # 异常位点预警数
        abnormal_mutation_card = self.create_stat_card(
            "异常位点预警", "0", "#f44336", "⚠️"
        )
        stats_layout.addWidget(abnormal_mutation_card, 0, 3)
        self.stats_cards['abnormal_mutations'] = abnormal_mutation_card
        
        layout.addLayout(stats_layout)
        return widget
        
    def create_stat_card(self, title, value, color, icon):
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 图标和标题
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: rgba(255, 255, 255, 0.9);
            }
        """)
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
            }
        """)
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                margin-top: 10px;
            }
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label)
        
        # 保存数值标签引用以便更新
        card.value_label = value_label
        
        return card
        
    def create_shortcuts_widget(self):
        """创建快捷入口"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        title_label = QLabel("快捷入口")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(title_label)
        
        # 快捷按钮
        shortcuts_layout = QGridLayout()
        shortcuts_layout.setSpacing(15)
        
        shortcuts = [
            ("样本管理", "📋", "sample_management"),
            ("数据解析", "🧬", "gene_analysis"),
            ("报告生成", "📄", "report_generation"),
            ("审核中心", "✅", "report_review"),
            ("统计查询", "📈", "statistics"),
            ("系统设置", "⚙️", "system_settings")
        ]
        
        for i, (name, icon, module_id) in enumerate(shortcuts):
            shortcut_btn = self.create_shortcut_button(name, icon, module_id)
            row = i // 3
            col = i % 3
            shortcuts_layout.addWidget(shortcut_btn, row, col)
        
        layout.addLayout(shortcuts_layout)
        return widget
        
    def create_shortcut_button(self, name, icon, module_id):
        """创建快捷按钮"""
        btn = QPushButton()
        btn.setFixedHeight(100)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #0078d4;
                color: #0078d4;
            }
        """)
        
        layout = QVBoxLayout(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # 点击事件
        btn.clicked.connect(lambda checked, mid=module_id: self.switch_module(mid))
        
        return btn
        
    def switch_module(self, module_id):
        """切换模块"""
        # 向上遍历找到 MainWindow
        parent = self.parent()
        while parent:
            if hasattr(parent, 'switch_module'):
                parent.switch_module(module_id)
                break
            parent = parent.parent()
        
    def create_recent_activity_widget(self):
        """创建最近活动"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        title_label = QLabel("最近活动")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(title_label)
        
        # 活动列表
        self.activity_list = QScrollArea()
        self.activity_list.setWidgetResizable(True)
        self.activity_list.setFixedHeight(200)
        self.activity_list.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        activity_content = QWidget()
        self.activity_layout = QVBoxLayout(activity_content)
        self.activity_layout.setSpacing(10)
        self.activity_layout.addStretch()
        
        self.activity_list.setWidget(activity_content)
        layout.addWidget(self.activity_list)
        
        return widget
        
    def setup_timer(self):
        """设置定时器"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 每30秒刷新一次
        
    def refresh_data(self):
        """刷新数据"""
        # 更新统计数据
        stats = db.get_dashboard_stats()
        
        if 'today_samples' in self.stats_cards:
            self.stats_cards['today_samples'].value_label.setText(str(stats['today_samples']))
        
        if 'pending_reviews' in self.stats_cards:
            self.stats_cards['pending_reviews'].value_label.setText(str(stats['pending_reviews']))
        
        if 'completed_reports' in self.stats_cards:
            self.stats_cards['completed_reports'].value_label.setText(str(stats['completed_reports']))
        
        if 'abnormal_mutations' in self.stats_cards:
            self.stats_cards['abnormal_mutations'].value_label.setText(str(stats['abnormal_mutations']))
        
        # 更新最近活动
        self.update_recent_activity()
        
    def update_recent_activity(self):
        """更新最近活动"""
        # 清空现有活动
        while self.activity_layout.count() > 1:
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取最近的审计日志
        cursor = db.execute_query("""
            SELECT al.*, u.real_name, u.username
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC
            LIMIT 10
        """)
        
        activities = cursor.fetchall()
        
        if not activities:
            no_activity_label = QLabel("暂无最近活动")
            no_activity_label.setStyleSheet("color: #999; font-style: italic;")
            no_activity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activity_layout.insertWidget(0, no_activity_label)
            return
        
        for activity in activities:
            activity_item = self.create_activity_item(activity)
            self.activity_layout.insertWidget(0, activity_item)
    
    def create_activity_item(self, activity):
        """创建活动项"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(item)
        
        # 用户信息
        user_info = f"{activity['real_name'] or activity['username']}"
        user_label = QLabel(user_info)
        user_label.setStyleSheet("color: #333; font-weight: bold;")
        layout.addWidget(user_label)
        
        # 操作描述
        action_desc = self.get_action_description(activity)
        action_label = QLabel(action_desc)
        action_label.setStyleSheet("color: #666;")
        layout.addWidget(action_label)
        
        layout.addStretch()
        
        # 时间
        time_label = QLabel(self.format_time(activity['created_at']))
        time_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(time_label)
        
        return item
    
    def get_action_description(self, activity):
        """获取操作描述"""
        action = activity['action']
        table_name = activity['table_name']
        
        action_map = {
            'login': '登录系统',
            'logout': '退出登录',
            'create': f'创建{table_name}记录',
            'update': f'更新{table_name}记录',
            'delete': f'删除{table_name}记录',
            'review': '审核报告',
            'generate': '生成报告'
        }
        
        return action_map.get(action, f'执行{action}操作')
    
    def format_time(self, time_str):
        """格式化时间"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return time_str