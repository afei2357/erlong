#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试耳聋基因报告生成独立函数
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from run_deaf_gene_report import generate_deaf_gene_reports

# 测试函数
def test_deaf_gene_report():
    print("=" * 60)
    print("测试耳聋基因报告生成独立函数")
    print("=" * 60)

    # 定义日志回调函数
    def logger(message):
        print(f"[LOG] {message}")

    # 测试参数
    excel_path = "sample_data_test.xlsx"
    output_dir = "test_reports"

    print(f"\n测试参数:")
    print(f"  Excel文件: {excel_path}")
    print(f"  输出目录: {output_dir}")

    # 调用函数
    print(f"\n开始生成报告...")
    result = generate_deaf_gene_reports(
        sample_excel_path=excel_path,
        output_dir=output_dir,
        log_callback=logger
    )

    # 输出结果
    print(f"\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    print(f"生成文件数: {len(result['output_files'])}")
    print(f"样本数: {len(result['samples'])}")

    if result['success']:
        print(f"\n生成的文件:")
        for file_info in result['output_files']:
            print(f"  - {file_info['name']} ({file_info['file_type']})")

        print(f"\n样本信息:")
        for sample in result['samples']:
            print(f"  - {sample['sample_id']}: {sample['name']}, 诊断: {sample['diagnosis']}")
    else:
        print(f"\n失败原因: {result['message']}")

    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    test_deaf_gene_report()