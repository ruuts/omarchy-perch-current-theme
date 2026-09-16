#!/usr/bin/env python3
"""Portable Perch Current installer. Python 3.11+, no third-party modules."""
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent
SLUG = 'perch-current'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def check_unlocked():
    result = run('omarchy-shell', 'lock', 'isLocked', capture_output=True, timeout=5)
    if result.stdout.strip() != 'false':
        raise RuntimeError('Unlock the desktop before activation or menu-plugin changes.')


def codex_ansi(text):
    """Change just the TUI theme, preserving unrelated TOML and comments."""
    config = tomllib.loads(text)
    if config.get('tui', {}).get('theme') == 'ansi':
        return text
    header = re.search(r'^\[tui\][ \t]*(?:#.*)?$', text, re.M)
    if not header:
        # A nested table such as [tui.model_availability_nux] creates an
        # implicit tui parent. TOML permits declaring that parent afterwards.
        if isinstance(config.get('tui'), dict) and 'theme' not in config['tui']:
            return text.rstrip() + '\n\n[tui]\ntheme = "ansi"\n'
        if 'tui' in config:
            raise ValueError('Codex uses a nonstandard TUI table. Set tui.theme = "ansi" manually.')
        return text.rstrip() + '\n\n[tui]\ntheme = "ansi"\n'
    next_table = re.search(r'^\s*\[', text[header.end():], re.M)
    end = header.end() + next_table.start() if next_table else len(text)
    body = text[header.end():end]
    key = re.search(r'^(\s*theme\s*=\s*)("[^"\n]*"|\x27[^\x27\n]*\x27)([^\n]*)$', body, re.M)
    if key:
        body = body[:key.start()] + key[1] + '"ansi"' + key[3] + body[key.end():]
    elif 'theme' in config.get('tui', {}):
        raise ValueError('Cannot safely edit the Codex theme key. Set it manually.')
    else:
        body = '\ntheme = "ansi"' + body
    result = text[:header.end()] + body + text[end:]
    assert tomllib.loads(result)['tui']['theme'] == 'ansi'
    return result


