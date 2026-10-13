#!/usr/bin/env python3
"""Preview, apply or undo the managed GNOME settings in the current session."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path

from gi.repository import Gio, GLib

REPO = Path(__file__).resolve().parent


def settings_for(schema_id, path=None, optional=False):
    schema = Gio.SettingsSchemaSource.get_default().lookup(schema_id, True)
    if schema is None:
        if optional:
            print(f'Skip optional schema: {schema_id}')
            return None
        raise ValueError(f'Missing GNOME schema: {schema_id}')
    return Gio.Settings.new_full(schema, None, path)


def add_change(changes, settings, key, text, optional=False):
    schema = settings.props.settings_schema
    if not schema.has_key(key):
        if optional:
            print(f'Skip optional key: {schema.get_id()} {key}')
            return
        raise ValueError(f'Missing GNOME key: {schema.get_id()} {key}')
    value = (settings.get_default_value(key) if text is None else
             GLib.Variant.parse(schema.get_key(key).get_value_type(), text, None, None))
    if not schema.get_key(key).range_check(value):
        raise ValueError(f'Invalid value for {schema.get_id()} {key}: {text}')
    if text is None:
        unchanged = settings.get_user_value(key) is None
    else:
        unchanged = settings.get_value(key).equal(value)
    if unchanged:
        return
    if not settings.is_writable(key):
        raise ValueError(f'GNOME setting is locked: {schema.get_id()} {key}')
    changes.append((settings, key, text, value))


def plan_settings():
    config = json.loads((REPO / 'gnome/settings.json').read_text())
    changes = []
    for group in config['schemas']:
        optional = group.get('optional', False)
        settings = settings_for(group['id'], optional=optional)
        if settings is not None:
            for key, text in group['values'].items():
                add_change(changes, settings, key, text, optional)
    media = settings_for('org.gnome.settings-daemon.plugins.media-keys')
    paths = media.get_strv('custom-keybindings')
    for binding in config['custom_keybindings']:
        path = binding['path']
        settings = settings_for(
            'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding', path)
        for key in ('name', 'command', 'binding'):
            add_change(changes, settings, key, GLib.Variant('s', binding[key]).print_(True))
        if path not in paths:
            paths.append(path)
    # Register our binding while retaining all existing custom shortcuts.
    add_change(changes, media, 'custom-keybindings', GLib.Variant('as', paths).print_(True))
    return changes


def plan_undo(backup):
    changes = []
    for item in json.loads(backup.read_text()):
        settings = settings_for(item['schema'], item['path'])
        add_change(changes, settings, item['key'], item['value'])
    return changes


def describe(changes):
    for settings, key, text, _ in changes:
        print(f'GNOME {settings.props.schema_id} {key} = {text if text is not None else "<default>"}')


def apply_settings(changes, backup_root):
    if not changes:
        return
    # Capture only managed keys, including whether they were explicitly set.
    original = []
    for settings, key, _, _ in changes:
        value = settings.get_user_value(key)
        original.append({
            'schema': settings.props.schema_id,
            'path': settings.props.path,
            'key': key,
            'value': value.print_(True) if value is not None else None,
        })
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / 'gnome-settings.json'
    # Never overwrite an earlier backup.
    with backup.open('x') as stream:
        os.chmod(backup, 0o600)
        json.dump(original, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(f'GNOME backup: {backup}')
    try:
        for settings, key, text, value in changes:
            if text is None:
                settings.reset(key)
            elif not settings.set_value(key, value):
                raise RuntimeError(f'Could not set {settings.props.schema_id} {key}')
        Gio.Settings.sync()
    except Exception:
        for item in original:
            settings = settings_for(item['schema'], item['path'])
            if item['value'] is None:
                settings.reset(item['key'])
            else:
                settings.set_value(item['key'], GLib.Variant.parse(
                    settings.get_value(item['key']).get_type(), item['value'], None, None))
        Gio.Settings.sync()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='write settings; default: preview')
    parser.add_argument('--undo', type=Path, help='preview/restore managed keys from a backup')
    args = parser.parse_args()
    if args.apply and os.environ.get('GSETTINGS_BACKEND', 'dconf') == 'dconf' and not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        parser.error('Run from a terminal in your GNOME desktop session, without sudo.')
    try:
        changes = plan_undo(args.undo) if args.undo else plan_settings()
        describe(changes)
        print(f'{len(changes)} GNOME setting(s) would change.')
        if args.apply:
            backup_root = Path.home() / '.local/state/ubuntu-dotfile-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            apply_settings(changes, backup_root)
    except (ValueError, GLib.Error, OSError, RuntimeError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
