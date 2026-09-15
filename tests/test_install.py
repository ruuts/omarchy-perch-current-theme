"""Exercise installation using a different username and an isolated home."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('perch_install', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='perch-install-test-')
        self.base = Path(self.temp.name)
        self.home = self.base / 'another user'
        self.home.mkdir()
        self.repo = self.base / 'checkout with spaces'
        (self.repo / 'theme/backgrounds').mkdir(parents=True)
        shutil.copy2(ROOT / 'install.py', self.repo / 'install.py')
        shutil.copy2(ROOT / 'perch-menu.qml', self.repo / 'perch-menu.qml')
        for name, value in {
            'colors.toml': 'background = "#273D36"\n',
            'neovim.lua': 'return {}\n',
            'hyprland.lua': 'hl.config({})\n',
            'opencode.json': '{"theme":{"text":"#EFEAD8"}}\n',
            'perch.svg': '<svg/>',
            'backgrounds/00-perch-current-ai-5k.png': 'fixture',
        }.items():
            (self.repo / 'theme' / name).write_text(value)
        (self.repo / 'theme/.git').mkdir()
        (self.repo / 'theme/.git/config').write_text('should not be copied')
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        # No real compositor, package manager, or network used by these tests.
        for command, source in {
            'omarchy-shell': '#!/bin/sh\nprintf "%s\\n" "${TEST_LOCKED:-false}"\n',
            'omarchy': '''#!/usr/bin/env python3
import os,sys,pathlib
h=pathlib.Path.home()
if sys.argv[1:3]==['theme','set']:
    p=h/'.local/state/omarchy/current'; p.mkdir(parents=True,exist_ok=True)
    (p/'theme.name').write_text(sys.argv[3]+'\\n')
elif sys.argv[1:4]==['plugin','clone','omarchy.menu']:
    p=h/'.config/omarchy/plugins'/f"{os.environ['USER']}.menu"
    p.mkdir(parents=True)
    (p/'BarWidget.qml').write_text('// stock clone')
''',
        }.items():
            path = self.bin / command
            path.write_text(source)
            path.chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), USER='riverfriend', PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        for key in ['XDG_CONFIG_HOME', 'XDG_STATE_HOME', 'CODEX_HOME']:
            self.env.pop(key, None)

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, *args, success=True):
        result = subprocess.run(['python3', str(self.repo / 'install.py'), *args], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return result

    def write(self, relative, value):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        return path

    def test_install_only_preserves_selection_and_drops_git_metadata(self):
        tui = self.write('.config/opencode/tui.json', '{"theme":"nord","scroll_speed":3}\n')
        self.invoke()
        target = self.home / '.config/omarchy/themes/perch-current'
        self.assertTrue((target / 'neovim.lua').exists())
        self.assertFalse((target / '.git').exists())
        self.assertEqual(json.loads(tui.read_text())['theme'], 'nord')
        self.assertFalse((self.home / '.local/state/omarchy/current/theme.name').exists())

    def test_activation_preserves_app_settings_and_uses_current_username(self):
        tui = self.write('.config/opencode/tui.json', '{"theme":"nord","scroll_speed":3}\n')
        codex = self.write('.codex/config.toml', '# Keep my config\nmodel = "my-model"\n[tui]\ntheme = "nord" # Keep comment\nnotifications = false\n[features]\nexample = true\n')
        transparency = self.write('.config/nvim/plugin/after/transparency.lua', 'local function make_transparent(name)\nend\n')
        self.invoke('--activate', '--perch-menu')
        self.assertEqual(json.loads(tui.read_text())['scroll_speed'], 3)
        self.assertEqual(json.loads(tui.read_text())['theme'], 'perch-current')
        parsed = tomllib.loads(codex.read_text())
        self.assertEqual(parsed['model'], 'my-model')
        self.assertEqual(parsed['tui'], {'theme': 'ansi', 'notifications': False})
        self.assertIn('# Keep comment', codex.read_text())
        self.assertTrue(parsed['features']['example'])
        self.assertIn('perch-current', transparency.read_text())
        widget = self.home / '.config/omarchy/plugins/riverfriend.menu/BarWidget.qml'
        self.assertIn('perch-current.enabled', widget.read_text())

    def test_reinstall_backs_up_local_changes(self):
        self.invoke()
        target = self.home / '.config/omarchy/themes/perch-current/colors.toml'
        target.write_text('local = "customization"\n')
        self.invoke()
        backups = list((self.home / '.local/state/perch-current/backups').glob('*/00-perch-current/colors.toml'))
        self.assertTrue(any(p.read_text() == 'local = "customization"\n' for p in backups))
        self.assertIn('background', target.read_text())

    def test_locked_session_stops_before_writing(self):
        self.env['TEST_LOCKED'] = 'true'
        self.invoke('--activate', success=False)
        self.assertFalse((self.home / '.config').exists())

    def test_existing_custom_menu_is_retained(self):
        widget = self.write('.config/omarchy/plugins/riverfriend.menu/BarWidget.qml', '// my own widget\n')
        self.invoke('--perch-menu', success=False)
        self.assertEqual(widget.read_text(), '// my own widget\n')
        self.assertFalse((self.home / '.config/omarchy/themes').exists())

    def test_symlinked_tui_contents_are_backed_up(self):
        actual = self.write('dotfiles/tui.json', '{"theme":"nord","scroll_speed":3}\n')
        tui = self.home / '.config/opencode/tui.json'
        tui.parent.mkdir(parents=True)
        tui.symlink_to(actual)
        self.invoke('--activate')
        self.assertTrue(tui.is_symlink())
        backups = list((self.home / '.local/state/perch-current/backups').glob('*/*-tui.json'))
        self.assertTrue(any(json.loads(p.read_text())['theme'] == 'nord' for p in backups))

    def test_codex_missing_theme_and_inline_table(self):
        text = '[tui]\nnotifications = false\n[features]\nexample = true\n'
        output = installer.codex_ansi(text)
        self.assertFalse(tomllib.loads(output)['tui']['notifications'])
        self.assertEqual(tomllib.loads(output)['tui']['theme'], 'ansi')
        with self.assertRaises(ValueError):
            installer.codex_ansi('tui = { theme = "nord" }\n')


if __name__ == '__main__':
    unittest.main()
