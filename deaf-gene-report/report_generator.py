from docxtpl import DocxTemplate,InlineImage
from docx.shared import Mm
import datetime
import os
import json
from subprocess import call
from pathlib import Path

# 获取模块目录
module_dir = Path(__file__).parent


def todocx(results,outdir,temp_doc):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    time = datetime.datetime.now().strftime('%Y-%m-%d')
    results.setdefault('reportdate',time)

    # 使用模块目录下的模板
    template_path = module_dir / "resources" / "template" / temp_doc
    tpl = DocxTemplate(str(template_path))
    tpl.render(results)

    # 批次号和时间
    sample_no = results['采血卡号']
    # 保存json
    jsonf = f'{outdir}/{sample_no}.deaf.identify.report.json'
    with open(jsonf,'w', encoding='utf-8') as outf:
        outf.write(json.dumps(results,indent=4, ensure_ascii=False))
    # 保存word
    docf = f'{outdir}/{sample_no}.deaf.identify.report.docx'
    tpl.save(docf)
    pdff = f'{outdir}/{sample_no}.deaf.identify.report.pdf'

    # 使用 worker 的 word2pdf.jar
    # 尝试多个可能的路径
    possible_jar_paths = [
        module_dir.parent.parent / "tools" / "word2pdf.jar",  # worker/tools/word2pdf.jar
        module_dir.parent / "tools" / "word2pdf.jar",  # aone_deaf_gene/tools/word2pdf.jar
        Path("tools") / "word2pdf.jar"  # 当前目录下的 tools/word2pdf.jar
    ]
    
    jar_path = None
    for path in possible_jar_paths:
        if path.exists():
            jar_path = path
            break
    
    if jar_path is None:
        print(f"警告: 未找到 word2pdf.jar，跳过PDF生成")
        return jsonf, docf, ""
    
    call(f'java -jar  "{jar_path}" "{docf}" "{pdff}"', shell=True)
    return jsonf, docf, pdff
