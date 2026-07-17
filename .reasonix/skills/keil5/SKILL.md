---
name: keil5
description: Keil MDK-ARM 嵌入式开发全能技能 — 下载安装/CLI编译/烧录/调试/动态硬件接线图生成，兼容 Claude Code/Reasonix/Codex/Cursor
run_as: inline
---

# Keil5 嵌入式开发全能技能 (Keil MDK-ARM)

> **一次掌握 Keil MDK-ARM 全套开发流程** — 下载安装 → 编写代码 → CLI编译 → 烧录 → 调试 → 硬件接线
> 兼容 Claude Code、Reasonix Code、Codex、Cursor、Windsurf 等主流 AI 编程代理

---

## 📦 一、下载与安装

### 1.1 下载 Keil MDK-ARM v5.43a

**官方下载**（需要填写联系表）：

```
https://www.keil.com/demo/eval/arm.htm
```

填写说明：
| 字段 | 填写建议 |
|------|----------|
| First Name / Last Name | 任意英文名 |
| E-mail | 你的真实邮箱（用于接收下载链接） |
| Company | 随意填写 |
| Country/Region | China |
| Device | 目标芯片型号，如 `STM32F103C8T6` |

> 安装包约 **872 MB**，下载后文件名为 `MDK543a.exe`

**备用下载**（百度网盘）：
- 链接: `https://pan.baidu.com/s/1zl3Iwb2MgKB3g8d2X7La3w` 提取码: `musy`

### 1.2 安装步骤

```
1. 右键 MDK543a.exe → 以管理员身份运行
2. Next → I agree to all terms
3. 选择安装路径（建议默认 C:\Keil_v5\）
4. 填写用户信息（任意）
5. 等待安装完成（5-10分钟）
6. ✔ 安装完成
```

### 1.3 添加环境变量

安装后执行以下命令，将 UV4 添加进 PATH：

```powershell
# PowerShell (管理员)
$uv4Path = "C:\Keil_v5\UV4"
$oldPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$oldPath;$uv4Path", "User")
```

验证安装：
```batch
UV4.exe -?     :: 显示帮助信息（确认安装成功）
```

### 1.4 安装 Device Pack（芯片支持包）

以 STM32F1 系列为例：
```batch
UV4.exe --pack  Keil.STM32F1xx_DFP.2.4.1.pack
```

或通过 Pack Installer GUI: `UV4.exe` → Pack Installer → 搜索并安装所需芯片包

在线安装命令（需连网）：
```batch
UV4.exe --pack --list                    :: 列出可用包
UV4.exe --pack --install Keil::STM32F1xx  :: 安装指定包
```

---

## 🛠 二、CLI 命令速查表

### 2.1 项目操作

| 命令 | 说明 |
|------|------|
| `UV4.exe -?` | 显示帮助信息 |
| `UV4.exe -b project.uvprojx` | **编译**（Build）项目 |
| `UV4.exe -r project.uvprojx` | **重新编译全部**（Rebuild All） |
| `UV4.exe -j0 project.uvprojx` | 静默编译（无 GUI 弹窗） |
| `UV4.exe -c project.uvprojx` | 编译后编程烧录 |
| `UV4.exe -d project.uvprojx` | 启动调试会话 |
| `UV4.exe -e project.uvprojx` | 擦除目标 Flash |
| `UV4.exe -f project.uvprojx` | 烧录到目标 Flash |
| `UV4.exe -n project.uvprojx` | 编译并显示编译结果编号 |
| `UV4.exe -o output.txt project.uvprojx` | 编译并将日志输出到文件 |
| `UV4.exe -t project.uvprojx` | 仅翻译（Translated）文件 |
| `UV4.exe -v project.uvprojx` | 详细输出模式 |

### 2.2 返回值（Exit Code）

| 返回值 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 警告（编译通过但有警告） |
| 2 | 错误（编译失败） |
| 3 | 致命错误 |

### 2.3 文件格式转换

