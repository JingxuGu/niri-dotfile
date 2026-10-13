#!/usr/bin/env python3
"""Preview or restore Ubuntu 22.04 + GNOME configuration with backups."""
import argparse
from datetime import datetime
from pathlib import Path
import json
import os
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true', help='write files (default: preview only)')
parser.add_argument('--home', type=Path, default=Path.home(), help='destination home directory')
parser.add_argument('--gnome', action='store_true', help='also preview/apply settings in the current GNOME session (requires python3-gi)')
args = parser.parse_args()
repo = Path(__file__).resolve().parent
target_home = args.home.expanduser().resolve()
backup_root = target_home / '.local/state/ubuntu-dotfile-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
if args.gnome and target_home != Path.home().resolve():
    parser.error('--gnome affects the current session and cannot be used with another --home')
gnome_changes = []
if args.gnome:
    if args.apply and os.environ.get('GSETTINGS_BACKEND', 'dconf') == 'dconf' and not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        parser.error('Run from a terminal in your GNOME desktop session, without sudo.')
    try:
        from gnome import plan_settings, describe, apply_settings
        gnome_changes = plan_settings()
    except (ImportError, ValueError) as error:
        parser.exit(1, f'GNOME preflight failed: {error}\n')
changes = []
snapshot = json.loads((repo / 'snapshot.json').read_text())
for item in sorted(snapshot['files'], key=lambda item: item['path']):
    source = repo / item['path']
    if not source.is_file() or source.is_symlink() or repo / 'home' not in source.resolve().parents:
        raise SystemExit(f'Invalid snapshot source: {source}')
    relative = source.relative_to(repo / 'home')
    target = target_home / relative
    if not target.parent.resolve().is_relative_to(target_home):
        raise SystemExit(f'Refusing destination outside target home: {target}')
    # Detect parent-file conflicts before restoring any files.
    for parent in target.parents:
        if parent == target_home:
            break
        if parent.exists() and not parent.is_dir():
            raise SystemExit(f'Destination parent is not a directory: {parent}')
    if target.exists() and target.is_dir():
        raise SystemExit(f'Refusing to replace a directory: {target}')
    content = source.read_text().replace(snapshot['source_home'], str(target_home))
    if target.is_file() and not target.is_symlink() and target.read_bytes() == content.encode():
        continue
    changes.append((source, relative, target, content))

if changes or gnome_changes:
    if not backup_root.resolve().is_relative_to(target_home):
        raise SystemExit(f'Refusing backup location outside target home: {backup_root}')

for source, relative, target, content in changes:
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
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    target.chmod(source.stat().st_mode & 0o777)
print(f'{len(changes)} file(s) ' + ('restored.' if args.apply else 'would change. Use --apply to restore.'))
if args.gnome:
    describe(gnome_changes)
    print(f'{len(gnome_changes)} GNOME setting(s) ' + ('to apply.' if args.apply else 'would change.'))
    if args.apply:
        apply_settings(gnome_changes, backup_root)
if args.apply:
    if changes or gnome_changes:
        print(f'Backup location (created when needed): {backup_root}')
    print('Next: deploy Rime in Fcitx5; log out and back in; reopen Kitty.')
