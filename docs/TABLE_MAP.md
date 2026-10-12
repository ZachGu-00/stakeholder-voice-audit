# Table and data guide

| Manuscript table | Deposited source | Check or output |
| --- | --- | --- |
| S1 | `data/survey_items.csv` | 43 item distributions; `survey_marginals.csv` |
| S2 | `data/survey_items.csv`, `data/survey_pairs.csv`, `data/survey_scale_anchors.csv` | Original wording, translations and response options |
| S3 | `data/survey_joint_counts.csv` | Main threshold in `joint_summary.csv` |
| S4 | Same joint counts | Four joint response categories |
| S5 | Same joint counts | Strict threshold in `joint_summary.csv` |
| S6 | Same joint counts | All 175 cells, with X as benefit and Y as concern |
| S7 | `data/scenarios.csv` | Category, difficulty and source-form counts |
| S8 | `data/codebook.json` | Thirteen features and two derived indicators |
| S9 | `data/labels.csv` | `agreement.csv`: contingency counts, agreement and kappa |
| S10 | `data/labels.csv`, `data/replies.csv` | `prevalence.csv`, coding version 1 |
| S11 | Same labels and replies | `prevalence.csv`, coding version 2 |
| S12 | Same labels and replies | `contrasts.csv`, coding version 1 |
| S13 | Same labels and replies | `contrasts.csv`, coding version 2 |
| S14 | Same labels and replies | Complete-scenario and double-coded-subset sensitivity |
| S15 | Same labels and replies | Results by model |
| S16 | Labels, replies and scenarios | Results by scenario category |
| S17 | Labels, replies and scenarios | Results by difficulty |

The exact manuscript LaTeX tables are in `results/tables/`. The reproduction command checks their numeric cells and writes reports to `results/reproduced/`. Main Tables 2 and 3 are also checked.

## Labels and replies

`response_id` is a release identifier linking replies to labels. `scenario_id` links to the constructed scenario. Model names follow the manuscript. `coding_split` is `calibration`, `single` or `double`. The 840 label records contain 552 single labels and 144 labels from each of two independent coders. A blank cell records an uncertain judgement.

Version 1 combines `single` and `coder_a`; version 2 combines `single` and `coder_b`. The versions share observations and are not independent studies. Joint indicators require both component labels to be observed.

Conditions A–D are `campus`, `procedure`, `boundary` and `procedure_boundary`. The primary contrast is B minus A. Other contrasts are secondary. Effects average paired differences within scenario and then across scenarios. Intervals resample scenarios 5,000 times. Condition prevalences use their observed denominators and are separate estimands.

## Questionnaire counts

`survey_items.csv` retains Chinese wording, English translations and frequencies of options 1–5. Main endorsement uses 4 or 5; strict endorsement uses 5. In `survey_joint_counts.csv`, each count was computed from two answers by the same respondent. The deposited aggregates reproduce the reported analyses without person-level records. Parent and teacher pairs reuse respondents, so pair denominators must not be added as distinct people.

Wilson intervals are descriptive and do not account for school clustering. Items differ across forms. Pair definitions and full wording are retained rather than treated as a common acceptance score.