```batch
:: .axf → .hex (Intel HEX)
"C:\Keil_v5\ARM\ARMCC\bin\fromelf.exe" --i32 -o output.hex output.axf

:: .axf → .bin (Binary)
"C:\Keil_v5\ARM\ARMCC\bin\fromelf.exe" --bin -o output.bin output.axf

:: .axf → 反汇编 .txt
"C:\Keil_v5\ARM\ARMCC\bin\fromelf.exe" -c -o output.disasm.txt output.axf

:: .axf → 包含调试信息的 .hex
"C:\Keil_v5\ARM\ARMCC\bin\fromelf.exe" --i32 --debug -o output_with_dbg.hex output.axf
```

---

## 📝 三、代码编写与项目管理

### 3.1 创建 Keil 项目

项目由一个 `.uvprojx` 文件（XML 格式）定义。以下是用 Python 生成模板项目的脚本：

```python
"""create_keil_project.py — 生成 Keil MDK 项目模板"""
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

def create_keil_project(name: str, mcu: str = "STM32F103C8", 
                       device_pack: str = "Keil.STM32F1xx_DFP.2.4.1"):
    """生成 Keil uVision5 项目骨架"""
    
    proj_dir = Path(name)
    proj_dir.mkdir(exist_ok=True)
    
    # 创建源文件目录
    (proj_dir / "Src").mkdir(exist_ok=True)
    (proj_dir / "Inc").mkdir(exist_ok=True)
    
    # ====== 生成 main.c ======
    main_c = """#include "main.h"

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_USART1_UART_Init();
    
    while (1)
    {
        HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
        HAL_Delay(500);
    }
}

void SystemClock_Config(void)
{
    // 系统时钟配置（HSE 8MHz → SYSCLK 72MHz）
}

void MX_GPIO_Init(void)
{
    // GPIO 初始化
}

void MX_USART1_UART_Init(void)
{
    // USART1 初始化
}

void Error_Handler(void)
{
    __disable_irq();
    while (1) {}
}
"""
    (proj_dir / "Src" / "main.c").write_text(main_c, encoding="utf-8")
    
    # ====== 生成 main.h ======
    main_h = """#ifndef __MAIN_H
#define __MAIN_H

#include "stm32f1xx_hal.h"

#define LD2_Pin       GPIO_PIN_13
#define LD2_GPIO_Port GPIOC

void Error_Handler(void);
void SystemClock_Config(void);
void MX_GPIO_Init(void);
void MX_USART1_UART_Init(void);

#endif /* __MAIN_H */
"""
    (proj_dir / "Inc" / "main.h").write_text(main_h, encoding="utf-8")
    
    # ====== 生成 .uvprojx 骨架 ======
    # 注意：完整项目文件需从 Keil GUI 创建后导出
    # 这里生成一个简化版本供参考
    
    print(f"[✓] 项目 '{name}' 创建成功!")
    print(f"    目录结构:")
    print(f"    {name}/")
    print(f"    ├── Src/main.c")
    print(f"    └── Inc/main.h")
    print()
    print(f"下一步: 在 Keil uVision5 中创建同名项目，导入源文件")
```

### 3.2 使用 Makefile + armcc（无 GUI 构建）

如果不想用 .uvprojx 文件，可以直接用 ARMCC 编译器：

