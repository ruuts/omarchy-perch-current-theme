"""Exercise real Omarchy staging and real Neovim highlighting in isolation."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from PIL import Image

ROOT = Path(__file__).resolve().parent
HOME = Path.home()

with tempfile.TemporaryDirectory(prefix='perch-theme-check-') as directory:
    isolated = Path(directory)
    target = isolated / '.config/omarchy/themes/perch-current'
    target.parent.mkdir(parents=True)
    shutil.copytree(ROOT / 'theme', target)
    (isolated / '.local/state/omarchy/current').mkdir(parents=True)
    env = dict(os.environ, HOME=str(isolated), XDG_CONFIG_HOME=str(isolated / '.config'), XDG_STATE_HOME=str(isolated / '.local/state'), XDG_DATA_HOME=str(isolated / '.local/share'), OMARCHY_PATH=os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'), OMARCHY_THEME_HEADLESS='1')
    subprocess.run(['omarchy', 'theme', 'set', 'perch-current'], env=env, check=True, timeout=40)
    current = isolated / '.local/state/omarchy/current/theme'
    for item in current.iterdir():
        if item.suffix in {'.toml', '.lua', '.json', '.conf', '.ini', '.theme', '.css'}:
            assert '{{' not in item.read_text(), f'Unresolved template in {item.name}'
        if item.suffix == '.toml':
            tomllib.loads(item.read_text())
        if item.suffix == '.json':
            json.loads(item.read_text())
        if item.suffix == '.lua':
            subprocess.run(['luajit', '-e', f'assert(loadfile({json.dumps(str(item))}))'], check=True)
    shell = tomllib.loads((current / 'shell.toml').read_text())
    assert shell['perch-current']['enabled'] == 1
    assert shell['bar']['background'] == '#21352E'
    assert shell['launcher']['selected-background'] == '#354E43'
    assert shell['popups']['background-alpha'] == .94
    assert shell['popups']['border-width'] == 2
    assert shell['menu']['border'] == '#AEBF70'
    with Image.open(current / 'backgrounds/00-perch-current-ai-5k.png') as image:
        assert image.size == (5120, 2880)
    theme = json.loads((current / 'opencode.json').read_text())['theme']
    assert len(theme) == 50, f'Unexpected OpenCode color count: {len(theme)}'
    assert all(re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in theme.values())
    lua = isolated / 'check.lua'
    lua.write_text('''
vim.opt.rtp:prepend(vim.env.PERCH_AETHER_PATH)
local specs = dofile(vim.env.PERCH_NVIM_THEME)
require("aether").setup(specs[1].opts)
vim.cmd.colorscheme("aether")
local expected = {
  Normal = { fg = 0xEFEAD8, bg = 0x273D36 },
  Keyword = { fg = 0xD0BCDA },
  Function = { fg = 0xA0DCCE },
  String = { fg = 0xB9DB93 },
  Cursor = { bg = 0xD3E880 },
  PmenuSel = { fg = 0xD3E880, bg = 0x354E43 },
  SnacksIndent = { fg = 0x40584C },
  SnacksIndentScope = { fg = 0x5A715E },
}
for group, fields in pairs(expected) do
  local actual = vim.api.nvim_get_hl(0, { name = group, link = false })
  for key, value in pairs(fields) do
    assert(actual[key] == value, group .. "." .. key .. " mismatched: " .. vim.inspect(actual))
  end
end
local opts = {}
specs[3].opts(nil, opts)
assert(opts.options.theme.normal.a.bg == "#354E43", "Lualine must use Quiet accents")
print("Aether actual highlight and Quiet lualine checks passed")
vim.cmd("qa!")
''')
    nvim_env = dict(env, PERCH_AETHER_PATH=str(HOME / '.local/share/nvim/lazy/aether'), PERCH_NVIM_THEME=str(current / 'neovim.lua'))
    subprocess.run(['nvim', '--headless', '-u', 'NONE', '-l', str(lua)], env=nvim_env, check=True, timeout=20)
    shutil.copy2(current / 'shell.toml', ROOT / 'validated-shell.toml')
    print(f'Validated {len(list(current.iterdir()))} staged theme entries, terminal templates, shell overlays, 50 OpenCode roles, 5K export, and real Neovim highlights.')
