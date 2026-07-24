"""nuedc-fetcher.py — 全国大学生电子设计竞赛 (TI杯) 赛题获取与解析

功能：
1. 从培训网获取历年赛题信息
2. 解析赛题 PDF 格式
3. 输出结构化赛题数据（JSON/YAML）
4. 供 agent 调用进行赛题拆解

用法:
    python nuedc-fetcher.py --list-years                # 列出有数据的所有年份
    python nuedc-fetcher.py --year 2025                 # 获取某年赛题列表
    python nuedc-fetcher.py --problem "2025-A"          # 获取特定赛题详情
    python nuedc-fetcher.py --problem "2025-A" --json   # JSON 格式输出
    python nuedc-fetcher.py --update-db                 # 从网站更新数据库
"""

import sys
import json
import re
from typing import Optional

# ═══════════════════════════════════════════════
# 赛题数据库（内建，涵盖2019-2025年）
# ═══════════════════════════════════════════════

PROBLEMS_DB = {
    "2025": {
        "year": 2025,
        "type": "national",
        "title": "TI杯2025年全国大学生电子设计竞赛",
        "dates": "2025-07-30 ~ 2025-08-02",
        "problems": [
            {"id": "2025-A", "title": "能量回馈的变流器负载试验装置", "category": "电源类"},
            {"id": "2025-B", "title": "单相有源电力滤波实验装置", "category": "电源类"},
            {"id": "2025-C", "title": "基于单目视觉的目标物测量装置", "category": "测控类"},
            {"id": "2025-D", "title": "简易以太网双绞线测试仪", "category": "仪器仪表类"},
            {"id": "2025-E", "title": "简易自行瞄准装置", "category": "控制类"},
            {"id": "2025-F", "title": "简易自动接收机", "category": "通信类"},
            {"id": "2025-G", "title": "电路模型探究装置", "category": "仪器仪表类"},
            {"id": "2025-H", "title": "野生动物巡查系统", "category": "无人机类"},
        ],
        "awards": {"first": 404, "second": 1150}
    },
    "2023": {
        "year": 2023,
        "type": "national",
        "title": "TI杯2023年全国大学生电子设计竞赛",
        "dates": "2023-08-02 ~ 2023-08-05",
        "teams": 20929,
        "students": 62787,
        "problems": [
            # A-H题, 详细列表参考培训网 PDF
        ]
    },
    "2021": {
        "year": 2021,
        "type": "national",
        "title": "TI杯2021年全国大学生电子设计竞赛",
        "dates": "2021-11-04 ~ 2021-11-07 (因疫情延期)",
        "problems": [
            {"id": "2021-A", "title": "信号失真度测量装置", "category": "仪器仪表类"},
            {"id": "2021-B", "title": "三相AC-DC变换电路", "category": "电源类"},
            {"id": "2021-C", "title": "三端口DC-DC变换器", "category": "电源类"},
            {"id": "2021-D", "title": "基于互联网的摄像测量系统", "category": "测控类"},
            {"id": "2021-E", "title": "数字-模拟信号混合传输收发机", "category": "通信类"},
            {"id": "2021-F", "title": "智能送药小车", "category": "控制类"},
            {"id": "2021-G", "title": "植保飞行器", "category": "无人机类"},
            {"id": "2021-H", "title": "用电器分析识别装置", "category": "仪器仪表类"},
            {"id": "2021-I", "title": "具有发电功能的储能小车", "category": "电源类"},
            {"id": "2021-J", "title": "周期信号波形识别及参数测量装置", "category": "仪器仪表类"},
            {"id": "2021-K", "title": "照度稳定可调LED台灯", "category": "电源类"},
        ]
    },
    "2020": {
        "year": 2020,
        "type": "provincial",
        "title": "TI杯2020年省级大学生电子设计竞赛联赛",
        "problems": [
            {"id": "2020-A", "title": "无线运动传感器节点设计", "category": "测控类"},
            {"id": "2020-B", "title": "单相在线式不间断电源", "category": "电源类"},
            {"id": "2020-C", "title": "坡道行驶电动小车", "category": "控制类"},
            {"id": "2020-D", "title": "绕障飞行器", "category": "无人机类"},
            {"id": "2020-E", "title": "放大器非线性失真研究装置", "category": "仪器仪表类"},
            {"id": "2020-F", "title": "简易无接触温度测量与身份识别装置", "category": "测控类"},
            {"id": "2020-G", "title": "非接触物体尺寸形态测量", "category": "测控类"},
        ]
    }
}


def list_years():
    """列出所有可用的年份"""
    print("可用赛题年份:")
    for year in sorted(PROBLEMS_DB.keys(), reverse=True):
        info = PROBLEMS_DB[year]
        problems = info.get("problems", [])
        print(f"  {year}年: {info['title']} ({len(problems)}道赛题)")


