#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
耳聋基因检测报告生成工具

独立调用函数，无需依赖 worker 框架
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import json
import traceback
from datetime import datetime

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util

def import_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

deaf_gene_dir = Path(__file__).parent / "deaf-gene-report"
mutation_analyzer = import_module_from_path("mutation_analyzer", deaf_gene_dir / "mutation_analyzer.py")
report_generator = import_module_from_path("report_generator", deaf_gene_dir / "report_generator.py")

sum_mutation = mutation_analyzer.sum_mutation
todocx = report_generator.todocx


def generate_deaf_gene_reports(
    sample_excel_path: str,
    output_dir: Optional[str] = None,
    log_callback=None
) -> Dict[str, Any]:
    """
    生成耳聋基因检测报告

    Args:
        sample_excel_path: 样本信息 Excel 文件路径
        output_dir: 报告输出目录，默认为当前目录下的 reports 文件夹
        log_callback: 日志回调函数，接收字符串参数

    Returns:
        Dict: 处理结果
        {
            "success": bool,
            "message": str,
            "output_files": [
                {
                    "path": str,
                    "label": str,
                    "name": str,
                    "sample_id": str,
                    "sample_name": str,
                    "file_type": str
                }
            ],
            "samples": [
                {
                    "sample_id": str,
                    "name": str,
                    "sample_type": str,
                    "gender": str,
                    "age": str,
                    "hospital": str,
                    "sample_date": str,
                    "diagnosis": str
                }
            ]
        }
    """
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    try:
        log(f"开始处理耳聋基因检测报告")

        # 验证输入文件
        excel_path = Path(sample_excel_path)
        if not excel_path.exists():
            raise FileNotFoundError(f"样本信息表不存在: {sample_excel_path}")

        log(f"样本信息表: {excel_path}")

        # 设置输出目录
        if output_dir:
            reports_dir = Path(output_dir)
        else:
            reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        log(f"报告输出目录: {reports_dir}")

        # 读取样本数据
        import pandas as pd
        df = pd.read_excel(excel_path)
        log(f"已加载 {len(df)} 条样本数据")

        # 处理每个样本
        output_files = []
        samples_data = []
        success_count = 0

        for idx, row in df.iterrows():
            try:
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
                log(f"处理样本: {sample_no}")

                # 创建样本工作目录
                sample_dir = reports_dir / sample_no
                sample_dir.mkdir(exist_ok=True)

                # 分析变异
                params['genes'], params['is_mutation'] = sum_mutation(params['初筛结果'])
                conclustion = '异常' if params['is_mutation'] else '正常'

                # 生成报告
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
                log(f"  ✓ {sample_no} 报告生成成功")

            except Exception as e:
                error_msg = f"处理样本失败 ({row.get('采血卡号', 'unknown')}): {e}"
                log(f"  ✗ {error_msg}")
                traceback.print_exc()

        log(f"报告生成完成: {success_count}/{len(df)} 个")

        return {
            "success": True,
            "message": f"成功生成 {success_count} 份报告",
            "output_files": output_files,
            "samples": samples_data
        }

    except Exception as e:
        error_msg = f"处理失败: {str(e)}"
        traceback_str = traceback.format_exc()
        log(traceback_str)
        log(error_msg)

        return {
            "success": False,
            "message": str(e),
            "output_files": [],
            "samples": []
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="耳聋基因检测报告生成工具")
    parser.add_argument("excel_path", help="样本信息 Excel 文件路径")
    parser.add_argument("-o", "--output", help="报告输出目录", default=None)

    args = parser.parse_args()

    result = generate_deaf_gene_reports(
        sample_excel_path=args.excel_path,
        output_dir=args.output
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
