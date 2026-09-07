"""Apply the released SetFit classifier with the original chunk-mean procedure."""
from pathlib import Path
import argparse
import json
import os
os.environ.setdefault('WANDB_DISABLED', 'true')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
import numpy as np
import pandas as pd
from setfit import SetFitModel

ROOT = Path(__file__).resolve().parents[1]
ROLES = ['student', 'parent', 'teacher', 'principal']


def predict(model, texts, batch_size=64):
    tokenizer = model.model_body.tokenizer
    chunks, owners = [], []
    counts = np.zeros(len(texts), dtype=int)
    for owner, text in enumerate(texts):
        ids = tokenizer.encode(str(text or ''), add_special_tokens=False, verbose=False)
        if not ids:
            # Retain one chunk for an empty input instead of dividing by zero.
            chunks.append(' ')
            owners.append(owner)
            counts[owner] = 1
            continue
        for start in range(0, len(ids), 120):
            chunks.append(tokenizer.decode(ids[start:start + 120], skip_special_tokens=True))
            owners.append(owner)
            counts[owner] += 1
    if not chunks:
        return np.array([], dtype=str), np.empty((0, 4)), counts
    chunk_probs = np.asarray(model.predict_proba(chunks, batch_size=batch_size, as_numpy=True,
                                                 show_progress_bar=True), dtype=float)
    probs = np.zeros((len(texts), 4), dtype=float)
    np.add.at(probs, owners, chunk_probs)
    probs /= counts[:, None]
    return np.asarray(ROLES)[probs.argmax(axis=1)], probs, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=ROOT / 'models/checkpoint')
    parser.add_argument('--input', type=Path, default=ROOT / 'data/llm/responses.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/inference_predictions.csv')
    parser.add_argument('--limit', type=int, default=0, help='0 processes every row')
    parser.add_argument('--batch-size', type=int, default=64)
    args = parser.parse_args()
    if not args.model.is_dir():
        parser.error('Checkpoint not found. Run python scripts/download_model.py first.')
    data = pd.read_csv(args.input)
    if args.limit:
        data = data.head(args.limit)
    if 'response_text' not in data:
        parser.error('Input must contain a response_text column.')
    model = SetFitModel.from_pretrained(str(args.model), local_files_only=True)
    if list(model.labels) != ROLES:
        raise ValueError(f'Unexpected class order: {model.labels}')
    labels, probs, counts = predict(model, data.response_text.fillna('').tolist(), args.batch_size)
    output = data[['response_id']].copy() if 'response_id' in data else pd.DataFrame(index=data.index)
    output['predicted_role'] = labels
    output['chunk_count'] = counts
    for index, role in enumerate(ROLES):
        output[f'prob_{role}'] = probs[:, index]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, encoding='utf-8')
    report = {'responses': len(data), 'output': str(args.output)}
    if 'bridge_role' in data and len(data):
        report['agreement_with_archived_labels'] = float(np.mean(labels == data.bridge_role))
        expected = data[[f'bridge_prob_{r}' for r in ROLES]].to_numpy()
        report['max_absolute_probability_difference'] = float(np.max(np.abs(probs - expected)))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
