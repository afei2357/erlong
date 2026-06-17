#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QTextEdit, QComboBox, 
    QTabWidget, QFrame, QGroupBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.database import db
from core.auth import auth_manager
from config import REPORT_STATUS


class ReportReview(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_reports()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("报告审核中心")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; border-radius: 8px; }
            QTabBar::tab { background-color: #f0f0f0; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background-color: white; border-bottom: 3px solid #0078d4; font-weight: bold; }
        """)
        
        self.pending_tab = self.create_pending_tab()
        self.tab_widget.addTab(self.pending_tab, "待审核报告")
        
        self.approved_tab = self.create_approved_tab()
        self.tab_widget.addTab(self.approved_tab, "已审核报告")
        
        self.rejected_tab = self.create_rejected_tab()
        self.tab_widget.addTab(self.rejected_tab, "驳回报告")
        
        layout.addWidget(self.tab_widget)
        
    def create_pending_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.pending_table = self.create_review_table("pending")
        layout.addWidget(self.pending_table)
        
        action_layout = QHBoxLayout()
        
        self.approve_btn = QPushButton("✅ 通过")
        self.approve_btn.clicked.connect(self.approve_report)
        action_layout.addWidget(self.approve_btn)
        
        self.reject_btn = QPushButton("❌ 驳回")
        self.reject_btn.clicked.connect(self.reject_report)
        action_layout.addWidget(self.reject_btn)
        
        self.view_detail_btn = QPushButton("👁️ 查看详情")
        self.view_detail_btn.clicked.connect(self.view_report_detail)
        action_layout.addWidget(self.view_detail_btn)
        
        action_layout.addStretch()
        
        self.batch_approve_btn = QPushButton("✅ 批量通过")
        self.batch_approve_btn.clicked.connect(self.batch_approve_reports)
        action_layout.addWidget(self.batch_approve_btn)
        
        self.batch_reject_btn = QPushButton("❌ 批量驳回")
        self.batch_reject_btn.clicked.connect(self.batch_reject_reports)
        action_layout.addWidget(self.batch_reject_btn)
        
        layout.addLayout(action_layout)
        
        return widget
        
    def create_approved_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.approved_table = self.create_review_table("approved")
        layout.addWidget(self.approved_table)
        
        return widget
        
    def create_rejected_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.rejected_table = self.create_review_table("rejected")
        layout.addWidget(self.rejected_table)
        
        return widget
        
    def create_review_table(self, status):
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        
        headers = [
            "报告编号", "样本编号", "受检者姓名", "送检单位", 
            "模板类型", "提交时间", "审核人", "审核时间", "状态"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        table.verticalHeader().setDefaultSectionSize(40)
        table.verticalHeader().setVisible(False)
        
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        table.table_status = status
        
        return table
        
    def load_reports(self):
        try:
            self.populate_table(self.pending_table, "pending")
            self.populate_table(self.approved_table, "approved")
            self.populate_table(self.rejected_table, "rejected")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载报告数据失败: {str(e)}")
    
    def populate_table(self, table, status):
        try:
            cursor = db.execute_query("""
                SELECT 
                    r.*, 
                    s.sample_no, s.patient_name, s.hospital,
                    u.real_name as reviewer_name
                FROM reports r
                LEFT JOIN samples s ON r.sample_id = s.id
                LEFT JOIN users u ON r.reviewer_id = u.id
                WHERE r.status = ?
                ORDER BY r.created_at DESC
            """, (status,))
            
            rows = cursor.fetchall()
            reports = [dict(row) for row in rows]
            table.setRowCount(len(reports))
            
            for row, report in enumerate(reports):
                table.setItem(row, 0, QTableWidgetItem(report['report_no']))
                table.setItem(row, 1, QTableWidgetItem(report.get('sample_no', '')))
                table.setItem(row, 2, QTableWidgetItem(report.get('patient_name', '')))
                table.setItem(row, 3, QTableWidgetItem(report.get('hospital', '')))
                table.setItem(row, 4, QTableWidgetItem(report.get('template_type', '')))
                table.setItem(row, 5, QTableWidgetItem(self.format_datetime(report.get('created_at', ''))))
                table.setItem(row, 6, QTableWidgetItem(report.get('reviewer_name', '')))
                table.setItem(row, 7, QTableWidgetItem(self.format_datetime(report.get('reviewed_at', ''))))
                
                status_item = QTableWidgetItem(REPORT_STATUS.get(status, status))
                self.set_status_color(status_item, status)
                table.setItem(row, 8, status_item)
                
        except Exception as e:
            print(f"填充表格失败: {e}")
    
    def set_status_color(self, item, status):
        color_map = {
            'pending': QColor('#ff9800'),
            'approved': QColor('#4caf50'),
            'rejected': QColor('#f44336')
        }
        
        color = color_map.get(status, QColor('#666'))
        item.setForeground(color)
    
    def format_datetime(self, datetime_str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str
    
    def get_current_table(self):
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            return self.pending_table
        elif current_index == 1:
            return self.approved_table
        else:
            return self.rejected_table
    
    def approve_report(self):
        table = self.get_current_table()
        if table.table_status != "pending":
            QMessageBox.warning(self, "提示", "只能对待审核的报告进行操作")
            return
        
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要审核的报告")
            return
        
        reply = QMessageBox.question(
            self, '确认通过',
            '确定要通过这个报告吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                report_no = table.item(current_row, 0).text()
                
                db.update_report_status(
                    report_id=self.get_report_id(report_no),
                    status="approved",
                    reviewer_id=auth_manager.current_user['id']
                )
                
                db.log_audit(
                    user_id=auth_manager.current_user['id'],
                    action="review",
                    table_name="reports",
                    record_id=self.get_report_id(report_no),
                    new_values="approved"
                )
                
                QMessageBox.information(self, "成功", "报告已通过审核")
                self.load_reports()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"审核失败: {str(e)}")
    
    def reject_report(self):
        table = self.get_current_table()
        if table.table_status != "pending":
            QMessageBox.warning(self, "提示", "只能对待审核的报告进行操作")
            return
        
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要审核的报告")
            return
        
        dialog = RejectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reject_reason = dialog.get_reason()
            
            try:
                report_no = table.item(current_row, 0).text()
                
                db.update_report_status(
                    report_id=self.get_report_id(report_no),
                    status="rejected",
                    reviewer_id=auth_manager.current_user['id'],
                    comment=reject_reason
                )
                
                db.log_audit(
                    user_id=auth_manager.current_user['id'],
                    action="review",
                    table_name="reports",
                    record_id=self.get_report_id(report_no),
                    new_values=f"rejected: {reject_reason}"
                )
                
                QMessageBox.information(self, "成功", "报告已驳回")
                self.load_reports()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"驳回失败: {str(e)}")
    
    def batch_approve_reports(self):
        table = self.pending_table
        
        selected_rows = sorted(set(index.row() for index in table.selectedIndexes()))
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要批量审核的报告")
            return
        
        reply = QMessageBox.question(
            self, '确认批量通过',
            f'确定要通过选中的 {len(selected_rows)} 个报告吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success_count = 0
                fail_count = 0
                
                for row in selected_rows:
                    try:
                        report_no = table.item(row, 0).text()
                        
                        db.update_report_status(
                            report_id=self.get_report_id(report_no),
                            status="approved",
                            reviewer_id=auth_manager.current_user['id']
                        )
                        
                        db.log_audit(
                            user_id=auth_manager.current_user['id'],
                            action="review",
                            table_name="reports",
                            record_id=self.get_report_id(report_no),
                            new_values="approved (batch)"
                        )
                        
                        success_count += 1
                    except Exception:
                        fail_count += 1
                
                QMessageBox.information(self, "批量审核完成",
                    f"批量审核完成！\n成功：{success_count} 份\n失败：{fail_count} 份")
                self.load_reports()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"批量审核失败: {str(e)}")
    
    def batch_reject_reports(self):
        """批量驳回报告"""
        table = self.pending_table
        
        selected_rows = sorted(set(index.row() for index in table.selectedIndexes()))
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要批量驳回的报告")
            return
        
        reply = QMessageBox.question(
            self, '确认批量驳回',
            f'确定要驳回选中的 {len(selected_rows)} 个报告吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 显示驳回原因对话框
        dialog = RejectDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        reject_reason = dialog.get_reason()
        
        try:
            success_count = 0
            fail_count = 0
            
            for row in selected_rows:
                try:
                    report_no = table.item(row, 0).text()
                    
                    db.update_report_status(
                        report_id=self.get_report_id(report_no),
                        status="rejected",
                        reviewer_id=auth_manager.current_user['id'],
                        comment=reject_reason
                    )
                    
                    db.log_audit(
                        user_id=auth_manager.current_user['id'],
                        action="review",
                        table_name="reports",
                        record_id=self.get_report_id(report_no),
                        new_values=f"rejected (batch): {reject_reason}"
                    )
                    
                    success_count += 1
                except Exception:
                    fail_count += 1
            
            QMessageBox.information(self, "批量驳回完成",
                f"批量驳回完成！\n成功：{success_count} 份\n失败：{fail_count} 份")
            self.load_reports()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量驳回失败: {str(e)}")
    
    def view_report_detail(self):
        """查看报告详情"""
        table = self.get_current_table()
        current_row = table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要查看的报告")
            return
        
        report_no = table.item(current_row, 0).text()
        
        # 显示报告详情对话框
        dialog = ReportDetailDialog(self, report_no)
        dialog.exec()
    
    def get_report_id(self, report_no):
        """根据报告编号获取报告ID"""
        cursor = db.execute_query(
            "SELECT id FROM reports WHERE report_no = ?",
            (report_no,)
        )
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def refresh_data(self):
        """刷新数据"""
        self.load_reports()


class RejectDialog(QDialog):
    """驳回原因对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("驳回原因")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel("请输入驳回原因：")
        info_label.setStyleSheet("color: #333; font-weight: bold;")
        layout.addWidget(info_label)
        
        # 驳回原因输入
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("请详细说明驳回原因...")
        self.reason_input.setMinimumHeight(100)
        layout.addWidget(self.reason_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        submit_btn = QPushButton("提交驳回")
        submit_btn.clicked.connect(self.validate_and_submit)
        button_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def validate_and_submit(self):
        """验证并提交"""
        reason = self.reason_input.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "验证失败", "请输入驳回原因")
            return
        
        self.accept()
    
    def get_reason(self):
        """获取驳回原因"""
        return self.reason_input.toPlainText().strip()


class ReportDetailDialog(QDialog):
    """报告详情对话框"""
    
    def __init__(self, parent=None, report_no=None):
        super().__init__(parent)
        self.report_no = report_no
        self.init_ui()
        self.load_report_detail()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"报告详情 - {self.report_no}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # 报告内容显示
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 20px;
            }
        """)
        layout.addWidget(self.content_display)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_report_detail(self):
        """加载报告详情"""
        try:
            cursor = db.execute_query("""
                SELECT r.*, s.sample_no, s.patient_name, s.hospital,
                       u.real_name as reviewer_name
                FROM reports r
                LEFT JOIN samples s ON r.sample_id = s.id
                LEFT JOIN users u ON r.reviewer_id = u.id
                WHERE r.report_no = ?
            """, (self.report_no,))
            
            report = cursor.fetchone()
            
            if report:
                # 显示报告内容
                html_content = f"""
                <div style="font-family: 'Microsoft YaHei', sans-serif; padding: 20px;">
                    <h2 style="color: #333; border-bottom: 2px solid #0078d4; padding-bottom: 10px;">
                        报告基本信息
                    </h2>
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>报告编号：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report['report_no']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>样本编号：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report.get('sample_no', '')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>受检者姓名：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report.get('patient_name', '')}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>送检单位：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report.get('hospital', '')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>模板类型：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report.get('template_type', '')}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>状态：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report.get('status', '')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>审核人：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{report.get('reviewer_name', '')}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; background: #f8f9fa;"><strong>审核时间：</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{self.format_datetime(report.get('reviewed_at', ''))}</td>
                        </tr>
                    </table>
                    
                    <h2 style="color: #333; border-bottom: 2px solid #0078d4; padding-bottom: 10px;">
                        审核意见
                    </h2>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        {report.get('review_comment', '无审核意见')}
                    </div>
                </div>
                """
                
                self.content_display.setHtml(html_content)
            else:
                self.content_display.setText("未找到报告信息")
                
        except Exception as e:
            self.content_display.setText(f"加载报告详情失败: {str(e)}")
    
    def format_datetime(self, datetime_str):
        """格式化日期时间"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime_str