#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成耳聋基因检测示例Excel文件
"""

import pandas as pd
from datetime import datetime, timedelta

# 创建示例数据
sample_data = [
    {
        "采血卡号": "TEST001",
        "样本编号": "S001",
        "采血单位": "北京市妇幼保健院",
        "初筛结果": "GJB2 c.235delC 正常",
        "母亲姓名": "张三",
        "婴儿性别": "男",
        "采血日期": "2024-06-15"
    },
    {
        "采血卡号": "TEST002",
        "样本编号": "S002",
        "采血单位": "上海市儿童医院",
        "初筛结果": "GJB2 c.235delC 异常",
        "母亲姓名": "李四",
        "婴儿性别": "女",
        "采血日期": "2024-06-16"
    },
    {
        "采血卡号": "TEST003",
        "样本编号": "S003",
        "采血单位": "广州市妇女儿童医疗中心",
        "初筛结果": "SLC26A4 IVS7-2A>G 正常",
        "母亲姓名": "王五",
        "婴儿性别": "男",
        "采血日期": "2024-06-17"
    },
    {
        "采血卡号": "TEST004",
        "样本编号": "S004",
        "采血单位": "深圳市妇幼保健院",
        "初筛结果": "",  # 空初筛结果，测试正常情况
        "母亲姓名": "赵六",
        "婴儿性别": "女",
        "采血日期": "2024-06-18"
    },
    {
        "采血卡号": "TEST005",
        "样本编号": "S005",
        "采血单位": "杭州市妇产科医院",
        "初筛结果": "MT-RNR1 m.1555A>G 正常",
        "母亲姓名": "孙七",
        "婴儿性别": "男",
        "采血日期": "2024-06-19"
    }
]

# 创建DataFrame
df = pd.DataFrame(sample_data)

# 保存为Excel文件
output_file = "sample_data_test.xlsx"
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"示例Excel文件已生成: {output_file}")
print(f"包含 {len(df)} 条样本数据")
print("\n数据预览:")
print(df.to_string(index=False))