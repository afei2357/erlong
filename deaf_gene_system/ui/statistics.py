#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统计查询界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QComboBox, QDateEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFrame, QGroupBox, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from core.database import db


class Statistics(QWidget):
    """统计查询界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_statistics()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("统计查询")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 筛选条件区域
        filter_area = self.create_filter_area()
        layout.addWidget(filter_area)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #0078d4;
                font-weight: bold;
            }
        """)
        
        # 数据表格
        self.data_tab = self.create_data_tab()
        self.tab_widget.addTab(self.data_tab, "数据表格")
        
        # 图表展示
        self.chart_tab = self.create_chart_tab()
        self.tab_widget.addTab(self.chart_tab, "图表展示")
        
        layout.addWidget(self.tab_widget)
        
        # 操作按钮
        action_bar = self.create_action_bar()
        layout.addWidget(action_bar)
        
    def create_filter_area(self):
        """创建筛选条件区域"""
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        
        layout = QGridLayout(filter_frame)
        layout.setSpacing(15)
        
        # 时间范围
        layout.addWidget(QLabel("时间范围:"), 0, 0)
        
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        
        layout.addLayout(date_layout, 0, 1)
        
        # 送检单位
        layout.addWidget(QLabel("送检单位:"), 0, 2)
        self.hospital_filter = QComboBox()
        self.hospital_filter.addItem("全部", None)
        layout.addWidget(self.hospital_filter, 0, 3)
        
        # 基因类型
        layout.addWidget(QLabel("基因类型:"), 1, 0)
        self.gene_filter = QComboBox()
        self.gene_filter.addItem("全部", None)
        self.gene_filter.addItem("GJB2", "GJB2")
        self.gene_filter.addItem("GJB3", "GJB3")
        self.gene_filter.addItem("SLC26A4", "SLC26A4")
        self.gene_filter.addItem("MT-RNR1", "MT-RNR1")
        layout.addWidget(self.gene_filter, 1, 1)
        
        # 突变类型
        layout.addWidget(QLabel("突变类型:"), 1, 2)
        self.mutation_filter = QComboBox()
        self.mutation_filter.addItem("全部", None)
        self.mutation_filter.addItem("致病", "pathogenic")
        self.mutation_filter.addItem("疑似致病", "likely_pathogenic")
        self.mutation_filter.addItem("良性", "benign")
        layout.addWidget(self.mutation_filter, 1, 3)
        
        # 检测结果
        layout.addWidget(QLabel("检测结果:"), 2, 0)
        self.result_filter = QComboBox()
        self.result_filter.addItem("全部", None)
        self.result_filter.addItem("异常", "abnormal")
        self.result_filter.addItem("正常", "normal")
        layout.addWidget(self.result_filter, 2, 1)
        
        # 查询按钮
        query_btn = QPushButton("🔍 查询")
        query_btn.clicked.connect(self.query_data)
        layout.addWidget(query_btn, 2, 2)
        
        # 重置按钮
        reset_btn = QPushButton("🔄 重置")
        reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(reset_btn, 2, 3)
        
        return filter_frame
        
    def create_data_tab(self):
        """创建数据表格标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计表格
        self.stats_table = QTableWidget()
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                gridline-color: #eee;
                color: #333;
            }
            QTableWidget::item {
                padding: 8px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # 设置列
        headers = [
            "日期", "样本数量", "异常数量", "正常数量", 
            "GJB2突变", "SLC26A4突变", "MT-RNR1突变", "其他突变"
        ]
        self.stats_table.setColumnCount(len(headers))
        self.stats_table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 设置行高
        self.stats_table.verticalHeader().setDefaultSectionSize(40)
        self.stats_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.stats_table)
        
        return widget
        
    def create_chart_tab(self):
        """创建图表展示标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 图表区域（这里用简单的统计卡片代替）
        charts_layout = QGridLayout()
        charts_layout.setSpacing(15)
        
        # 总样本数
        total_card = self.create_stat_card("总样本数", "0", "#0078d4", "📊")
        charts_layout.addWidget(total_card, 0, 0)
        self.total_card = total_card
        
        # 异常样本数
        abnormal_card = self.create_stat_card("异常样本数", "0", "#f44336", "⚠️")
        charts_layout.addWidget(abnormal_card, 0, 1)
        self.abnormal_card = abnormal_card
        
        # 正常样本数
        normal_card = self.create_stat_card("正常样本数", "0", "#4caf50", "✅")
        charts_layout.addWidget(normal_card, 0, 2)
        self.normal_card = normal_card
        
        # 异常率
        rate_card = self.create_stat_card("异常率", "0%", "#ff9800", "📈")
        charts_layout.addWidget(rate_card, 0, 3)
        self.rate_card = rate_card
        
        layout.addLayout(charts_layout)
        
        # 基因突变分布
        gene_group = QGroupBox("基因突变分布")
        gene_layout = QVBoxLayout()
        
        self.gene_distribution_table = QTableWidget()
        self.gene_distribution_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                gridline-color: #eee;
                color: #333;
            }
            QTableWidget::item {
                padding: 8px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        self.gene_distribution_table.setColumnCount(3)
        self.gene_distribution_table.setHorizontalHeaderLabels(["基因名称", "突变数量", "占比"])
        self.gene_distribution_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gene_distribution_table.verticalHeader().setVisible(False)
        gene_layout.addWidget(self.gene_distribution_table)
        
        gene_group.setLayout(gene_layout)
        layout.addWidget(gene_group)
        
        return widget
        
    def create_stat_card(self, title, value, color, icon):
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # 标题和图标
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px; color: rgba(255, 255, 255, 0.9);")
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 14px;")
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: white;
            font-size: 36px;
            font-weight: bold;
            margin-top: 10px;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label)
        
        # 保存数值标签引用
        card.value_label = value_label
        
        return card
        
    def create_action_bar(self):
        """创建操作栏"""
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # 导出Excel按钮
        export_excel_btn = QPushButton("📊 导出Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        layout.addWidget(export_excel_btn)
        
        # 打印报表按钮
        print_btn = QPushButton("🖨️ 打印报表")
        print_btn.clicked.connect(self.print_report)
        layout.addWidget(print_btn)
        
        layout.addStretch()
        
        return action_frame
        
    def load_statistics(self):
        """加载统计数据"""
        try:
            # 加载送检单位列表
            cursor = db.execute_query("""
                SELECT DISTINCT hospital FROM samples 
                WHERE hospital IS NOT NULL AND hospital != ''
                ORDER BY hospital
            """)
            hospitals = cursor.fetchall()
            
            # 保存当前选择
            current_hospital = self.hospital_filter.currentData()
            
            # 重新填充送检单位下拉框
            self.hospital_filter.clear()
            self.hospital_filter.addItem("全部", None)
            for hospital in hospitals:
                self.hospital_filter.addItem(hospital['hospital'], hospital['hospital'])
            
            # 恢复选择
            if current_hospital:
                index = self.hospital_filter.findData(current_hospital)
                if index >= 0:
                    self.hospital_filter.setCurrentIndex(index)
            
            # 执行查询
            self.query_data()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载统计数据失败: {str(e)}")
    
    def query_data(self):
        """查询数据"""
        try:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            hospital = self.hospital_filter.currentData()
            gene_name = self.gene_filter.currentData()
            mutation_type = self.mutation_filter.currentData()
            result_status = self.result_filter.currentData()
            
            conditions = []
            params = [start_date, end_date]
            
            conditions.append("DATE(s.created_at) BETWEEN ? AND ?")
            
            if hospital:
                conditions.append("s.hospital = ?")
                params.append(hospital)
            
            where_clause = " WHERE " + " AND ".join(conditions)
            
            gene_conditions = []
            gene_params = []
            
            if gene_name:
                gene_conditions.append("g.gene_name = ?")
                gene_params.append(gene_name)
            
            if mutation_type:
                mapping = {
                    'pathogenic': '致病性',
                    'likely_pathogenic': '可能致病性',
                    'benign': '良性'
                }
                gene_conditions.append("g.pathogenicity = ?")
                gene_params.append(mapping.get(mutation_type, mutation_type))
            
            if result_status:
                if result_status == 'abnormal':
                    gene_conditions.append("g.pathogenicity IN ('致病性', '可能致病性', '异常')")
                else:
                    gene_conditions.append("g.pathogenicity NOT IN ('致病性', '可能致病性', '异常') OR g.pathogenicity IS NULL")
            
            gene_subquery = ""
            if gene_conditions:
                gene_subquery = " AND " + " AND ".join(gene_conditions)
            
            cursor = db.execute_query(f"""
                SELECT 
                    DATE(s.created_at) as date,
                    COUNT(s.id) as total,
                    SUM(CASE WHEN EXISTS (
                        SELECT 1 FROM gene_data g 
                        WHERE g.sample_id = s.id{gene_subquery}
                        AND g.pathogenicity IN ('致病性', '可能致病性', '异常')
                    ) THEN 1 ELSE 0 END) as abnormal,
                    SUM(CASE WHEN NOT EXISTS (
                        SELECT 1 FROM gene_data g 
                        WHERE g.sample_id = s.id{gene_subquery}
                        AND g.pathogenicity IN ('致病性', '可能致病性', '异常')
                    ) THEN 1 ELSE 0 END) as normal
                FROM samples s
                {where_clause}
                GROUP BY DATE(s.created_at)
                ORDER BY date DESC
            """, tuple(params + gene_params))
            
            results = cursor.fetchall()
            
            self.populate_data_table(results)
            
            self.update_charts(results)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询数据失败: {str(e)}")
    
    def populate_data_table(self, results):
        """填充数据表格"""
        self.stats_table.setRowCount(len(results))
        
        total_samples = 0
        total_abnormal = 0
        
        for row, result in enumerate(results):
            # 日期
            self.stats_table.setItem(row, 0, QTableWidgetItem(result['date']))
            
            # 样本数量
            total_samples += result['total']
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(result['total'])))
            
            # 异常数量
            total_abnormal += result['abnormal']
            self.stats_table.setItem(row, 2, QTableWidgetItem(str(result['abnormal'])))
            
            # 正常数量
            normal_count = result['normal']
            self.stats_table.setItem(row, 3, QTableWidgetItem(str(normal_count)))
            
            # 各基因突变数量（这里用模拟数据）
            self.stats_table.setItem(row, 4, QTableWidgetItem(str(result['abnormal'] // 2)))  # GJB2
            self.stats_table.setItem(row, 5, QTableWidgetItem(str(result['abnormal'] // 3)))  # SLC26A4
            self.stats_table.setItem(row, 6, QTableWidgetItem(str(result['abnormal'] // 6)))  # MT-RNR1
            self.stats_table.setItem(row, 7, QTableWidgetItem(str(result['abnormal'] // 6)))  # 其他
        
        # 更新统计卡片
        self.total_card.value_label.setText(str(total_samples))
        self.abnormal_card.value_label.setText(str(total_abnormal))
        self.normal_card.value_label.setText(str(total_samples - total_abnormal))
        
        if total_samples > 0:
            rate = (total_abnormal / total_samples) * 100
            self.rate_card.value_label.setText(f"{rate:.1f}%")
        else:
            self.rate_card.value_label.setText("0%")
    
    def update_charts(self, results):
        """更新图表"""
        # 更新基因突变分布
        total_abnormal = sum(result['abnormal'] for result in results)
        
        gene_data = [
            ("GJB2", total_abnormal // 2),
            ("SLC26A4", total_abnormal // 3),
            ("MT-RNR1", total_abnormal // 6),
            ("GJB3", total_abnormal // 6)
        ]
        
        self.gene_distribution_table.setRowCount(len(gene_data))
        
        for row, (gene_name, count) in enumerate(gene_data):
            self.gene_distribution_table.setItem(row, 0, QTableWidgetItem(gene_name))
            self.gene_distribution_table.setItem(row, 1, QTableWidgetItem(str(count)))
            
            if total_abnormal > 0:
                percentage = (count / total_abnormal) * 100
                self.gene_distribution_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            else:
                self.gene_distribution_table.setItem(row, 2, QTableWidgetItem("0%"))
    
    def reset_filters(self):
        """重置筛选条件"""
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        self.hospital_filter.setCurrentIndex(0)
        self.gene_filter.setCurrentIndex(0)
        self.mutation_filter.setCurrentIndex(0)
        self.result_filter.setCurrentIndex(0)
        self.query_data()
    
    def export_excel(self):
        """导出Excel"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存统计报表", "", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            # 这里实现Excel导出逻辑
            QMessageBox.information(self, "提示", "Excel导出功能开发中...")
    
    def print_report(self):
        """打印报表"""
        QMessageBox.information(self, "提示", "打印功能开发中...")
    
    def refresh_data(self):
        """刷新数据"""
        self.load_statistics()