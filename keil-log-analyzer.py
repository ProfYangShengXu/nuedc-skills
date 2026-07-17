#!/usr/bin/env python3
"""
keil-log-analyzer.py — Keil UV4 编译日志自动化解析工具

功能:
  1. 解析 UV4.exe 编译输出 (stdout/stderr / log file)
  2. 提取 errors / warnings / fatal / info
  3. 按文件分组错误位置
  4. 统计错误类别 (语法/链接/声明/类型)
  5. 输出结构化的 Markdown / JSON / 摘要报告
  6. 与上次编译对比差异

用法:
    # 从文件解析
    python keil-log-analyzer.py build.log
    
    # 从标准输入
    UV4.exe -b project.uvprojx -j0 2>&1 | python keil-log-analyzer.py -
    
    # 只看摘要
    python keil-log-analyzer.py build.log --summary
    
    # JSON 输出
    python keil-log-analyzer.py build.log --json
    
    # 与上次对比 (增量分析)
    python keil-log-analyzer.py build.log --diff previous.log
    
    # 持续监控 (tail 模式)
    python keil-log-analyzer.py --watch build.log
"""

import sys
import re
import json
import os
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

# ═════════════════════════════════════════════════════
# 1. 解析规则 (Keil UV4 + ARMCC 常见格式)
# ═════════════════════════════════════════════════════

# 通用错误: "file.c(line): error:  #20: identifier x is undefined"
RE_ERROR = re.compile(
    r'^(?:\.?[/\\]?)?'                     # optional leading path
    r'([^:]+?)'                             # filename (group 1)
    r'(?:\((\d+)\))?'                       # optional line number (group 2)
    r'\s*:\s*'                              
    r'(error|warning|fatal|note|info)'      # severity (group 3)
    r'(\s*#[^:]+)?'                         # optional error code #20 (group 4)
    r':\s*(.+)',                            # message (group 5)
    re.IGNORECASE
)

# 链接器错误: ".\Objects\firmware.axf: Error: L6218E: Undefined symbol xxx"
RE_LINKER = re.compile(
    r'([^:]+\.(?:axf|elf|out))\s*:\s*'
    r'(error|warning|fatal)'
    r'(:?\s*L\d+E)?'
    r':\s*(.+)',
    re.IGNORECASE
)

# 编译摘要: "0 Error(s), 0 Warning(s)"
RE_SUMMARY = re.compile(
    r'(\d+)\s*Error[s]?\s*[,;]?\s*(\d+)\s*Warning[s]?',
    re.IGNORECASE
)

# ARMClang/AC6 格式: "firmware.c:42:5: error: expected ';'"
RE_AC6 = re.compile(
    r'^([^:]+):(\d+):(\d+):\s*(error|warning|fatal|note):\s*(.+)',
    re.IGNORECASE
)

# 工程统计: "Build Time: 00:00:05" 之类
RE_BUILD_TIME = re.compile(
    r'Build\s*[Tt]ime\s*:\s*([\d:]+)',
    re.IGNORECASE
)

# 内存占用: "Program Size: Code=1234 RO-data=567 RW-data=89 ZI-data=12345"
RE_MEMORY = re.compile(
    r'Program\s*Size\s*:\s*'
    r'Code\s*=\s*(\d+)'
    r'(?:\s+RO-data\s*=\s*(\d+))?'
    r'(?:\s+RW-data\s*=\s*(\d+))?'
    r'(?:\s+ZI-data\s*=\s*(\d+))?',
    re.IGNORECASE
)


# ═════════════════════════════════════════════════════
# 2. 错误分类
# ═════════════════════════════════════════════════════

ERROR_CATEGORIES = {
    'syntax':     ['expected', 'syntax', 'missing', 'unexpected', ';', '}'],
    'type':       ['incompatible', 'implicit', 'conflicting', 'type', 'cast'],
    'undefined':  ['undefined', 'undeclared', 'unresolved', 'unknown identifier'],
    'linker':     ['L6000', 'L6200', 'L6218', 'L6300', 'L6305', 'L6320',
                   'undefined symbol', 'multiply defined'],
    'include':    ['#include', 'no such file', 'cannot open', 'file not found'],
    'memory':     'out of memory|region|overflow|spilling',
    'warning':    ['warning', '#1-D', '#177', '#223', '#225', '#301', '#381', '#550', '#870'],
}

def categorize_error(msg):
    """对错误消息分类"""
    msg_lower = msg.lower()
    
    if re.search(r'L\d+E', msg):
        return 'linker'
    
    for cat, patterns in ERROR_CATEGORIES.items():
        if isinstance(patterns, str):
            if re.search(patterns, msg_lower):
                return cat
        else:
            for p in patterns:
                if p.lower() in msg_lower:
                    return cat
    return 'other'


# ═════════════════════════════════════════════════════
# 3. 解析器
# ═════════════════════════════════════════════════════

