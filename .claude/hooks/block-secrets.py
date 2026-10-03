#!/usr/bin/env python3
# PreToolUse hook：寫入的內容裡疑似有 API 金鑰就擋下（exit 2，原因回傳給 Claude）
import json, re, sys

PATTERNS = {
    'Anthropic 金鑰': r'sk-ant-[A-Za-z0-9_-]{20,}',
    'OpenAI 金鑰': r'sk-(?:proj-)?[A-Za-z0-9]{20,}',
    'AWS Access Key': r'AKIA[0-9A-Z]{16}',
    'GitHub Token': r'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}',
    'Google API 金鑰': r'AIza[0-9A-Za-z_-]{35}',
    'Slack Token': r'xox[abprs]-[A-Za-z0-9-]{10,}',
    '私鑰': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    '寫死的金鑰字串': r'(?i)(?:api[_-]?key|secret|token)["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
}

inp = json.load(sys.stdin).get('tool_input', {})
# Write/Edit/MultiEdit/NotebookEdit 的新內容，以及 Bash 指令（heredoc、sed 也會寫檔）
texts = [inp.get(k) or '' for k in ('content', 'new_string', 'new_source', 'command')]
texts += [e.get('new_string') or '' for e in inp.get('edits') or []]
text = '\n'.join(texts)

hits = [name for name, p in PATTERNS.items() if re.search(p, text)]
if hits:
    print(f'已擋下：內容疑似含有 API 金鑰（{"、".join(hits)}）。請改用環境變數或不進版控的設定檔。', file=sys.stderr)
    sys.exit(2)
