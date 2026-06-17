import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
db_path = DATA_DIR / "deaf_gene_system.db"

print(f"数据库路径: {db_path}")
print(f"文件是否存在: {db_path.exists()}")

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

print('\n=== 样本数据 ===')
cursor = conn.execute('SELECT id, sample_no, patient_name, clinical_diagnosis, created_at FROM samples')
for row in cursor.fetchall():
    print(f"ID:{row['id']} 样本号:{row['sample_no']} 姓名:{row['patient_name']} 诊断:{row['clinical_diagnosis']} 日期:{row['created_at']}")

print('\n=== 基因数据 ===')
cursor = conn.execute('SELECT sample_id, gene_name, pathogenicity FROM gene_data')
for row in cursor.fetchall():
    print(f"样本ID:{row['sample_id']} 基因:{row['gene_name']} 致病性:{row['pathogenicity']}")

conn.close()