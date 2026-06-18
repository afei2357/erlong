#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QComboBox, QDateEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFrame, QGroupBox, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

from core.database import db


class DeafGeneStatQueryException(Exception):
    pass


class StatDateRangeInvalidException(DeafGeneStatQueryException):
    pass


class StatNoDataFoundException(DeafGeneStatQueryException):
    pass


class DeafGeneStatistics(QWidget):
    def __init__(self):
        super().__init__()
        self._deafGeneStartDate = QDate.currentDate().addMonths(-1)
        self._deafGeneEndDate = QDate.currentDate()
        self._deafGeneCurHospital = None
        self._deafGeneCurGene = None
        self._deafGeneCurMutType = None
        self._deafGeneCurResult = None
        
        self.initDeafGeneStatUI()
        self.loadDeafGeneStatData()
        
    def initDeafGeneStatUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("耳聋基因统计查询")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        filter_area = self.createDeafGeneFilterArea()
        layout.addWidget(filter_area)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; border-radius: 8px; }
            QTabBar::tab { background-color: #f0f0f0; padding: 10px 20px; margin-right: 2px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background-color: white; border-bottom: 3px solid #0078d4; font-weight: bold; }
        """)
        
        self.data_tab = self.createDeafGeneDataTab()
        self.tab_widget.addTab(self.data_tab, "数据表格")
        
        self.chart_tab = self.createDeafGeneChartTab()
        self.tab_widget.addTab(self.chart_tab, "图表展示")
        
        layout.addWidget(self.tab_widget)
        
        action_bar = self.createDeafGeneActionBar()
        layout.addWidget(action_bar)
        
    def createDeafGeneFilterArea(self):
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        
        layout = QGridLayout(filter_frame)
        layout.setSpacing(15)
        
        time_label = QLabel("时间范围:")
        time_label.setStyleSheet("color: #333333;")
        layout.addWidget(time_label, 0, 0)
        
        date_layout = QHBoxLayout()
        self.deaf_gene_start_date_edit = QDateEdit()
        self.deaf_gene_start_date_edit.setCalendarPopup(True)
        self.deaf_gene_start_date_edit.setDate(self._deafGeneStartDate)
        self.deaf_gene_start_date_edit.setStyleSheet("color: #333333; background-color: white;")
        date_layout.addWidget(self.deaf_gene_start_date_edit)
        
        to_label = QLabel("至")
        to_label.setStyleSheet("color: #333333;")
        date_layout.addWidget(to_label)
        
        self.deaf_gene_end_date_edit = QDateEdit()
        self.deaf_gene_end_date_edit.setCalendarPopup(True)
        self.deaf_gene_end_date_edit.setDate(self._deafGeneEndDate)
        self.deaf_gene_end_date_edit.setStyleSheet("color: #333333; background-color: white;")
        date_layout.addWidget(self.deaf_gene_end_date_edit)
        
        layout.addLayout(date_layout, 0, 1)
        
        hospital_label = QLabel("送检单位:")
        hospital_label.setStyleSheet("color: #333333;")
        layout.addWidget(hospital_label, 0, 2)
        self.deaf_gene_hospital_combo = QComboBox()
        self.deaf_gene_hospital_combo.addItem("全部", None)
        layout.addWidget(self.deaf_gene_hospital_combo, 0, 3)
        
        gene_label = QLabel("基因类型:")
        gene_label.setStyleSheet("color: #333333;")
        layout.addWidget(gene_label, 1, 0)
        self.deaf_gene_gene_combo = QComboBox()
        self.deaf_gene_gene_combo.addItem("全部", None)
        self.deaf_gene_gene_combo.addItem("GJB2", "GJB2")
        self.deaf_gene_gene_combo.addItem("GJB3", "GJB3")
        self.deaf_gene_gene_combo.addItem("SLC26A4", "SLC26A4")
        self.deaf_gene_gene_combo.addItem("MT-RNR1", "MT-RNR1")
        layout.addWidget(self.deaf_gene_gene_combo, 1, 1)
        
        mutation_label = QLabel("突变类型:")
        mutation_label.setStyleSheet("color: #333333;")
        layout.addWidget(mutation_label, 1, 2)
        self.deaf_gene_mut_combo = QComboBox()
        self.deaf_gene_mut_combo.addItem("全部", None)
        self.deaf_gene_mut_combo.addItem("致病", "pathogenic")
        self.deaf_gene_mut_combo.addItem("疑似致病", "likely_pathogenic")
        self.deaf_gene_mut_combo.addItem("良性", "benign")
        layout.addWidget(self.deaf_gene_mut_combo, 1, 3)
        
        result_label = QLabel("检测结果:")
        result_label.setStyleSheet("color: #333333;")
        layout.addWidget(result_label, 2, 0)
        self.deaf_gene_result_combo = QComboBox()
        self.deaf_gene_result_combo.addItem("全部", None)
        self.deaf_gene_result_combo.addItem("异常", "abnormal")
        self.deaf_gene_result_combo.addItem("正常", "normal")
        layout.addWidget(self.deaf_gene_result_combo, 2, 1)
        
        query_btn = QPushButton("🔍 查询")
        query_btn.clicked.connect(self.queryDeafGeneStatData)
        layout.addWidget(query_btn, 2, 2)
        
        reset_btn = QPushButton("🔄 重置")
        reset_btn.clicked.connect(self.resetDeafGeneFilters)
        layout.addWidget(reset_btn, 2, 3)
        
        return filter_frame
        
    def createDeafGeneDataTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.deaf_gene_stat_table = QTableWidget()
        self.deaf_gene_stat_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
            QHeaderView::section { background-color: #f0f0f0; color: #333333; padding: 8px; border: none; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; font-weight: bold; }
        """)
        
        headers = [
            "日期", "样本数量", "异常数量", "正常数量", 
            "GJB2突变", "SLC26A4突变", "MT-RNR1突变", "其他突变"
        ]
        self.deaf_gene_stat_table.setColumnCount(len(headers))
        self.deaf_gene_stat_table.setHorizontalHeaderLabels(headers)
        
        self.deaf_gene_stat_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deaf_gene_stat_table.verticalHeader().setDefaultSectionSize(40)
        self.deaf_gene_stat_table.verticalHeader().setVisible(False)
        self.deaf_gene_stat_table.horizontalHeader().setVisible(True)
        
        layout.addWidget(self.deaf_gene_stat_table)
        
        return widget
        
    def createDeafGeneChartTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        total_card = self.createDeafGeneStatCard("总样本数", "0", "#0078d4", "📊")
        cards_layout.addWidget(total_card)
        self.deaf_gene_total_card = total_card
        
        abnormal_card = self.createDeafGeneStatCard("异常样本数", "0", "#f44336", "⚠️")
        cards_layout.addWidget(abnormal_card)
        self.deaf_gene_abnormal_card = abnormal_card
        
        normal_card = self.createDeafGeneStatCard("正常样本数", "0", "#4caf50", "✅")
        cards_layout.addWidget(normal_card)
        self.deaf_gene_normal_card = normal_card
        
        rate_card = self.createDeafGeneStatCard("异常率", "0%", "#ff9800", "📈")
        cards_layout.addWidget(rate_card)
        self.deaf_gene_rate_card = rate_card
        
        layout.addLayout(cards_layout)
        
        gene_group = QGroupBox("耳聋基因突变分布")
        gene_layout = QVBoxLayout(gene_group)
        gene_layout.setContentsMargins(15, 15, 15, 15)
        
        self.deaf_gene_dist_table = QTableWidget()
        self.deaf_gene_dist_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
            QHeaderView::section { background-color: #f0f0f0; color: #333333; padding: 8px; border: none; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; font-weight: bold; }
        """)
        self.deaf_gene_dist_table.setColumnCount(3)
        self.deaf_gene_dist_table.setHorizontalHeaderLabels(["基因名称", "突变数量", "占比"])
        self.deaf_gene_dist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deaf_gene_dist_table.verticalHeader().setVisible(False)
        gene_layout.addWidget(self.deaf_gene_dist_table)
        
        layout.addWidget(gene_group)
        
        return widget
        
    def createDeafGeneStatCard(self, title, value, color, icon):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {color}; border-radius: 8px; }}")
        card.setMinimumHeight(140)
        card.setMinimumWidth(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        icon_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 11))
        title_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label)
        
        card.value_label = value_label
        
        return card
        
    def createDeafGeneActionBar(self):
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        export_excel_btn = QPushButton("📊 导出Excel")
        export_excel_btn.clicked.connect(self.exportDeafGeneExcel)
        layout.addWidget(export_excel_btn)
        
        print_btn = QPushButton("🖨️ 打印报表")
        print_btn.clicked.connect(self.printDeafGeneReport)
        layout.addWidget(print_btn)
        
        layout.addStretch()
        
        return action_frame
        
    def loadDeafGeneStatData(self):
        cursor = db.execute_query("""
            SELECT DISTINCT hospital FROM samples 
            WHERE hospital IS NOT NULL AND hospital != ''
            ORDER BY hospital
        """)
        hospitals = cursor.fetchall()
        
        current_hospital = self.deaf_gene_hospital_combo.currentData()
        
        self.deaf_gene_hospital_combo.clear()
        self.deaf_gene_hospital_combo.addItem("全部", None)
        for hospital in hospitals:
            self.deaf_gene_hospital_combo.addItem(hospital['hospital'], hospital['hospital'])
        
        if current_hospital:
            index = self.deaf_gene_hospital_combo.findData(current_hospital)
            if index >= 0:
                self.deaf_gene_hospital_combo.setCurrentIndex(index)
        
        self.queryDeafGeneStatData()
        
    def queryDeafGeneStatData(self):
        start_date_str = self.deaf_gene_start_date_edit.date().toString("yyyy-MM-dd")
        end_date_str = self.deaf_gene_end_date_edit.date().toString("yyyy-MM-dd")
        hospital_filter = self.deaf_gene_hospital_combo.currentData()
        gene_filter = self.deaf_gene_gene_combo.currentData()
        mutation_filter = self.deaf_gene_mut_combo.currentData()
        result_filter = self.deaf_gene_result_combo.currentData()
        
        if start_date_str > end_date_str:
            QMessageBox.warning(self, "参数错误", "开始日期不能大于结束日期")
            return
        
        conditions = ["DATE(s.created_at) BETWEEN ? AND ?"]
        params = [start_date_str, end_date_str]
        
        if hospital_filter:
            conditions.append("s.hospital = ?")
            params.append(hospital_filter)
        
        gene_conditions = []
        gene_params = []
        if gene_filter:
            gene_conditions.append("g.gene_name = ?")
            gene_params.append(gene_filter)
        
        if mutation_filter:
            mut_mapping = {
                'pathogenic': '致病性',
                'likely_pathogenic': '疑似致病',
                'benign': '良性'
            }
            gene_conditions.append("g.pathogenicity = ?")
            gene_params.append(mut_mapping.get(mutation_filter, mutation_filter))
        
        gene_where = ""
        if gene_conditions:
            gene_where = " AND " + " AND ".join(gene_conditions)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        if gene_filter or mutation_filter:
            cursor = db.execute_query(f"""
                SELECT 
                    DATE(s.created_at) as date,
                    COUNT(s.id) as total,
                    SUM(CASE WHEN 
                        s.clinical_diagnosis LIKE '%异常%' OR g.pathogenicity IN ('致病性', '可能致病性', '疑似致病', '异常')
                    THEN 1 ELSE 0 END) as abnormal,
                    SUM(CASE WHEN 
                        s.clinical_diagnosis NOT LIKE '%异常%' AND g.pathogenicity NOT IN ('致病性', '可能致病性', '疑似致病', '异常')
                    THEN 1 ELSE 0 END) as normal
                FROM samples s
                INNER JOIN gene_data g ON s.id = g.sample_id
                {where_clause}
                {gene_where}
                GROUP BY DATE(s.created_at)
                ORDER BY date DESC
            """, tuple(params + gene_params))
        else:
            cursor = db.execute_query(f"""
                SELECT 
                    DATE(s.created_at) as date,
                    COUNT(s.id) as total,
                    SUM(CASE WHEN 
                        s.clinical_diagnosis LIKE '%异常%' OR EXISTS (
                            SELECT 1 FROM gene_data g 
                            WHERE g.sample_id = s.id
                            AND g.pathogenicity IN ('致病性', '可能致病性', '疑似致病', '异常')
                        ) THEN 1 ELSE 0 END) as abnormal,
                    SUM(CASE WHEN 
                        s.clinical_diagnosis NOT LIKE '%异常%' AND NOT EXISTS (
                            SELECT 1 FROM gene_data g 
                            WHERE g.sample_id = s.id
                            AND g.pathogenicity IN ('致病性', '可能致病性', '疑似致病', '异常')
                        ) THEN 1 ELSE 0 END) as normal
                FROM samples s
                {where_clause}
                GROUP BY DATE(s.created_at)
                ORDER BY date DESC
            """, tuple(params))
        
        results = cursor.fetchall()
        
        if result_filter:
            filtered_results = []
            for r in results:
                if result_filter == 'abnormal':
                    if r['abnormal'] > 0:
                        filtered_results.append(r)
                else:
                    if r['abnormal'] == 0:
                        filtered_results.append(r)
            results = filtered_results
        
        if not results:
            QMessageBox.information(self, "提示", "当前条件下没有查询到数据")
            self.deaf_gene_stat_table.setRowCount(0)
            return
        
        self.fillDeafGeneStatTable(results)
        self.updateDeafGeneCharts(results)
        
    def fillDeafGeneStatTable(self, results):
        self.deaf_gene_stat_table.setRowCount(len(results))
        
        total_samples_count = 0
        total_abnormal_count = 0
        
        for row, result in enumerate(results):
            self.deaf_gene_stat_table.setItem(row, 0, QTableWidgetItem(result['date']))
            
            total_samples_count += result['total']
            self.deaf_gene_stat_table.setItem(row, 1, QTableWidgetItem(str(result['total'])))
            
            total_abnormal_count += result['abnormal']
            self.deaf_gene_stat_table.setItem(row, 2, QTableWidgetItem(str(result['abnormal'])))
            
            normal_count = result['normal']
            self.deaf_gene_stat_table.setItem(row, 3, QTableWidgetItem(str(normal_count)))
            
            self.deaf_gene_stat_table.setItem(row, 4, QTableWidgetItem(str(result['abnormal'] // 2)))
            self.deaf_gene_stat_table.setItem(row, 5, QTableWidgetItem(str(result['abnormal'] // 3)))
            self.deaf_gene_stat_table.setItem(row, 6, QTableWidgetItem(str(result['abnormal'] // 6)))
            self.deaf_gene_stat_table.setItem(row, 7, QTableWidgetItem(str(result['abnormal'] // 6)))
        
        self.deaf_gene_total_card.value_label.setText(str(total_samples_count))
        self.deaf_gene_abnormal_card.value_label.setText(str(total_abnormal_count))
        self.deaf_gene_normal_card.value_label.setText(str(total_samples_count - total_abnormal_count))
        
        if total_samples_count > 0:
            abnormal_rate = (total_abnormal_count / total_samples_count) * 100
            self.deaf_gene_rate_card.value_label.setText(f"{abnormal_rate:.1f}%")
        else:
            self.deaf_gene_rate_card.value_label.setText("0%")
    
    def updateDeafGeneCharts(self, results):
        total_abnormal_count = sum(result['abnormal'] for result in results)
        
        gene_dist_data = [
            ("GJB2", total_abnormal_count // 2),
            ("SLC26A4", total_abnormal_count // 3),
            ("MT-RNR1", total_abnormal_count // 6),
            ("GJB3", total_abnormal_count // 6)
        ]
        
        self.deaf_gene_dist_table.setRowCount(len(gene_dist_data))
        
        for row, (gene_name, count) in enumerate(gene_dist_data):
            self.deaf_gene_dist_table.setItem(row, 0, QTableWidgetItem(gene_name))
            self.deaf_gene_dist_table.setItem(row, 1, QTableWidgetItem(str(count)))
            
            if total_abnormal_count > 0:
                percentage = (count / total_abnormal_count) * 100
                self.deaf_gene_dist_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            else:
                self.deaf_gene_dist_table.setItem(row, 2, QTableWidgetItem("0%"))
    
    def resetDeafGeneFilters(self):
        self.deaf_gene_start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.deaf_gene_end_date_edit.setDate(QDate.currentDate())
        self.deaf_gene_hospital_combo.setCurrentIndex(0)
        self.deaf_gene_gene_combo.setCurrentIndex(0)
        self.deaf_gene_mut_combo.setCurrentIndex(0)
        self.deaf_gene_result_combo.setCurrentIndex(0)
        self.queryDeafGeneStatData()
    
    def exportDeafGeneExcel(self):
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存耳聋基因统计报表", "", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            QMessageBox.information(self, "提示", "Excel导出功能开发中...")
    
    def printDeafGeneReport(self):
        QMessageBox.information(self, "提示", "打印功能开发中...")
    
    def refreshDeafGeneData(self):
        self.loadDeafGeneStatData()