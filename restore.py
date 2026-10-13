#!/usr/bin/env python3
"""Preview or restore this configuration snapshot, backing up changed files."""
import argparse
from datetime import datetime
from pathlib import Path
import json
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true', help='write files (default: preview only)')
parser.add_argument('--home', type=Path, default=Path.home(), help='destination home directory')
args = parser.parse_args()
repo = Path(__file__).resolve().parent
target_home = args.home.expanduser().resolve()
backup_root = target_home / '.local/state/niri-dotfile-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
changed = 0
snapshot = json.loads((repo / 'snapshot.json').read_text())
for item in sorted(snapshot['files'], key=lambda item: item['path']):
    source = repo / item['path']
    if not source.is_file() or repo / 'home' not in source.resolve().parents:
        raise SystemExit(f'Invalid snapshot source: {source}')
    relative = source.relative_to(repo / 'home')
    target = target_home / relative
    content = source.read_text().replace('/home/grainrain', str(target_home))
    if target.is_file() and target.read_text() == content:
        continue
    changed += 1
    print(('Restore ' if args.apply else 'Would restore ') + str(relative))
    if not args.apply:
        continue
    if target.exists() or target.is_symlink():
        saved = backup_root / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            saved.symlink_to(target.readlink())
            target.unlink()
        elif target.is_file():
            shutil.copy2(target, saved)
        else:
            raise SystemExit(f'Refusing to replace a directory: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    target.chmod(source.stat().st_mode & 0o777)
print(f'{changed} file(s) ' + ('restored.' if args.apply else 'would change. Use --apply to restore.'))
if args.apply:
    print(f'Existing files backed up under: {backup_root}')
    print('Next: niri validate; fuzzel --check-config; rebuild Rime; reopen Kitty.')
