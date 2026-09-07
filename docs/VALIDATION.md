# Release validation

Validation performed on 7 September 2026 using the deposited data and fitted checkpoint.

| Check | Result |
|---|---|
| Survey records and form counts | 27,396 records across five forms; counts match the analytical sample |
| H1 profiles | All four-role means and standard deviations agree with the archived results within `1e-8` |
| Exploratory AI-attitude correlations | All 54 available positive/concern-composite correlations agree with the archived coefficients within numerical tolerance |
| Released scores versus recomputation | Six SEL dimensions and two AI-attitude composites agree within `1e-12` |
| Generated reply keys | 1,800 unique replies with expected condition counts |
| Content-code linkage | All 420 records link to their scenario, generator, condition and sample-index-1 reply |
| Code validity | Thirteen binary fields per response; composite sums verified |
| Training anchors | 80 human answers plus 138 role-redacted portraits; H3 response IDs absent |
| Checkpoint packaging | Archive and extracted model-file SHA-256 checks passed |
| Full checkpoint inference replay | All 1,800 predicted classes match the archived predictions; maximum absolute probability difference `2.024e-6` |
| Figures | Both figures regenerated from reproduced tables and visually inspected |

The small probability differences arise in a replay using the same fitted weights on a different runtime/hardware configuration. Full classifier retraining and fresh hosted-model generation were not performed for this release. The repository includes the archived grouped validation outputs and code for optional retraining.

Summary reconstruction used Python 3.12 with NumPy 2.3.5, pandas 3.0.1, SciPy 1.16.1 and Matplotlib 3.10.6. Checkpoint replay used PyTorch 2.8.0, SetFit 1.1.3, Sentence Transformers 5.1.0, Transformers 4.55.2 and scikit-learn 1.6.1.
