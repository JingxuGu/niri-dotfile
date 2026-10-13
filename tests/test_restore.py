import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.home.mkdir()

    def restore(self, *options, success=True):
        result = subprocess.run(
            [sys.executable, str(REPO / 'restore.py'), '--home', str(self.home), *options],
            capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_manifest_covers_only_current_template_files(self):
        manifest = json.loads((REPO / 'snapshot.json').read_text())
        listed = [item['path'] for item in manifest['files']]
        actual = [str(path.relative_to(REPO)) for path in (REPO / 'home').rglob('*') if path.is_file()]
        self.assertEqual(set(listed), set(actual))
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(manifest['system'], 'Ubuntu 22.04 LTS')

    def test_preview_apply_backup_and_second_apply(self):
        old = self.home / '.bashrc'
        old.write_text('original shell configuration\n')
        preview = self.restore()
        self.assertIn('Would restore .bashrc', preview.stdout)
        self.assertEqual(list(self.home.iterdir()), [old])
        result = self.restore('--apply')
        backups = list(self.home.glob('.local/state/ubuntu-dotfile-backups/*/.bashrc'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'original shell configuration\n')
        fastfetch = self.home / '.config/fastfetch/config.jsonc'
        self.assertIn(str(self.home), fastfetch.read_text())
        self.assertNotIn('/home/grainrain', fastfetch.read_text())
        self.assertIn('19 file(s) restored.', result.stdout)
        self.assertIn('0 file(s) restored.', self.restore('--apply').stdout)
        self.assertEqual(len(list(self.home.glob('.local/state/ubuntu-dotfile-backups/*'))), 1)

    def test_external_file_symlink_is_saved_without_changing_referent(self):
        external = Path(self.temp.name) / 'external'
        external.write_text('external data\n')
        (self.home / '.bashrc').symlink_to(external)
        self.restore('--apply')
        saved = next(self.home.glob('.local/state/ubuntu-dotfile-backups/*/.bashrc'))
        self.assertTrue(saved.is_symlink())
        self.assertEqual(saved.readlink(), external)
        self.assertEqual(external.read_text(), 'external data\n')
        self.assertFalse((self.home / '.bashrc').is_symlink())

    def test_broken_symlink_is_saved(self):
        (self.home / '.bashrc').symlink_to('missing')
        self.restore('--apply')
        saved = next(self.home.glob('.local/state/ubuntu-dotfile-backups/*')) / '.bashrc'
        self.assertTrue(saved.is_symlink())
        self.assertEqual(saved.readlink(), Path('missing'))

    def test_conflicting_directory_fails_before_any_write(self):
        (self.home / '.zshrc').mkdir()
        result = self.restore('--apply', success=False)
        self.assertIn('Refusing to replace a directory', result.stderr)
        self.assertFalse((self.home / '.bashrc').exists())

    def test_external_parent_symlink_is_rejected(self):
        external = Path(self.temp.name) / 'external-directory'
        external.mkdir()
        (self.home / '.config').symlink_to(external, target_is_directory=True)
        result = self.restore('--apply', success=False)
        self.assertIn('outside target home', result.stderr)
        self.assertEqual(list(external.iterdir()), [])
        self.assertFalse((self.home / '.bashrc').exists())

    def test_conflicting_parent_file_fails_before_any_write(self):
        (self.home / '.config').write_text('not a directory')
        result = self.restore('--apply', success=False)
        self.assertIn('not a directory', result.stderr)
        self.assertFalse((self.home / '.bashrc').exists())

    def test_other_home_cannot_change_current_gnome_session(self):
        result = self.restore('--apply', '--gnome', success=False)
        self.assertIn('cannot be used with another --home', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
