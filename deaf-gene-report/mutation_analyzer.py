import os
import json
from pathlib import Path

# 获取模块目录
module_dir = Path(__file__).parent

def sum_mutation(mut_results):
    print(f"检测结果为{mut_results}")
    mutation_infos = json.load(open(module_dir / 'resources' / 'mutations.json','r', encoding='utf-8'))
    gene_list = mutation_infos.keys()
    mutation_list = [j  for i,i_val in mutation_infos.items() for j in i_val['mutations']]
    
    # 处理空值或nan值
    if not mut_results or mut_results == 'nan':
        mutation_flag = False
    else:
        mutation_flag = True
    
    if mutation_flag:
        res = mut_results.split()
        if res[0] not in gene_list:
            raise Exception(f'Gene {res[0]} not in gene list')
        if res[1] not in mutation_list:
            raise Exception(f'mutation {res[1]} not in gene list')
        ## 替换变异
        try:
            mutation_infos[res[0]]['mutations'][res[1]]['results'] = res[2]
        except:
            print(f'{res[0]} and {res[1]} not in mutaions dict')
    
    new_genes = []
    genes = list(mutation_infos.values()).copy()
    for gene in genes:
        #print(gene)
        gene['mutations'] = list(gene['mutations'].values())
        new_genes.append(gene)
    return (new_genes,mutation_flag)
    