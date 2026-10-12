-- One oracle case in nvim. Run as:
--   nvim --headless -u NONE -i NONE -n -l nvim_driver.lua OUT HEXTEXT ROW COL KEYS
-- and it writes one result line to the file OUT, in the format that
-- tests/t_oracle_run.m31 prints (see its header).

local out_path, text_hex, row, col, keys_csv, plugins = unpack(arg)

local function unhex(s)
  return (s:gsub('..', function(c) return string.char(tonumber(c, 16)) end))
end
local function hex(s)
  return (s:gsub('.', function(c) return string.format('%02x', c:byte()) end))
end

local SPECIAL = {
  [63232] = '<Up>', [63233] = '<Down>', [63234] = '<Left>', [63235] = '<Right>',
  [63236] = '<Home>', [63237] = '<End>', [63238] = '<PageUp>', [63239] = '<PageDown>',
  [63240] = '<Del>', [63241] = '<Insert>',
}

local function key_string(csv)
  local parts = {}
  for piece in string.gmatch(csv, '[^,]+') do
    local k = tonumber(piece)
    if SPECIAL[k] then
      parts[#parts + 1] = SPECIAL[k]
    elseif k == 127 then
      parts[#parts + 1] = '<BS>'
    elseif k == 60 then
      parts[#parts + 1] = '<lt>'
    elseif k == 0 then
      parts[#parts + 1] = '<Nul>'
    elseif k == 22 then
      parts[#parts + 1] = '<C-v>'
    else
      parts[#parts + 1] = vim.fn.nr2char(k)
    end
  end
  return table.concat(parts)
end

-- vim plugins the case wants (the engine has them built in)
local PLUGIN_DIRS = { surround = 'vim-surround', repeat_ = 'vim-repeat', ['auto-pairs'] = 'auto-pairs' }
local plugin_root = os.getenv('M3D_PLUGINS') or (os.getenv('HOME') .. '/.vim/plugged')
for name in string.gmatch(plugins or '', '%S+') do
  local dir = PLUGIN_DIRS[name == 'repeat' and 'repeat_' or name]
  vim.opt.runtimepath:append(plugin_root .. '/' .. dir)
  if name ~= 'repeat' then
    vim.cmd('runtime plugin/' .. name .. '.vim')
  end
end

local text = unhex(text_hex)
local lines = vim.split(text, '\n', { plain = true })
-- a clean undo history: the initial text is not an undoable change
-- (loaded from a file so that "U" has no saved line either: setting the lines
-- through the API would leave the empty first line behind for it)
local tmp = os.tmpname()
vim.fn.writefile(lines, tmp)
vim.cmd('silent noautocmd edit! ' .. vim.fn.fnameescape(tmp))
vim.bo.undolevels = 1000
vim.o.inccommand = ''
os.remove(tmp)
-- a fresh window's context mark is the start of the buffer
vim.fn.setpos("''", { 0, 1, 1, 0 })
-- setpos() on the context mark leaves a jumplist entry; a fresh window has none
vim.cmd('clearjumps')
vim.api.nvim_win_set_cursor(0, { tonumber(row) + 1, tonumber(col) })

local keys = vim.api.nvim_replace_termcodes(key_string(keys_csv or ''), true, true, true)
pcall(vim.api.nvim_feedkeys, keys, 'xt', false)

local mode = vim.fn.mode()
local function mode_char(m)
  if m == 'v' or m == 'V' then return m end
  if m == '\22' then return 'b' end
  return 'n'
end
local final_mode = mode_char(mode)
local result_lines = vim.api.nvim_buf_get_lines(0, 0, -1, false)
local cur = vim.api.nvim_win_get_cursor(0)

local names = { '"', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', 'a', 'b', 'c', 'd', '.', '/', ':' }
local regs = {}
for _, name in ipairs(names) do
  local t = vim.fn.getregtype(name)
  local content = vim.fn.getreg(name, 1, true)
  local empty = (#content == 0) or (#content == 1 and content[1] == '')
  if t ~= '' and not (empty and (name == '.' or name == '/' or name == ':')) then
    local kind = 'v'
    if t == 'V' then kind = 'V' elseif t:sub(1, 1) == '\22' then kind = 'b' end
    regs[#regs + 1] = name .. ':' .. kind .. ':' .. hex(table.concat(content, '\n'))
  end
end

local vrow, vcol = '-', '-'
if final_mode ~= 'n' then
  local p = vim.fn.getpos('v')
  vrow, vcol = tostring(p[2] - 1), tostring(p[3] - 1)
end
local f = assert(io.open(out_path, 'w'))
f:write(table.concat({
  '0', hex(table.concat(result_lines, '\n')), tostring(cur[1] - 1), tostring(cur[2]),
  final_mode, vrow, vcol, table.concat(regs, ';'), tostring(vim.fn.line('w0') - 1),
}, '\t'), '\n')
f:close()
vim.cmd('qa!')
