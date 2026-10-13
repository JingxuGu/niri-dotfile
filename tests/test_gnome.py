from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

# Set before loading Gio or any settings; never write the real desktop.
os.environ['GSETTINGS_BACKEND'] = 'memory'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gnome


class GnomeTests(unittest.TestCase):
    def test_separate_profile_preserves_other_extensions_and_avoids_shortcuts(self):
        shell = gnome.settings_for('org.gnome.shell')
        original = {key: shell.get_user_value(key) for key in (
            'enabled-extensions', 'disabled-extensions', 'disable-user-extensions')}
        shell.set_strv('enabled-extensions', ['other.extension'])
        shell.set_strv('disabled-extensions', ['wanted.extension', 'other.disabled'])
        shell.set_boolean('disable-user-extensions', True)
        try:
            with tempfile.TemporaryDirectory() as directory, redirect_stdout(StringIO()):
                root = Path(directory)
                profile = root / 'profile.json'
                profile.write_text(json.dumps({'schemas': [], 'enable_extensions': ['wanted.extension']}))
                changes = gnome.plan_settings(profile)
                self.assertEqual(len(changes), 3)
                self.assertTrue(all(setting.props.schema_id == 'org.gnome.shell' for setting, _, _, _ in changes))
                gnome.apply_settings(changes, root / 'backup')
                self.assertEqual(shell.get_strv('enabled-extensions'), ['other.extension', 'wanted.extension'])
                self.assertEqual(shell.get_strv('disabled-extensions'), ['other.disabled'])
                self.assertFalse(shell.get_boolean('disable-user-extensions'))
                self.assertEqual(gnome.plan_settings(profile), [])
                gnome.apply_settings(gnome.plan_undo(root / 'backup/gnome-settings.json'), root / 'undo')
                self.assertEqual(shell.get_strv('enabled-extensions'), ['other.extension'])
                self.assertEqual(shell.get_strv('disabled-extensions'), ['wanted.extension', 'other.disabled'])
                self.assertTrue(shell.get_boolean('disable-user-extensions'))
        finally:
            for key, value in original.items():
                if value is None:
                    shell.reset(key)
                else:
                    shell.set_value(key, value)

    def test_apply_preserves_custom_shortcuts_and_undo_restores_defaults(self):
        interface = gnome.settings_for('org.gnome.desktop.interface')
        interface.set_string('gtk-theme', 'test-existing-theme')
        media = gnome.settings_for('org.gnome.settings-daemon.plugins.media-keys')
        previous_binding = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/existing/'
        media.set_strv('custom-keybindings', [previous_binding])
        before = gnome.plan_settings()
        originals = [(settings, key, settings.get_user_value(key)) for settings, key, _, _ in before]
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            root = Path(directory)
            gnome.apply_settings(before, root / 'first')
            self.assertEqual(interface.get_string('gtk-theme'), 'Yaru-dark')
            self.assertIn(previous_binding, media.get_strv('custom-keybindings'))
            self.assertEqual(len(media.get_strv('custom-keybindings')), 2)
            self.assertEqual(gnome.plan_settings(), [])
            backup = root / 'first/gnome-settings.json'
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
            gnome.apply_settings(gnome.plan_undo(backup), root / 'undo')
            self.assertEqual(media.get_strv('custom-keybindings'), [previous_binding])
            for settings, key, previous in originals:
                restored = settings.get_user_value(key)
                if previous is None:
                    self.assertIsNone(restored)
                else:
                    self.assertTrue(previous.equal(restored), key)
            self.assertTrue((root / 'undo/gnome-settings.json').is_file())

    def test_invalid_value_fails_during_planning(self):
        settings = gnome.settings_for('org.gnome.desktop.interface')
        with self.assertRaises((ValueError, gnome.GLib.Error)):
            gnome.add_change([], settings, 'color-scheme', "'invalid-theme-mode'")

    def test_missing_optional_schema_is_skipped(self):
        with redirect_stdout(StringIO()) as output:
            self.assertIsNone(gnome.settings_for('invalid.dotfile.optional', optional=True))
        self.assertIn('Skip optional schema', output.getvalue())
        with self.assertRaises(ValueError):
            gnome.settings_for('invalid.dotfile.required')


if __name__ == '__main__':
    unittest.main()
