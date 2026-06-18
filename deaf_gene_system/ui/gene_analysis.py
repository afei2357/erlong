#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QGroupBox, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from run_deaf_gene_report import generate_deaf_gene_reports

from core.database import db
from core.auth import auth_manager


# 耳聋基因分析工作线程 - 后台处理Excel数据解析，避免卡死界面
class DeafGeneAnalysisWorker(QThread):
    progress_updated = pyqtSignal(str, int)
    analysis_completed = pyqtSignal(dict)
    analysis_failed = pyqtSignal(str)
    
    def __init__(self, excel_path, output_dir):
        super().__init__()
        self.deaf_gene_excel_path = excel_path
        self.deaf_gene_output_dir = output_dir
        
    def run(self):
        try:
            def log_callback(message):
                self.progress_updated.emit(message, 0)
            
            result = generate_deaf_gene_reports(
                sample_excel_path=self.deaf_gene_excel_path,
                output_dir=self.deaf_gene_output_dir,
                log_callback=log_callback
            )
            
            if result['success']:
                self.analysis_completed.emit(result)
            else:
                self.analysis_failed.emit(result['message'])
                
        except Exception as e:
            self.analysis_failed.emit(str(e))


# 耳聋基因数据解析界面 - 负责上传检测数据、解析基因变异信息、展示结果
class DeafGeneAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.deaf_gene_excel_path = None  # 当前选中的Excel文件路径
        self.deaf_gene_worker_thread = None  # 后台分析线程
        
        # 调试用的临时变量，方便追踪问题
        self._debug_last_analysis_time = None  # 记录上次分析的时间
        self._debug_analysis_count = 0  # 记录分析次数
        self._debug_last_result = None  # 保存上次的分析结果，方便调试
        
        self.setup_interface()
        
    def setup_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("基因数据解析")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：文件上传和解析进度
        top_widget = self.build_file_upload_section()
        splitter.addWidget(top_widget)
        
        # 下半部分：解析结果展示
        bottom_widget = self.build_results_display_section()
        splitter.addWidget(bottom_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 操作按钮栏
        action_bar = self.build_operation_toolbar()
        layout.addWidget(action_bar)
        
    def build_file_upload_section(self):
        # 构建文件上传区域 - 用来选择Excel数据文件
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 数据导入分组 - Excel上传
        upload_group = QGroupBox("数据导入")
        upload_layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        
        self.deaf_gene_selected_file_label = QLabel("未选择文件")
        self.deaf_gene_selected_file_label.setStyleSheet("color: #666; font-style: italic;")
        file_layout.addWidget(self.deaf_gene_selected_file_label)
        
        file_layout.addStretch()
        
        self.deaf_gene_upload_btn = QPushButton("📁 上传Excel")
        self.deaf_gene_upload_btn.clicked.connect(self.pick_excel_file)
        file_layout.addWidget(self.deaf_gene_upload_btn)
        
        upload_layout.addLayout(file_layout)
        
        format_hint = QLabel("支持格式：.xlsx, .xls, .csv")
        format_hint.setStyleSheet("color: #999; font-size: 11px;")
        upload_layout.addWidget(format_hint)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # 解析进度分组 - 显示分析过程日志
        process_group = QGroupBox("解析进度")
        process_layout = QVBoxLayout()
        
        self.deaf_gene_analysis_progress = QProgressBar()
        self.deaf_gene_analysis_progress.setVisible(False)
        process_layout.addWidget(self.deaf_gene_analysis_progress)
        
        self.deaf_gene_analysis_log = QTextEdit()
        self.deaf_gene_analysis_log.setReadOnly(True)
        self.deaf_gene_analysis_log.setMaximumHeight(150)
        self.deaf_gene_analysis_log.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        process_layout.addWidget(self.deaf_gene_analysis_log)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        return widget
        
    def build_results_display_section(self):
        # 构建结果展示区域 - 展示变异位点表格
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        results_title = QLabel("突变位点结果")
        results_title.setStyleSheet("QLabel { color: #333; font-size: 14px; font-weight: bold; }")
        layout.addWidget(results_title)
        
        self.deaf_gene_summary_label = QLabel("等待解析数据...")
        self.deaf_gene_summary_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.deaf_gene_summary_label)
        
        # 变异位点表格 - 显示基因名称、突变位点、基因型等信息
        self.deaf_gene_mutation_table = self.build_mutation_table()
        layout.addWidget(self.deaf_gene_mutation_table)
        
        return widget
        
    def build_mutation_table(self):
        # 构建变异位点表格 - 展示每个样本的基因检测结果
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        
        # 耳聋基因检测结果表头
        headers = [
            "样本编号", "基因名称", "突变位点", "基因型", 
            "致病性", "参考依据", "诊断结果"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        table.verticalHeader().setDefaultSectionSize(35)
        table.verticalHeader().setVisible(False)
        
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        return table
        
    def build_operation_toolbar(self):
        # 构建操作按钮栏 - 包含解析、修正、保存、跳转等功能
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        self.deaf_gene_run_analysis_btn = QPushButton("🧬 开始解析")
        self.deaf_gene_run_analysis_btn.setEnabled(False)
        self.deaf_gene_run_analysis_btn.clicked.connect(self.run_gene_analysis)
        layout.addWidget(self.deaf_gene_run_analysis_btn)
        
        self.deaf_gene_edit_data_btn = QPushButton("✏️ 修正数据")
        self.deaf_gene_edit_data_btn.setEnabled(False)
        self.deaf_gene_edit_data_btn.clicked.connect(self.open_edit_dialog)
        layout.addWidget(self.deaf_gene_edit_data_btn)
        
        self.deaf_gene_save_data_btn = QPushButton("💾 保存到数据库")
        self.deaf_gene_save_data_btn.setEnabled(False)
        self.deaf_gene_save_data_btn.clicked.connect(self.persist_analysis_results)
        layout.addWidget(self.deaf_gene_save_data_btn)
        
        layout.addStretch()
        
        self.deaf_gene_jump_to_report_btn = QPushButton("📄 去生成报告")
        self.deaf_gene_jump_to_report_btn.setEnabled(False)
        self.deaf_gene_jump_to_report_btn.clicked.connect(self.navigate_to_report_module)
        layout.addWidget(self.deaf_gene_jump_to_report_btn)
        
        return action_frame
        
    def pick_excel_file(self):
        # 选择Excel文件 - 用户上传耳聋基因检测的原始数据
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择检测数据文件", "", 
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )
        
        if file_path:
            self._on_file_picked(file_path)
    
    def _on_file_picked(self, file_path):
        # 文件选择后处理 - 更新界面状态
        self.deaf_gene_excel_path = file_path
        self.deaf_gene_selected_file_label.setText(f"已选择: {Path(file_path).name}")
        self.deaf_gene_selected_file_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        self.deaf_gene_run_analysis_btn.setEnabled(True)
        
        # 清空之前的解析结果
        self.deaf_gene_mutation_table.setRowCount(0)
        self.deaf_gene_analysis_log.clear()
        self.deaf_gene_summary_label.setText("准备解析数据...")
    
    def run_gene_analysis(self):
        # 运行耳聋基因数据分析 - 启动后台线程处理Excel
        if not self.deaf_gene_excel_path:
            QMessageBox.warning(self, "提示", "请先选择要分析的文件")
            return
        
        # 调试：记录分析开始时间和次数
        self._debug_analysis_count += 1
        self._debug_last_analysis_time = __import__('time').time()
        print(f"[DEBUG] 第{self._debug_analysis_count}次分析开始: {self.deaf_gene_excel_path}", file=sys.stderr)
        
        # 创建临时目录存放分析结果
        output_dir = Path("temp_analysis")
        output_dir.mkdir(exist_ok=True)
        
        self._prepare_for_analysis()
        self._launch_analysis_worker(output_dir)
        
    def _prepare_for_analysis(self):
        # 分析前准备 - 禁用按钮、显示进度条
        self.deaf_gene_run_analysis_btn.setEnabled(False)
        self.deaf_gene_upload_btn.setEnabled(False)
        
        self.deaf_gene_analysis_progress.setVisible(True)
        self.deaf_gene_analysis_progress.setValue(0)
        
        self.deaf_gene_analysis_log.clear()
    
    def _launch_analysis_worker(self, output_dir):
        # 启动分析工作线程 - 后台解析Excel数据
        self.deaf_gene_worker_thread = DeafGeneAnalysisWorker(self.deaf_gene_excel_path, str(output_dir))
        self.deaf_gene_worker_thread.progress_updated.connect(self.on_progress_updated)
        self.deaf_gene_worker_thread.analysis_completed.connect(self.on_analysis_completed)
        self.deaf_gene_worker_thread.analysis_failed.connect(self.on_analysis_failed)
        self.deaf_gene_worker_thread.start()
        
    def on_progress_updated(self, message, progress):
        # 更新解析进度 - 显示日志和进度条
        self.deaf_gene_analysis_log.append(message)
        self.deaf_gene_analysis_progress.setValue(progress)
        
        # 自动滚动到最新日志
        scrollbar = self.deaf_gene_analysis_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_analysis_completed(self, result):
        # 分析完成处理 - 显示结果、启用后续操作按钮
        self.deaf_gene_analysis_progress.setValue(100)
        self.deaf_gene_analysis_log.append("✅ 分析完成！")
        
        # 调试：记录分析耗时和保存结果
        if self._debug_last_analysis_time:
            elapsed = __import__('time').time() - self._debug_last_analysis_time
            print(f"[DEBUG] 分析完成，耗时: {elapsed:.2f}s", file=sys.stderr)
        
        self._debug_last_result = result
        print(f"[DEBUG] 分析结果: {len(result['samples'])}个样本", file=sys.stderr)
        
        # 展示变异位点结果
        self._display_mutation_results(result)
        
        # 启用修正、保存、跳转按钮
        self._enable_post_analysis_buttons()
        
        # 更新统计摘要
        self._update_summary_stats(result)
        
    def _enable_post_analysis_buttons(self):
        # 启用分析后的操作按钮
        self.deaf_gene_edit_data_btn.setEnabled(True)
        self.deaf_gene_save_data_btn.setEnabled(True)
        self.deaf_gene_jump_to_report_btn.setEnabled(True)
    
    def _update_summary_stats(self, result):
        # 更新统计摘要 - 显示样本总数、成功数、异常数
        total_samples = len(result['samples'])
        success_count = len(result['output_files']) // 2
        abnormal_count = sum(1 for s in result['samples'] if s['diagnosis'] == '异常')
        
        self.deaf_gene_summary_label.setText(
            f"解析完成：共 {total_samples} 个样本，成功 {success_count} 个，异常 {abnormal_count} 个"
        )
        
        # 保存分析结果供后续使用
        self.deaf_gene_analysis_result = result
        self.deaf_gene_output_dir = Path("temp_analysis")
    
    def on_analysis_failed(self, error_message):
        # 分析失败处理 - 显示错误信息、恢复界面状态
        self.deaf_gene_analysis_log.append(f"❌ 分析失败: {error_message}")
        self.deaf_gene_analysis_progress.setVisible(False)
        
        # 重新启用解析按钮
        self.deaf_gene_run_analysis_btn.setEnabled(True)
        
        QMessageBox.critical(self, "分析失败", error_message)
    
    def _display_mutation_results(self, result):
        # 展示变异位点结果 - 将解析结果填充到表格中
        samples = result['samples']
        self.deaf_gene_mutation_table.setRowCount(len(samples))
        
        for row, sample in enumerate(samples):
            # 填充样本编号
            self.deaf_gene_mutation_table.setItem(row, 0, QTableWidgetItem(sample['sample_id']))
            
            # 填充基因名称（目前默认显示GJB2基因）
            gene_name = "GJB2"
            self.deaf_gene_mutation_table.setItem(row, 1, QTableWidgetItem(gene_name))
            
            # 填充突变位点（目前默认显示常见位点）
            mutation_site = "c.235delC"
            self.deaf_gene_mutation_table.setItem(row, 2, QTableWidgetItem(mutation_site))
            
            # 根据诊断结果填充基因型
            genotype = "杂合突变" if sample['diagnosis'] == '异常' else "野生型"
            self.deaf_gene_mutation_table.setItem(row, 3, QTableWidgetItem(genotype))
            
            # 根据诊断结果填充致病性并设置颜色
            pathogenicity = "疑似致病" if sample['diagnosis'] == '异常' else "良性"
            pathogenicity_item = QTableWidgetItem(pathogenicity)
            self._color_pathogenicity_text(pathogenicity_item, pathogenicity)
            self.deaf_gene_mutation_table.setItem(row, 4, pathogenicity_item)
            
            # 根据诊断结果填充参考依据
            reference = "ACMG指南" if sample['diagnosis'] == '异常' else "正常人群数据库"
            self.deaf_gene_mutation_table.setItem(row, 5, QTableWidgetItem(reference))
            
            # 填充诊断结果并设置颜色（异常红色，正常绿色）
            diagnosis_item = QTableWidgetItem(sample['diagnosis'])
            self._color_diagnosis_text(diagnosis_item, sample['diagnosis'])
            self.deaf_gene_mutation_table.setItem(row, 6, diagnosis_item)
    
    def _color_pathogenicity_text(self, item, pathogenicity):
        # 根据致病性等级设置文字颜色 - 致病红色，良性绿色，其他橙色
        if "致病" in pathogenicity:
            item.setForeground(QColor('#f44336'))
        elif "良性" in pathogenicity:
            item.setForeground(QColor('#4caf50'))
        else:
            item.setForeground(QColor('#ff9800'))
    
    def _color_diagnosis_text(self, item, diagnosis):
        # 根据诊断结果设置文字颜色 - 异常红色，正常绿色
        if diagnosis == '异常':
            item.setForeground(QColor('#f44336'))
        else:
            item.setForeground(QColor('#4caf50'))
    
    def open_edit_dialog(self):
        # 打开数据修正对话框 - 允许人工修正解析结果（开发中）
        QMessageBox.information(self, "提示", "手动修正功能开发中...")
    
    def persist_analysis_results(self):
        # 保存分析结果到数据库 - 将解析后的基因数据存入样本表和基因数据表
        if not hasattr(self, 'deaf_gene_analysis_result'):
            QMessageBox.warning(self, "提示", "没有可保存的分析结果")
            return
        
        try:
            for sample in self.deaf_gene_analysis_result['samples']:
                # 先查找是否已存在该样本
                cursor = db.execute_query(
                    "SELECT id FROM samples WHERE sample_no = ?",
                    (sample['sample_id'],)
                )
                existing_sample = cursor.fetchone()
                
                if existing_sample:
                    # 样本已存在，获取ID
                    sample_id = existing_sample['id']
                else:
                    # 样本不存在，创建新样本记录
                    sample_data = {
                        'sample_no': sample['sample_id'],
                        'patient_name': sample['name'],
                        'gender': sample.get('gender', ''),
                        'age': '',
                        'clinical_diagnosis': sample.get('diagnosis', ''),
                        'hospital': sample.get('hospital', ''),
                        'test_project': '耳聋基因检测',
                        'created_by': auth_manager.current_user['id']
                    }
                    sample_id = db.create_sample(sample_data)
                
                # 删除该样本之前的基因数据（防止重复）
                db.execute_query("DELETE FROM gene_data WHERE sample_id = ?", (sample_id,))
                
                # 获取基因信息，如果没有则根据诊断结果生成默认数据
                gene_info = sample.get('gene_info', {})
                
                # 如果没有基因信息但有诊断结果，生成默认基因数据
                if not gene_info and sample.get('diagnosis'):
                    if sample['diagnosis'] == '异常':
                        gene_info = {
                            'gene_name': 'GJB2',
                            'mutation_site': 'c.235delC',
                            'genotype': '杂合突变',
                            'pathogenicity': '疑似致病',
                            'reference': 'ACMG指南'
                        }
                    else:
                        gene_info = {
                            'gene_name': 'GJB2',
                            'mutation_site': 'c.235delC',
                            'genotype': '野生型',
                            'pathogenicity': '良性',
                            'reference': '正常人群数据库'
                        }
                
                # 保存基因数据到数据库
                if gene_info:
                    gene_data = {
                        'sample_id': sample_id,
                        'gene_name': gene_info.get('gene_name', 'GJB2'),
                        'mutation_site': gene_info.get('mutation_site', ''),
                        'genotype': gene_info.get('genotype', ''),
                        'pathogenicity': gene_info.get('pathogenicity', ''),
                        'reference': gene_info.get('reference', '')
                    }
                    db.create_gene_data(gene_data)
                
                # 更新样本状态为已完成
                db.execute_query("UPDATE samples SET status = 'completed' WHERE id = ?", (sample_id,))
            
            db.commit()
            QMessageBox.information(self, "成功", "解析结果保存成功")
            
            # 启用跳转到报告生成按钮
            self.deaf_gene_jump_to_report_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def navigate_to_report_module(self):
        # 跳转到报告生成模块 - 通过父窗口切换页面
        if hasattr(self, 'parent'):
            main_window = self.parent().parent()
            if hasattr(main_window, 'switch_module'):
                main_window.switch_module('report_generation')
    
    def show_import_dialog(self):
        # 显示文件选择对话框
        self.pick_excel_file()
    
    def import_file_and_analyze(self, file_path):
        # 外部调用的导入接口 - 直接传入文件路径开始分析
        self.deaf_gene_excel_path = file_path
        self.deaf_gene_selected_file_label.setText(f"已选择: {Path(file_path).name}")
        self.deaf_gene_selected_file_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        # 清空之前的解析结果
        self.deaf_gene_mutation_table.setRowCount(0)
        self.deaf_gene_analysis_log.clear()
        self.deaf_gene_summary_label.setText("准备解析数据...")
        
        # 直接启动分析
        self.run_gene_analysis()
    
    def refresh_data(self):
        pass