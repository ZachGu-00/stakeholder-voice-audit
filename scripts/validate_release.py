"""Validate the public package's integrity, joins and analytical sample counts."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    manifest = json.loads((ROOT / 'data/file_manifest.json').read_text())
    for record in manifest:
        path = ROOT / record['path']
        assert path.is_file(), f'Missing file: {record["path"]}'
        assert sha(path) == record['sha256'], f'Changed file: {record["path"]}'
    counts = pd.read_csv(ROOT / 'data/survey/sample_counts.csv')
    assert counts.n.sum() == 27396
    dictionary = pd.read_csv(ROOT / 'data/survey/item_dictionary.csv')
    for row in counts.itertuples():
        data = pd.read_csv(ROOT / f'data/survey/{row.form}.csv')
        assert len(data) == row.n and data.record_id.is_unique
        expected = dictionary[dictionary.form.eq(row.form)].variable.tolist()
        assert list(data.columns) == ['record_id'] + expected
        assert all(re.fullmatch('q[0-9]{3}', c) for c in expected)
        assert all(pd.api.types.is_numeric_dtype(data[c]) for c in expected)
    replies = pd.read_csv(ROOT / 'data/llm/responses.csv')
    assert replies.response_id.is_unique and len(replies) == 1800
    assert replies.condition.value_counts().to_dict() == {'default': 900, 'principal_prompt': 540,
        'gpt5_4_default': 180, 'principal_speaker': 90, 'teacher_speaker': 90}
    roles = ['student', 'parent', 'teacher', 'principal']
    probs = replies[[f'bridge_prob_{r}' for r in roles]].to_numpy()
    assert np.isfinite(probs).all() and ((probs >= 0) & (probs <= 1)).all()
    np.testing.assert_allclose(probs.sum(axis=1), 1, atol=1e-8)
    np.testing.assert_array_equal(np.asarray(roles)[probs.argmax(axis=1)], replies.bridge_role)
    codes = pd.read_csv(ROOT / 'data/coding/response_codes.csv')
    assert len(codes) == 420 and codes.response_id.is_unique
    assert codes.condition.value_counts().to_dict() == {'default': 180, 'principal_prompt': 180,
        'teacher_speaker': 30, 'principal_speaker': 30}
    joined = codes.merge(replies[['response_id', 'scenario_id', 'model', 'condition', 'sample_index']],
        on=['response_id', 'scenario_id', 'model', 'condition'], validate='one_to_one')
    assert len(joined) == 420 and joined.sample_index.eq(1).all()
    features = [c for c in codes if c not in ['response_id', 'scenario_id', 'model', 'condition', 'positive_index', 'risk_index']]
    assert len(features) == 13 and codes[features].isin([0, 1]).all().all()
    training = pd.read_csv(ROOT / 'data/classifier/voice_bridge_training_manifest.csv')
    assert len(training) == 218 and training.record_id.is_unique
    assert training.source_domain.value_counts().to_dict() == {'h2_role_portrait': 138, 'p01_human_response': 80}
    assert not set(training.record_id) & set(replies.response_id)
    assert not training.loc[training.source_domain.eq('h2_role_portrait'), 'text'].str.contains('学生|家长|教师|校长').any()
    print(json.dumps({'integrity_checked_files': len(manifest), 'survey_records': 27396,
        'llm_responses': 1800, 'coded_responses': 420, 'classifier_anchors': 218, 'status': 'passed'}))


if __name__ == '__main__':
    main()
