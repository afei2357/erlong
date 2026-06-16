# 耳聋基因检测模块

## 功能说明

处理耳聋基因检测数据，生成检测报告（Word 和 PDF 格式）。

## 输入文件

- `sample_excel`: 样本信息表 (Excel 格式)
  - 必填字段：采血卡号、样本编号、采血单位、初筛结果
  - 可选字段：母亲姓名、婴儿性别、采血日期

## 处理流程

1. 读取样本信息表
2. 解析初筛结果（基因变异信息）
3. 匹配 mutations.json 中的基因和变异数据库
4. 判断检测结果（正常/异常）
5. 使用 docxtpl 模板引擎生成 Word 报告
6. 使用 word2pdf.jar 转换为 PDF
7. 上报样本信息和报告文件

## 初筛结果格式

初筛结果格式: `基因名 变异位点 检测结果`

示例: `GJB2 c.235delC 杂合`

## 输出文件

- `{采血卡号}.deaf.identify.report.json`: 原始数据
- `{采血卡号}.deaf.identify.report.docx`: Word 报告
- `{采血卡号}.deaf.identify.report.pdf`: PDF 报告

## 依赖

- docxtpl: Word 模板引擎
- python-docx: Word 文档处理
- pandas: 数据处理
- openpyxl: Excel 文件读取
- Java: PDF 转换（word2pdf.jar）

## 注意事项

1. 需要 Java 环境支持 PDF 转换
2. mutations.json 包含基因和变异数据库
3. 报告模板: deaf.template_v2.docx