class BuildLog:
    def __init__(self):
        self.entries = []       # list of dicts
        self.summary = {}       # error/warning counts
        self.memory = {}        # code/ro/rw/zi sizes
        self.build_time = ""
        self.project = ""
        
    def parse_line(self, line, line_no=0):
        line_s = line.rstrip('\n\r')
        
        # Try AC6 format first
        m = RE_AC6.match(line_s)
        if m:
            self.entries.append({
                'type': 'diagnostic',
                'file': m.group(1),
                'line': int(m.group(2)),
                'col': int(m.group(3)),
                'severity': m.group(4).lower(),
                'code': '',
                'message': m.group(5),
                'raw': line_s,
                'category': categorize_error(m.group(5)),
            })
            return
        
        # Try standard Keil format
        m = RE_ERROR.match(line_s)
        if m:
            self.entries.append({
                'type': 'diagnostic',
                'file': m.group(1),
                'line': int(m.group(2)) if m.group(2) else 0,
                'col': 0,
                'severity': m.group(3).lower(),
                'code': (m.group(4) or '').strip(),
                'message': m.group(5),
                'raw': line_s,
                'category': categorize_error(f"{m.group(4) or ''} {m.group(5)}"),
            })
            return
        
        # Linker errors
        m = RE_LINKER.match(line_s)
        if m:
            self.entries.append({
                'type': 'diagnostic',
                'file': m.group(1),
                'line': 0,
                'col': 0,
                'severity': m.group(2).lower(),
                'code': m.group(3) or '',
                'message': m.group(4),
                'raw': line_s,
                'category': 'linker',
            })
            return
        
        # Summary
        m = RE_SUMMARY.match(line_s)
        if m:
            self.summary = {
                'errors': int(m.group(1)),
                'warnings': int(m.group(2)),
            }
            return
        
        # Memory info
        m = RE_MEMORY.match(line_s)
        if m:
            self.memory = {
                'code': int(m.group(1)),
                'ro_data': int(m.group(2)) if m.group(2) else 0,
                'rw_data': int(m.group(3)) if m.group(3) else 0,
                'zi_data': int(m.group(4)) if m.group(4) else 0,
            }
            return
        
        # Build time
        m = RE_BUILD_TIME.match(line_s)
        if m:
            self.build_time = m.group(1)
            return

    def parse_file(self, path):
        """从文件解析"""
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f, 1):
                self.parse_line(line, i)
        return self
    
    def parse_text(self, text):
        """从文本解析"""
        for i, line in enumerate(text.split('\n'), 1):
            self.parse_line(line, i)
        return self

    @property
    def errors(self):
        return [e for e in self.entries if e['severity'] in ('error', 'fatal')]
    
    @property
    def warnings(self):
        return [e for e in self.entries if e['severity'] == 'warning']
    
    @property
    def error_count(self):
        return self.summary.get('errors', len(self.errors))
    
    @property
    def warning_count(self):
        return self.summary.get('warnings', len(self.warnings))
    
    def by_file(self):
        """按文件分组"""
        groups = defaultdict(list)
        for e in self.errors + self.warnings:
            groups[e['file']].append(e)
        return dict(groups)
    
    def by_category(self):
        """按错误类别统计"""
        return dict(Counter(e['category'] for e in self.errors))

    def report_text(self):
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"Keil Build Analysis  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        
        # Summary
        lines.append(f"📊 Summary:  {self.error_count} Error(s), {self.warning_count} Warning(s)")
        if self.build_time:
            lines.append(f"⏱  Build Time: {self.build_time}")
        if self.memory:
            m = self.memory
            total = m['code'] + m['ro_data'] + m['rw_data'] + m['zi_data']
            lines.append(f"💾 Flash: {m['code']+m['ro_data']} B  |  RAM: {m['rw_data']+m['zi_data']} B  |  Total: {total} B")
        lines.append("")
        
        if not self.errors and not self.warnings:
            lines.append("✅ Build successful! No errors, no warnings.")
            return '\n'.join(lines)
        
        # Errors by category
        if self.errors:
            cat_counts = self.by_category()
            lines.append(f"❌ Errors ({len(self.errors)}) by category:")
            for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
                lines.append(f"   {cat}: {cnt}")
            lines.append("")
        
        # Error details
        if self.errors:
            lines.append("─" * 60)
            lines.append("Error Details:")
            lines.append("─" * 60)
            for e in self.errors[:30]:  # cap at 30
                loc = f"{e['file']}:{e['line']}" if e['line'] else e['file']
                code = f" [{e['code']}]" if e['code'] else ""
                lines.append(f"  ❌ {loc}{code}")
                lines.append(f"     {e['message'][:120]}")
            if len(self.errors) > 30:
                lines.append(f"  ... and {len(self.errors) - 30} more errors")
            lines.append("")
        
        # Warning details
        if self.warnings:
            lines.append("─" * 60)
            lines.append(f"Warning Details (showing first 20):")
            lines.append("─" * 60)
            for e in self.warnings[:20]:
                loc = f"{e['file']}:{e['line']}" if e['line'] else e['file']
                lines.append(f"  ⚠ {loc}: {e['message'][:100]}")
            if len(self.warnings) > 20:
                lines.append(f"  ... and {len(self.warnings) - 20} more warnings")
            lines.append("")
        
        # Most common errors
        if self.errors:
            common = Counter(e['message'] for e in self.errors).most_common(5)
            lines.append("📌 Most Common Errors:")
            for msg, cnt in common:
                lines.append(f"   [{cnt}x] {msg[:80]}")
            lines.append("")
        
        lines.append("=" * 60)
        return '\n'.join(lines)
    
    def report_json(self):
        """生成 JSON 报告"""
        return json.dumps({
            'summary': {
                'errors': self.error_count,
                'warnings': self.warning_count,
                'build_time': self.build_time,
                'memory': self.memory,
            },
            'errors': [{
                'file': e['file'],
                'line': e['line'],
                'severity': e['severity'],
                'code': e['code'],
                'message': e['message'],
                'category': e['category'],
            } for e in self.errors],
            'warnings': [{
                'file': e['file'],
                'line': e['line'],
                'message': e['message'],
            } for e in self.warnings],
            'by_file': {k: len(v) for k, v in self.by_file().items()},
            'by_category': self.by_category(),
        }, ensure_ascii=False, indent=2)


