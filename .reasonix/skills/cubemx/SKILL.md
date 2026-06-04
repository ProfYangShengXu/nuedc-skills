---
name: cubemx
description: STM32CubeMX/CubeMX2 MCU 配置与代码生成技能 — 引脚分配→时钟树→外设配置→生成 Keil/Makefile/GCC 工程，含 CLI 自动化，电赛 STM32 开发首选，兼容 Reasonix/Claude Code/Codex/Cursor
run_as: inline
---

# STM32CubeMX MCU 配置与代码生成全能技能

> **STM32CubeMX 6.x** — ST 官方图形化 MCU 配置工具，电赛 STM32 项目起点
> 选型 → 引脚分配 → 时钟树 → 外设 → 中间件 → 一键生成 Keil / Makefile / STM32CubeIDE 工程

---

## 📦 一、下载与安装

### 1.1 下载

| 来源 | 地址 |
|------|------|
| ST 官网 | `https://www.st.com/en/development-tools/stm32cubemx.html` |
| ST 中文 | `https://www.st.com.cn/zh/development-tools/stm32cubemx.html` |

> ⚠️ ST 官网下载需要注册 ST 账号（免费）。点击 "Get Software" → 登录 → 下载。

**备用下载**（无需登录，各版本独立链接）：
```
# STM32CubeMX 6.13.0 (约 450MB)
https://www.st.com/content/st_com/en/products/development-tools/software-development-tools/stm32-software-development-tools/stm32-configurators-and-code-generators/stm32cubemx.html#get-software
```

### 1.2 安装步骤

```
1. 运行 SetupSTM32CubeMX-6.x.x.exe
2. Next → Accept License
3. 选择安装路径 (默认 C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeMX\)
4. 勾选:
   ☑ STM32CubeMX            — 主程序
   ☑ STM32Cube MCU Packages — MCU 支持包（按需选）
   ☐ STM32CubeIDE            — 如果已有 Keil 则不需要
5. 等待安装 (5-10 分钟)
6. ✔ 完成
```

### 1.3 验证安装

```batch
:: CubeMX2 CLI 版本
D:\cubemx\.bin\cube.exe --version
:: → cube wrapper version: 0.10.2

:: 启动 CubeMX2 GUI
D:\cubemx\.bin\cube.exe mx start

:: 查看所有命令
D:\cubemx\.bin\cube.exe --help
D:\cubemx\.bin\cube.exe mx --help
```

### 1.4 安装 MCU 包

```batch
:: STM32CubeMX 首次启动会自动提示安装 MCU Pack
:: 也可手动下载: https://www.st.com/en/embedded-software/stm32cube-mcu-packages.html

:: 电赛常用 MCU 包:
::  - STM32F1  (F103C8T6/C8T6/RCT6)
::  - STM32F4  (F407VGT6/F411CEU6)
::  - STM32G0  (G030F6P6/G071RBT6)
::  - STM32H7  (H743VIT6/H750VBT6)
```

---

## 🛠 二、CLI 命令与自动化

### 2.1 启动 CubeMX2

```batch
:: 启动 CubeMX2 (GUI + Backend Server)
D:\cubemx\.bin\cube.exe mx start

:: 启动时自动打开项目
D:\cubemx\.bin\cube.exe mx start D:\projects\nuedc_test\nuedc_test.ioc

:: 指定端口启动（CLI 需要连这个端口）
D:\cubemx\.bin\cube.exe mx start --port 5123
```

### 2.2 CLI 命令速查（CubeMX2）

```batch
:: 通用格式: cube mx <command> [options]

:: 项目管理
cube mx project create-from-mcu --cpn STM32F103C8Tx --project-location . --project-name my_project --port 5123
cube mx project save     --port 5123
cube mx project close    --port 5123

:: 查看支持的 MCU
cube mx finder device list   --port 5123
cube mx finder device info STM32F103C8Tx  --port 5123

:: 代码生成
cube mx ide-project list-toolchain   --port 5123
cube mx ide-project list-format      --port 5123
cube mx ide-project set-format --format "MDK-ARM V5" --port 5123
cube mx ide-project generate         --port 5123

:: 引脚/时钟/外设配置（CLI）
cube mx pinout       --port 5123
cube mx clock        --port 5123
cube mx peripherals  --port 5123
cube mx nvic         --port 5123
cube mx dma          --port 5123
```

