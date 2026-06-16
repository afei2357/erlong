#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
耳聋基因检测模块处理器
"""

from pathlib import Path
from typing import Dict, Any
import sys
import json
import traceback
from datetime import datetime

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_processor import BaseProcessor
from .mutation_analyzer import sum_mutation
from .report_generator import todocx


class DeafGeneProcessor(BaseProcessor):
    """耳聋基因检测报告处理器"""

    def __init__(self, work_dir: Path, batch_info: Dict, module_info: Dict, batch_files: list, log_callback=None):
        super().__init__(work_dir, batch_info, module_info, batch_files, log_callback)

        # 创建报告输出目录
        self.reports_dir = self.work_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def process(self) -> Dict[str, Any]:
        """处理耳聋基因检测报告"""
        try:
            self.log(f"开始处理耳聋基因检测报告 - 批次: {self.batch_no}")

            # 1. 获取样本信息表
            sample_excel_info = self.get_file_by_label("sample_excel")
            if not sample_excel_info:
                raise ValueError("未找到样本信息表 (file_label: sample_excel)")

            sample_excel_path = self.get_downloaded_file_path(sample_excel_info.get("file_name"))
            if not sample_excel_path.exists():
                raise FileNotFoundError(f"样本信息表不存在: {sample_excel_path}")

            self.log(f"样本信息表: {sample_excel_path}")

            # 2. 读取样本数据
            import pandas as pd
            df = pd.read_excel(sample_excel_path)
            self.log(f"已加载 {len(df)} 条样本数据")

            # 3. 处理每个样本
            output_files = []
            samples_data = []
            success_count = 0

            for idx, row in df.iterrows():
                try:
                    # 准备样本参数
                    params = {
                        "采血卡号": str(row.get("采血卡号", "")),
                        "样本编号": str(row.get("样本编号", "")),
                        "采血单位": str(row.get("采血单位", "")),
                        "初筛结果": str(row.get("初筛结果", "")),
                        "母亲姓名": str(row.get("母亲姓名", "")),
                        "婴儿性别": str(row.get("婴儿性别", "")),
                        "采血日期": str(row.get("采血日期", "")),
                    }

                    sample_no = params["采血卡号"]
                    self.log(f"处理样本: {sample_no}")

                    # 创建样本工作目录
                    sample_dir = self.reports_dir / sample_no
                    sample_dir.mkdir(exist_ok=True)

                    # 分析变异
                    params['genes'], params['is_mutation'] = sum_mutation(params['初筛结果'])
                    conclustion = '异常' if params['is_mutation'] else '正常'

                    # 生成报告
                    module_dir = Path(__file__).parent
                    template_name = 'deaf.template_v2.docx'

                    jsonf, docf, pdff = todocx(params, str(sample_dir), template_name)

                    # 添加到输出文件列表
                    output_files.append({
                        "path": docf,
                        "label": f"report_word_{idx + 1}",
                        "name": Path(docf).name,
                        "sample_id": sample_no,
                        "sample_name": params.get("母亲姓名", ""),
                        "file_type": "docx"
                    })

                    output_files.append({
                        "path": pdff,
                        "label": f"report_pdf_{idx + 1}",
                        "name": Path(pdff).name,
                        "sample_id": sample_no,
                        "sample_name": params.get("母亲姓名", ""),
                        "file_type": "pdf"
                    })

                    # 准备样本信息
                    samples_data.append({
                        "sample_id": sample_no,
                        "name": params.get("母亲姓名", ""),
                        "sample_type": "干血斑",
                        "gender": params.get("婴儿性别", ""),
                        "age": "",
                        "hospital": params.get("采血单位", ""),
                        "sample_date": params.get("采血日期", ""),
                        "diagnosis": conclustion
                    })

                    success_count += 1
                    self.log(f"  ✓ {sample_no} 报告生成成功")

                except Exception as e:
                    error_msg = f"处理样本失败 ({row.get('采血卡号', 'unknown')}): {e}"
                    self.log(f"  ✗ {error_msg}")
                    traceback.print_exc()

            self.log(f"报告生成完成: {success_count}/{len(df)} 个")

            return {
                "success": True,
                "message": f"成功生成 {success_count} 份报告",
                "output_files": output_files,
                "samples": samples_data
            }

        except Exception as e:
            import traceback
            error_msg = f"处理失败: {str(e)}"
            traceback_str = traceback.format_exc()
            self.log(traceback_str)
            self.log(error_msg)

            return {
                "success": False,
                "message": str(e),
                "output_files": [],
                "samples": []
            }


# 模块导出
def create_processor(work_dir: Path, batch_info: Dict, module_info: Dict, batch_files: list, log_callback=None) -> BaseProcessor:
    """创建处理器实例"""
    return DeafGeneProcessor(work_dir, batch_info, module_info, batch_files, log_callback)
