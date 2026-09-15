return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      transparent = false,
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
      colors = {
        bg = "#273D36",
        dark_bg = "#21352E",
        darker_bg = "#1C2E28",
        lighter_bg = "#354E43",

        fg = "#EFEAD8",
        dark_fg = "#B2C5B4",
        light_fg = "#F3EFDF",
        bright_fg = "#F7F2E2",
        muted = "#B2C5B4",

        red = "#F4A790",
        yellow = "#F0D28C",
        orange = "#F0D28C",
        green = "#B9DB93",
        cyan = "#8FDEBC",
        blue = "#A0DCCE",
        magenta = "#D0BCDA",
        brown = "#D3B992",

        bright_red = "#FFC0AC",
        bright_yellow = "#F6DEA5",
        bright_green = "#CCE9AA",
        bright_cyan = "#AFEACE",
        bright_blue = "#B9E9DF",
        bright_magenta = "#E0CFE8",

        accent = "#D3E880",
        cursor = "#D3E880",
        foreground = "#EFEAD8",
        background = "#273D36",
        selection = "#354E43",
        selection_foreground = "#EFEAD8",
        selection_background = "#354E43",
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "aether",
    },
  },
  {
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
