# ⚡ 电赛七件套 · NUEDC Toolchain Skills

> *"赛题发下来那一刻，你已经赢了。"*

一套给 AI 编程代理用的电赛技能包。赛题拆解 → 电路仿真 → MCU 配置 → 代码生成 → 编译烧录 → PCB 打样，除了**接线和焊接**，AI 替你全包了。

---

## 🧰 七把武器

| # | 技能 | 一句话 | 电赛考点 |
|:--:|------|--------|----------|
| 🔍 | **nuedc** | 赛题拆解引擎 | 读题 → 方案 → 评分点核对 |
| ⚙️ | **cubemx** | STM32 引脚/时钟/外设配置 | CubeMX2 CLI 一键生成 Keil 工程 |
| 🔫 | **keil5** | ARM 编译/烧录/调试 | UV4 CLI + JLink/ST-Link |
| ⚡ | **ltspice** | 免费 SPICE 仿真 | Buck/Boost/运放/滤波/FFT |
| 🧬 | **modelsim** | Verilog/VHDL 仿真 | Testbench + 波形 + 覆盖率 |
| 💎 | **quartus** | FPGA 综合/布局/下载 | Cyclone IV → .sof 生成 |
| 📐 | **kicad** | PCB 设计 | 原理图 → 布线 → Gerber 打样 |

---

## 🚀 快速开始

把整个仓库丢进你的 Reasonix/Claude Code 项目的 `.reasonix/skills/` 目录：

```bash
git clone https://github.com/YOUR_USER/nuedc-skills.git .reasonix/skills
```

然后对 AI 说：

```
用 nuedc 技能分析 2025 年 A 题
```

AI 会自动：

```
赛题拆解 → 判定赛题类型
             ├─ 模拟电路 → 调 ltspice 仿真验证方案
             ├─ STM32    → 调 cubemx 生成 HAL 框架 → keil5 编译烧录
             ├─ FPGA     → 调 modelsim 仿真 → quartus 综合下载
             └─ 全部     → 调 kicad 出 PCB
```

---

## 🎯 赛题 → 工具自动路由

| 赛题类型 | 主控 | 仿真 | 代码 |
|----------|:----:|------|------|
| 🔌 电源类 | STM32/DSP | `ltspice` (功率拓扑) | `cubemx` + `keil5` |
| 🚗 控制类 | STM32 | `ltspice` (电机驱动) | `cubemx` + `keil5` |
| 📡 测控/仪器 | STM32/FPGA | `ltspice` + `modelsim` | `cubemx`+`keil5` / `quartus` |
| 📻 高频/通信 | FPGA+STM32 | `ltspice` + `modelsim` | `quartus` + `keil5` |
| 🛸 无人机 | STM32 | — | `cubemx` + `keil5` |
| 🧪 综合测评 | 纯模拟 | `ltspice` (运放) | — |

---

## 📂 目录结构

```
.reasonix/skills/
├── nuedc/SKILL.md       ← 总指挥：赛题拆解 + 工具路由
├── cubemx/SKILL.md      ← STM32CubeMX2 CLI
├── keil5/SKILL.md       ← Keil MDK-ARM
├── ltspice/SKILL.md     ← LTspice SPICE 仿真
├── modelsim/SKILL.md    ← ModelSim HDL 仿真
├── quartus/SKILL.md     ← Intel Quartus II
└── kicad/SKILL.md       ← KiCad EDA
```

每个 `SKILL.md` 都包含：安装指引 + CLI 速查表 + 代码模板 + 电赛场景 + 排错 FAQ。

---

## 🧪 已验证的实战场景

| 工具 | 验证内容 | 结果 |
|------|----------|:--:|
| `modelsim` | 计数器 Testbench (597 个自动比对点) | ✅ |
| `quartus` | EP4CE6 全流程编译 → `counter.sof` (Fmax=283MHz) | ✅ |
| `cubemx` | CubeMX2 CLI 启动 + 设备查询 | ✅ |
| `ltspice` | 安装验证 (v26) + 批处理模式确认 | ✅ |

---

## ⚠️ 免责声明

这套技能包**不会**帮你：
- 🪛 拿烙铁
- 🔌 插杜邦线
- 📟 拧示波器旋钮

但它会让你在动手之前**已经知道每一根线该往哪插、每一行代码该写什么、每一个波形长什么样**。

---

<p align="center">
  <i>Made with ❤️‍🔥 for NUEDC contestants. 四天三夜，冲就完了。</i>
</p>
