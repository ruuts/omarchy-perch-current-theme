"""Build Perch Current from the approved palette; no live configuration writes."""
from pathlib import Path
import json
import os
import re
import shutil
import tomllib
from PIL import Image, ImageOps

from theme_utils import fish, luminance

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'theme'
DEFAULTS = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'default/themed'
NATIVE_THEME_FILES = [
    'btop.theme', 'colors.toml', 'helix.toml', 'icons.theme',
    'shell.bar.toml', 'shell.controls.toml', 'shell.launcher.toml',
    'shell.lock.toml', 'shell.menu.toml', 'shell.notifications.toml',
    'shell.perch-current.toml', 'shell.popups.toml', 'shell.tooltip.toml',
    'backgrounds/00-perch-current-ai-5k.png',
]


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / 'backgrounds').mkdir(exist_ok=True)
    p = json.loads((ROOT / 'palette.json').read_text())
    focus_border = '#AEBF70'
    colors = dict(
        mode='dark', accent=p['accent'], background=p['bg'], dark_background=p['inset'],
        darker_background='#1C2E28', lighter_background=p['panel'],
        foreground=p['fg'], dark_foreground=p['muted'], light_foreground='#F3EFDF',
        bright_foreground='#F7F2E2', muted=p['muted'], structure=p['structure'], structure_active=p['structure_active'],
        selection=p['panel'], selection_background=p['panel'], selection_foreground=p['fg'],
        red=p['red'], yellow=p['yellow'], orange=p['yellow'], green=p['green'],
        cyan=p['cyan'], blue=p['blue'], magenta=p['purple'], purple=p['purple'], brown='#D3B992',
        bright_red='#FFC0AC', bright_yellow='#F6DEA5', bright_green='#CCE9AA',
        bright_cyan='#AFEACE', bright_blue='#B9E9DF', bright_magenta='#E0CFE8',
        hyprland_active_border=focus_border, hyprland_inactive_border='#52715D',
        theme_type='dark',
    )
    (OUT / 'colors.toml').write_text('# Perch Current — Quiet accents\n' + ''.join(f'{key} = "{value}"\n' for key, value in colors.items()))
    tomllib.loads((OUT / 'colors.toml').read_text())
    checks = []
    for key in ['foreground', 'muted', 'accent', 'red', 'yellow', 'green', 'cyan', 'blue', 'magenta', 'brown']:
        for surface in ['background', 'dark_background', 'lighter_background']:
            ratio = (luminance(colors[key]) + .05) / (luminance(colors[surface]) + .05)
            checks.append(f'{key} on {surface}: {ratio:.2f}:1')
            assert ratio >= 4.5, checks[-1]
    (ROOT / 'theme-contrast-report.txt').write_text('\n'.join(checks) + '\n')

    def render_template(name):
        content = (DEFAULTS / (name + '.tpl')).read_text()
        return re.sub(r'\{\{ (\w+) \}\}', lambda m: colors[m[1][:-6]].lstrip('#') if m[1].endswith('_strip') else colors[m[1]], content)

    # Theme-specific terminal files retain Omarchy's template mappings and use
    # the approved chartreuse cursor rather than the template's bone default.
    for name in ['alacritty.toml', 'foot.ini', 'ghostty.conf', 'kitty.conf']:
        content = render_template(name)
        if name == 'ghostty.conf':
            content = content.replace(f'cursor-color = {colors["bright_foreground"]}', f'cursor-color = {p["accent"]}')
            content += '\nbackground-opacity = 0.92\n'
        elif name == 'kitty.conf':
            content = re.sub(r'^cursor .+$', f'cursor {p["accent"]}', content, flags=re.M)
            content = content.replace(f'active_tab_background {p["accent"]}', f'active_tab_background {p["panel"]}\nactive_tab_foreground {p["accent"]}')
            content += '\nbackground_opacity 0.92\n'
        elif name == 'alacritty.toml':
            content = content.replace(f'cursor = "{colors["bright_foreground"]}"', f'cursor = "{p["accent"]}"')
            content += '\n[window]\nopacity = 0.92\n'
        elif name == 'foot.ini':
            content = content.replace(f'cursor={p["bg"][1:]} {colors["bright_foreground"][1:]}', f'cursor={p["bg"][1:]} {p["accent"][1:]}')
            content += '\n# Apply translucency to default-color cells, including Neovim Normal.\nalpha=0.92\nalpha-mode=matching\n'
        (OUT / name).write_text(content)

    # Omarchy's default templates reuse muted text for structural UI. These
    # color-only outputs retain readable comments while quieting guides, rules,
    # and btop's box treatment.
    btop = render_template('btop.theme')
    for key in ['cpu_box', 'mem_box', 'net_box', 'proc_box']:
        btop = re.sub(rf'^(theme\[{key}\]=).*$', rf'\g<1>"{p["structure_active"]}"', btop, flags=re.M)
    btop = re.sub(r'^(theme\[div_line\]=).*$', rf'\g<1>"{p["structure"]}"', btop, flags=re.M)
    btop = btop.replace(f'theme[gradient_color_3]="{p["muted"]}"', f'theme[gradient_color_3]="{p["structure"]}"')
    btop = btop.replace(f'theme[gradient_color_4]="{p["muted"]}"', f'theme[gradient_color_4]="{p["structure_active"]}"')
    (OUT / 'btop.theme').write_text(btop)

    helix = render_template('helix.toml')
    helix_lines = {
        '"ui.linenr"': f'"ui.linenr" = {{ fg = "{p["structure"]}" }}',
        '"ui.window"': f'"ui.window" = {{ fg = "{p["structure_active"]}" }}',
        '"ui.bufferline"': f'"ui.bufferline" = {{ fg = "{p["structure"]}", bg = "background" }}',
        '"ui.virtual"': f'"ui.virtual" = "{p["structure"]}"',
        '"ui.virtual.indent-guide"': f'"ui.virtual.indent-guide" = "{p["structure"]}"',
        '"ui.virtual.inlay-hint"': f'"ui.virtual.inlay-hint" = {{ fg = "{p["structure_active"]}" }}',
        '"ui.virtual.whitespace"': f'"ui.virtual.whitespace" = "{p["structure"]}"',
        '"ui.statusline"': '"ui.statusline" = { fg = "foreground", bg = "dark_background" }',
        '"ui.statusline.inactive"': f'"ui.statusline.inactive" = {{ fg = "{p["muted"]}", bg = "dark_background" }}',
        '"ui.statusline.normal"': '"ui.statusline.normal" = { fg = "background", bg = "accent", modifiers = ["bold"] }',
        '"ui.statusline.insert"': '"ui.statusline.insert" = { fg = "background", bg = "color2", modifiers = ["bold"] }',
        '"ui.statusline.select"': '"ui.statusline.select" = { fg = "background", bg = "color5", modifiers = ["bold"] }',
        '"ui.menu.selected"': '"ui.menu.selected" = { fg = "accent", bg = "lighter_background", modifiers = ["bold"] }',
        '"ui.cursor"': '"ui.cursor" = { fg = "background", bg = "cursor" }',
        '"ui.cursor.primary"': '"ui.cursor.primary" = { fg = "background", bg = "cursor" }',
        '"ui.cursor.primary.normal"': '"ui.cursor.primary.normal" = { fg = "background", bg = "cursor" }',
        '"ui.cursor.primary.insert"': '"ui.cursor.primary.insert" = { fg = "background", bg = "cursor" }',
        '"ui.cursor.primary.select"': '"ui.cursor.primary.select" = { fg = "background", bg = "cursor" }',
    }
    for prefix, replacement in helix_lines.items():
        helix = re.sub(rf'^{re.escape(prefix)}.*$', replacement, helix, flags=re.M)
    helix = helix.replace(
        '# Statusline uses an inverted band (background-color text on foreground-color\n'
        '# background) to guarantee contrast across both light and dark Omarchy themes.',
        '# Keep the statusline grounded; small mode labels carry color instead of an\n'
        '# inverted foreground band.',
    )
    helix = helix.replace(f'cursor = "{colors["bright_foreground"]}"', f'cursor = "{p["accent"]}"')
    (OUT / 'helix.toml').write_text(helix)

    vscode = json.loads(render_template('vscode-theme.json'))
    vscode['name'] = 'Perch Current'
    ui = vscode['colors']
    subtle = p['structure']
    structural = p['structure_active']
    for key in ['tree.indentGuidesStroke', 'editorWhitespace.foreground', 'editorRuler.foreground']:
        ui[key] = subtle
    for key in ['tree.inactiveIndentGuidesStroke']:
        ui[key] = subtle + '60'
    for key in [f'editorIndentGuide.background{i}' for i in range(1, 7)]:
        ui[key] = subtle + '70'
    for key in [f'editorIndentGuide.activeBackground{i}' for i in range(1, 7)]:
        ui[key] = structural
    for key in ['tree.tableColumnsBorder', 'checkbox.border', 'dropdown.border', 'input.border', 'editorWidget.border', 'editorSuggestWidget.border', 'editorHoverWidget.border', 'menu.border', 'notificationCenter.border', 'notificationToast.border', 'notifications.border', 'pickerGroup.border', 'panelInput.border', 'commandCenter.border']:
        ui[key] = structural
    for key in ['sideBarSectionHeader.border', 'editorGroup.border', 'panel.border', 'panelSection.border', 'panelSectionHeader.border', 'terminal.border']:
        ui[key] = structural + '80'
    ui.update({
        'button.background': p['panel'], 'button.foreground': p['accent'], 'button.hoverBackground': structural,
        'button.secondaryBackground': p['panel'], 'button.secondaryHoverBackground': structural,
        'checkbox.selectBackground': p['panel'], 'checkbox.selectBorder': p['accent'],
        'editorCursor.foreground': p['accent'], 'terminalCursor.foreground': p['accent'],
        'terminalOverviewRuler.cursorForeground': p['accent'],
    })
    (OUT / 'vscode-theme.json').write_text(json.dumps(vscode, indent=2) + '\n')

    # Theme-scoped geometry; switching themes returns to Omarchy's defaults.
    (OUT / 'hyprland.lua').write_text('''hl.config({
  general = {
    border_size = 2,
    col = { active_border = "#D3E880", inactive_border = "#52715D" },
  },
  decoration = {
    rounding = 8,
    blur = { enabled = true, size = 2, passes = 1 },
  },
  group = {
    col = { border_active = "#D3E880", border_inactive = "#52715D" },
  },
})
'''.replace('#D3E880', focus_border))

    # Let Omarchy generate its full shell defaults, overriding just the approved
    # surfaces and control treatment through its supported section overlays.
    sections = {
        'bar': {'background': p['inset'], 'background-alpha': 1.0, 'text': p['fg'], 'active': p['red']},
        'controls': {'normal-color': p['fg'], 'normal-fill-alpha': .04, 'normal-border': '#52715D', 'normal-border-width': 1, 'normal-border-alpha': 1.0,
                     'hover-cursor-color': p['fg'], 'hover-cursor-fill-alpha': .08, 'hover-cursor-border': p['accent'], 'hover-cursor-border-width': 1, 'hover-cursor-border-alpha': .45,
                     'focus-color': p['accent'], 'focus-fill-alpha': .06, 'focus-border': focus_border, 'focus-border-width': 1, 'focus-border-alpha': 1.0,
                     'selected-color': p['accent'], 'selected-fill-alpha': .08, 'selected-border': p['accent'], 'selected-border-width': '0 0 1 0', 'selected-border-alpha': 1.0,
                     'pressed-fill-alpha': .12, 'selection-fill-alpha': .18},
        'menu': {'background': p['bg'], 'background-alpha': .94, 'text': p['fg'], 'border': focus_border, 'border-alpha': 1.0, 'border-width': 2, 'scrim': p['inset'], 'scrim-alpha': .3,
                 'selected-background': p['panel'], 'selected-background-alpha': 1.0, 'selected-text': p['accent'], 'selected-border': p['accent'], 'selected-border-alpha': .6},
        'lock': {'background': p['bg'], 'background-alpha': 1.0, 'text': p['fg'], 'placeholder': p['muted'], 'text-error': p['red'], 'border': '#52715D', 'border-active': p['accent'], 'border-error': p['red'], 'border-alpha': 1.0, 'selection': p['panel'], 'selection-alpha': 1.0},
        'perch-current': {'enabled': 1},
        'popups': {'background': p['bg'], 'background-alpha': .94, 'text': p['fg'], 'border': focus_border, 'border-alpha': 1.0, 'border-width': 2},
        'notifications': {'background': p['bg'], 'background-alpha': .94, 'text': p['fg'], 'border': focus_border, 'border-alpha': 1.0, 'border-width': 2, 'countdown': p['accent']},
        'tooltip': {'background': p['bg'], 'background-alpha': .94, 'text': p['fg'], 'border': focus_border, 'border-alpha': 1.0, 'border-width': 2},
    }
    sections['launcher'] = dict(sections['menu'])
    for name, values in sections.items():
        content = f'[{name}]\n' + ''.join(f'{k} = {json.dumps(v)}\n' for k, v in values.items())
        tomllib.loads(content)
        (OUT / f'shell.{name}.toml').write_text(content)
    (OUT / 'icons.theme').write_text('Yaru-sage\n')
    (OUT / 'perch.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="90" height="45" viewBox="0 0 90 45">' + fish(p) + '</svg>')

    nvim = (DEFAULTS / 'neovim.lua.tpl').read_text()
    nvim = re.sub(r'\{\{ (\w+) \}\}', lambda m: colors[m[1]], nvim)
    nvim = nvim.replace('cursor = "' + colors['bright_foreground'] + '"', 'cursor = "' + p['accent'] + '"')
    nvim = nvim.replace('      colors = {', '''      transparent = false,
      styles = { comments = { italic = true }, keywords = {}, sidebars = "dark", floats = "dark" },
      on_highlights = function(h, c)
        local function set(names, spec)
          for _, name in ipairs(names) do h[name] = vim.deepcopy(spec) end
        end
        set({ "Keyword", "Conditional", "Repeat", "Statement", "Exception", "Include", "StorageClass", "@keyword", "@keyword.function", "@keyword.return", "@keyword.conditional", "@keyword.repeat", "@keyword.import" }, { fg = c.magenta })
        set({ "Function", "@function", "@function.call", "@function.method", "@function.method.call" }, { fg = c.blue })
        set({ "Type", "@type", "@type.builtin" }, { fg = c.cyan })
        set({ "Number", "Float", "Boolean", "@number", "@boolean" }, { fg = c.yellow })
        set({ "String", "@string" }, { fg = c.green })
        set({ "Comment", "@comment" }, { fg = c.muted, italic = true })
        -- Structural guides recede; the current scope stays gently visible.
        set({ "SnacksIndent", "SnacksIndentBlank", "IblIndent", "IblWhitespace", "IndentBlanklineChar" }, { fg = "#40584C", nocombine = true })
        set({ "SnacksIndentScope", "SnacksIndentChunk", "IblScope", "MiniIndentscopeSymbol", "IndentBlanklineContextChar" }, { fg = "#5A715E", nocombine = true })
        set({ "Normal", "NormalNC" }, { fg = c.fg, bg = c.bg })
        set({ "Cursor", "lCursor" }, { fg = c.bg, bg = c.accent })
        set({ "CursorLine", "Visual" }, { bg = c.lighter_bg })
        set({ "NormalFloat", "NeoTreeNormal", "NeoTreeNormalNC" }, { fg = c.fg, bg = c.dark_bg })
        set({ "FloatBorder" }, { fg = c.accent, bg = c.dark_bg })
        set({ "WinSeparator" }, { fg = "#52715D", bg = c.bg })
        set({ "TabLineSel", "BufferLineBufferSelected", "BufferLineTabSelected" }, { fg = c.fg, bg = c.bg, bold = true })
        set({ "BufferLineIndicatorSelected", "NeoTreeCursorLine" }, { fg = c.accent, bg = c.lighter_bg })
        set({ "PmenuSel" }, { fg = c.accent, bg = c.lighter_bg, bold = true })
        set({ "Search" }, { fg = c.yellow, bg = c.dark_bg, underline = true })
        set({ "IncSearch", "CurSearch" }, { fg = c.bg, bg = c.accent })
        h.DiffAdd = { bg = "#304B3B" }
        h.DiffDelete = { fg = c.red, bg = "#493B36" }
        h.DiffChange = { bg = c.lighter_bg }
        h.DiffText = { fg = c.fg, bg = c.dark_bg, underline = true }
      end,
      colors = {''', 1)
    nvim = nvim.rstrip()[:-1] + '''  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      local base = { fg = "#EFEAD8", bg = "#21352E" }
      local quiet = { fg = "#D3E880", bg = "#354E43", gui = "bold" }
      local section = { a = quiet, b = base, c = base }
      opts.options = opts.options or {}
      opts.options.theme = { normal = section, insert = section, visual = section,
        replace = section, command = section, inactive = { a = base, b = base, c = base } }
    end,
  },
}
'''
    (OUT / 'neovim.lua').write_text(nvim)

    roles = {
        'primary': 'accent', 'secondary': 'blue', 'accent': 'accent', 'error': 'red', 'warning': 'yellow', 'success': 'green', 'info': 'cyan',
        'text': 'fg', 'textMuted': 'muted', 'background': 'bg', 'backgroundPanel': 'inset', 'backgroundElement': 'panel',
        'border': 'border', 'borderActive': 'accent', 'borderSubtle': 'border',
        'diffAdded': 'green', 'diffRemoved': 'red', 'diffContext': 'fg', 'diffHunkHeader': 'blue',
        'diffHighlightAdded': 'green', 'diffHighlightRemoved': 'red', 'diffAddedBg': 'addedBg', 'diffRemovedBg': 'removedBg',
        'diffContextBg': 'bg', 'diffLineNumber': 'muted', 'diffAddedLineNumberBg': 'addedBg', 'diffRemovedLineNumberBg': 'removedBg',
        'markdownText': 'fg', 'markdownHeading': 'accent', 'markdownLink': 'blue', 'markdownLinkText': 'cyan',
        'markdownCode': 'green', 'markdownBlockQuote': 'muted', 'markdownEmph': 'yellow', 'markdownStrong': 'fg',
        'markdownHorizontalRule': 'muted', 'markdownListItem': 'accent', 'markdownListEnumeration': 'cyan',
        'markdownImage': 'blue', 'markdownImageText': 'cyan', 'markdownCodeBlock': 'fg',
        'syntaxComment': 'muted', 'syntaxKeyword': 'purple', 'syntaxFunction': 'blue', 'syntaxVariable': 'fg',
        'syntaxString': 'green', 'syntaxNumber': 'yellow', 'syntaxType': 'cyan', 'syntaxOperator': 'fg', 'syntaxPunctuation': 'fg',
    }
    p.update(border='#52715D', addedBg='#304B3B', removedBg='#493B36')
    theme = {'$schema': 'https://opencode.ai/theme.json', 'theme': {key: p[value] for key, value in roles.items()}}
    (OUT / 'opencode.json').write_text(json.dumps(theme, indent=2) + '\n')
    # Conventional high-quality resampling only; never describe this as native 5K.
    source = Image.open(ROOT / 'assets/perch-current-source.png').convert('RGB')
    ImageOps.fit(source, (5120, 2880), method=Image.Resampling.LANCZOS).save(OUT / 'backgrounds/01-perch-current-5k.png')
    ai_master = ROOT / 'upscaling/perch-current-high-fidelity-4x.png'
    if ai_master.exists():
        with Image.open(ai_master) as image:
            assert image.size == (6688, 3764), 'Unexpected AI master dimensions'
            ImageOps.fit(image.convert('RGB'), (5120, 2880), method=Image.Resampling.LANCZOS).save(OUT / 'backgrounds/00-perch-current-ai-5k.png')
    (OUT / 'README.md').write_text('''# Perch Current — Quiet

Personal Omarchy theme: green water, old pine, bone text and a chartreuse perch.
Source artwork: user-approved generated interpretation of their Japan photo.
Preferred wallpaper: Upscayl High Fidelity 4× master (6688 × 3764), downsampled
to 5120 × 2880 when available. Original source: 1672 × 941. The conventional
Lanczos enlargement remains available as a fallback. Neither is native 5K art.

`colors.toml` drives Omarchy terminal, shell, btop, Helix and other stock templates.
`neovim.lua` uses the installed Aether theme with explicit quiet UI highlights.
`opencode.json` is installed as `~/.config/opencode/themes/perch-current.json`.
Codex's existing `tui.theme = "ansi"` follows the terminal palette automatically.
Shell overlays preserve defaults while setting the approved surfaces.
The user-owned menu clone shows the perch only when this theme's marker is active.
''')
    # `omarchy theme install` clones a repository directly into a theme
    # directory, so its safe color-only payload must live at repository root.
    for name in NATIVE_THEME_FILES:
        destination = ROOT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT / name, destination)
    print(f'Built {OUT}; {len(checks)} color contrast checks passed.')


if __name__ == '__main__':
    main()
