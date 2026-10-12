"""Statistics for the deposited labels."""
import numpy as np

SEED = 20261011
FEATURES = ['emotional_validation', 'institutional_stake_recognition', 'responsible_actor_attribution', 'procedural_remedy', 'safeguarding_escalation', 'student_autonomy', 'over_escalation', 'unsupported_authority_claim', 'individualisation', 'under_escalation', 'punitive_framing', 'privacy_risk', 'autonomy_loss']

def features():
    return FEATURES

def agreement_stats(a,b):
    if len(a)!=len(b): raise ValueError('Lengths differ')
    counts={(i,j):sum(x==i and y==j for x,y in zip(a,b)) for i in [0,1] for j in [0,1]}
    n=len(a)
    if not n: return {'n':0,'kappa':None,'agreement':None,'positive_agreement':None,'negative_agreement':None,
                      'a_positive_rate':None,'b_positive_rate':None,'n00':0,'n01':0,'n10':0,'n11':0}
    p=sum(a)/n;q=sum(b)/n;observed=(counts[0,0]+counts[1,1])/n;expected=p*q+(1-p)*(1-q)
    discordant=counts[0,1]+counts[1,0]
    return {'n':n,'kappa':(observed-expected)/(1-expected) if expected<1 else None,'agreement':observed,
        'positive_agreement':2*counts[1,1]/(2*counts[1,1]+discordant) if 2*counts[1,1]+discordant else None,
        'negative_agreement':2*counts[0,0]/(2*counts[0,0]+discordant) if 2*counts[0,0]+discordant else None,
        'a_positive_rate':p,'b_positive_rate':q,**{f'n{i}{j}':counts[i,j] for i,j in counts}}

def interval(draws):
    draws = np.asarray(draws)
    valid = draws[np.isfinite(draws)]
    if not len(valid):
        return {'ci_low': None, 'ci_high': None, 'valid_bootstraps': 0}
    lo, hi = np.quantile(valid, [.025, .975])
    return {'ci_low': float(lo), 'ci_high': float(hi), 'valid_bootstraps': len(valid)}

def groupings(records):
    yield 'overall', 'all', records
    for field in ['model', 'category', 'difficulty']:
        for value in sorted({r[field] for r in records}):
            yield field, value, [r for r in records if r[field] == value]

def prevalence(records, feature, condition, resamples):
    rows = [r for r in records if r['condition'] == condition]
    clusters = sorted({r['scenario_id'] for r in rows})
    num = np.array([sum(r[feature] == 1 for r in rows if r['scenario_id'] == s) for s in clusters], dtype=float)
    den = np.array([sum(r[feature] is not None for r in rows if r['scenario_id'] == s) for s in clusters], dtype=float)
    n, positive = int(den.sum()), int(num.sum())
    if clusters:
        idx = np.random.default_rng(SEED).integers(0, len(clusters), (resamples, len(clusters)))
        drawn_n = den[idx].sum(axis=1)
        draws = np.divide(num[idx].sum(axis=1), drawn_n, out=np.full(resamples, np.nan), where=drawn_n > 0)
    else:
        draws = []
    return {'n_assigned': len(rows), 'n_observed': n, 'n_missing': len(rows) - n, 'n_positive': positive,
            'estimate': positive / n if n else None, 'n_scenarios_assigned': len(clusters),
            'n_scenarios_observed': int(np.count_nonzero(den)), **interval(draws)}

def paired_contrast(records, feature, lhs, rhs, resamples):
    cells = {(r['scenario_id'], r['model'], r['condition']): r for r in records}
    assert len(cells) == len(records)
    models = sorted({r['model'] for r in records})
    scenarios = sorted({r['scenario_id'] for r in records})
    scenario_values, left_values, right_values, pair_counts = [], [], [], []
    for scenario in scenarios:
        pairs = []
        for model in models:
            left, right = cells.get((scenario, model, lhs)), cells.get((scenario, model, rhs))
            if left is None or right is None or left[feature] is None or right[feature] is None:
                continue
            pairs.append((left[feature], right[feature]))
        if pairs:
            lv, rv = np.mean(pairs, axis=0)
            scenario_values.append(lv - rv)
            left_values.append(lv)
            right_values.append(rv)
            pair_counts.append(len(pairs))
    if scenario_values:
        a = np.array(scenario_values)
        draws = a[np.random.default_rng(SEED).integers(0, len(a), (resamples, len(a)))].mean(axis=1)
        complete = a[np.array(pair_counts) == len(models)]
        full_draws = complete[np.random.default_rng(SEED).integers(0, len(complete), (resamples, len(complete)))].mean(axis=1) if len(complete) else []
    else:
        draws, complete, full_draws = [], [], []
    full_ci = interval(full_draws)
    return {'estimate': float(np.mean(scenario_values)) if scenario_values else None,
            'lhs_matched_scenario_mean': float(np.mean(left_values)) if left_values else None,
            'rhs_matched_scenario_mean': float(np.mean(right_values)) if right_values else None,
            'n_pairs': sum(pair_counts), 'n_scenarios': len(scenario_values), 'n_models_in_group': len(models),
            'n_scenarios_all_models_paired': sum(n == len(models) for n in pair_counts),
            'min_model_pairs_per_scenario': min(pair_counts) if pair_counts else 0,
            'max_model_pairs_per_scenario': max(pair_counts) if pair_counts else 0,
            **interval(draws), 'complete_scenario_estimate': float(np.mean(complete)) if len(complete) else None,
            'complete_scenario_ci_low': full_ci['ci_low'], 'complete_scenario_ci_high': full_ci['ci_high']}

def reliability(imported, keys, resamples):
    a, b = imported['coder_a'], imported['coder_b']
    output = []
    for feature in features():
        pairs = [(keys[bid]['scenario_id'], int(a[bid][feature]), int(b[bid][feature])) for bid in a
                 if a[bid][feature] != 'U' and b[bid][feature] != 'U']
        result = agreement_stats([r[1] for r in pairs], [r[2] for r in pairs])
        clusters = sorted({r[0] for r in pairs})
        counts = np.array([[sum(s == scenario and x == i and y == j for s, x, y in pairs)
                            for i, j in [(0, 0), (0, 1), (1, 0), (1, 1)]] for scenario in clusters])
        idx = np.random.default_rng(SEED).integers(0, len(clusters), (resamples, len(clusters)))
        n00, n01, n10, n11 = counts[idx].sum(axis=1).T
        n = n00 + n01 + n10 + n11
        p, q = (n10 + n11) / n, (n01 + n11) / n
        observed, expected = (n00 + n11) / n, p * q + (1 - p) * (1 - q)
        k = np.divide(observed - expected, 1 - expected, out=np.full(resamples, np.nan), where=expected < 1)
        ci = interval(k)
        enough = ci['valid_bootstraps'] >= .8 * resamples
        result.update(feature=feature, total_assigned=144, excluded_uncertain=144 - len(pairs), n_scenarios=len(clusters),
                      kappa_ci_low=ci['ci_low'] if enough else None, kappa_ci_high=ci['ci_high'] if enough else None,
                      valid_bootstraps=ci['valid_bootstraps'], ci_status='ok' if enough else 'insufficient_nondegenerate_bootstraps')
        output.append(result)
    return output
