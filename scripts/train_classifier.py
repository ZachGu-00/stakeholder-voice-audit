"""Retrain the classifier from the released anchors; optionally rerun grouped CV."""
from pathlib import Path
import argparse
import gc
import os
os.environ.setdefault('WANDB_DISABLED', 'true')
os.environ.setdefault('WANDB_MODE', 'disabled')
import numpy as np
import pandas as pd
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
ROLES = ['student', 'parent', 'teacher', 'principal']


def fit(frame, backbone, output, seed):
    model = SetFitModel.from_pretrained(backbone, labels=ROLES)
    dataset = Dataset.from_dict({'text': frame.text.tolist(),
                                 'label': [ROLES.index(label) for label in frame.label]})
    args = TrainingArguments(output_dir=str(output), batch_size=(16, 4), num_epochs=(1, 16),
        num_iterations=10, body_learning_rate=(2e-5, 1e-5), head_learning_rate=.01,
        max_length=128, show_progress_bar=False, report_to='none', logging_strategy='no',
        save_strategy='no', seed=seed)
    trainer = Trainer(model=model, args=args, train_dataset=dataset)
    trainer.train()
    del trainer, dataset
    gc.collect()
    return model


def validate(human, portraits, backbone, output):
    rows = []
    tasks = [('p01_scenario_grouped', human, portraits,
              StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20260825)),
             ('h2_generator_grouped', portraits, human, GroupKFold(n_splits=5))]
    for name, target, anchors, splitter in tasks:
        for fold, (train_index, test_index) in enumerate(splitter.split(target.text, target.label, target.group), start=1):
            pieces = [target.iloc[train_index], anchors] if name == 'p01_scenario_grouped' else [anchors, target.iloc[train_index]]
            train = pd.concat(pieces, ignore_index=True)
            seed = (20260825 if name == 'p01_scenario_grouped' else 20260925) + fold
            model = fit(train, backbone, output / name / f'fold_{fold}', seed)
            test = target.iloc[test_index].copy()
            prediction = np.asarray(model.predict(test.text.tolist(), as_numpy=True, use_labels=True, show_progress_bar=False))
            if np.issubdtype(prediction.dtype, np.integer):
                prediction = np.asarray(ROLES)[prediction]
            for record, label in zip(test.to_dict('records'), prediction):
                rows.append({'validation': name, 'record_id': record['record_id'],
                             'group': record['group'], 'label': record['label'], 'prediction': label})
            del model
            gc.collect()
    result = pd.DataFrame(rows)
    result.to_csv(output / 'oof_predictions.csv', index=False)
    metrics = []
    for name, group in result.groupby('validation'):
        metrics.append({'validation': name, 'n': len(group),
            'accuracy': accuracy_score(group.label, group.prediction),
            'macro_f1': f1_score(group.label, group.prediction, labels=ROLES, average='macro')})
    pd.DataFrame(metrics).to_csv(output / 'validation_metrics.csv', index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backbone', default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                        help='Upstream backbone name or local path; use the released checkpoint for exact inference.')
    parser.add_argument('--output', type=Path, default=ROOT / 'training_output')
    parser.add_argument('--cross-validate', action='store_true', help='Run all grouped folds before final training')
    args = parser.parse_args()
    training = pd.read_csv(ROOT / 'data/classifier/voice_bridge_training_manifest.csv')
    human = training[training.source_domain.eq('p01_human_response')].reset_index(drop=True)
    portraits = training[training.source_domain.eq('h2_role_portrait')].reset_index(drop=True)
    assert len(human) == 80 and human.group.nunique() == 20
    assert len(portraits) == 138 and portraits.group.nunique() == 9
    assert not portraits.text.str.contains('学生|家长|教师|校长', regex=True).any()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.cross_validate:
        validate(human, portraits, args.backbone, args.output)
    model = fit(training, args.backbone, args.output / 'training', 20260825)
    model.save_pretrained(str(args.output / 'checkpoint'))
    print(f'Saved retrained checkpoint to {args.output / "checkpoint"}')


if __name__ == '__main__':
    main()
