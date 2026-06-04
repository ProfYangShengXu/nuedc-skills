---
name: kicad
description: KiCad EDA 10.0 PCB 设计全流程技能 — 原理图→布局→布线→Gerber→3D预览，兼容 Reasonix/Claude Code/Codex/Cursor
run_as: inline
---

# KiCad EDA PCB 设计全流程技能

> **KiCad 10.0.3 版** — 开源 PCB 设计，电赛学生首选
> 从原理图到 Gerber 打样，agent 全程辅助

---

## 📦 一、安装与验证

### 1.1 安装 KiCad

```bash
# winget 安装（推荐）
winget install --id KiCad.KiCad --exact

# 或手动下载
# https://www.kicad.org/download/windows/
# 选择 kicad-10.0.3-x86_64.exe (~921MB)
```

### 1.2 验证安装

```bash
kicad-cli version          # 显示版本号: 10.0.3
kicad-cli --help           # 查看所有 CLI 命令
```

### 1.3 确认 Python API 可用

```bash
# 在 KiCad 内置 Python 中运行
& "C:\Program Files\KiCad.0in\python.exe" -c "import pcbnew; print(pcbnew.VERSION)"
```

---

## 🛠 二、KiCad CLI 命令速查

### 2.1 原理图操作

| 命令 | 说明 |
|------|------|
| `kicad-cli sch export svg schematic.kicad_sch --output output.svg` | 原理图导出 SVG |
| `kicad-cli sch export pdf schematic.kicad_sch --output output.pdf` | 原理图导出 PDF |
| `kicad-cli sch export bom schematic.kicad_sch --output bom.csv` | 导出 BOM |
| `kicad-cli sch export netlist schematic.kicad_sch --output netlist.net` | 导出网表 |

### 2.2 PCB 操作

| 命令 | 说明 |
|------|------|
| `kicad-cli pcb export gerber board.kicad_pcb --output gerber/` | 导出 Gerber（JLCPCB 打样） |
| `kicad-cli pcb export drill board.kicad_pcb --output gerber/` | 导出钻孔文件 |
| `kicad-cli pcb export svg board.kicad_pcb --output pcb.svg` | PCB 导出 SVG |
| `kicad-cli pcb export pdf board.kicad_pcb --output pcb.pdf` | PCB 导出 PDF |
| `kicad-cli pcb export pos board.kicad_pcb --output pos.csv` | 导出贴片坐标 |
| `kicad-cli pcb export step board.kicad_pcb --output board.step` | 导出 3D STEP |

### 2.3 设计规则检查 (DRC)

```bash
kicad-cli pcb drc board.kicad_pcb --output drc.rpt
# 输出: 间距错误 / 未连接网络 / 丝印冲突
```

---

## 🐍 三、Python API (pcbnew) 编程

### 3.1 自动创建 PCB 板

```python
import pcbnew

board = pcbnew.BOARD()
board.SetDesignSettings(pcbnew.DESIGN_SETTINGS())

# 设置板子大小
W = pcbnew.FromMM(50)
H = pcbnew.FromMM(40)

# 画板框
outline = pcbnew.PCB_SHAPE()
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetStart(pcbnew.VECTOR2I(0, 0))
outline.SetEnd(pcbnew.VECTOR2I(W, H))
board.Add(outline)

board.Save("my_board.kicad_pcb")
```

### 3.2 自动摆放元件

```python
import pcbnew

board = pcbnew.LoadBoard("my_board.kicad_pcb")

# 加载封装
fp = pcbnew.FootprintLoad("", "Package_QFP:LQFP-48_7x7mm_P0.5mm")
fp.SetReference("U1")
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25), pcbnew.FromMM(20)))
fp.SetOrientationDegrees(0)
board.Add(fp)

board.Save("my_board.kicad_pcb")
```

### 3.3 自动布线触发

```python
# KiCad 10.0 内部使用 FreeRouting 引擎
# 在 PCB Editor 中: Route → Auto-route → Route All
# 或通过 CLI:
# kicad-cli pcb autoroute board.kicad_pcb
```