```makefile
# Makefile for Keil ARMCC
# 用法: make, make clean, make flash

# 工具链路径
ARMCC_PATH  = C:/Keil_v5/ARM/ARMCC/bin
CC          = $(ARMCC_PATH)/armcc.exe
ASM         = $(ARMCC_PATH)/armasm.exe
LINK        = $(ARMCC_PATH)/armlink.exe
FROMELF     = $(ARMCC_PATH)/fromelf.exe

# 项目设置
TARGET      = firmware
MCU         = STM32F103C8
CPU_FLAGS   = --cpu Cortex-M3 -O2 --apcs=interwork
LD_FLAGS    = --cpu Cortex-M3 --scatter=scatter.sct

# 源文件
SRC_DIR     = Src
INC_DIR     = Inc
STARTUP_DIR = startup
OBJ_DIR     = Obj

C_SOURCES   = $(wildcard $(SRC_DIR)/*.c)
ASM_SOURCES = $(wildcard $(STARTUP_DIR)/*.s)
C_OBJECTS   = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(C_SOURCES))
ASM_OBJECTS = $(patsubst $(STARTUP_DIR)/%.s, $(OBJ_DIR)/%.o, $(ASM_SOURCES))
OBJECTS     = $(C_OBJECTS) $(ASM_OBJECTS)

# 头文件路径
INCLUDES    = -I$(INC_DIR) -I$(ARMCC_PATH)/../include

# 编译规则
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) -c $(CPU_FLAGS) $(INCLUDES) -o $@ $<

$(OBJ_DIR)/%.o: $(STARTUP_DIR)/%.s
	@mkdir -p $(OBJ_DIR)
	$(ASM) $(CPU_FLAGS) -o $@ $<

# 链接
$(TARGET).axf: $(OBJECTS)
	$(LINK) $(LD_FLAGS) --list=$(TARGET).map -o $@ $^
	$(FROMELF) --bin -o $(TARGET).bin $@
	$(FROMELF) --i32 -o $(TARGET).hex $@
	@echo "=== Build Complete: $(TARGET).hex ==="

.PHONY: all clean flash
all: $(TARGET).axf

clean:
	rm -rf $(OBJ_DIR) $(TARGET).axf $(TARGET).bin $(TARGET).hex $(TARGET).map

flash:
	$(FROMELF) --i32 -o $(TARGET).hex $(TARGET).axf
	@echo "请使用烧录工具（J-Flash / ST-Link Utility）写入 $(TARGET).hex"
```

---

## 🔥 四、烧录 / 编程 (Flash/Program)

### 4.1 通过 UV4（需配置 debug 选项）

```batch
:: 编译并烧录
UV4.exe -c project.uvprojx

:: 仅烧录（不编译）
UV4.exe -f project.uvprojx
```

### 4.2 通过 J-Link (SEGGER)

```batch
:: 直接烧录 HEX 文件
JLink.exe -device STM32F103C8 -if SWD -speed 4000 -autoconnect 1 -CommanderScript flash.jlink
```

```
:: flash.jlink 脚本文件内容
device STM32F103C8
si SWD
speed 4000
connect
erase
loadfile firmware.hex
r
g
exit
```

### 4.3 通过 ST-Link CLI

```batch
:: 使用 ST-Link 官方工具烧录 HEX
"C:\Program Files\STMicroelectronics\STM32 ST-LINK Utility\ST-LINK Utility\ST-LINK_CLI.exe" -c SWD -P firmware.hex -Rst

:: 使用 stm32flash (串口方式，需配置 Boot0)
stm32flash -w firmware.hex -v -g 0x0 COM3
```

### 4.4 通过 OpenOCD

```batch
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program firmware.hex verify reset exit"
```

### 4.5 通过 pyOCD (Python)

```bash
# 安装
pip install pyocd

# 列出可用目标
pyocd list --targets

# 烧录
pyocd flash --target stm32f103c8 firmware.hex

# 带调试信息烧录
pyocd flash --target stm32f103c8 --erase auto firmware.hex
```

---

## 🐛 五、调试 (Debug)

### 5.1 UV4 GUI 调试

```batch
:: 启动调试会话
UV4.exe -d project.uvprojx
```

### 5.2 GDB + pyOCD（命令行调试）

```bash
# 终端 1: 启动 GDB 服务器
pyocd gdbserver --target stm32f103c8 -p 3333

# 终端 2: 连接 GDB
arm-none-eabi-gdb firmware.elf
(gdb) target remote localhost:3333
(gdb) monitor reset halt
(gdb) load
(gdb) break main
(gdb) continue
(gdb) info registers
(gdb) monitor help
```

### 5.3 GDB + OpenOCD

```bash
# 终端 1
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg

# 终端 2
arm-none-eabi-gdb firmware.elf
(gdb) target remote localhost:3333
(gdb) monitor reset halt
(gdb) flash write_image erase firmware.hex
(gdb) break main.c:42
(gdb) continue
(gdb) print x
(gdb) display/10i $pc
```

### 5.4 常用 GDB 调试命令

