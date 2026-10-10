-- The nvim half of the regex oracle. Run as:
--   nvim --headless -u NONE -i NONE -n -l nvim_regex.lua CASES OUT
-- CASES holds `index  hex(pattern)  hex(text)  flags` lines (see
-- tests/t_regex_run.m31); OUT gets one result line per case in the same
-- format that program prints.
local cases_path, out_path = unpack(arg)

local function unhex(s)
  return (s:gsub('..', function(c) return string.char(tonumber(c, 16)) end))
end
local function hex(s)
  return (s:gsub('.', function(c) return string.format('%02x', c:byte()) end))
end

local out = {}
for line in io.lines(cases_path) do
  local f = vim.split(line, '\t', { plain = true })
  local pat, text = unhex(f[2]), unhex(f[3])
  local flags = f[4] or ''
  vim.o.ignorecase = flags:find('i', 1, true) ~= nil
  vim.o.smartcase = flags:find('s', 1, true) ~= nil
  local ok, res = pcall(vim.fn.matchstrpos, text, pat)
  if not ok then
    out[#out + 1] = f[1] .. '\terr'
  elseif res[2] < 0 then
    out[#out + 1] = f[1] .. '\tnone'
  else
    local _, list = pcall(vim.fn.matchlist, text, pat)
    local parts = {}
    for g = 1, 10 do
      parts[g] = hex(list[g] or '')
    end
    out[#out + 1] = string.format('%s\t%d\t%d\t%s', f[1], res[2], res[3], table.concat(parts, ';'))
  end
end
local fh = io.open(out_path, 'w')
fh:write(table.concat(out, '\n'), '\n')
fh:close()
