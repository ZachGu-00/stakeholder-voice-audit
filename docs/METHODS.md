# Methods and reproduction scope

## Questionnaire profiles

The study summarises responses from five questionnaire forms into six SEL dimensions. Student forms are scored separately and combined for the four-role descriptive summaries. Each item is normalised using its observed minimum and maximum within its form; available mapped items are averaged. There is no reverse-scoring transformation in this implementation. Item-level inputs, mapping order and normalisation ranges are deposited to make the transformation reproducible.

Cross-form contrasts concern the selected observed measures. They do not establish invariant latent differences or stakeholder preferences. Reliability is recomputed separately for each form and dimension using complete cases for the mapped items.

The exploratory analysis examines within-form Spearman associations between the AI-attitude composites and SEL dimensions. The deposited analytical subset reproduces the positive/concern composite correlations. Raw demographics and distress-module items are excluded, so demographic-adjusted models and distress-subgroup analyses are outside the public reconstruction scope.

## Profile-to-portrait translation

`data/portraits` preserves the generated portrait objects and their archived metric exports. Materialised prompts document Full, no-qualitative-level and numeric-only inputs. The two ablation comparisons are descriptive and use their respective generator subsets. `reproduce.py` averages their per-generator exported metrics; those exports are rounded to four decimals. The comparison does not test significance of a difference between metric declines.

## Classifier

The multilingual MiniLM–SetFit classifier uses 80 human role-conditioned answers and 138 nonempty portrait anchors. Portrait inputs remove explicit role names and omit pairwise role contrasts. H3 replies and condition labels are excluded from training.

Validation uses five folds grouped by the 20 human-answer scenarios, and a separate five-fold split grouped across nine portrait generators. The other anchor domain remains in training for each validation task. The archive includes out-of-fold predictions and grouped validation metrics.

Inference splits each reply into non-overlapping chunks of 120 tokenizer tokens, predicts probabilities for each chunk and averages those probabilities. The largest averaged probability determines the dominant predicted class. Both the saved checkpoint and portable training/inference scripts are provided.

## Framing and content

The Principal instruction combines identity and governance-focused task priorities. Speaker/task rewrites change the speaker's responsibilities, available information and requested action. Interpret these contrasts as effects of the tested framing packages.

Lexical matching counts exact occurrences of each listed Chinese string. Overlapping strings can contribute separate hits. The 32-term governance lexicon is an instruction-uptake measure; the content codes separately capture responsibility features and risks.

Bootstrap calculations use 5,000 scenario resamples and seed `20260825`. Content differences use paired scenario means, retaining the observed generators. Reproduced intervals condition on the stored fitted classifier and stored responses.

## What the commands do

| Script | Operation |
|---|---|
| `validate_release.py` | Check file hashes, data keys, counts, probabilities, codes and anchor separation |
| `reproduce.py` | Recompute descriptive profiles, selected E1 correlations, H2 summary comparisons, H3 shares and content results |
| `plot_results.py` | Regenerate both result figures from the reproduced tables |
| `download_model.py` | Download the versioned checkpoint and verify archive/file hashes |
| `infer.py` | Apply the saved classifier to archived replies or a supplied response CSV |
| `train_classifier.py` | Retrain on the anchor manifest and optionally rerun grouped validation |

The summary/plot commands perform no generation requests. The archived response corpus is the reproducibility source for the manuscript's generation results. Reissuing prompts to changing hosted models may produce different outputs.

The model card records the original training environment. Summary reconstruction is tested separately in the public package's pinned environment. Full retraining is optional and is not represented as having been rerun when packaging this release.