### 2.3 命令行一键生成代码

```batch
:: one_click_gen.bat — 启动 CubeMX2 + 创建项目 + 生成 Keil 工程
@echo off
set CUBE=D:\cubemx\.bin\cube.exe
set PORT=5123

echo [1/4] Starting CubeMX backend...
start "CubeMX" %CUBE% mx start --port %PORT%
timeout /t 5 >nul

echo [2/4] Creating project for STM32F103C8T6...
%CUBE% mx project create-from-mcu --cpn STM32F103C8Tx --project-location D:\projects --project-name nuedc_test --port %PORT%

echo [3/4] Setting toolchain to MDK-ARM V5...
%CUBE% mx ide-project set-format --format "MDK-ARM V5" --port %PORT%

echo [4/4] Generating code...
%CUBE% mx ide-project generate --port %PORT%

echo Done! Project at D:\projects\nuedc_test\
```

### 2.4 Python 脚本修改 .ioc2 文件

CubeMX2 的 `.ioc2` 文件是 JSON 格式，可以用脚本批量修改配置：

```python
"""modify_ioc.py — 批量修改 CubeMX 项目配置"""
import json

# 读取 .ioc 文件
with open("nuedc_test.ioc", "r", encoding="utf-8") as f:
    ioc = json.load(f)

# 修改时钟配置: HSE=8MHz, SYSCLK=72MHz
ioc["Clock"] = {
    "HSE": "8MHz",
    "SYSCLK": "72MHz",
    "AHB": "72MHz",
    "APB1": "36MHz",
    "APB2": "72MHz"
}

# 修改外设配置
ioc["Peripherals"]["USART1"] = {
    "Mode": "Asynchronous",
    "BaudRate": 115200,
    "WordLength": "8",
    "Parity": "None",
    "StopBits": "1"
}

# 保存
with open("nuedc_test_modified.ioc", "w", encoding="utf-8") as f:
    json.dump(ioc, f, indent=2)

print("[OK] .ioc modified")
```

---

## 📐 三、CubeMX 配置速查

### 3.1 Pinout 引脚分配

```
CubeMX 引脚配置界面:
  Pinout View → 右键引脚 → 选择功能

电赛常用引脚功能速查:
┌────────────────┬─────────────────────────────────┐
│ 功能           │ STM32F103C8T6 常用引脚          │
├────────────────┼─────────────────────────────────┤
│ SWD (调试)     │ PA13(SWDIO), PA14(SWCLK)         │
│ USART1 (串口)  │ PA9(TX), PA10(RX)               │
│ I2C1 (OLED)    │ PB6(SCL), PB7(SDA)              │
│ SPI1 (传感器)  │ PA5(SCK), PA6(MISO), PA7(MOSI)  │
│ TIM2 CH1 (PWM) │ PA0                              │
│ TIM2 CH2 (PWM) │ PA1                              │
│ TIM2 CH3 (PWM) │ PA2                              │
│ TIM2 CH4 (PWM) │ PA3                              │
│ ADC1 IN0       │ PA0                              │
│ ADC1 IN1       │ PA1                              │
│ GPIO Output    │ PB0, PB1, PC13 (LED)             │
│ GPIO Input     │ PA4, PA5, PA6 (按键)             │
└────────────────┴─────────────────────────────────┘
```

### 3.2 时钟树配置

