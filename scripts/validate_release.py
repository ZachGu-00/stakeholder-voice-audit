"""Validate file checksums and input structure."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
def read(name):
    with (ROOT/'data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
replies=read('replies.csv');labels=read('labels.csv');scenarios=read('scenarios.csv');items=read('survey_items.csv');counts=read('survey_joint_counts.csv')
assert len(replies)==720 and len({r['response_id'] for r in replies})==720
assert len(scenarios)==60 and len({r['id'] for r in scenarios})==60
assert Counter(r['coding_split'] for r in replies)=={'calibration':24,'single':552,'double':144}
assert len({(r['scenario_id'],r['model'],r['condition']) for r in replies})==720
assert Counter(r['coder'] for r in labels)=={'single':552,'coder_a':144,'coder_b':144}
assert len({(r['response_id'],r['coder']) for r in labels})==840
book=json.loads((ROOT/'data/codebook.json').read_text(encoding='utf-8'))
features=[r['field'] for r in book['features'] if not r['derived']]
assert all(r[f] in ['0','1',''] for r in labels for f in features)
assert sum(not r[f] for r in labels for f in features)==12
assert len(items)==43 and len(counts)==175
form_n={r['form']:int(r['n_total']) for r in items};assert sum(form_n.values())==27396
for pair in read('survey_pairs.csv'):
    block=[r for r in counts if r['pair_id']==pair['id']]
    assert len(block)==25 and sum(int(r['n']) for r in block)==form_n[pair['form']]
    for axis,col in [('x','x_value'),('y','y_value')]:
        item=next(r for r in items if r['form']==pair['form'] and r['variable']==pair[axis])
        assert all(sum(int(r['n']) for r in block if int(r[col])==v)==int(item[f'n_{v}']) for v in range(1,6))
print('Release validation passed:',len(manifest['files']),'files.')
