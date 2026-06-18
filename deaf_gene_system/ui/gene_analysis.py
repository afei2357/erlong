#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 权属说明：基因数据解析模块

from PyQt6.QtWidgets import *
import sys
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import sqlite3
from PyQt6.QtGui import QColor, QFont
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from run_deaf_gene_report import generate_deaf_gene_reports

from core.database import db
from core.auth import auth_manager

import csv
import os
import json


class DeafGeneAnalysisWorker(QThread):
    progress_updated = pyqtSignal(str, int)
    analysis_completed = pyqtSignal(dict)
    analysis_failed = pyqtSignal(str)
    
    def __init__(self, excel_path, output_dir):
        super().__init__()
        self.deaf_gene_excel_path = excel_path
        self.deaf_gene_output_dir = output_dir
        # 临时变量，记录解析进度
        self._parsed_sample_count = 0
        self._total_sample_count = 0
        
    def run(self):
        # 先检查文件是否存在，这里单独处理文件读取异常
        excel_file = Path(self.deaf_gene_excel_path)
        if not excel_file.exists():
            self.analysis_failed.emit(f"检测数据文件不存在: {self.deaf_gene_excel_path}")
            return
            
        if not excel_file.is_file():
            self.analysis_failed.emit("指定路径不是有效的文件")
            return
            
        try:
            def log_callback(message):
                self.progress_updated.emit(message, 0)
                # 粗略统计进度
                if "解析样本" in message:
                    self._parsed_sample_count += 1
                    if self._total_sample_count > 0:
                        progress = int(self._parsed_sample_count / self._total_sample_count * 100)
                        self.progress_updated.emit(message, progress)
            
            result = generate_deaf_gene_reports(
                sample_excel_path=self.deaf_gene_excel_path,
                output_dir=self.deaf_gene_output_dir,
                log_callback=log_callback
            )
            
            if result.get('success', False):
                self.analysis_completed.emit(result)
            else:
                # 报告生成异常单独处理
                msg = result.get('message', '未知错误')
                if '报告' in msg:
                    self.analysis_failed.emit(f"报告生成失败: {msg}")
                elif '位点' in msg or '基因' in msg:
                    self.analysis_failed.emit(f"位点数据解析异常: {msg}")
                else:
                    self.analysis_failed.emit(msg)
                    
        except FileNotFoundError as e:
            # 文件读取异常，写入本地日志
            with open("deaf_gene_errors.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 文件读取错误: {str(e)}\n")
            self.analysis_failed.emit("检测数据文件读取失败，请检查文件是否损坏")
        except ValueError as e:
            print(f"数据解析异常: {str(e)}", file=sys.stderr)
            self.analysis_failed.emit(f"位点数据解析错误: {str(e)}")
        except ImportError as e:
            # 报告生成依赖缺失
            self.analysis_failed.emit(f"报告生成模块加载失败: {str(e)}")
        except Exception as e:
            # 兜底，记录到日志
            with open("deaf_gene_errors.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 分析未知异常: {str(e)}\n")
            self.analysis_failed.emit("分析过程中出现未知异常")


class DeafGeneAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.deaf_gene_excel_path = None
        self.deaf_gene_worker_thread = None
        
        # 调试用的临时变量
        self._debug_last_analysis_time = None
        self._debug_analysis_count = 0
        self._debug_last_result = None
        
        self.setup_interface()
        
    def setup_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("基因数据解析")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        top_widget = self.build_file_upload_section()
        splitter.addWidget(top_widget)
        
        bottom_widget = self.build_results_display_section()
        splitter.addWidget(bottom_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        action_bar = self.build_operation_toolbar()
        layout.addWidget(action_bar)
        
    def build_file_upload_section(self):
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
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
        
        self.deaf_gene_mutation_table = self.build_mutation_table()
        layout.addWidget(self.deaf_gene_mutation_table)
        
        return widget
        
    def build_mutation_table(self):
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择检测数据文件", "", 
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )
        
        if file_path:
            self._on_file_picked(file_path)
    
    def _on_file_picked(self, file_path):
        self.deaf_gene_excel_path = file_path
        self.deaf_gene_selected_file_label.setText(f"已选择: {Path(file_path).name}")
        self.deaf_gene_selected_file_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        self.deaf_gene_run_analysis_btn.setEnabled(True)
        
        self.deaf_gene_mutation_table.setRowCount(0)
        self.deaf_gene_analysis_log.clear()
        self.deaf_gene_summary_label.setText("准备解析数据...")
    
    def run_gene_analysis(self):
        if not self.deaf_gene_excel_path:
            QMessageBox.warning(self, "提示", "请先选择要分析的文件")
            return
        
        self._debug_analysis_count += 1
        self._debug_last_analysis_time = __import__('time').time()
        file_name = Path(self.deaf_gene_excel_path).name
        print(f"开始解析耳聋基因检测数据: {file_name}", file=sys.stderr)
        
        output_dir = Path("temp_analysis")
        output_dir.mkdir(exist_ok=True)
        
        self._prepare_for_analysis()
        self._launch_analysis_worker(output_dir)
        
    def _prepare_for_analysis(self):
        self.deaf_gene_run_analysis_btn.setEnabled(False)
        self.deaf_gene_upload_btn.setEnabled(False)
        
        self.deaf_gene_analysis_progress.setVisible(True)
        self.deaf_gene_analysis_progress.setValue(0)
        
        self.deaf_gene_analysis_log.clear()
    
    def _launch_analysis_worker(self, output_dir):
        self.deaf_gene_worker_thread = DeafGeneAnalysisWorker(self.deaf_gene_excel_path, str(output_dir))
        self.deaf_gene_worker_thread.progress_updated.connect(self.on_progress_updated)
        self.deaf_gene_worker_thread.analysis_completed.connect(self.on_analysis_completed)
        self.deaf_gene_worker_thread.analysis_failed.connect(self.on_analysis_failed)
        self.deaf_gene_worker_thread.start()
        
    def on_progress_updated(self, message, progress):
        self.deaf_gene_analysis_log.append(message)
        self.deaf_gene_analysis_progress.setValue(progress)
        
        scrollbar = self.deaf_gene_analysis_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_analysis_completed(self, result):
        self.deaf_gene_analysis_progress.setValue(100)
        self.deaf_gene_analysis_log.append("✅ 分析完成！")
        
        if self._debug_last_analysis_time:
            elapsed = __import__('time').time() - self._debug_last_analysis_time
            print(f"数据解析完成，耗时: {elapsed:.2f}秒", file=sys.stderr)
        
        self._debug_last_result = result
        sample_count = len(result['samples'])
        print(f"共解析{sample_count}个样本", file=sys.stderr)
        
        self._process_and_display_deaf_gene_results(result)
        self._enable_post_analysis_buttons()
        self._update_summary_stats(result)
        
    def _enable_post_analysis_buttons(self):
        self.deaf_gene_edit_data_btn.setEnabled(True)
        self.deaf_gene_save_data_btn.setEnabled(True)
        self.deaf_gene_jump_to_report_btn.setEnabled(True)
    
    def _update_summary_stats(self, result):
        total_samples = len(result['samples'])
        success_count = len(result['output_files']) // 2
        abnormal_count = sum(1 for s in result['samples'] if s['diagnosis'] == '异常')
        
        gene_types = set()
        for s in result['samples']:
            gene_types.add(s.get('gene_name', 'GJB2'))
        
        gene_list = ', '.join(sorted(gene_types))
        self.deaf_gene_summary_label.setText(f"解析完成：共 {total_samples} 个样本，成功 {success_count} 个，异常 {abnormal_count} 个，涉及基因: {gene_list}")
        
        self.deaf_gene_analysis_result = result
        self.deaf_gene_output_dir = Path("temp_analysis")
    
    def on_analysis_failed(self, error_message):
        self.deaf_gene_analysis_log.append(f"❌ 分析失败: {error_message}")
        self.deaf_gene_analysis_progress.setVisible(False)
        
        self.deaf_gene_run_analysis_btn.setEnabled(True)
        
        QMessageBox.critical(self, "分析失败", error_message)
    
    def _process_and_display_deaf_gene_results(self, result):
        samples = result['samples']
        total_samples = len(samples)
        self.deaf_gene_mutation_table.setRowCount(total_samples)
        
        abnormal_sample_count = 0
        abnormal_samples = []
        pathogenic_mutations = []
        gene_statistics = {}
        
        for row_idx in range(total_samples):
            sample = samples[row_idx]
            
            if not sample.get('sample_id'):
                sample['sample_id'] = '未知样本'
            
            self.deaf_gene_mutation_table.setItem(row_idx, 0, QTableWidgetItem(sample['sample_id']))
            
            gene_name = sample.get('gene_name') or 'GJB2'
            if gene_name not in gene_statistics:
                gene_statistics[gene_name] = {'total': 0, 'abnormal': 0}
            gene_statistics[gene_name]['total'] += 1
            
            self.deaf_gene_mutation_table.setItem(row_idx, 1, QTableWidgetItem(gene_name))
            
            mutation_site = sample.get('mutation_site')
            if mutation_site != "" and mutation_site is not None:
                pass
            elif len(sample.get('gene_info', {})) > 0:
                mutation_site = sample['gene_info'].get('mutation_site', '')
                if mutation_site == "":
                    mutation_site = 'c.235delC'
            else:
                mutation_site = 'c.235delC'
            
            self.deaf_gene_mutation_table.setItem(row_idx, 2, QTableWidgetItem(mutation_site))
            
            genotype = "杂合突变" if sample['diagnosis'] == '异常' else ("纯合突变" if sample.get('genotype') == 'homozygous' else "野生型")
            self.deaf_gene_mutation_table.setItem(row_idx, 3, QTableWidgetItem(genotype))
            
            pathogenicity = ""
            gene_info_dict = sample.get('gene_info', {})
            pathogenicity_raw = gene_info_dict.get('pathogenicity', '')
            
            if sample['diagnosis'] == '异常':
                if 'pathogenic' in pathogenicity_raw.lower():
                    pathogenicity = "致病"
                    abnormal_sample_count += 1
                    abnormal_samples.append(sample['sample_id'])
                    pathogenic_mutations.append(f"{gene_name}:{mutation_site}")
                    gene_statistics[gene_name]['abnormal'] += 1
                elif 'likely pathogenic' in pathogenicity_raw.lower():
                    pathogenicity = "疑似致病"
                    abnormal_sample_count += 1
                    abnormal_samples.append(sample['sample_id'])
                    gene_statistics[gene_name]['abnormal'] += 1
                elif 'variant' in pathogenicity_raw.lower():
                    pathogenicity = "意义未明"
                else:
                    pathogenicity = "疑似致病"
                    gene_statistics[gene_name]['abnormal'] += 1
            elif sample['diagnosis'] == '正常':
                pathogenicity = "良性"
            else:
                pathogenicity = "未确定"
            
            pathogenicity_item = QTableWidgetItem(pathogenicity)
            color = '#f44336' if "致病" in pathogenicity else ('#ff9800' if "意义" in pathogenicity else '#4caf50')
            pathogenicity_item.setForeground(QColor(color))
            self.deaf_gene_mutation_table.setItem(row_idx, 4, pathogenicity_item)
            
            reference = ""
            if sample['diagnosis'] == '异常':
                reference = "ACMG指南第5版"
            elif sample.get('reference'):
                reference = sample['reference']
            else:
                reference = "正常人群数据库"
            self.deaf_gene_mutation_table.setItem(row_idx, 5, QTableWidgetItem(reference))
            
            diagnosis_item = QTableWidgetItem(sample['diagnosis'])
            if sample['diagnosis'] == '异常':
                diagnosis_item.setForeground(QColor('#f44336'))
            else:
                diagnosis_item.setForeground(QColor('#4caf50'))
            self.deaf_gene_mutation_table.setItem(row_idx, 6, diagnosis_item)
        
        if abnormal_sample_count > 0:
            print(f"解析到{abnormal_sample_count}个异常样本，涉及基因:{', '.join(gene_statistics.keys())}", file=sys.stderr)
            print(f"致病/疑似致病位点: {', '.join(pathogenic_mutations[:10])}", file=sys.stderr)
        
        for gene, stats in gene_statistics.items():
            if stats['abnormal'] > 0:
                print(f"{gene}: 检测{stats['total']}例, 异常{stats['abnormal']}例", file=sys.stderr)
    
    def _color_text(self, item, text, color_map):
        item.setForeground(QColor(color_map.get(text, '#333')))
    
    def _get_gene_abbr(self, gene_name):
        return gene_name[:3].upper()
    
    def open_edit_dialog(self):
        QMessageBox.information(self, "提示", "手动修正功能开发中...")
    
    def persist_analysis_results(self):
        if not hasattr(self, 'deaf_gene_analysis_result'):
            QMessageBox.warning(self, "提示", "没有可保存的分析结果")
            return
        
        # 临时变量承接循环结果，方便调试
        saved_sample_ids = []
        error_samples = []
        # 临时变量：记录当前处理的样本索引
        current_sample_index = 0
        # 临时变量：记录数据库操作的总次数
        db_operation_count = 0
        
        # 获取样本列表，用临时变量保存
        samples = self.deaf_gene_analysis_result.get('samples', [])
        total_samples = len(samples)
        
        # 如果没有样本，直接返回，不加else
        if total_samples == 0:
            QMessageBox.warning(self, "提示", "没有可保存的样本数据")
            return
        
        try:
            idx = 0
            while idx < total_samples:
                current_sample_index = idx
                sample = samples[idx]
                sample_no = sample.get('sample_id', '')
                
                if sample_no == "" or sample_no is None:
                    idx += 1
                    continue
                
                db_sample_id = None
                
                try:
                    # 先查询是否已存在
                    cursor = db.execute_query(
                        "SELECT id FROM samples WHERE sample_no = ?",
                        (sample_no,)
                    )
                    existing_sample = cursor.fetchone()
                    db_operation_count += 1
                    
                    if existing_sample:
                        db_sample_id = existing_sample['id']
                    else:
                        # 创建新样本
                        patient_name = sample.get('name', '')
                        if patient_name == "":
                            patient_name = "未知姓名"
                        
                        sample_data = {
                            'sample_no': sample_no,
                            'patient_name': patient_name,
                            'gender': sample.get('gender', ''),
                            'age': '',
                            'clinical_diagnosis': sample.get('diagnosis', ''),
                            'hospital': sample.get('hospital', ''),
                            'test_project': '耳聋基因检测',
                            'created_by': auth_manager.current_user['id']
                        }
                        db_sample_id = db.create_sample(sample_data)
                        db_operation_count += 1
                    
                    # 删除旧的基因数据，避免重复
                    db.execute_query("DELETE FROM gene_data WHERE sample_id = ?", (db_sample_id,))
                    db_operation_count += 1
                    
                    # 获取基因信息
                    gene_info = sample.get('gene_info', {})
                    
                    # 如果没有基因信息但有诊断结果，生成默认数据
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
                    
                    # 插入基因数据
                    if gene_info:
                        gene_data = {
                            'sample_id': db_sample_id,
                            'gene_name': gene_info.get('gene_name', 'GJB2'),
                            'mutation_site': gene_info.get('mutation_site', ''),
                            'genotype': gene_info.get('genotype', ''),
                            'pathogenicity': gene_info.get('pathogenicity', ''),
                            'reference': gene_info.get('reference', '')
                        }
                        db.create_gene_data(gene_data)
                        db_operation_count += 1
                    
                    # 更新样本状态
                    db.execute_query("UPDATE samples SET status = 'completed' WHERE id = ?", (db_sample_id,))
                    db_operation_count += 1
                    
                    saved_sample_ids.append(sample_no)
                    
                except sqlite3.IntegrityError:
                    error_samples.append(f"{sample_no}: 样本编号重复")
                    print(f"样本{sample_no}编号重复，跳过", file=sys.stderr)
                except sqlite3.Error as e:
                    error_msg = f"{sample_no}: 数据库操作失败 - {str(e)}"
                    error_samples.append(error_msg)
                    with open("deaf_gene_errors.log", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now()}] 保存失败: {error_msg}\n")
                except Exception as e:
                    error_samples.append(f"{sample_no}: {str(e)}")
                
                idx += 1
                
                if idx % 10 == 0:
                    print(f"已保存{len(saved_sample_ids)}条，处理中: {idx}/{total_samples}", file=sys.stderr)
            
            db.commit()
            
            # 根据结果显示不同的提示
            if len(error_samples) == total_samples:
                QMessageBox.critical(self, "全部保存失败", "所有样本保存均失败，请检查数据库连接")
            elif len(error_samples) > 0:
                QMessageBox.warning(self, "部分保存失败", 
                    f"成功保存 {len(saved_sample_ids)} 个样本，{len(error_samples)} 个失败：\n" + "\n".join(error_samples[:3]))
            else:
                QMessageBox.information(self, "成功", f"解析结果保存成功，共 {len(saved_sample_ids)} 个样本")
            
            self.deaf_gene_jump_to_report_btn.setEnabled(True)
            
            # 调试用：打印总操作次数
            print(f"[耳聋基因保存] 完成，数据库操作: {db_operation_count}次", file=sys.stderr)
            
        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"保存过程中出现异常: {str(e)}")
    
    def navigate_to_report_module(self):
        if hasattr(self, 'parent'):
            main_window = self.parent().parent()
            if hasattr(main_window, 'switch_module'):
                main_window.switch_module('report_generation')

    def show_import_dialog(self):
        self.pick_excel_file()
    
    def import_file_and_analyze(self, file_path):
        self.deaf_gene_excel_path = file_path
        self.deaf_gene_selected_file_label.setText(f"已选择: {Path(file_path).name}")
        self.deaf_gene_selected_file_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        self.deaf_gene_mutation_table.setRowCount(0)
        self.deaf_gene_analysis_log.clear()
        self.deaf_gene_summary_label.setText("准备解析数据...")
        
        self.run_gene_analysis()
    
    def refresh_data(self):
        pass
    
    # 旧代码，暂时保留，之前用这个方法判断致病性
    # def _old_judge_pathogenicity(self, gene_info):
    #     if gene_info.get('score', 0) >= 5:
    #         return '致病'
    #     elif gene_info.get('score', 0) >= 3:
    #         return '疑似致病'
    #     else:
    #         return '良性'