class Backups:
    def __init__(self, path):
        self.path = path
        self.entries = []

    def save(self, destination):
        self.path.mkdir(parents=True, exist_ok=True)
        saved = None
        if destination.exists() or destination.is_symlink():
            saved = self.path / f'{len(self.entries):02d}-{destination.name}'
            if destination.is_dir() and not destination.is_symlink():
                shutil.copytree(destination, saved, symlinks=True)
            elif destination.is_symlink() and not destination.is_file():
                saved.symlink_to(os.readlink(destination))
            else:
                shutil.copy2(destination, saved)
        self.entries.append({'destination': str(destination), 'backup': str(saved) if saved else None,
                             'symlink_target': os.readlink(destination) if destination.is_symlink() else None})
        (self.path / 'manifest.json').write_text(json.dumps(self.entries, indent=2) + '\n')

    def write(self, destination, text):
        self.save(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Follow existing file symlinks for user configuration, retaining them.
        destination.write_text(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true', help='Apply theme and select its app colors')
    parser.add_argument('--perch-menu', action='store_true', help='Add the perch to a user-owned menu clone (unlocked desktop required)')
    args = parser.parse_args(argv)
    home = Path.home()
    config = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    state = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state'))
    # Current Omarchy shell/theme commands use these conventional locations.
    if config != home / '.config' or state != home / '.local/state':
        raise RuntimeError('This Omarchy version requires ~/.config and ~/.local/state; unset custom XDG paths for installation.')
    source = ROOT / 'theme'
    for name in ['colors.toml', 'neovim.lua', 'hyprland.lua', 'opencode.json', 'backgrounds/00-perch-current-ai-5k.png']:
        if not (source / name).is_file():
            raise RuntimeError(f'Missing release asset: {name}')
    tomllib.loads((source / 'colors.toml').read_text())
    app_theme = json.loads((source / 'opencode.json').read_text())
    assert isinstance(app_theme['theme'], dict)
    if args.activate or args.perch_menu:
        if not shutil.which('omarchy') or not shutil.which('omarchy-shell'):
            raise RuntimeError('Activation requires a running, current Omarchy installation.')
        check_unlocked()

    # Parse app configs before changing files so malformed input is left intact.
    tui_path = config / 'opencode/tui.json'
    tui = json.loads(tui_path.read_text()) if args.activate and tui_path.exists() else {}
    if not isinstance(tui, dict):
        raise ValueError('OpenCode tui.json must contain an object.')
    codex_path = Path(os.environ.get('CODEX_HOME', home / '.codex')) / 'config.toml'
    codex_text = None
    if args.activate and codex_path.exists():
        codex_text = codex_ansi(codex_path.read_text())
    username = os.environ.get('USER') or getpass.getuser()
    menu = config / 'omarchy/plugins' / f'{username}.menu'
    widget = menu / 'BarWidget.qml'
    if args.perch_menu and menu.exists() and (not widget.exists() or 'perch-current.enabled' not in widget.read_text()):
        raise RuntimeError(f'Existing menu customization retained: {menu}. Rerun without --perch-menu.')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = Backups(state / SLUG / 'backups' / stamp)
    target = config / 'omarchy/themes' / SLUG
    backup.save(target)
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Copy plain files rather than symlinking a git checkout: Omarchy then keeps
    # the custom Neovim/terminal Lua and configs as a user-owned theme.
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '01-perch-current-5k.png'))
    open_theme = config / 'opencode/themes' / f'{SLUG}.json'
    backup.write(open_theme, json.dumps(app_theme, indent=2) + '\n')

    if args.perch_menu:
        check_unlocked()
        backup.save(config / 'omarchy/shell.json')
        if not menu.exists():
            run('omarchy', 'plugin', 'clone', 'omarchy.menu', timeout=30)
        for name, content in [('BarWidget.qml', (ROOT / 'perch-menu.qml').read_text()), ('perch.svg', (source / 'perch.svg').read_text())]:
            check_unlocked()
            backup.write(menu / name, content)

    if args.activate:
        check_unlocked()
        # Save configs before Omarchy's own hooks can touch them.
        backup.save(tui_path)
        backup.save(state / 'omarchy/current/theme.name')
        backup.save(state / 'omarchy/current/background')
        cursor_hook = config / 'omarchy/hooks/theme-set.d/perch-current-cursor'
        backup.write(cursor_hook, (ROOT / 'hooks/theme-set.d/perch-current-cursor').read_text())
        cursor_hook.chmod(0o755)
        run('omarchy', 'theme', 'set', SLUG, timeout=120)
        tui.setdefault('$schema', 'https://opencode.ai/tui.json')
        tui['theme'] = SLUG
        tui_path.parent.mkdir(parents=True, exist_ok=True)
        tui_path.write_text(json.dumps(tui, indent=2) + '\n')
        if codex_text is not None and codex_text != codex_path.read_text():
            backup.write(codex_path, codex_text)

        # This optional user customization existed on the development machine.
        # Patch only the recognized script, preserving its behavior for other themes.
        transparency = config / 'nvim/plugin/after/transparency.lua'
        if transparency.exists():
            text = transparency.read_text()
            if 'perch-current' not in text and 'local function make_transparent(name)' in text:
                guard = '''-- Perch Current supplies intentional backgrounds for alpha matching.
local perch_name = vim.fn.expand("~/.local/state/omarchy/current/theme.name")
if vim.fn.filereadable(perch_name) == 1 and vim.fn.readfile(perch_name)[1] == "perch-current" then
  return
end

'''
                backup.write(transparency, guard + text)
        if args.perch_menu:
            # Copying unchanged QML does not reliably trigger the plugin watcher.
            check_unlocked()
            run('omarchy', 'restart', 'shell', timeout=30)
        print('Activated Perch Current. Restart OpenCode/Neovim/Codex and open a new Foot window.')
    else:
        print('Installed assets. Run again with --activate from your unlocked Omarchy desktop to apply.')
    print(f'Theme: {target}\nBackups: {backup.path}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Installation stopped: {error}', file=sys.stderr)
        sys.exit(1)