| 命令 | 说明 |
|------|------|
| `target remote :3333` | 连接到 GDB Server |
| `monitor reset halt` | 复位并停止 |
| `load` | 加载固件到 Flash |
| `break main` | 设置断点 |
| `info registers` | 查看寄存器 |
| `print var` | 打印变量值 |
| `display var` | 每次暂停时自动打印变量 |
| `step` / `next` | 单步 / 跳过函数 |
| `continue` | 继续执行 |
| `backtrace` | 查看调用栈 |
| `x/10x $sp` | 查看栈内存 |
| `monitor help` | 查看 monitor 命令 |

---

## 🔌 六、硬件接线指南 — 动态 SVG 接线图生成器

> 不再用死板的 ASCII 图！现在根据你的 MCU 型号和外设，**动态生成 SVG 接线图**。
> 管线接法、引脚编号、外设电路，全都按你的项目自动匹配。

### 6.1 快速开始

```bash
# 生成 STM32F103C8 的调试器接线图
python keil-wiring-diagram.py --mcu STM32F103C8

# 生成带 LED 的接线图（LED 接 PB0）
python keil-wiring-diagram.py --mcu STM32F103C8 --peripherals "LED:PB0"

# 直接从 Keil 项目文件读取 MCU 型号
python keil-wiring-diagram.py --project firmware.uvprojx --peripherals "LED:PC13"

# 英文版
python keil-wiring-diagram.py --mcu STM32F103C8 --lang en

# 保存到指定路径
python keil-wiring-diagram.py --mcu STM32F407VG --peripherals "LED:PE0,OLED:I2C1" -o my_wiring.svg
```

### 6.2 命令行参数速查

| 参数 | 说明 | 示例 |
|------|------|------|
| `--mcu` | MCU 型号 | `STM32F103C8`, `STM32F407VG`, `STM32G030F6` |
| `--peripherals` | 外设列表（逗号分隔） | `"LED:PB0,BUTTON:PA0,SERVO:PA1"` |
| `--debug` | 调试接口 | `swd`（默认）, `jtag`, `uart` |
| `--project` | 从 .uvprojx 读取 MCU | `--project test.uvprojx` |
| `--lang` | 语言 | `zh`（默认）, `en` |
| `--mode` | 配色模式 | `color`（默认）, `dark`, `high-contrast` |
| `-o` | 输出路径 | `-o output/wiring.svg` |
| `--list-mcus` | 列出支持的 MCU | — |
| `--list-peripherals` | 列出支持的外设 | — |
| `--all` | 批量生成所有 MCU 组合 | — |

### 6.3 支持的 MCU（可在运行时动态扩展）

| MCU 型号 | 完整名称 | 内核 | 封装 |
|----------|---------|------|------|
| `STM32F103C8` | STM32F103C8T6 | Cortex-M3 | LQFP48 |
| `STM32F103R6` | STM32F103R6T6 | Cortex-M3 | LQFP64 |
| `STM32F103VE` | STM32F103VET6 | Cortex-M3 | LQFP100 |
| `STM32F407VG` | STM32F407VGT6 | Cortex-M4 (FPU) | LQFP100 |
| `STM32F411CE` | STM32F411CEU6 | Cortex-M4 (FPU) | UFQFPN48 |
| `STM32G030F6` | STM32G030F6P6 | Cortex-M0+ | TSSOP20 |

### 6.4 支持的外设

| 外设 | 语法 | 说明 |
|------|------|------|
| **LED** | `LED:PA0` | GPIO → 限流电阻 → LED → GND |
| **按钮** | `BUTTON:PA1` | GPIO → 按钮 → 3.3V (上拉/下拉自适应) |
| **舵机** | `SERVO:PA2` | PWM 引脚 → 舵机信号线 |
| **蜂鸣器** | `BUZZER:PA3` | GPIO → 三极管驱动 → 蜂鸣器 |
| **OLED** | `OLED:I2C1` | I2C 接口 → OLED 屏 (SSD1306) |
| **I2C** | `I2C1` | I2C 总线 (SCL/SDA) |
| **SPI** | `SPI1` | SPI 总线 (CS/SCK/MOSI/MISO) |
| **UART** | `UART:PA9-PA10` | 串口 (TX/RX) |

### 6.5 多外设组合示例

