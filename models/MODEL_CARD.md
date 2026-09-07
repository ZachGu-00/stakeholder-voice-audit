# Stakeholder voice classifier

## Model and intended use

A multilingual MiniLM–SetFit classifier for the dominant stakeholder-associated register of Chinese chatbot replies to school-related social-emotional scenarios. Class order: **student, parent, teacher, principal**.

The backbone is [`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2), with a 384-dimensional embedding and a multinomial logistic-regression head. This checkpoint was fine-tuned for the present audit.

## Training data

- 80 human role-conditioned answers: 20 scenarios and four role labels.
- 138 nonempty H2 portrait anchors from nine generators.
- Explicit role names are removed from portrait text; pairwise role contrasts are omitted.
- Generated H3 replies and framing labels are excluded from training.

Training examples and group identifiers are deposited in `data/classifier/voice_bridge_training_manifest.csv`.

## Archived validation

| Held-out domain | Records | Grouping | Accuracy | Macro-F1 |
|---|---:|---|---:|---:|
| Human role-conditioned answers | 80 | Five folds across 20 scenarios | 0.9125 | 0.9133 |
| Portrait anchors | 138 | Five folds across nine generators | 1.0000 | 1.0000 |

The second domain is closely related to the construct-defining portrait material. These values describe validation within the deposited domains and do not establish performance for arbitrary languages, tasks or actual stakeholder identity.

## Inference

Inputs are split into non-overlapping 120-token chunks. The classifier's four probabilities are computed for each chunk and averaged per reply. The argmax determines the predicted register. Probabilities are model scores, not the proportion of a reply expressing institutional responsibility.

`scripts/infer.py` implements the archived inference procedure. The checkpoint is packaged as `stakeholder-voice-classifier-v1.0.0.zip` in the repository's v1.0.0 release. `release_asset.json` and `checkpoint_files.json` provide SHA-256 hashes.

## Original framework versions

The saved model card records Python 3.13.5, SetFit 1.1.3, Sentence Transformers 5.1.0, Transformers 4.55.2, PyTorch 2.8.0+cu128, Datasets 5.0.1 and Tokenizers 0.21.4. The persisted logistic-regression head records scikit-learn 1.6.1. `requirements-model.txt` specifies a portable environment with the matching model-library versions.

Training settings: batch sizes `(16, 4)`, epochs `(1, 16)`, ten contrastive iterations, body learning rates `(2e-5, 1e-5)`, head learning rate `0.01`, maximum length 128 and final-training seed `20260825`. The released fitted weights preserve the archived model; retraining may vary across hardware or upstream checkpoint revisions.

## Attribution and use

The upstream backbone is distributed under Apache 2.0. Its license and attribution accompany this derived checkpoint. The saved `model_head.pkl` is a Python pickle; load checkpoint files only from a trusted source and verify the supplied checksums.

Use the classifier for research on response registers. Content quality, procedural appropriateness and safety are assessed separately through the study's coding framework.
