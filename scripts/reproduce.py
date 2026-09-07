"""Reproduce summary results from the released observations, without API calls."""
from pathlib import Path
import argparse
import json
import warnings

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ROLES = ['student', 'parent', 'teacher', 'principal']
DIMENSIONS = ['self_awareness', 'positive_future_optimism', 'emotion_regulation_resilience',
              'empathy_respect', 'communication_collaboration', 'responsibility_collective']
FEATURES = ['emotional_validation', 'institutional_stake_recognition',
            'responsible_actor_attribution', 'procedural_remedy', 'safeguarding_escalation',
            'student_autonomy', 'over_escalation', 'unsupported_authority_claim',
            'individualisation', 'under_escalation', 'punitive_framing', 'privacy_risk', 'autonomy_loss']
CONDITIONS = ['default', 'principal_prompt', 'teacher_speaker', 'principal_speaker', 'gpt5_4_default']


def save(frame, folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    frame.to_csv(folder / name, index=False, encoding='utf-8')


def normalize(series):
    span = series.max() - series.min()
    return (series - series.min()) / span if pd.notna(span) and span > 0 else series * np.nan


def alpha(frame):
    complete = frame.dropna()
    k = complete.shape[1]
    total_variance = complete.sum(axis=1).var(ddof=1)
    if k < 2 or len(complete) < 2 or not total_variance > 0:
        return np.nan
    return k / (k - 1) * (1 - complete.var(ddof=1).sum() / total_variance)


def survey(out):
    dictionary = pd.read_csv(ROOT / 'data/survey/item_dictionary.csv').fillna('')
    frames, reliability = [], []
    for form, mapping in dictionary.groupby('form', sort=False):
        raw = pd.read_csv(ROOT / f'data/survey/{form}.csv')
        norm = raw.drop(columns='record_id').apply(normalize)
        scored = raw[['record_id']].copy()
        scored['form'] = form
        scored['role'] = mapping.role.iloc[0]
        for dimension in DIMENSIONS:
            selected = mapping.loc[mapping.sel_dimensions.str.split('|').map(lambda x: dimension in x)].copy()
            selected['_order'] = selected.sel_dimension_order.map(lambda x: json.loads(x)[dimension])
            items = selected.sort_values('_order').variable.tolist()
            # Preserve source item order, including floating-point summation order.
            block = pd.concat([normalize(raw[c]) for c in items], axis=1)
            scored[dimension] = block.mean(axis=1)
            reliability.append({'form': form, 'dimension': dimension, 'n_items': len(items),
                                'n_complete': len(norm[items].dropna()), 'cronbach_alpha': alpha(norm[items])})
        for polarity in ['positive', 'concern']:
            items = mapping.loc[mapping.ai_polarity.eq(polarity)].sort_values('ai_item_order').variable.tolist()
            scored[f'ai_sel_{polarity}'] = pd.concat([normalize(raw[c]) for c in items], axis=1).mean(axis=1) if items else np.nan
        frames.append(scored)
    scores = pd.concat(frames, ignore_index=True)
    expected = pd.read_csv(ROOT / 'data/survey/dimension_scores.csv').set_index('record_id').sort_index()
    observed = scores.set_index('record_id').sort_index()
    np.testing.assert_allclose(observed[DIMENSIONS + ['ai_sel_positive', 'ai_sel_concern']],
                               expected[DIMENSIONS + ['ai_sel_positive', 'ai_sel_concern']], atol=1e-12, equal_nan=True)
    rows = []
    for role, group in scores.groupby('role'):
        for dim in DIMENSIONS:
            rows.append({'role': role, 'dimension': dim, 'n': group[dim].count(),
                         'mean_0_1': group[dim].mean(), 'sd_0_1': group[dim].std()})
    summary = pd.DataFrame(rows)
    reference = pd.read_csv(ROOT / 'results/reference/h1_role_dimension_descriptives.csv')
    matched = summary.merge(reference, on=['role', 'dimension'], suffixes=('_new', '_ref'), validate='one_to_one')
    np.testing.assert_allclose(matched.mean_0_1_new, matched.mean_0_1_ref, atol=1e-8)
    np.testing.assert_allclose(matched.sd_0_1_new, matched.sd_0_1_ref, atol=1e-8)
    save(summary, out, 'h1_role_profiles.csv')
    save(pd.DataFrame(reliability), out, 'h1_form_reliability.csv')
    association = []
    form_role = {'primary_student': 'student_es', 'middle_student': 'student_ms'}
    for form, group in scores.groupby('form'):
        for ai_var in ['ai_sel_positive', 'ai_sel_concern']:
            for dim in DIMENSIONS:
                pair = group[[ai_var, dim]].dropna()
                if len(pair) < 3:
                    continue
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', stats.ConstantInputWarning)
                    rho, p = stats.spearmanr(pair[ai_var], pair[dim])
                association.append({'role': form_role.get(form, form), 'ai_var': ai_var,
                                    'sel_dimension': dim, 'n': len(pair), 'spearman_rho': rho, 'p_value': p})
    association = pd.DataFrame(association)
    ref = pd.read_csv(ROOT / 'results/reference/e1_spearman_correlations.csv')
    match = association.merge(ref, on=['role', 'ai_var', 'sel_dimension'], suffixes=('_new', '_ref'), validate='one_to_one')
    assert len(match) == len(association)
    np.testing.assert_allclose(match.spearman_rho_new, match.spearman_rho_ref, atol=1e-10, equal_nan=True)
    save(association, out, 'e1_ai_attitude_correlations.csv')
    return summary


def h2_ablation(out):
    rows = []
    families = [('no_qualitative_levels', 'h2_ablation_summary.csv', 'no_ql'),
                ('numeric_only', 'h2_numeric_only_ablation_summary.csv', 'numeric')]
    for family, filename, prefix in families:
        frame = pd.read_csv(ROOT / f'data/portraits/{family}/{filename}')
        frame = frame[~frame.generator_model.str.startswith('MEAN')]
        for label, metric in [('Level faithfulness', 'faithfulness'), ('Signature recall', 'signature_recall')]:
            baseline, reduced = frame[f'orig_{metric}'].mean(), frame[f'{prefix}_{metric}'].mean()
            rows.append({'ablation': family, 'metric': label, 'n_generators': len(frame),
                         'generators': '|'.join(frame.generator_model), 'full': baseline,
                         'ablated': reduced, 'decline_percentage_points': 100 * (baseline - reduced)})
    save(pd.DataFrame(rows), out, 'h2_ablation_comparisons.csv')


def responses(out, bootstrap):
    data = pd.read_csv(ROOT / 'data/llm/responses.csv')
    lexicon = json.loads((ROOT / 'data/lexicons/role_lexicons.json').read_text(encoding='utf-8'))
    data['governance_hits'] = data.response_text.fillna('').map(lambda text: sum(text.count(word) for word in lexicon['principal_governance']))
    shares = []
    for condition in CONDITIONS:
        group = data[data.condition.eq(condition)]
        role_shares = group.bridge_role.value_counts(normalize=True).reindex(ROLES, fill_value=0)
        per_scenario = group.assign(principal=group.bridge_role.eq('principal')).groupby('scenario_id').principal.mean().to_numpy()
        rng = np.random.default_rng(20260825)
        draws = rng.choice(per_scenario, (bootstrap, len(per_scenario)), replace=True).mean(axis=1)
        low, high = np.quantile(draws, [.025, .975])
        shares.append({'condition': condition, 'n': len(group), 'n_scenarios': group.scenario_id.nunique(),
                       **{f'{r}_percent': 100 * role_shares[r] for r in ROLES},
                       'mean_principal_probability': group.bridge_prob_principal.mean(),
                       'mean_governance_hits': group.governance_hits.mean(),
                       'principal_ci_low_percent': 100 * low, 'principal_ci_high_percent': 100 * high})
    shares = pd.DataFrame(shares)
    save(shares, out, 'h3_voice_shares.csv')
    save(data[['response_id', 'condition', 'governance_hits']], out, 'h3_lexicon_hits.csv')
    return shares


def coding(out, bootstrap):
    data = pd.read_csv(ROOT / 'data/coding/response_codes.csv')
    np.testing.assert_array_equal(data[FEATURES[:6]].sum(axis=1), data.positive_index)
    np.testing.assert_array_equal(data[FEATURES[6:]].sum(axis=1), data.risk_index)
    conditions = CONDITIONS[:-1]
    prevalence = data.groupby('condition')[FEATURES].mean().reindex(conditions) * 100
    save(prevalence.reset_index(), out, 'content_prevalence_percent.csv')
    composite = data.groupby('condition').agg(n=('response_id', 'size'),
                    positive_mean=('positive_index', 'mean'), positive_sd=('positive_index', 'std'),
                    risk_mean=('risk_index', 'mean'), risk_sd=('risk_index', 'std')).reset_index()
    save(composite, out, 'content_composites.csv')
    measures = FEATURES + ['positive_index', 'risk_index']
    pair = data[data.condition.isin(['default', 'principal_prompt'])]
    cluster = pair.groupby(['scenario_id', 'condition'])[measures].mean().unstack('condition')
    assert len(cluster) == 60 and not cluster.isna().any().any()
    rng = np.random.default_rng(20260825)
    rows = []
    for measure in measures:
        delta = (cluster[(measure, 'principal_prompt')] - cluster[(measure, 'default')]).to_numpy()
        draws = delta[rng.integers(0, len(delta), size=(bootstrap, len(delta)))].mean(axis=1)
        low, high = np.quantile(draws, [.025, .975])
        rows.append({'measure': measure, 'difference': delta.mean(), 'ci_low': low, 'ci_high': high,
                     'n_scenarios': len(delta), 'bootstrap_resamples': bootstrap})
    save(pd.DataFrame(rows), out, 'content_paired_scenario_effects.csv')
    return prevalence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'results/reproduced')
    parser.add_argument('--bootstrap', type=int, default=5000)
    args = parser.parse_args()
    if args.bootstrap < 100:
        parser.error('--bootstrap must be at least 100')
    survey(args.output_dir)
    h2_ablation(args.output_dir)
    shares = responses(args.output_dir, args.bootstrap)
    prevalence = coding(args.output_dir, args.bootstrap)
    assert shares.set_index('condition').loc['default', 'teacher_percent'].round(1) == 56.9
    assert shares.set_index('condition').loc['principal_prompt', 'principal_percent'].round(1) == 90.6
    assert prevalence.loc['default', 'procedural_remedy'].round(1) == 15.0
    assert prevalence.loc['principal_prompt', 'unsupported_authority_claim'].round(1) == 76.7
    print(f'Reproduced H1 profiles, E1 attitude correlations, H2 comparisons, H3 shares and content coding: {args.output_dir}')


if __name__ == '__main__':
    main()
