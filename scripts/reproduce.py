"""Reproduce the deposited results from labels and survey counts."""
from pathlib import Path
import csv, json, math, subprocess, sys
import numpy as np
from statistics import FEATURES, groupings, prevalence, paired_contrast, reliability

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/reproduced'
OUT.mkdir(parents=True,exist_ok=True)
CONDITIONS=['campus','procedure','boundary','procedure_boundary']
CONTRASTS={'B_minus_A':('procedure','campus'),'D_minus_B':('procedure_boundary','procedure'),
           'C_minus_A':('boundary','campus'),'D_minus_C':('procedure_boundary','boundary')}
JOINTS={'procedure_and_emotional_validation':['procedural_remedy','emotional_validation'],
        'procedure_and_institutional_stakes':['procedural_remedy','institutional_stake_recognition']}

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def save(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def compare(name,rows,keys):
    expected={tuple(r[k] for k in keys):r for r in read(ROOT/'results/reference'/name)}
    observed={tuple(str(r[k]) for k in keys):r for r in rows}
    assert len(expected)==len(rows) and set(expected)==set(observed),name
    numeric=0
    for key,row in observed.items():
        for field,value in row.items():
            if field not in expected[key]:continue
            want=expected[key][field]
            if value is None:assert want=='',(name,key,field)
            elif isinstance(value,(float,int,np.integer)):
                assert want!='' and math.isclose(float(value),float(want),rel_tol=1e-11,abs_tol=1e-12),(name,key,field,value,want)
                numeric+=1
            else:assert str(value)==want,(name,key,field)
    return {'file':name,'rows':len(rows),'numeric_cells':numeric}

replies={r['response_id']:r for r in read(ROOT/'data/replies.csv')}
scenarios={r['id']:r for r in read(ROOT/'data/scenarios.csv')}
labels=read(ROOT/'data/labels.csv')
by_coder={c:{} for c in ['single','coder_a','coder_b']}
for r in labels:by_coder[r['coder']][r['response_id']]=r
assert len(replies)==720 and len(by_coder['single'])==552
assert len(by_coder['coder_a'])==144 and set(by_coder['coder_a'])==set(by_coder['coder_b'])
assert not (set(by_coder['single']) & set(by_coder['coder_a']))
pr,cr=[],[]
for scope in ['all_noncalibration','double_coded_subset']:
    for coder,version in [('coder_a','rater_1'),('coder_b','rater_2')]:
        pool=dict(by_coder[coder])
        if scope=='all_noncalibration':pool.update(by_coder['single'])
        records=[]
        for rid,label in sorted(pool.items()):
            r=replies[rid];s=scenarios[r['scenario_id']]
            rec={k:r[k] for k in ['response_id','scenario_id','model','condition']}
            rec.update({k:s[k] for k in ['category','difficulty']})
            rec.update({f:int(label[f]) if label[f] else None for f in FEATURES})
            for joint,members in JOINTS.items():rec[joint]=None if any(rec[f] is None for f in members) else int(all(rec[f]==1 for f in members))
            records.append(rec)
        for group,value,subset in groupings(records):
            for feature in FEATURES+list(JOINTS):
                prefix=dict(scope=scope,coding_version=version,coder_stream=coder,group_type=group,group_value=value,group_display_name=value,feature=feature)
                for condition in CONDITIONS:pr.append({**prefix,'condition':condition,**prevalence(subset,feature,condition,5000)})
                for contrast,(lhs,rhs) in CONTRASTS.items():cr.append({**prefix,'contrast':contrast,'lhs':lhs,'rhs':rhs,**paired_contrast(subset,feature,lhs,rhs,5000)})
        print('Computed',scope,version,flush=True)
imported={c:{rid:{f:r[f] if r[f] else 'U' for f in FEATURES} for rid,r in by_coder[c].items()} for c in ['coder_a','coder_b']}
ar=reliability(imported,replies,5000)
report=[]
for name,rows,keys in [('prevalence.csv',pr,['scope','coding_version','group_type','group_value','feature','condition']),
                       ('contrasts.csv',cr,['scope','coding_version','group_type','group_value','feature','contrast']),
                       ('agreement.csv',ar,['feature'])]:
    report.append(compare(name,rows,keys));save(name,rows)

def wilson(k,n):
    if not n:return None,None
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,center-half),min(1.,center+half)

items=read(ROOT/'data/survey_items.csv');pairs=read(ROOT/'data/survey_pairs.csv');counts=read(ROOT/'data/survey_joint_counts.csv')
marg=[]
for r in items:
    n=sum(int(r[f'n_{i}']) for i in range(1,6))
    assert n+int(r['n_missing'])==int(r['n_total'])
    marg.append({'form':r['form'],'variable':r['variable'],'n':n,
        'agree_pct':100*(int(r['n_4'])+int(r['n_5']))/n,'undecided_pct':100*int(r['n_3'])/n,'disagree_pct':100*(int(r['n_1'])+int(r['n_2']))/n})
save('survey_marginals.csv',marg)
summary=[];plot=[]
for pair in pairs:
    block=[r for r in counts if r['pair_id']==pair['id']];assert len(block)==25
    n=sum(int(r['n']) for r in block)
    for threshold,values in [('primary',{4,5}),('strict',{5})]:
        x=sum(int(r['n']) for r in block if int(r['x_value']) in values)
        y=sum(int(r['n']) for r in block if int(r['y_value']) in values)
        b=sum(int(r['n']) for r in block if int(r['x_value']) in values and int(r['y_value']) in values)
        row={'pair_id':pair['id'],'form':pair['form'],'threshold':threshold,'agree_values':'|'.join(map(str,sorted(values))),
             'n_total':n,'n_complete':n,'n_missing_either':0,'n_missing_x':0,'n_missing_y':0,'n_missing_both':0,
             'n_x_agree':x,'n_y_agree':y,'n_both_agree':b,'n_x_only':x-b,'n_y_only':y-b,'n_neither_agree':n-x-y+b,'n_not_x_agree':n-x}
        for metric,k,den in [('p_both_among_complete',b,n),('p_x_agree_among_complete',x,n),('p_y_agree_among_complete',y,n),
                             ('p_y_among_x_agree',b,x),('p_x_among_y_agree',b,y),('p_y_among_not_x_agree',y-b,n-x)]:
            row[metric]=k/den if den else None
            row[metric+'_wilson_low'],row[metric+'_wilson_high']=wilson(k,den)
        summary.append(row)
        plot.append({'pair_id':pair['id'],'form':pair['form'],'threshold':threshold,'n_complete':n,'n_benefit_agree':x,'n_concern_agree':y,'n_both':b,
                     'benefit_agree_pct':100*x/n,'concern_agree_pct':100*y/n,'both_pct':100*b/n,'concern_among_benefit_pct':100*b/x})
for name,rows in [('joint_summary.csv',summary),('joint_plot_data.csv',plot)]:
    report.append(compare(name,rows,['pair_id','threshold']));save(name,rows)
for script in ['check_human_tables.py','check_survey_tables.py']:
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)],check=True)
(OUT/'validation.json').write_text(json.dumps({'passed':True,'comparisons':report},indent=2)+'\n',encoding='utf-8')
print('Reproduction passed:',sum(r['numeric_cells'] for r in report),'numeric cells.')
