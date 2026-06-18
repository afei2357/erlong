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


class DeafGeneReportReviewException(Exception):
    pass


class DeafGeneReportStatusInvalidException(DeafGeneReportReviewException):
    pass


class DeafGeneReportNoPermissionException(DeafGeneReportReviewException):
    pass


class DeafGeneReportReview(QWidget):
    def __init__(self):
        super().__init__()
        self._deafGeneCurTab = None
        self._deafGeneLastReviewTime = None
        self._deafGeneBatchOpsCount = 0
        self.initDeafGeneReviewUI()
        self.loadDeafGeneReports()
        
    def initDeafGeneReviewUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("耳聋基因报告审核中心")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        self.deaf_gene_tab_widget = QTabWidget()
        self.deaf_gene_tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; border-radius: 8px; }
            QTabBar::tab { background-color: #f0f0f0; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background-color: white; border-bottom: 3px solid #0078d4; font-weight: bold; }
        """)
        
        self.deaf_gene_pending_tab = self.createDeafGenePendingTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_pending_tab, "待审核报告")
        
        self.deaf_gene_approved_tab = self.createDeafGeneApprovedTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_approved_tab, "已审核报告")
        
        self.deaf_gene_rejected_tab = self.createDeafGeneRejectedTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_rejected_tab, "驳回报告")
        
        layout.addWidget(self.deaf_gene_tab_widget)
        
    def createDeafGenePendingTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.deaf_gene_pending_table = self.createDeafGeneReviewGrid("pending")
        layout.addWidget(self.deaf_gene_pending_table)
        
        action_layout = QHBoxLayout()
        
        self.deaf_gene_approve_btn = QPushButton("✅ 通过")
        self.deaf_gene_approve_btn.clicked.connect(self.approveDeafGeneReport)
        action_layout.addWidget(self.deaf_gene_approve_btn)
        
        self.deaf_gene_reject_btn = QPushButton("❌ 驳回")
        self.deaf_gene_reject_btn.clicked.connect(self.rejectDeafGeneReport)
        action_layout.addWidget(self.deaf_gene_reject_btn)
        
        self.deaf_gene_view_detail_btn = QPushButton("👁️ 查看详情")
        self.deaf_gene_view_detail_btn.clicked.connect(self.viewDeafGeneReportDetail)
        action_layout.addWidget(self.deaf_gene_view_detail_btn)
        
        action_layout.addStretch()
        
        self.deaf_gene_batch_approve_btn = QPushButton("✅ 批量通过")
        self.deaf_gene_batch_approve_btn.clicked.connect(self.batchApproveDeafGeneReports)
        action_layout.addWidget(self.deaf_gene_batch_approve_btn)
        
        self.deaf_gene_batch_reject_btn = QPushButton("❌ 批量驳回")
        self.deaf_gene_batch_reject_btn.clicked.connect(self.batchRejectDeafGeneReports)
        action_layout.addWidget(self.deaf_gene_batch_reject_btn)
        
        layout.addLayout(action_layout)
        
        return widget
        
    def createDeafGeneApprovedTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.deaf_gene_approved_table = self.createDeafGeneReviewGrid("approved")
        layout.addWidget(self.deaf_gene_approved_table)
        
        return widget
        
    def createDeafGeneRejectedTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.deaf_gene_rejected_table = self.createDeafGeneReviewGrid("rejected")
        layout.addWidget(self.deaf_gene_rejected_table)
        
        return widget
        
    def createDeafGeneReviewGrid(self, status):
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
        
        table.deaf_gene_status = status
        
        return table
        
    def loadDeafGeneReports(self):
        self.populateDeafGeneReviewGrid(self.deaf_gene_pending_table, "pending")
        self.populateDeafGeneReviewGrid(self.deaf_gene_approved_table, "approved")
        self.populateDeafGeneReviewGrid(self.deaf_gene_rejected_table, "rejected")
    
    def populateDeafGeneReviewGrid(self, table, status):
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
            table.setItem(row, 5, QTableWidgetItem(self.formatDeafGeneDatetime(report.get('created_at', ''))))
            table.setItem(row, 6, QTableWidgetItem(report.get('reviewer_name', '')))
            table.setItem(row, 7, QTableWidgetItem(self.formatDeafGeneDatetime(report.get('reviewed_at', ''))))
            
            status_item = QTableWidgetItem(REPORT_STATUS.get(status, status))
            self.colorDeafGeneStatusText(status_item, status)
            table.setItem(row, 8, status_item)
    
    def colorDeafGeneStatusText(self, item, status):
        color_map = {
            'pending': QColor('#ff9800'),
            'approved': QColor('#4caf50'),
            'rejected': QColor('#f44336')
        }
        
        color = color_map.get(status, QColor('#666'))
        item.setForeground(color)
    
    def formatDeafGeneDatetime(self, datetime_str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str
    
    def getCurrentDeafGeneTable(self):
        current_index = self.deaf_gene_tab_widget.currentIndex()
        if current_index == 0:
            return self.deaf_gene_pending_table
        elif current_index == 1:
            return self.deaf_gene_approved_table
        else:
            return self.deaf_gene_rejected_table
    
    def approveDeafGeneReport(self):
        table = self.getCurrentDeafGeneTable()
        if table.deaf_gene_status != "pending":
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
            report_no = table.item(current_row, 0).text()
            
            try:
                report_id = self.getDeafGeneReportId(report_no)
                if not report_id:
                    QMessageBox.warning(self, "数据错误", "报告不存在")
                    return
                
                db.update_report_status(
                    report_id=report_id,
                    status="approved",
                    reviewer_id=auth_manager.current_user['id']
                )
                
                db.log_audit(
                    user_id=auth_manager.current_user['id'],
                    action="review",
                    table_name="reports",
                    record_id=report_id,
                    new_values="approved"
                )
                
                QMessageBox.information(self, "成功", "报告已通过审核")
                self.loadDeafGeneReports()
                
            except Exception as e:
                QMessageBox.critical(self, "审核错误", f"审核操作失败: {str(e)}")
    
    def rejectDeafGeneReport(self):
        table = self.getCurrentDeafGeneTable()
        if table.deaf_gene_status != "pending":
            QMessageBox.warning(self, "提示", "只能对待审核的报告进行操作")
            return
        
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要审核的报告")
            return
        
        dialog = DeafGeneRejectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reject_reason = dialog.getDeafGeneRejectReason()
            
            try:
                report_no = table.item(current_row, 0).text()
                report_id = self.getDeafGeneReportId(report_no)
                
                if not report_id:
                    QMessageBox.warning(self, "数据错误", "报告不存在")
                    return
                
                db.update_report_status(
                    report_id=report_id,
                    status="rejected",
                    reviewer_id=auth_manager.current_user['id'],
                    comment=reject_reason
                )
                
                db.log_audit(
                    user_id=auth_manager.current_user['id'],
                    action="review",
                    table_name="reports",
                    record_id=report_id,
                    new_values=f"rejected: {reject_reason}"
                )
                
                QMessageBox.information(self, "成功", "报告已驳回")
                self.loadDeafGeneReports()
                
            except Exception as e:
                QMessageBox.critical(self, "驳回错误", f"驳回操作失败: {str(e)}")
    
    def batchApproveDeafGeneReports(self):
        table = self.deaf_gene_pending_table
        
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
            success_count = 0
            fail_count = 0
            
            for row in selected_rows:
                try:
                    report_no = table.item(row, 0).text()
                    report_id = self.getDeafGeneReportId(report_no)
                    
                    if not report_id:
                        fail_count += 1
                        continue
                    
                    db.update_report_status(
                        report_id=report_id,
                        status="approved",
                        reviewer_id=auth_manager.current_user['id']
                    )
                    
                    db.log_audit(
                        user_id=auth_manager.current_user['id'],
                        action="review",
                        table_name="reports",
                        record_id=report_id,
                        new_values="approved (batch)"
                    )
                    
                    success_count += 1
                except Exception:
                    fail_count += 1
            
            QMessageBox.information(self, "批量审核完成",
                f"批量审核完成！\n成功：{success_count} 份\n失败：{fail_count} 份")
            self.loadDeafGeneReports()
    
    def batchRejectDeafGeneReports(self):
        table = self.deaf_gene_pending_table
        
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
        
        dialog = DeafGeneRejectDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        reject_reason = dialog.getDeafGeneRejectReason()
        
        success_count = 0
        fail_count = 0
        
        for row in selected_rows:
            try:
                report_no = table.item(row, 0).text()
                report_id = self.getDeafGeneReportId(report_no)
                
                if not report_id:
                    fail_count += 1
                    continue
                
                db.update_report_status(
                    report_id=report_id,
                    status="rejected",
                    reviewer_id=auth_manager.current_user['id'],
                    comment=reject_reason
                )
                
                db.log_audit(
                    user_id=auth_manager.current_user['id'],
                    action="review",
                    table_name="reports",
                    record_id=report_id,
                    new_values=f"rejected (batch): {reject_reason}"
                )
                
                success_count += 1
            except Exception:
                fail_count += 1
        
        QMessageBox.information(self, "批量驳回完成",
            f"批量驳回完成！\n成功：{success_count} 份\n失败：{fail_count} 份")
        self.loadDeafGeneReports()
    
    def viewDeafGeneReportDetail(self):
        table = self.getCurrentDeafGeneTable()
        current_row = table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要查看的报告")
            return
        
        report_no = table.item(current_row, 0).text()
        
        dialog = DeafGeneReportDetailDialog(self, report_no)
        dialog.exec()
    
    def getDeafGeneReportId(self, report_no):
        cursor = db.execute_query(
            "SELECT id FROM reports WHERE report_no = ?",
            (report_no,)
        )
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def refreshDeafGeneData(self):
        self.loadDeafGeneReports()


class DeafGeneRejectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initDeafGeneRejectUI()
        
    def initDeafGeneRejectUI(self):
        self.setWindowTitle("驳回原因")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel("请输入驳回原因：")
        info_label.setStyleSheet("color: #333; font-weight: bold;")
        layout.addWidget(info_label)
        
        self.deaf_gene_reason_input = QTextEdit()
        self.deaf_gene_reason_input.setPlaceholderText("请详细说明驳回原因...")
        self.deaf_gene_reason_input.setMinimumHeight(100)
        layout.addWidget(self.deaf_gene_reason_input)
        
        button_layout = QHBoxLayout()
        
        submit_btn = QPushButton("提交驳回")
        submit_btn.clicked.connect(self.validateDeafGeneRejectReason)
        button_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def validateDeafGeneRejectReason(self):
        reason = self.deaf_gene_reason_input.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "验证失败", "请输入驳回原因")
            return
        
        self.accept()
    
    def getDeafGeneRejectReason(self):
        return self.deaf_gene_reason_input.toPlainText().strip()


class DeafGeneReportDetailDialog(QDialog):
    def __init__(self, parent=None, report_no=None):
        super().__init__(parent)
        self._deafGeneReportNo = report_no
        self.initDeafGeneDetailUI()
        self.loadDeafGeneReportDetail()
        
    def initDeafGeneDetailUI(self):
        self.setWindowTitle(f"报告详情 - {self._deafGeneReportNo}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        self.deaf_gene_content_display = QTextEdit()
        self.deaf_gene_content_display.setReadOnly(True)
        self.deaf_gene_content_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 20px;
            }
        """)
        layout.addWidget(self.deaf_gene_content_display)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def loadDeafGeneReportDetail(self):
        cursor = db.execute_query("""
            SELECT r.*, s.sample_no, s.patient_name, s.hospital,
                   u.real_name as reviewer_name
            FROM reports r
            LEFT JOIN samples s ON r.sample_id = s.id
            LEFT JOIN users u ON r.reviewer_id = u.id
            WHERE r.report_no = ?
        """, (self._deafGeneReportNo,))
        
        report = cursor.fetchone()
        
        if report:
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
                        <td style="padding: 10px; border: 1px solid #ddd;">{self.formatDeafGeneDatetime(report.get('reviewed_at', ''))}</td>
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
            
            self.deaf_gene_content_display.setHtml(html_content)
        else:
            self.deaf_gene_content_display.setText("未找到报告信息")
    
    def formatDeafGeneDatetime(self, datetime_str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime_str