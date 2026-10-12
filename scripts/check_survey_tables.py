"""Check Tables S1 to S8 against the deposited data."""
from pathlib import Path
from collections import Counter
import csv,json,re

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def nums(cell):return [float(s) for s in re.findall(r'\d+(?:\.\d+)?',cell.replace('{,}','').replace(',',''))]
checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)})
    assert value,name
def text(name):return (ROOT/'results/tables'/name).read_text(encoding='utf-8')
items=read(ROOT/'data/survey_items.csv');pairs=read(ROOT/'data/survey_pairs.csv');counts=read(ROOT/'data/survey_joint_counts.csv')
forms={'Primary students':'primary_student','Middle students':'middle_student','Parents':'parent','Teachers':'teacher','Principals':'principal'}
form=None;total=0
for line in text('appendix_items.tex').splitlines():
    if not re.search(r' & q\d+ & ',line):continue
    cells=line.split(' & ')
    for name,key in forms.items():
        if cells[0].startswith(name):form=key
    row=next(r for r in items if r['form']==form and r['variable']==cells[1]);n=int(row['n_total'])-int(row['n_missing'])
    expected=[round(100*sum(int(row[f'n_{i}']) for i in ix)/n,1) for ix in [[4,5],[3],[1,2]]]
    check('S1:'+form+':'+cells[1],[nums(c)[0] for c in cells[-3:]]==expected and cells[2]==row['question_en']);total+=1
check('S1:43 items',total==43)
joint=text('appendix_joint.tex');parts={}
for part in joint.split('\\begin{longtable}'):
    m=re.search(r'\\label\{([^}]+)\}',part)
    if m:parts[m[1]]=part
def lines(label):return [l for l in parts[label].splitlines() if ' & ' in l and l.rstrip().endswith('\\\\') and not l.startswith(('\\toprule','\\caption','\\bottomrule'))]
summary=read(ROOT/'results/reproduced/joint_summary.csv')
primary=[next(r for r in summary if r['pair_id']==p['id'] and r['threshold']=='primary') for p in pairs]
strict=[next(r for r in summary if r['pair_id']==p['id'] and r['threshold']=='strict') for p in pairs]
iv=lambda r,k:int(r[k]);pc=lambda r,k:round(float(r[k])*100,1)
for line,r in zip(lines('tab:joint_main'),primary):
    ex=[[iv(r,'n_complete')],[iv(r,'n_x_agree'),pc(r,'p_x_agree_among_complete')],[iv(r,'n_y_agree'),pc(r,'p_y_agree_among_complete')],
        [iv(r,'n_both_agree'),pc(r,'p_both_among_complete')],[pc(r,'p_both_among_complete_wilson_low'),pc(r,'p_both_among_complete_wilson_high')],
        [pc(r,'p_y_among_x_agree')],[pc(r,'p_x_among_y_agree')]]
    check('S3:'+r['pair_id'],[nums(c) for c in line.split(' & ')[1:]]==ex)
for line,r in zip(lines('tab:joint_quadrants'),primary):
    ex=[[iv(r,k),round(iv(r,k)/iv(r,'n_complete')*100,1)] for k in ['n_both_agree','n_x_only','n_y_only','n_neither_agree']]
    check('S4:'+r['pair_id'],[nums(c) for c in line.split(' & ')[1:]]==ex)
for line,r in zip(lines('tab:joint_strict'),strict):
    ex=[[iv(r,'n_x_agree')],[iv(r,'n_y_agree')],[iv(r,'n_both_agree'),pc(r,'p_both_among_complete')],
        [pc(r,'p_y_among_x_agree')],[pc(r,'p_both_among_complete_wilson_low'),pc(r,'p_both_among_complete_wilson_high')]]
    check('S5:'+r['pair_id'],[nums(c) for c in line.split(' & ')[1:]]==ex)
expected=[]
for pair in pairs:
    block=[r for r in counts if r['pair_id']==pair['id']]
    for x in range(1,6):
        ns=[int(next(r for r in block if int(r['x_value'])==x and int(r['y_value'])==y)['n']) for y in range(1,6)]
        expected.append([[x]]+[[v] for v in ns]+[[sum(ns)]])
check('S3-S6:row counts',[len(lines(k)) for k in ['tab:joint_main','tab:joint_quadrants','tab:joint_strict','tab:joint_5x5']]==[7,7,7,35])
for i,(line,ex) in enumerate(zip(lines('tab:joint_5x5'),expected)):check('S6:row '+str(i+1),[nums(c) for c in line.split(' & ')[1:]]==ex)
for p in pairs:
    for axis in ['x','y']:
        r=next(r for r in items if r['form']==p['form'] and r['variable']==p[axis])
        check('S2:'+p['id']+':'+axis,r['question_en'] in parts['tab:joint_items'])
sc=read(ROOT/'data/scenarios.csv')
counts_by_theme=Counter(r['category'] for r in sc);counts_by_diff=Counter(r['difficulty'] for r in sc)
themes={'Relationship skills':'relationship_skills','Social awareness':'social_awareness','Responsible decision':'responsible_decision','Self awareness':'self_awareness','Self management':'self_management','Academic pressure':'academic_pressure','Bullying':'bullying','Social anxiety':'social_anxiety'}
for line in text('appendix_scenarios.tex').splitlines():
    cells=[s.strip() for s in line.split('&')]
    if cells[0] in themes:
        check('S7:'+cells[0],nums(cells[1])==[counts_by_theme[themes[cells[0]]]])
        if len(cells)>3 and cells[2].lower() in counts_by_diff:check('S7:'+cells[2],nums(cells[3])==[counts_by_diff[cells[2].lower()]])
check('S7:60 scenarios',len(sc)==60)
source_counts=Counter('primary' if r['source_module'].startswith('学生卷') else 'middle' if r['source_module'].startswith('初中生卷') else 'parent' if r['source_module'].startswith('家长卷') else 'teacher' if r['source_module'].startswith('教师卷') else 'principal' for r in sc)
check('S7:source forms',source_counts=={'primary':25,'middle':13,'parent':6,'teacher':4,'principal':12})
book=json.loads((ROOT/'data/codebook.json').read_text(encoding='utf-8'))
coding=text('appendix_coding.tex')
for r in book['features']:check('S8:'+r['field'],r['definition'] in coding)
check('S8:15 definitions',len(book['features'])==15)
(ROOT/'results/reproduced/survey_table_check.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2)+'\n',encoding='utf-8')
print('Survey and definition checks:',len(checks))