```bash
# STM32F407 综合项目：LED + OLED + 按钮 + 舵机
python keil-wiring-diagram.py --mcu STM32F407VG ^
  --peripherals "LED:PE0,OLED:I2C1,BUTTON:PE4,SERVO:PA0" ^
  --lang zh -o project_wiring.svg

# STM32G030 最小系统 + LED + 按钮
python keil-wiring-diagram.py --mcu STM32G030F6 ^
  --peripherals "LED:PA1,BUTTON:PA2" --debug swd

# 深色模式，直接打印
python keil-wiring-diagram.py --mcu STM32F411CE ^
  --peripherals "LED:PC13" --mode dark -o dark_wiring.svg
```

### 6.6 器材选购指南

运行以下命令生成精美的 SVG 器材清单：

```bash
python keil-wiring-diagram.py --all      # 含器材清单 SVG
```

已预生成的 SVG 文件位于 `wiring-diagrams/` 目录，直接用浏览器打开：

| 文件 | 内容 |
|------|------|
| `wiring-diagrams/component-guide_zh.svg` | 中文器材选购指南 |
| `wiring-diagrams/component-guide_en.svg` | English Component Guide |
| `wiring-diagrams/wiring_STM32F103C8.svg` | STM32F103C8 接线图 |
| `wiring-diagrams/wiring_STM32F103C8_LED_PB0.svg` | F103C8 + LED 接线图 |
| `wiring-diagrams/wiring_STM32F407VG_LED_PE0_OLED_I2C1.svg` | F407 + LED + OLED |
| `wiring-diagrams/wiring_STM32F411CE_LED_PC13_SERVO_PA0.svg` | F411 + LED + 舵机 |

### 6.7 接线原则（不论什么芯片都通用）

```
ST-Link V2       杜邦线颜色       STM32 开发板
───────────      ─────────        ─────────────
 3.3V (Pin 4)  ─── 红色 ───→     3.3V / VCC
 GND  (Pin 3)  ─── 黑色 ───→     GND
 SWDIO(Pin 2)  ─── 黄色 ───→     PA13 (SWDIO)
 SWCLK(Pin 1)  ─── 绿色 ───→     PA14 (SWCLK)

⚠️ 红线=3.3V, 黑线=GND — 这两根接反会烧板子！
⚠️ 先断开所有 USB 再插拔线
⚠️ 不同版本 ST-Link 引脚排列可能不同，以 SVG 图为准
```

---

## 🧰 七、常见问题排查 (FAQ)

### 7.1 工具链问题

| 问题 | 检查项 |
|------|--------|
| `UV4.exe` 找不到 | 确认已添加到 PATH 或使用完整路径 |
| 编译报错 `L6218E: Undefined symbol` | 检查是否缺少 .c 文件或库引用 |
| 烧录报错 `Flash Download failed` | 1. 检查接线 2. 确认芯片型号 3. 检查复位电路 |
| 找不到目标芯片 | 安装对应的 Device Family Pack |
| `Error: Connection refused` | ST-Link 驱动没装好，检查设备管理器 |

### 7.2 硬件问题

| 问题 | 解决 |
|------|------|
| 电脑不识别 ST-Link | 安装 ST-Link 驱动 (stlink driver) |
| 烧录时报 RDDI-DAP 错误 | 接线松动，重新插拔杜邦线 |
| LED 不亮 | 可能接反了（长脚接正！）或电阻太大了 |
| 板子不工作 | 检查 3.3V 供电是否正常 |
| ST-Link 红灯不亮 | USB 线可能只是供电线(无数据线功能)，换一根 |

### 7.3 编译日志自动分析

```bash
# 分析上次编译结果
python keil-log-analyzer.py build.log

# 只看摘要
python keil-log-analyzer.py build.log --summary

# JSON 输出 (供 CI/其他工具消费)
python keil-log-analyzer.py build.log --json

# 实时监控 (tail 模式，编译时自动输出新错误)
python keil-log-analyzer.py --watch build.log

# 与上次编译对比 (看修复了哪些/新增了哪些)
python keil-log-analyzer.py build.log --diff previous_build.log
```

