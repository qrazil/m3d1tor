-- The nvim half of the regex oracle. Run as:
--   nvim --headless -u NONE -i NONE -n -l nvim_regex.lua CASES OUT
-- CASES holds `index  hex(pattern)  hex(text)  flags` lines (see
-- tests/t_regex_run.m31); OUT gets one result line per case in the format that
-- program prints:
--   index  srow  scol  erow  ecol  hex(whole);hex(\1);...;hex(\9)
-- (0-based row, byte column, end exclusive; `index none` / `index err`
-- otherwise). The text goes into a buffer and is searched the way `/` does it
-- (so `\n` matches a line break); the groups are read through a `:s`
-- replacement expression.
local cases_path, out_path = unpack(arg)

local function unhex(s)
  return (s:gsub('..', function(c) return string.char(tonumber(c, 16)) end))
end
local function hex(s)
  return (s:gsub('.', function(c) return string.format('%02x', c:byte()) end))
end

local captured
function _G.med_cap(list)
  captured = list
  return ''
end

local out = {}
for line in io.lines(cases_path) do
  local f = vim.split(line, '\t', { plain = true })
  local pat, text = unhex(f[2]), unhex(f[3])
  local flags = f[4] or ''
  vim.o.ignorecase = flags:find('i', 1, true) ~= nil
  vim.o.smartcase = flags:find('s', 1, true) ~= nil
  vim.api.nvim_buf_set_lines(0, 0, -1, false, vim.split(text, '\n', { plain = true }))
  vim.fn.cursor(1, 1)
  captured = nil
  local ok, pos = pcall(vim.fn.searchpos, pat, 'cnW')
  if ok and vim.split(text, '\n', { plain = true })[1] == '' then
    -- searchpos() skips a match at the NUL of an empty first line (searchit's
    -- "one back" rule): assume such a match starts at column 0 when :s finds it.
    vim.fn.setreg('/', pat)
    if pcall(vim.cmd, 'silent keeppatterns 1s//x/') then
      pos = { 1, 1 }
    else
      pos = { 0, 0 }
    end
    vim.api.nvim_buf_set_lines(0, 0, -1, false, vim.split(text, '\n', { plain = true }))
  end
  if not ok then
    out[#out + 1] = f[1] .. '\terr'
  elseif pos[1] ~= 1 then
    out[#out + 1] = f[1] .. '\tnone'
  else
    vim.fn.setreg('/', pat)
    local expr = '\\=luaeval("med_cap(_A)", [submatch(0), submatch(1), submatch(2), submatch(3), submatch(4), submatch(5), submatch(6), submatch(7), submatch(8), submatch(9)])'
    local sok = pcall(vim.cmd, 'silent keeppatterns 1s//' .. expr .. '/')
    if not sok or not captured then
      out[#out + 1] = f[1] .. '\tnone'
    else
      local whole = captured[1]
      local srow, scol = 0, pos[2] - 1
      local erow, ecol = 0, scol + #whole
      local last = whole:match('.*\n()')
      if last then
        local _, n = whole:gsub('\n', '')
        erow = n
        ecol = #whole - last + 1
      end
      local parts = {}
      for g = 1, 10 do
        parts[g] = hex(captured[g] or '')
      end
      out[#out + 1] = string.format('%s\t%d\t%d\t%d\t%d\t%s', f[1], srow, scol, erow, ecol, table.concat(parts, ';'))
    end
  end
end
local fh = io.open(out_path, 'w')
fh:write(table.concat(out, '\n'), '\n')
fh:close()