```
STM32F103 典型时钟树 (72MHz):
  HSE (外部晶振 8MHz)
   → PLL ×9
      → SYSCLK = 72MHz
         ├→ AHB = 72MHz
         ├→ APB1 = 36MHz (最大)
         └→ APB2 = 72MHz

CubeMX 操作:
  Clock Configuration → HSE: Crystal/Ceramic Resonator
                      → PLL Source Mux: HSE
                      → PLL Mul: ×9
                      → System Clock Mux: PLLCLK
                      → APB1 Prescaler: /2
```

### 3.3 外设配置

| 外设 | 配置路径 | 常用参数 |
|------|----------|----------|
| **GPIO** | System Core → GPIO | Output PP, No Pull, High Speed |
| **USART** | Connectivity → USART1 | 115200-8-N-1, Async |
| **I2C** | Connectivity → I2C1 | 100kHz/400kHz, 7-bit |
| **SPI** | Connectivity → SPI1 | Full-Duplex Master, 8-bit, MSB |
| **TIM (PWM)** | Timers → TIM2 | CH1 PWM Gen, 20kHz, 50% duty |
| **ADC** | Analog → ADC1 | IN0 Single-ended, 12-bit, Scan |
| **DMA** | System Core → DMA | Memory→Peripheral, Circular |
| **NVIC** | System Core → NVIC | 中断优先级分组 4-bit |
| **RCC** | System Core → RCC | HSE Crystal, LSE Disable |
| **SYS** | System Core → SYS | Debug: Serial Wire |

### 3.4 项目设置

```
Project Manager → Project:
  Project Name:     nuedc_2025_test
  Project Location: D:\projects\
  Toolchain:        MDK-ARM V5 (Keil)
  ☑ Generate Under Root

Project Manager → Code Generator:
  ☑ Copy only the necessary library files
  ☑ Generate peripheral initialization as a pair of '.c/.h'
  ☑ Set all free pins as analog (low power)
  ☑ Enable Full Assert

Project Manager → Advanced Settings:
  Driver Selector:
    GPIO  → HAL
    USART → HAL
    TIM   → HAL
    ADC   → HAL
```

---

## 📝 四、电赛实战 — 从 .ioc 到 Keil 工程

### 4.1 新建 CubeMX 项目

```
1. File → New Project → 选择 MCU: STM32F103C8T6
2. Pinout & Configuration:
   - RCC: HSE = Crystal
   - SYS: Debug = Serial Wire
   - USART1: Mode = Asynchronous
   - TIM2: CH1 = PWM Generation CH1
   - GPIO: PB0 = Output (LED)
   - ADC1: IN0 = Single-ended
3. Clock Configuration:
   - 8MHz HSE → ×9 PLL → 72MHz SYSCLK
4. Project Manager:
   - Toolchain: MDK-ARM V5
   - ☑ Generate peripheral initialization .c/.h
5. GENERATE CODE
```

### 4.2 生成后的 Keil 项目结构

```
nuedc_test/
├── nuedc_test.ioc              ← CubeMX 配置文件
├── Drivers/
│   ├── CMSIS/                  ← ARM CMSIS 内核文件
│   └── STM32F1xx_HAL_Driver/   ← HAL 库驱动
├── Inc/
│   ├── main.h
│   ├── gpio.h
│   ├── usart.h
│   ├── tim.h
│   ├── adc.h
│   └── stm32f1xx_it.h
├── Src/
│   ├── main.c                  ← 主程序 (在 USER CODE 区写业务逻辑)
│   ├── gpio.c
│   ├── usart.c
│   ├── tim.c
│   ├── adc.c
│   └── stm32f1xx_it.c
├── MDK-ARM/
│   └── nuedc_test.uvprojx      ← Keil 工程文件
└── .mxproject                  ← CubeMX 项目元数据
```

### 4.3 main.c 中的用户代码区

CubeMX 用 `USER CODE BEGIN` / `USER CODE END` 注释保护用户代码，重新生成时不覆盖：