输出示例：
```
📊 Summary:  3 Error(s), 2 Warning(s)
⏱  Build Time: 00:00:03
💾 Flash: 1290 B  |  RAM: 1036 B

❌ Errors by category:
   undefined: 2
   linker: 2

❌ main.c:12  #20: identifier "HAL_Init" is undefined
❌ gpio.c:8   #20: identifier "GPIO_PIN_0" is undefined
❌ firmware.axf  L6218E: Undefined symbol HAL_Init
❌ firmware.axf  L6218E: Undefined symbol HAL_GPIO_WritePin

📌 Most Common:
   [2x] Undefined symbol / identifier
```

### 7.4 诊断脚本

```batch
:: check-keil-env.bat — 检查 Keil 开发环境
@echo off
echo ═══ Keil 环境检查 ═══

where UV4.exe >nul 2>&1
if %errorlevel%==0 (
    echo [✓] UV4.exe 已找到
) else (
    echo [✗] UV4.exe 未在 PATH 中
)

if exist "C:\Keil_v5\UV4\UV4.exe" (
    echo [✓] Keil v5 已安装
) else (
    echo [✗] Keil v5 未安装
)

where JLink.exe >nul 2>&1
if %errorlevel%==0 (
    echo [✓] J-Link 工具已找到
) else (
    echo [─] J-Link 未安装
)

where openocd.exe >nul 2>&1
if %errorlevel%==0 (
    echo [✓] OpenOCD 已找到
) else (
    echo [─] OpenOCD 未安装
)

:: 检查 ST-Link
pnputil /enum-devices 2>nul | findstr /i "STLink ST-Link" >nul
if %errorlevel%==0 (
    echo [✓] ST-Link 驱动已安装
) else (
    echo [─] ST-Link 驱动未检测到
)

echo ═══ 检查完成 ═══
```

---

## 🧩 八、代理集成指南

### 8.1 Reasonix Code

在 Reasonix 中，通过 `run_skill("keil5", arguments="...")` 调用：

```
用户 → "帮我编译项目 C:\project\test.uvprojx"
Agent → `run_skill("keil5", arguments="编译 C:\project\test.uvprojx")`
```

### 8.2 Claude Code

通过 `.claude/settings.json` 或自定义工具注册：

```json
// .claude/settings.json
{
  "tools": [
    {
      "name": "keil-build",
      "description": "编译 Keil 项目 (.uvprojx)",
      "command": "UV4.exe -b {{project_path}} -j0"
    },
    {
      "name": "keil-flash",
      "description": "烧录 hex 到目标板",
      "command": "JLink.exe -device {{device}} -if SWD -speed 4000 -autoconnect 1 -CommanderScript flash.jlink"
    }
  ]
}
```

### 8.3 Cursor / Windsurf

在 `.cursorrules` 或 project rules 中引用此 SKILL.md：

```markdown
<!-- .cursorrules -->
请在回答 Keil/嵌入式相关问题时参考 `.reasonix/skills/keil5/SKILL.md` 中的知识。
```

### 8.4 Codex / 其他 AI 代理

在对话开始时注入该技能：
```
请参考以下 Keil5 开发技能文档回答我的嵌入式开发问题:
<skill>keil5</skill>
```

---

---

## 🖨️ 九、PCB 设计 — 原理图 → 打样全流程

> 从赛题指标到 Gerber 文件，agent 帮你一步到位。
> 配合 `nuedc-pcb-gen.py` + `nuedc-pcb-svg.py` 自动生成原理图、网表、BOM、布局指导、下单参数。

### 10.1 核心工具

| 工具 | 文件 | 功能 |
|------|------|------|
| 电路计算器 | `nuedc-pcb-gen.py` | Buck/Boost/LDO/运放/H桥参数自动计算 |
| SVG原理图 | `nuedc-pcb-svg.py` | 生成带元件符号+标号+参数表的电路图 |
| 立创EDA网表 | 内置在 SVG 输出中 | 可手动导入立创EDA |
| BOM 表 | 内置 CSV 格式输出 | 含立创商城料号，直接下单 |

### 10.2 生成原理图

```bash
# Buck 降压 12V→3.3V@2A
python nuedc-pcb-svg.py

# 输出 → wiring-diagrams/buck_12to3v3.svg (SVG原理图)
#        wiring-diagrams/boost_5to12.svg  (SVG原理图)
```