# ═════════════════════════════════════════════════════
# 4. 差异比较
# ═════════════════════════════════════════════════════

def diff_logs(old_path, new_path):
    """比较两次编译的差异"""
    old = BuildLog().parse_file(old_path)
    new = BuildLog().parse_file(new_path)
    
    old_errors = {(e['file'], e['line'], e['message']) for e in old.errors}
    new_errors = {(e['file'], e['line'], e['message']) for e in new.errors}
    
    fixed = old_errors - new_errors
    added = new_errors - old_errors
    same = old_errors & new_errors
    
    lines = []
    lines.append("=" * 60)
    lines.append("Build Diff Report")
    lines.append(f"  Old: {old.error_count}E/{old.warning_count}W -> New: {new.error_count}E/{new.warning_count}W")
    lines.append("=" * 60)
    
    if fixed:
        lines.append(f"\n✅ Fixed ({len(fixed)}):")
        for f in sorted(fixed)[:15]:
            lines.append(f"  ✗ {f[0]}:{f[1]}  {f[2][:80]}")
    
    if added:
        lines.append(f"\n❌ New ({len(added)}):")
        for a in sorted(added)[:15]:
            lines.append(f"  + {a[0]}:{a[1]}  {a[2][:80]}")
    
    if not fixed and not added:
        lines.append("\n  No change in error set.")
    
    return '\n'.join(lines)


# ═════════════════════════════════════════════════════
# 5. 持续监控 (tail 模式)
# ═════════════════════════════════════════════════════

def watch_log(path):
    """实时监控编译日志文件变化"""
    print(f"[*] Watching: {path}")
    print("[*] Press Ctrl+C to stop")
    log = BuildLog()
    last_size = 0
    try:
        while True:
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    last_size = f.tell()
                
                for line in new_lines:
                    log.parse_line(line)
                    # Print real-time errors
                    if 'error' in line.lower() and ('error:' in line.lower() or 'Error:' in line):
                        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {line.rstrip()}")
                
                import time
                time.sleep(0.5)
            except FileNotFoundError:
                import time
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nFinal Report:")
        print(log.report_text())
        sys.exit(0)


# ═════════════════════════════════════════════════════
# 6. 主入口
# ═════════════════════════════════════════════════════

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    if "--watch" in sys.argv:
        idx = sys.argv.index("--watch") + 1
        if idx < len(sys.argv):
            watch_log(sys.argv[idx])
        return
    
    # 取日志源 (文件 或 stdin)
    log_sources = [a for a in sys.argv[1:] if not a.startswith('--')]
    
    if not log_sources:
        # Read from stdin
        text = sys.stdin.read()
        log = BuildLog().parse_text(text)
    else:
        log = BuildLog().parse_file(log_sources[0])
    
    # 差异比较
    if "--diff" in sys.argv:
        idx = sys.argv.index("--diff") + 1
        if idx < len(sys.argv):
            print(diff_logs(sys.argv[idx], log_sources[0]))
            return
    
    # 输出
    if "--json" in sys.argv:
        print(log.report_json())
    elif "--summary" in sys.argv:
        print(f"Errors: {log.error_count}  Warnings: {log.warning_count}")
        if log.build_time:
            print(f"Time: {log.build_time}")
        if log.memory:
            m = log.memory
            print(f"Code: {m['code']}B  RO: {m['ro_data']}B  RW: {m['rw_data']}B  ZI: {m['zi_data']}B")
    else:
        print(log.report_text())
    
    # 退出码
    if log.error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
