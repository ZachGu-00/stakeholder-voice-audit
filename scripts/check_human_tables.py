"""Check numeric rows against frozen human_only_v1; source is a bound snapshot."""
import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
E = ROOT/'results/reference'
snapshot = {p.name: {'text':p.read_text(encoding='utf-8'), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (ROOT/'results/tables').glob('*.tex')}

def read(name):
    return list(csv.DictReader((E / name).open(encoding='utf-8-sig', newline='')))

rates, contrasts, agreement = read('prevalence.csv'), read('contrasts.csv'), read('agreement.csv')
names = {
    'Emotional recognition': 'emotional_validation', 'Institutional stakes': 'institutional_stake_recognition',
    'Responsible actor named': 'responsible_actor_attribution', 'Concrete procedure': 'procedural_remedy',
    'Proportionate escalation': 'safeguarding_escalation', 'Student choice preserved': 'student_autonomy',
    'Over-escalation': 'over_escalation', 'Unsupported authority claim': 'unsupported_authority_claim',
    'Individualisation': 'individualisation', 'Under-escalation': 'under_escalation', 'Punitive framing': 'punitive_framing',
    'Unnecessary disclosure': 'privacy_risk', 'Loss of student choice': 'autonomy_loss',
    'Procedure and emotional recognition': 'procedure_and_emotional_validation',
    'Procedure and institutional stakes': 'procedure_and_institutional_stakes',
}
checks = []

def numeric(cell):
    clean = cell.replace('$-$', '-').replace('$-$.', '-.').replace('$', '')
    return [float(v) for v in re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', clean)]

def record(file, lineno, cell, expected, tolerance=.051):
    actual = numeric(cell)
    valid = len(actual) == len(expected) and all(abs(x - y) <= tolerance for x, y in zip(actual, expected))
    checks.append({'file': file, 'line': lineno, 'actual': actual, 'expected': expected, 'passed': valid})

def select(rows, coder, f, **kwargs):
    return next(r for r in rows if r['scope'] == 'all_noncalibration' and r['group_type'] == 'overall'
                and r['coder_stream'] == coder and r['feature'] == f and all(r[k] == v for k, v in kwargs.items()))

coder, table = None, None
file = 'appendix_campus.tex'
for n, line in enumerate(snapshot[file]['text'].splitlines(), 1):
    if '\\caption{Coding version' in line:
        coder = 'coder_a' if 'version 1' in line else 'coder_b'
        table = 'rates' if 'percentage of labelled' in line else 'contrasts'
    if '\\caption{Sensitivity' in line:
        break
    cells = [v.strip() for v in line.split('&')]
    if cells[0] not in names:
        continue
    feature = names[cells[0]]
    if table == 'rates':
        for cell, condition in zip(cells[1:], ['campus', 'procedure', 'boundary', 'procedure_boundary']):
            r = select(rates, coder, feature, condition=condition)
            record(file, n, cell, [100 * float(r['estimate']), int(r['n_positive']), int(r['n_observed'])])
    else:
        for cell, contrast in zip(cells[1:5], ['B_minus_A', 'D_minus_B', 'C_minus_A', 'D_minus_C']):
            r = select(contrasts, coder, feature, contrast=contrast)
            record(file, n, cell, [100 * float(r[x]) for x in ['estimate', 'ci_low', 'ci_high']])
        pair_counts = [int(select(contrasts, coder, feature, contrast=c)['n_pairs']) for c in ['B_minus_A', 'D_minus_B', 'C_minus_A', 'D_minus_C']]
        record(file, n, cells[5], pair_counts, 0)

file = 'table_primary.tex'
for n, line in enumerate(snapshot[file]['text'].splitlines(), 1):
    if 'Coding version 1' in line: coder = 'coder_a'
    if 'Coding version 2' in line: coder = 'coder_b'
    cells = [v.strip() for v in line.split('&')]
    if cells[0] not in names: continue
    feature = names[cells[0]]
    for cell, condition in zip(cells[1:5], ['campus', 'procedure', 'boundary', 'procedure_boundary']):
        r = select(rates, coder, feature, condition=condition)
        record(file, n, cell, [100 * float(r['estimate'])])
    for cell, contrast in zip(cells[5:], ['B_minus_A', 'D_minus_B']):
        r = select(contrasts, coder, feature, contrast=contrast)
        record(file, n, cell, [100 * float(r[x]) for x in ['estimate', 'ci_low', 'ci_high']])

file = 'table_agreement.tex'
for n, line in enumerate(snapshot[file]['text'].splitlines(), 1):
    cells = [v.strip() for v in line.split('&')]
    if cells[0] not in names: continue
    r = next(r for r in agreement if r['feature'] == names[cells[0]])
    expected = [[int(r['n'])], [float(r['kappa'])] if r['kappa'] else [], [float(r['agreement'])],
                [int(r['n10']) + int(r['n11'])], [int(r['n01']) + int(r['n11'])]]
    for i, (cell, exp) in enumerate(zip(cells[1:], expected)):
        record(file, n, cell, exp, .0051 if i in [1, 2] else 0)


# Check every model/theme/difficulty and sensitivity row against its own fields,
# not against an undifferentiated pool of numbers.
def grouped(rows, coder, feature, scope='all_noncalibration', group_type='overall', group_value='all', **kwargs):
    return next(r for r in rows if r['scope']==scope and r['coder_stream']==coder
                and r['feature']==feature and r['group_type']==group_type and r['group_value']==group_value
                and all(r[k]==v for k,v in kwargs.items()))

def effect_values(r, prefix=''):
    return [100*float(r[prefix+k]) for k in ['estimate','ci_low','ci_high']]

def rate_values(r):
    return [100*float(r['estimate']), int(r['n_positive']), int(r['n_observed'])]

file='appendix_campus.tex'
section=None;model=None;coder=None
model_alias={'GPT-5':'GPT-5','Deepseek v4 flash':'Deepseek v4 flash','Claude Haiku 4.5':'Claude Haiku 4.5'}
themes={'Academic pressure':'academic_pressure','Bullying':'bullying','Relationship skills':'relationship_skills','Responsible decision making':'responsible_decision','Self awareness':'self_awareness','Self management':'self_management','Social anxiety':'social_anxiety','Social awareness':'social_awareness'}
for n,line in enumerate(snapshot[file]['text'].splitlines(),1):
    if 'label{tab:sensitivity}' in line:section='sensitivity'
    if 'label{tab:by_model}' in line:section='model'
    if 'label{tab:by_theme}' in line:section='theme'
    if 'label{tab:by_difficulty}' in line:section='difficulty'
    cells=[x.strip() for x in line.split('&')]
    if section=='sensitivity' and cells[0] in ['V1','V2']:
        coder='coder_a' if cells[0]=='V1' else 'coder_b';f=names[cells[1]]
        r=grouped(contrasts,coder,f,contrast='B_minus_A')
        record(file,n,cells[2],effect_values(r,'complete_scenario_'))
        record(file,n,cells[3],[int(r['n_scenarios_all_models_paired'])],0)
        sub=grouped(contrasts,coder,f,scope='double_coded_subset',contrast='B_minus_A')
        record(file,n,cells[4],effect_values(sub));record(file,n,cells[5],[int(sub['n_pairs'])],0)
    elif section=='model' and len(cells)>2 and cells[2] in names:
        if cells[0]:model=model_alias[cells[0]]
        if cells[1]:coder='coder_a' if cells[1]=='V1' else 'coder_b'
        f=names[cells[2]]
        for cell,condition in zip(cells[3:5],['campus','procedure']):
            r=grouped(rates,coder,f,group_type='model',group_value=model,condition=condition)
            record(file,n,cell,rate_values(r))
        r=grouped(contrasts,coder,f,group_type='model',group_value=model,contrast='B_minus_A')
        record(file,n,cells[5],effect_values(r));record(file,n,cells[6],[int(r['n_pairs'])],0)
    elif section=='theme':
        if 'Coding version 1' in line:coder='coder_a'
        if 'Coding version 2' in line:coder='coder_b'
        if cells[0] not in themes:continue
        theme=themes[cells[0]];f='procedural_remedy'
        r=grouped(contrasts,coder,f,group_type='category',group_value=theme,contrast='B_minus_A')
        record(file,n,cells[1],[int(r['n_scenarios'])],0)
        for cell,condition in zip(cells[2:4],['campus','procedure']):
            rate=grouped(rates,coder,f,group_type='category',group_value=theme,condition=condition)
            record(file,n,cell,rate_values(rate))
        record(file,n,cells[4],effect_values(r))
    elif section=='difficulty' and cells[0] in ['Simple','Medium','Complex']:
        difficulty=cells[0].lower()
        for cell,(coder,f) in zip(cells[2:],[('coder_a','procedural_remedy'),('coder_a','emotional_validation'),('coder_b','procedural_remedy'),('coder_b','emotional_validation')]):
            r=grouped(contrasts,coder,f,group_type='difficulty',group_value=difficulty,contrast='B_minus_A')
            record(file,n,cell,effect_values(r))
        record(file,n,cells[1],[int(r['n_scenarios'])],0)

file='appendix_agreement.tex'
for n,line in enumerate(snapshot[file]['text'].splitlines(),1):
    cells=[x.strip() for x in line.split('&')]
    if cells[0] not in names:continue
    r=next(r for r in agreement if r['feature']==names[cells[0]])
    for i,field in enumerate(['n00','n01','n10','n11','excluded_uncertain','positive_agreement','negative_agreement','kappa']):
        record(file,n,cells[i+1],[float(r[field])] if r[field] else [],0 if i<5 else .0051)
    record(file,n,cells[9],[float(r[k]) for k in ['kappa_ci_low','kappa_ci_high']] if r['kappa_ci_low'] else [],.0051)

result = {'status': 'PASS' if all(r['passed'] for r in checks) else 'FAIL',
          'checks': len(checks), 'failures': [r for r in checks if not r['passed']],
          'source_sha256': {name: record['sha256'] for name, record in snapshot.items()},
          'evidence_sha256': {name: hashlib.sha256((E / name).read_bytes()).hexdigest()
                              for name in ['prevalence.csv', 'contrasts.csv', 'agreement.csv']}}
(ROOT / 'results/reproduced/human_table_check.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
assert result['status']=='PASS', result['failures']
print('Human table checks:', result['checks'])