```c
/* USER CODE BEGIN Includes */
#include "oled.h"
#include "pid.h"
/* USER CODE END Includes */

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_TIM2_Init();
  MX_ADC1_Init();

  /* USER CODE BEGIN 2 */
  OLED_Init();
  PID_Init(&pid, 1.0, 0.1, 0.05);
  HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);
  /* USER CODE END 2 */

  while (1)
  {
    /* USER CODE BEGIN 3 */
    uint16_t adc_val = ADC_Read();
    float duty = PID_Compute(&pid, target, adc_val);
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, duty);
    OLED_ShowFloat(0, 0, adc_val);
    HAL_Delay(10);
    /* USER CODE END 3 */
  }
}
```

### 4.4 修改配置后重新生成

```
1. 修改 .ioc (添加外设、改引脚)
2. GENERATE CODE
3. 在弹出的对话框中选择:
   ☑ Re-generate all files
   ☐ Delete previously generated files when not re-generated
4. OK → CubeMX 保留所有 USER CODE 区的代码 ✅
```

---

## 🔄 五、与电赛工具链集成

### 5.1 CubeMX → Keil 全流程

```
CubeMX 配引脚/时钟/外设
     ↓ GENERATE CODE
Keil 工程 (.uvprojx)
     ↓ 在 USER CODE 区写业务逻辑
     ↓ UV4.exe -b project.uvprojx
     ↓ JLink/ST-Link 烧录
目标板运行
```

### 5.2 命令行一键流水线

```batch
:: one_click.bat — 一键生成+编译
@echo off
set CUBEMX="C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeMX\STM32CubeMX.exe"

:: Step 1: CubeMX 生成代码
echo [1/2] Generating code from CubeMX...
%CUBEMX% -s generate.cmxs

:: Step 2: Keil 编译
echo [2/2] Building with Keil...
"C:\Keil_v5\UV4\UV4.exe" -b output\nuedc_test.uvprojx -j0 -o build.log

echo Done!
```

### 5.3 配合 nuedc 技能

```
赛题 → nuedc 技能 拆解 → 确定 MCU 型号 + 外设清单
     → cubemx 技能  生成 .ioc + 初始化代码
     → keil5 技能   写业务逻辑 + 编译 + 烧录
     → ltspice 技能 仿真外围模拟电路
     → kicad 技能   画 PCB
```

---

## 🧰 六、常见问题

| 问题 | 解决 |
|------|------|
| CubeMX 打不开 | 需要 Java JRE 8+ (STM32CubeMX 6.x 自带 JRE，不需要单独装) |
| 没有想要的 MCU | Help → Manage embedded software packages → 安装对应 MCU Pack |
| 生成代码后 Keil 编译报错 | 检查 Toolchain 是否选对 (MDK-ARM V5 vs V5.32) |
| USER CODE 区代码被覆盖 | 确认代码放在 `USER CODE BEGIN/END` 之间 |
| HAL 库版本不对 | Project Manager → Firmware Package → 选择版本 |
| 时钟配置报红 | HSE 频率要与实际晶振一致，APB1 不能超 36MHz (F1) |
| 生成 Makefile 项目 | Toolchain 选 Makefile，适合 GCC/ARM 工具链 |

---

## 📌 技能信息

- **版本**: v2.0 — 适配 CubeMX2 (CLI + GUI)
- **安装路径**: `D:\cubemx\.bin\cube.exe`
- **CLI 版本**: cube wrapper 0.10.2 / STM32CubeMX2 1.0.1
- **下载**: `https://www.st.com/en/development-tools/stm32cubemx.html`
- **配合技能**: `keil5` / `nuedc` / `ltspice` / `kicad`
- **电赛场景**: 全部 STM32 赛题

---

> **用法**: 告诉 agent "用 CubeMX 配一个 STM32F103C8T6 项目，要 USART1+ADC1+PWM+GPIO"，agent 会：
> 1. 给出精确的引脚分配表
> 2. 画出时钟树配置
> 3. 生成 .ioc 文件内容（JSON）
> 4. 指导 CubeMX GUI 操作步骤
> 5. 生成 main.c 用户代码模板
