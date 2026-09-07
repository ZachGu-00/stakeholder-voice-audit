# Data guide

## Survey observations

| File | Form | Records |
|---|---|---:|
| `data/survey/primary_student.csv` | Primary-school students | 9,566 |
| `data/survey/middle_student.csv` | Middle-school students | 3,923 |
| `data/survey/parent.csv` | Parents | 12,266 |
| `data/survey/teacher.csv` | Teachers | 1,546 |
| `data/survey/principal.csv` | Principals | 95 |

The two student forms together contain 13,489 observations. These are questionnaire participants, distinct from the generated-response and content-coding samples.

Each form has a new `record_id` and numeric question columns (`q001`, `q002`, etc.). Question identifiers are **form-specific**: `q001` in one form need not represent the same item as `q001` in another form. Blank CSV values mean missing observations. Recorded numeric item values are preserved without imputation or reversal. Category labels and question wording should be interpreted using the corresponding blank instrument.

`item_dictionary.csv` provides:

| Field | Meaning |
|---|---|
| `form`, `role` | Questionnaire form and stakeholder group |
| `variable` | Column name in the released form |
| `question_zh` | Original Chinese item header, retained to preserve the item mapping |
| `sel_dimensions` | Associated SEL dimensions, separated by `\|` where needed |
| `sel_dimension_order` | Original item summation order within each dimension |
| `ai_polarity`, `ai_item_label`, `ai_item_order` | Exploratory attitude-composite membership and order |
| `observed_min`, `observed_max`, `observed_values` | Observed coding range and values, not assumed theoretical endpoints |
| `n_observed` | Nonmissing response count |

`dimension_scores.csv` contains the six SEL scores and two AI-attitude composites, linked to the released form through `record_id`. Scores use item-wise observed min–max normalisation within each questionnaire form, followed by the mean of available mapped items. A constant item produces a missing normalised value. Some forms have no mapped concern items; their concern composite is missing.

The release omits source respondent identifiers, school and class identifiers, grade, demographic characteristics, free-text metadata and unmapped questions. Records are shuffled separately within each form. No linkage key to the original identifiers is published. This analytical subset supports the reported profiles and AI-attitude correlations; demographic-adjusted regressions and unrelated questionnaire modules are outside its reproduction scope.

## Generated replies

`data/llm/responses.csv` has one row per generated reply:

| Condition | Replies | Scenarios | Generators | Samples per scenario/generator |
|---|---:|---:|---:|---:|
| `default` | 900 | 60 | 3 | 5 |
| `principal_prompt` | 540 | 60 | 3 | 3 |
| `teacher_speaker` | 90 | 10 | 3 | 3 |
| `principal_speaker` | 90 | 10 | 3 | 3 |
| `gpt5_4_default` | 180 | 60 | 1 | 3 |

`response_id` is the primary key. `scenario_id` links to scenario materials. `model`, `condition` and `sample_index` identify the generation cell. `scenario_text` and `response_text` retain the original Chinese text. `prompt_text` is included where stored; blank values indicate that this field was absent in the source export. The separately deposited materialised prompts document each prompt family. `status` and `refusal` retain the recorded generation/status flags.

The final classifier outputs are `bridge_role`, `bridge_chunk_count` and `bridge_prob_student`, `bridge_prob_parent`, `bridge_prob_teacher`, `bridge_prob_principal`. Class probabilities sum to one. Historical cosine/fingerprint scores and runtime/error logs are excluded from the public response table.

## Content codes

`data/coding/response_codes.csv` contains 420 rows: 180 default, 180 Principal-instruction, 30 teacher-speaker and 30 principal-speaker replies. Each was linked to the deposited reply by scenario, generator, condition and normalised response text; the coding sample uses `sample_index = 1`.

The thirteen binary features are described in [CODING_GUIDE.md](CODING_GUIDE.md). `positive_index` sums the first six features (0–6); `risk_index` sums the remaining seven (0–7). This table contains the final codes used in the analysis. It does not contain separate pre-adjudication coder records, and cannot by itself reproduce inter-rater reliability.

## Classifier and portraits

The training manifest contains 80 human role-conditioned answers and 138 role-redacted portrait anchors. Fields are `record_id`, `label`, `text`, `group`, `source_domain` and `prompt_variant`. Group identifiers refer to human-answer scenarios or portrait generators. They are not personal identifiers. Training text remains in Chinese.

The Full portrait file preserves all 157 stored objects, including malformed or empty objects. Of these, 154 have a valid single-role label, and 138 also have a nonempty summary suitable for classifier training. Individual metric exports have their own evaluated row counts. Use the supplied training manifest for classifier inputs instead of assuming that every stored portrait is a training example.

The two ablations retain their original condition-specific files. Their three-generator subsets differ. Summary rows prefixed `MEAN` are legacy summaries; `scripts/reproduce.py` recomputes each comparison from that ablation's generator rows.

## File integrity and provenance

CSV files use UTF-8 with a single header row. JSON files use UTF-8. `data/provenance.json` identifies the source artifacts and transformations for curated exports. `data/file_manifest.json` records release file sizes and SHA-256 hashes. Run `python scripts/validate_release.py` on a clean checkout to check integrity.

Reference tables preserve archived results. `results/reproduced` contains tables regenerated from the released analytical inputs. Regenerating figures may alter image metadata while preserving plotted values.
