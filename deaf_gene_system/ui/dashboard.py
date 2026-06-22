#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 权属说明：仪表盘

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

import os,sys

from core.database import db
from config import SAMPLE_STATUS, REPORT_STATUS


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#f5f5f5"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # 临时变量，记录上次刷新时间
        self._last_refresh_time = None
        self._refresh_count = 0
        
        self.init_ui()
        self.setup_timer()
        self.refresh_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        layout.addWidget(self.create_welcome_widget())
        layout.addWidget(self.create_stats_widget())
        layout.addWidget(self.create_shortcuts_widget())
        layout.addWidget(self.create_recent_activity_widget())
        layout.addStretch()
        
    def create_welcome_widget(self):
        widget = QFrame()
        palette = widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("欢迎使用耳聋基因检测系统")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        palette = title_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        title_label.setPalette(palette)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("专业的基因检测与分析平台，为临床诊断提供精准支持")
        subtitle_label.setFont(QFont("Microsoft YaHei", 14))
        palette = subtitle_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#666666"))
        subtitle_label.setPalette(palette)
        layout.addWidget(subtitle_label)
        
        return widget
        
    def create_stats_widget(self):
        widget = QFrame()
        palette = widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("数据概览")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        
        palette = title_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        title_label.setPalette(palette)
        layout.addWidget(title_label)
        
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        self.stats_cards = {}
        
        today_sample_card = self.create_stat_card("今日样本数", "0", "#0078d4", "📋")
        stats_layout.addWidget(today_sample_card, 0, 0)
        self.stats_cards['today_samples'] = today_sample_card
        
        pending_review_card = self.create_stat_card("待审核报告", "0", "#ff9800", "⏳")
        stats_layout.addWidget(pending_review_card, 0, 1)
        self.stats_cards['pending_reviews'] = pending_review_card
        
        completed_report_card = self.create_stat_card("已完成报告", "0", "#4caf50", "✅")
        stats_layout.addWidget(completed_report_card, 0, 2)
        self.stats_cards['completed_reports'] = completed_report_card
        
        abnormal_mutation_card = self.create_stat_card("异常位点预警", "0", "#f44336", "⚠️")
        stats_layout.addWidget(abnormal_mutation_card, 0, 3)
        self.stats_cards['abnormal_mutations'] = abnormal_mutation_card
        
        layout.addLayout(stats_layout)
        return widget
        
    def create_stat_card(self, title, value, color, icon):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {color}; border-radius: 8px; }}")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header_layout = self._create_card_header(icon, title)
        layout.addLayout(header_layout)
        
        value_label = self._create_card_value(value)
        layout.addWidget(value_label)
        
        card.value_label = value_label
        return card
    
    def _create_card_header(self, icon, title):
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        icon_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 12))
        title_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        header_layout.addWidget(title_label)
        
        return header_layout
    
    def _create_card_value(self, value):
        value_label = QLabel(value)
        value_label.setFont(QFont("Microsoft YaHei", 32, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        return value_label
        
    def create_shortcuts_widget(self):
        widget = QFrame()
        palette = widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("快捷入口")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        palette = title_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        title_label.setPalette(palette)
        layout.addWidget(title_label)
        
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
        container = QWidget()
        container.setFixedHeight(130)
        container.setMinimumWidth(180)
        container.setCursor(Qt.CursorShape.PointingHandCursor)
        
        palette = container.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#f8f9fa"))
        container.setPalette(palette)
        container.setAutoFillBackground(True)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(QFont("Segoe UI Emoji", 40))
        palette = icon_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        icon_label.setPalette(palette)
        layout.addWidget(icon_label)
        
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 15, QFont.Weight.Bold))
        palette = name_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        name_label.setPalette(palette)
        layout.addWidget(name_label)
        
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.switch_module(module_id)
        container.mousePressEvent = mousePressEvent
        
        return container
        
    def switch_module(self, module_id):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'switchDeafGeneModule'):
                parent.switchDeafGeneModule(module_id)
                break
            elif hasattr(parent, 'switch_module'):
                parent.switch_module(module_id)
                break
            parent = parent.parent()
        
    def create_recent_activity_widget(self):
        widget = QFrame()
        palette = widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("最近活动")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        palette = title_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        title_label.setPalette(palette)
        layout.addWidget(title_label)
        
        self.activity_list = QScrollArea()
        self.activity_list.setWidgetResizable(True)
        self.activity_list.setFixedHeight(200)
        
        activity_content = QWidget()
        self.activity_layout = QVBoxLayout(activity_content)
        self.activity_layout.setSpacing(10)
        self.activity_layout.addStretch()
        
        self.activity_list.setWidget(activity_content)
        layout.addWidget(self.activity_list)
        
        return widget
        
    def setup_timer(self):
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 每30秒刷新一次
        
    def refresh_data(self):
        # 临时变量：记录刷新开始时间
        import time
        start_time = time.time()
        
        # 获取统计数据
        stats = db.get_dashboard_stats()
        
        # 临时变量：保存各统计项的值
        today_samples = stats.get('today_samples', 0)
        pending_reviews = stats.get('pending_reviews', 0)
        completed_reports = stats.get('completed_reports', 0)
        abnormal_mutations = stats.get('abnormal_mutations', 0)
        
        # 更新统计卡片，混合使用if和直接赋值
        if 'today_samples' in self.stats_cards:
            self.stats_cards['today_samples'].value_label.setText(str(today_samples))
        
        if 'pending_reviews' in self.stats_cards:
            self.stats_cards['pending_reviews'].value_label.setText(str(pending_reviews))
        
        if 'completed_reports' in self.stats_cards:
            self.stats_cards['completed_reports'].value_label.setText(str(completed_reports))
        
        if 'abnormal_mutations' in self.stats_cards:
            self.stats_cards['abnormal_mutations'].value_label.setText(str(abnormal_mutations))
        
        # 更新最近活动
        self.update_recent_activity()
        
        # 临时变量：记录刷新耗时
        elapsed = time.time() - start_time
        self._refresh_count += 1
        
        # 调试信息：每5次刷新打印一次耗时
        if self._refresh_count % 5 == 0:
            print(f"[仪表盘] 刷新#{self._refresh_count}，耗时: {elapsed:.2f}s", file=sys.stderr)
        
        # 调试信息：如果待审核报告大于10，打印警告
        if pending_reviews > 10:
            print(f"[WARN] 待审核报告数量较多: {pending_reviews}份", file=sys.stderr)
        
    def update_recent_activity(self):
        while self.activity_layout.count() > 1:
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
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
            no_activity_label.setFont(QFont("Microsoft YaHei", 11, QFont.StyleItalic))
            palette = no_activity_label.palette()
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#999999"))
            no_activity_label.setPalette(palette)
            no_activity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activity_layout.insertWidget(0, no_activity_label)
            return
        
        for activity in activities:
            activity_item = self.create_activity_item(activity)
            self.activity_layout.insertWidget(0, activity_item)
    
    def create_activity_item(self, activity):
        item = QFrame()
        palette = item.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#f8f9fa"))
        item.setPalette(palette)
        item.setAutoFillBackground(True)
        
        layout = QHBoxLayout(item)
        
        user_info = f"{activity['real_name'] or activity['username']}"
        user_label = QLabel(user_info)
        user_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        palette = user_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        user_label.setPalette(palette)
        layout.addWidget(user_label)
        
        action_desc = self.get_action_description(activity)
        action_label = QLabel(action_desc)
        action_label.setFont(QFont("Microsoft YaHei", 10))
        palette = action_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#666666"))
        action_label.setPalette(palette)
        layout.addWidget(action_label)
        
        layout.addStretch()
        
        time_label = QLabel(self.format_time(activity['created_at']))
        time_label.setFont(QFont("Microsoft YaHei", 11))
        
        palette = time_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#999999"))
        time_label.setPalette(palette)
        layout.addWidget(time_label)
        
        return item
    
    def get_action_description(self, activity):
        # 操作描述映射，之前用的是if-elif，后来改成字典更简洁
        action = activity['action']
        table_name = activity['table_name']
        
        # 临时变量：保存映射结果
        desc = ""
        
        # 混合使用if和字典映射
        if action == 'login':
            desc = '登录系统'
        elif action == 'logout':
            desc = '退出登录'
        elif action == 'review':
            desc = '审核报告'
        elif action == 'generate':
            desc = '生成报告'
        else:
            # 其他操作使用字典
            action_map = {
                'create': f'创建{table_name}记录',
                'update': f'更新{table_name}记录',
                'delete': f'删除{table_name}记录',
            }
            desc = action_map.get(action, f'执行{action}操作')
        
        return desc
    
    # 旧代码，之前直接用datetime处理，后来发现有些时间格式不对，加了try-except
    # def format_time_old(self, time_str):
    #     from datetime import datetime
    #     dt = datetime.fromisoformat(time_str)
    #     return dt.strftime("%Y-%m-%d %H:%M")
    
    def format_time(self, time_str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            # 时间格式不对，尝试其他格式
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M")
            except:
                # 实在解析不了，返回原始字符串
                return time_str
        except:
            return time_str