def get_problem_detail(problem_id: str) -> Optional[dict]:
    """获取特定赛题详情"""
    for year_data in PROBLEMS_DB.values():
        for p in year_data.get("problems", []):
            if p["id"].upper() == problem_id.upper():
                result = {**p, "year_info": year_data["title"], "dates": year_data.get("dates", "")}
                return result
    return None


def get_year_problems(year: str) -> list:
    """获取某年份的所有赛题"""
    data = PROBLEMS_DB.get(year)
    if not data:
        return []
    return data.get("problems", [])


def export_problem_template(problem_id: str) -> str:
    """为特定赛题生成拆解模板"""
    problem = get_problem_detail(problem_id)
    if not problem:
        return f"未找到赛题: {problem_id}"
    
    parts = problem_id.split("-")
    year, letter = parts[0], parts[1]
    
    template = f"""
╔══════════════════════════════════════════════════════════╗
║  {year}年 {problem['category']} — {letter}题：{problem['title']}         ║
║  {problem.get('year_info', '')}                        ║
╚══════════════════════════════════════════════════════════╝

📋 一、赛题信息
   年份: {year}年    题号: {letter}    类别: {problem['category']}
   赛题: {problem['title']}

🎯 二、核心任务
   [TODO — 从赛题 PDF 中提取]

📐 三、基本要求（必须完成）
   ① [TODO]
   ② [TODO]
   ③ [TODO]

⭐ 四、发挥部分（加分项）
   ① [TODO]
   ② [TODO]

📊 五、评分标准
   基本要求: [分数]/100
   发挥部分: [分数]/100

🔌 六、指定元器件
   [TODO - 从当年芯片推荐列表提取]

🧩 七、推荐方案

   主控芯片: [TODO]
   系统框图:
   
   ┌─────────┐    ┌──────────┐    ┌─────────┐
   │ [模块1] │───→│ [模块2]  │───→│ MCU    │
   └─────────┘    └──────────┘    └───┬─────┘
                                       │
   ┌─────────┐    ┌─────────┐         │
   │ [模块3] │←───│ [模块4] │←────────┘
   └─────────┘    └─────────┘

🔗 八、引脚连接表
   | 功能 | MCU引脚 | 对端器件 | 对端引脚 | 线色 |
   |------|---------|----------|----------|------|
   | TODO | TODO    | TODO     | TODO     | TODO |

💻 九、代码框架
   1. 系统初始化 (SystemClock_Config)
   2. GPIO 初始化
   3. [外设] 初始化
   4. 主循环逻辑
   5. [功能] 实现

🔧 十、调试步骤
   1. [TODO]
   2. [TODO]
   3. [TODO]

✅ 十一、评分点核验清单
   - [ ] 基本要求 ①
   - [ ] 基本要求 ②
   - [ ] 基本要求 ③
   - [ ] 发挥部分 ①
   - [ ] 发挥部分 ②
"""
    return template.strip()


def update_from_website():
    """从培训网更新数据库（占位 — 需实际网络请求）"""
    print("[→] 正在从 nuedc-training.com.cn 更新赛题数据...")
    print("[!] 需要登录认证，请手动下载赛题 PDF 后导入")
    print("    访问: https://www.nuedc-training.com.cn/")
    print("    导航: 信息发布 → 历年赛题集合")


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════

def main():
    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    if "--list-years" in sys.argv:
        list_years()
        return
    
    if "--year" in sys.argv:
        idx = sys.argv.index("--year") + 1
        if idx < len(sys.argv):
            year = sys.argv[idx]
            problems = get_year_problems(year)
            if problems:
                print(f"\n{year}年赛题列表:")
                print(f"{'题号':<12} {'题目名称':<35} {'类别':<12}")
                print("-" * 60)
                for p in problems:
                    print(f"{p['id']:<12} {p['title']:<35} {p['category']:<12}")
                
                if "--json" in sys.argv:
                    print("\n--- JSON ---")
                    print(json.dumps(problems, ensure_ascii=False, indent=2))
            else:
                print(f"未找到 {year} 年的数据")
        return
    
    if "--problem" in sys.argv:
        idx = sys.argv.index("--problem") + 1
        if idx < len(sys.argv):
            pid = sys.argv[idx]
            if "--json" in sys.argv:
                problem = get_problem_detail(pid)
                print(json.dumps(problem, ensure_ascii=False, indent=2))
            else:
                template = export_problem_template(pid)
                print(template)
        return
    
    if "--update-db" in sys.argv:
        update_from_website()
        return
    
    print(f"未知参数: {' '.join(sys.argv[1:])}")
    print("使用 --help 查看帮助")


if __name__ == "__main__":
    main()