### 3.4 Gerber 导出（脚本方式）

```python
import pcbnew, os

board = pcbnew.LoadBoard("my_board.kicad_pcb")
plotter = pcbnew.PLOT_CONTROLLER(board)
options = plotter.GetPlotOptions()
options.SetOutputDirectory("gerber")
options.SetPlotFrameRef(False)

for layer in [pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_SilkS, pcbnew.B_SilkS,
              pcbnew.F_Mask, pcbnew.B_Mask, pcbnew.Edge_Cuts]:
    plotter.OpenLayer(layer)
    plotter.PlotLayer(layer)
    plotter.CloseLayer()

# 钻孔文件
drill = pcbnew.DRILL_WRITER(board)
drill.SetOutputDirectory("gerber")
drill.CreateDrillFile()

print("[OK] Gerber exported to gerber/")
```

---

## 🔄 四、与现有工具集成

### 4.1 从 `nuedc-pcb-place.py` 生成的脚本自动布局

```bash
# 1. 生成 KiCad 自动布局脚本
python nuedc-pcb-place.py buck --kicad-script

# 2. 在 KiCad Python 环境中运行
# C:\Program Files\KiCad.0in\python.exe wiring-diagrams/kicad_auto_buck.py

# 3. 产出 auto_placed.kicad_pcb
# 4. 在 KiCad PCB Editor 中打开 → Route → Auto-route
# 5. kicad-cli pcb export gerber auto_placed.kicad_pcb --output gerber/
```

### 4.2 完整 PCB 设计流程

```
赛题 → nuedc-pcb-gen.py 算参数
     → nuedc-pcb-svg.py 出 SVG 原理图（参考用）
     → nuedc-pcb-place.py 出摆放方案 + KiCad 脚本
     → 用户: 在 KiCad 中运行脚本 → 自动摆好元件
     → 用户: Route → Auto-route → 自动布线
     → kicad-cli 导出 Gerber → 上传 JLCPCB 打样
```

---

## 📝 五、设计规则（DRC 参数）

### 5.1 JLCPCB 兼容规则

| 参数 | 最小值 | 推荐值 | 说明 |
|------|:------:|:------:|------|
| 线宽 | 5 mil | 8-12 mil | 电源线按电流加宽 |
| 线距 | 5 mil | 8 mil | 高压区 ≥ 40 mil |
| 过孔内径 | 0.2mm | 0.3mm | 大电流双过孔 |
| 过孔外径 | 0.4mm | 0.6mm | |
| 板厚 | 0.4mm | 1.6mm | 标准 |
| 铜厚 | 0.5oz | 1oz | 大电流 2oz |

### 5.2 走线电流对照

| 电流 | 1oz 线宽 | 2oz 线宽 | 说明 |
|:----:|:--------:|:--------:|------|
| 0.5A | 10 mil | 8 mil | 信号 |
| 1A | 20 mil | 15 mil | 小功率 |
| 2A | 40 mil | 25 mil | 中等 |
| 3A | 60 mil | 40 mil | 功率 |
| 5A | 120 mil | 70 mil | 大功率+开窗 |

---

## 🔧 六、常见问题

| 问题 | 解决 |
|------|------|
| KiCad Python 没有 `pcbnew` 模块 | 必须用 KiCad 自带的 Python (不是系统 Python) |
| CLI 导出中文乱码 | `kicad-cli` 前设置 `set PYTHONIOENCODING=utf-8` |
| 自动布线结果差 | 先手动摆好关键元件位置，再走电源和地 |
| Gerber 上传 JLCPCB 报错 | 检查 Gerber 文件名是否符合 JLC 格式 |
| DRC 报错太多 | `kicad-cli pcb drc board.kicad_pcb --output drc.rpt` 定位 |

---

## 📌 技能信息

- **版本**: v1.0 | **更新**: 2025-08
- **适用**: KiCad 10.0.3
- **前置**: 已安装 KiCad (winget / 手动)
- **配合**: `nuedc-pcb-gen.py` / `nuedc-pcb-place.py` / `nuedc-pcb-svg.py`
