"""Download the versioned checkpoint and verify it before extraction."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an already downloaded archive')
    args = parser.parse_args()
    metadata = json.loads((ROOT / 'models/release_asset.json').read_text())
    expected = json.loads((ROOT / 'models/checkpoint_files.json').read_text())
    destination = ROOT / 'models/checkpoint'
    if destination.exists():
        if all((destination / item['path']).is_file() and digest(destination / item['path']) == item['sha256'] for item in expected):
            print('Checkpoint already present; all file checksums match.')
            return
        raise RuntimeError('Checkpoint directory exists with incomplete or different files. Move it aside before retrying.')
    with tempfile.TemporaryDirectory(prefix='voice-checkpoint-') as temporary:
        tmp = Path(temporary)
        archive = args.archive or tmp / metadata['name']
        if not args.archive:
            request = urllib.request.Request(metadata['url'], headers={'User-Agent': 'stakeholder-voice-audit'})
            with urllib.request.urlopen(request, timeout=120) as source, archive.open('wb') as target:
                shutil.copyfileobj(source, target)
        if digest(archive) != metadata['sha256']:
            raise ValueError('Checkpoint archive checksum mismatch.')
        unpacked = tmp / 'unpacked'
        unpacked.mkdir()
        with zipfile.ZipFile(archive) as zipped:
            for name in zipped.namelist():
                target = (unpacked / name).resolve()
                if not target.is_relative_to(unpacked.resolve()):
                    raise ValueError('Unsafe archive member path.')
            zipped.extractall(unpacked)
        candidate = unpacked / 'checkpoint'
        for item in expected:
            if digest(candidate / item['path']) != item['sha256']:
                raise ValueError(f'File checksum mismatch: {item["path"]}')
        shutil.move(str(candidate), str(destination))
    print(f'Installed verified checkpoint: {destination}')


if __name__ == '__main__':
    main()