生成的 SVG 包含：完整的元件符号（电阻/电容/电感/MOS管/二极管/IC方框）、连接导线、参数计算表（占空比/电感值/电容值/二极管电流/MOS管耐压）。

### 10.3 电路参数计算

```python
from nuedc_pcb_gen import calc_buck, calc_boost

# Buck: 12V→3.3V@2A, 500kHz
p = calc_buck(12, 3.3, 2, 500000)
# 结果: duty=0.275, L=9.6uH, Cout=33.3uF

# Boost: 5V→12V@1A, 400kHz
p = calc_boost(5, 12, 1, 400000)
# 结果: duty=0.583, L=10.4uH, Cout=24.1uF
```

### 10.4 元件选型（立创商城料号）

| 元件 | 型号 | 立创料号 | 封装 |
|------|------|---------|------|
| MCU | STM32F103C8T6 | C8329 | LQFP-48 |
| MCU | TMS320F28027 | C181138 | TQFP-48 |
| Buck IC | LM2596S-ADJ | C16713 | TO-263-5 |
| LDO 3.3V | AMS1117-3.3 | C6186 | SOT-223 |
| 运放 | LM358 | C7250 | SOP-8 |
| 比较器 | LM393 | C7459 | DIP-8 |
| N-MOS | IRF3205 | C4294 | TO-220 |
| 肖特基 | SS34 | C8673 | SMA |
| 电感 | CD54 10uH | C95901 | CD54 |

### 10.5 PCB 走线规则

| 电流 | 线宽(1oz铜) | 线宽(2oz铜) | 说明 |
|------|:----------:|:----------:|------|
| < 0.5A | 10 mil | 8 mil | 信号线 |
| 0.5-1A | 20 mil | 15 mil | 小功率 |
| 1-3A | 40 mil | 30 mil | 功率线 |
| 3-5A | 80 mil | 50 mil | 大功率 |
| 5-10A | 150 mil | 100 mil | 需加开窗 |

**间距规则（立创EDA默认）：**
- 信号线间距: ≥ 8 mil
- 电源线间距: ≥ 12 mil
- 高压区(>36V): ≥ 40 mil
- 过孔: 内径0.3mm / 外径0.6mm

### 10.6 JLCPCB 下单参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 板层 | 2层 | 绝大多数电赛够用 |
| 板厚 | 1.6mm | 标准厚度 |
| 铜厚 | 1 oz | 标准, 大电流选2oz |
| 颜色 | 绿色/蓝色 | 绿色最便宜 |
| 最小线宽 | 8 mil | 立创EDA DRC默认 |
| 最小间距 | 8 mil | |
| 阻焊 | 绿色 | 含 |
| 丝印 | 白色 | 含 |
| 打样数量 | 5片 | ¥20-50 |
| 交期 | 2-4天打样+3天快递 | 加急24H |

### 10.7 DRC 自查清单

```
□ 所有网络都有连接（无飞线）
□ 电源线宽满足电流要求
□ 高压区域间距 ≥ 40 mil
□ 去耦电容靠近芯片引脚
□ GND 覆铜完整（无孤岛）
□ 过孔数量足够（大电流双过孔）
□ 丝印不重叠
□ 板框尺寸正确
□ 安装孔带接地
□ 接口/排针方向标清
```

---

## 📚 十、参考资源

| 资源 | 链接 |
|------|------|
| Keil 官方文档 | https://www.keil.com/support/man/ |
| UV4 命令行参考 | `UV4.exe -?` |
| ARMCC 编译器指南 | `C:\Keil_v5\ARM\ARMCC\html\index.html` |
| ST-Link 文档 | https://www.st.com/en/development-tools/st-link-v2.html |
| OpenOCD 手册 | http://openocd.org/doc/html/ |
| pyOCD 文档 | https://pyocd.io/ |
| CMSIS-Pack 列表 | https://www.keil.com/dd2/pack/ |
| J-Link 命令参考 | `JLink.exe -?` |

---

> 📌 **技能版本**: v1.0 | **最后更新**: 2026-06 | **适用 Keil**: MDK-ARM v5.43a
> 🎯 兼容: Claude Code · Reasonix Code · Codex · Cursor · Windsurf · Continue
