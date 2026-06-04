---
name: quartus
description: Intel Quartus II/Prime FPGA 开发全能技能 — 下载安装→项目创建→Verilog/VHDL→综合适配→时序分析→SignalTap→烧录，兼容 Reasonix/Claude Code/Codex/Cursor
run_as: inline
---

# Intel Quartus II / Quartus Prime FPGA 开发全能技能

> **Quartus II 13.1 ~ Quartus Prime 24.x** — FPGA/CPLD 全流程开发
> 电赛 FPGA 题目必备：Verilog → 综合 → 引脚分配 → 时序约束 → SignalTap 调试 → 烧录

---

## 📦 一、下载与安装

### 1.1 版本选择

| 版本 | FPGA 支持 | 大小 | 电赛适用 |
|------|-----------|:----:|:--------:|
| **Quartus II 13.1 SP1** | Cyclone IV / MAX II/V | ~6 GB | ⭐ 最常用（轻量） |
| **Quartus II 18.1** | Cyclone V / MAX 10 | ~15 GB | 中等 |
| **Quartus Prime Lite 24.x** | Cyclone 10 LP / MAX 10 | ~20 GB | 新器件 |
| Quartus Prime Pro | Agilex / Stratix 10 | ~50 GB | 高级（电赛不需要） |

> **电赛推荐**: Quartus II 13.1 SP1 — 支持 Cyclone IV EP4CE6/EP4CE10/EP4CE15，体积小，兼容主流开发板。

### 1.2 下载

```
官方下载 (需注册 Intel 账号):
https://www.intel.com/content/www/us/en/software-kit/711791/intel-quartus-ii-web-edition-design-software-version-13-1-for-windows.html

选择:
  QuartusSetupWeb-13.1.0.162.exe          (~1.7 GB — 主程序)
  cyclone-13.1.0.162.qdz                  (~600 MB — Cyclone IV 器件库)
  cyclonev-13.1.0.162.qdz                 (~1.5 GB — Cyclone V 器件库)

备用: 百度网盘搜索 "Quartus II 13.1 下载"
```

### 1.3 安装步骤

```
注意: 安装路径不能有中文、空格、特殊符号！
推荐: C:\intelFPGA\13.1\

1. 以管理员身份运行 QuartusSetupWeb-13.1.0.162.exe
2. Next → I accept the agreement
3. 安装路径: C:\intelFPGA\13.1
4. 组件选择: ☑ Quartus II + ☑ ModelSim-Altera Starter
5. 等待安装完成 (15-30 分钟)
6. 安装器件库:
   双击 cyclone-13.1.0.162.qdz
   或: 工具 → Install Devices → 选择 .qdz 文件
7. ✔ 完成
```

### 1.4 USB-Blaster 驱动安装

```
插入 USB-Blaster 下载器:
1. 打开设备管理器 → 其他设备 → USB-Blaster (有黄色感叹号)
2. 右键 → 更新驱动 → 浏览我的电脑
3. 路径: C:\intelFPGA\13.1\quartus\drivers\usb-blaster
4. 安装 → 确认
5. 验证: 设备管理器显示 "Altera USB-Blaster" 且无感叹号
```

### 1.5 验证安装

```batch
:: 检查版本
"C:\intelFPGA\13.1\quartus\bin64\quartus_sh.exe" --version

:: 列出已安装器件
"C:\intelFPGA\13.1\quartus\bin64\quartus_sh.exe" --list-devices

:: 查看帮助
"C:\intelFPGA\13.1\quartus\bin64\quartus_sh.exe" --help
```

---

## 🛠 二、CLI 命令速查表

### 2.1 核心命令行工具

| 工具 | 功能 | 对应 GUI 操作 |
|------|------|-------------|
| `quartus_map` | 分析与综合 (Analysis & Synthesis) | Processing → Start → Analysis & Synthesis |
| `quartus_fit` | 适配/布局布线 (Fitter) | Processing → Start → Fitter |
| `quartus_asm` | 生成烧录文件 (Assembler) | Processing → Start → Assembler |
| `quartus_sta` | 静态时序分析 (TimeQuest) | Processing → Start → TimeQuest |
| `quartus_pow` | 功耗分析 (PowerPlay) | Processing → Start → PowerPlay |
| `quartus_cdb` | 生成调试数据库 | 自动 |
| `quartus_sh` | Quartus Shell (脚本入口) | — |
| `quartus_cpf` | 文件格式转换 | File → Convert Programming Files |
| `quartus_pgm` | 烧录/编程 | Tools → Programmer |

### 2.2 一键编译命令

```batch
:: 完整编译流程 (Analysis → Fitter → Assembler → STA)
quartus_sh --flow compile project_name

:: 等效于分步执行:
quartus_map   project_name   :: 分析与综合
quartus_fit   project_name   :: 适配/布局布线
quartus_asm   project_name   :: 生成 .sof / .pof
quartus_sta   project_name   :: 时序分析
quartus_eda   project_name   :: EDA 网表导出
```

### 2.3 项目操作

| 命令 | 说明 |
|------|------|
| `quartus_sh -t create_project.tcl` | 通过 Tcl 脚本创建项目 |
| `quartus_sh --flow compile proj` | 编译项目 |
| `quartus_sh --clean proj` | 清理编译中间文件 |
| `quartus_sh --archive proj` | 打包项目为 .qar |
| `quartus_sh --restore proj.qar` | 恢复打包项目 |
| `quartus_cpf -c output.sof output.jic` | .sof → .jic (Flash烧录) |

### 2.4 引脚分配

```batch
:: 从 CSV 导入引脚
quartus_sh -t import_pins.tcl project_name

:: 导出引脚到 CSV
quartus_sh -t export_pins.tcl project_name
```

### 2.5 时序分析

```batch
:: 生成时序报告
quartus_sta project_name --mode=report

:: 导出时序网表 (供第三方工具)
quartus_sta project_name --export_timing_sdc

:: 显示时序违例路径
quartus_sta project_name --report_timing
```

---

## 📝 三、项目创建与管理

### 3.1 Tcl 脚本创建项目（自动化）

```tcl
# create_project.tcl — 自动创建 Quartus 项目
# 用法: quartus_sh -t create_project.tcl

set project_name "led_blink"
set project_dir  "./$project_name"
set top_entity   "led_blink"
set device_family "Cyclone IV E"
set device_part   "EP4CE6E22C8"

# 创建项目
project_new $project_name -overwrite

# 设置器件
set_global_assignment -name FAMILY "$device_family"
set_global_assignment -name DEVICE $device_part

# 添加设计文件
set_global_assignment -name VERILOG_FILE "$project_dir/src/led_blink.v"
set_global_assignment -name VERILOG_FILE "$project_dir/src/pll.v"
set_global_assignment -name VERILOG_FILE "$project_dir/src/uart.v"

# 添加 SDC 约束文件
set_global_assignment -name SDC_FILE "$project_dir/constraints/timing.sdc"

# 引脚分配
set_location_assignment PIN_E1 -to clk_50m    ;# 50MHz 晶振
set_location_assignment PIN_M2 -to rst_n       ;# 复位按键
set_location_assignment PIN_T12 -to led[0]     ;# LED0
set_location_assignment PIN_T11 -to led[1]     ;# LED1
set_location_assignment PIN_N14 -to led[2]     ;# LED2
set_location_assignment PIN_N11 -to led[3]     ;# LED3

# I/O 标准
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to clk_50m
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to rst_n
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to led[*]

# 综合选项
set_global_assignment -name OPTIMIZATION_MODE "Performance"
set_global_assignment -name AUTO_RESOURCE_SHARING ON

# 适配选项
set_global_assignment -name FITTER_EFFORT "Standard Fit"
set_global_assignment -name ROUTER_TIMING_OPTIMIZATION_LEVEL "Maximum"

# 保存并关闭
project_close
```

### 3.2 常见电赛 FPGA 器件

| 器件 | 逻辑单元(LE) | RAM | PLL | 乘法器 | 封装 | 常用开发板 |
|------|:----------:|:---:|:---:|:-----:|------|-----------|
| **EP4CE6E22C8** | 6,272 | 270Kb | 2 | 15 | QFP144 | 黑金 AX301 / 小梅哥 AC620 |
| **EP4CE10E22C8** | 10,320 | 414Kb | 2 | 23 | QFP144 | 芯航线 / 正点原子 |
| **EP4CE15F23C8** | 15,408 | 504Kb | 4 | 56 | FBGA484 | DE0-Nano |
| **EP4CE22F17C8** | 22,320 | 594Kb | 4 | 66 | FBGA256 | DE2-115 |
| **10M08SAE144C8G** | 8,064 | 387Kb | 2 | 24 | EQFP144 | MAX10 小系统 |

### 3.3 引脚分配规则

```
┌────────────────────────────────────────────────┐
│  引脚分配原则 (电赛 FPGA 项目)                   │
│                                                 │
│  1. 时钟引脚: 只能接专用时钟输入脚 (CLK[x])      │
│     EP4CE6: CLK0=Pin_E1, CLK1=Pin_M1, ...      │
│                                                 │
│  2. PLL 时钟: 必须接到专用时钟输入脚             │
│                                                 │
│  3. JTAG: TMS/TDI/TDO/TCK 是固定引脚，不能改     │
│     EP4CE6: TMS=H7, TDI=G7, TDO=G8, TCK=H8    │
│                                                 │
│  4. 差分信号: 必须用差分对引脚 (DIFFIO_x)        │
│                                                 │
│  5. 高速信号: 优先分配到靠近 PLL 的引脚          │
│                                                 │
│  6. 电源引脚: VCCIO=3.3V/2.5V/1.8V/1.2V        │
│     每个 Bank 独立供电，注意电平匹配             │
│                                                 │
│  7. 未用引脚: 设置为 "As input tri-stated"      │
│     Assignments → Device → Unused Pins          │
└────────────────────────────────────────────────┘
```

---

## 🔤 四、Verilog/VHDL 模板

### 4.1 Verilog 基础模板

```verilog
// =================================================
//  led_blink.v — FPGA 入门：LED 闪烁
//  器件: EP4CE6E22C8  |  时钟: 50MHz
// =================================================
module led_blink (
    input  wire       clk_50m,    // 50MHz 时钟
    input  wire       rst_n,      // 异步复位，低有效
    output reg  [3:0] led         // 4路 LED 输出
);

    // 分频计数器 (50MHz → 1Hz)
    reg [25:0] cnt;
    
    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n)
            cnt <= 26'd0;
        else if (cnt == 26'd49_999_999)
            cnt <= 26'd0;
        else
            cnt <= cnt + 1'b1;
    end
    
    // LED 闪烁
    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n)
            led <= 4'b0000;
        else if (cnt == 26'd0)
            led <= led + 1'b1;   // 每秒切换
    end

endmodule
```

### 4.2 PLL 锁相环模板

```verilog
// =================================================
//  PLL 生成多路时钟: 50MHz → 100MHz / 25MHz / 10MHz
// =================================================
module pll_top (
    input  wire clk_50m,
    input  wire rst_n,
    output wire clk_100m,
    output wire clk_25m,
    output wire clk_10m,
    output wire pll_locked
);

    // MegaWizard 生成的 PLL 模块
    pll_quad u_pll (
        .areset   (~rst_n),
        .inclk0   (clk_50m),
        .c0       (clk_100m),    // ×2
        .c1       (clk_25m),     // ÷2
        .c2       (clk_10m),     // ÷5
        .locked   (pll_locked)
    );

endmodule
```

> **PLL 配置**: Tools → MegaWizard Plug-In Manager → I/O → ALTPLL

### 4.3 UART 收发模板

```verilog
// =================================================
//  uart_tx.v — UART 发送模块 (9600bps / 50MHz)
// =================================================
module uart_tx (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] tx_data,
    input  wire       tx_start,
    output reg        tx,
    output reg        tx_busy
);

    // 波特率分频: 50MHz / 9600 ≈ 5208
    localparam BAUD_DIV = 5208;
    
    reg [12:0] baud_cnt;
    reg [3:0]  bit_cnt;
    reg [9:0]  shift_reg;  // {stop, data[7:0], start}
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx <= 1'b1;
            tx_busy <= 1'b0;
            baud_cnt <= 13'd0;
            bit_cnt <= 4'd0;
        end
        else if (tx_busy) begin
            if (baud_cnt == BAUD_DIV - 1) begin
                baud_cnt <= 13'd0;
                tx <= shift_reg[0];
                shift_reg <= {1'b1, shift_reg[9:1]};
                if (bit_cnt == 4'd9) begin
                    tx_busy <= 1'b0;
                    bit_cnt <= 4'd0;
                end else
                    bit_cnt <= bit_cnt + 1'b1;
            end else
                baud_cnt <= baud_cnt + 1'b1;
        end
        else if (tx_start) begin
            shift_reg <= {1'b1, tx_data, 1'b0};  // stop + data + start
            tx_busy <= 1'b1;
            baud_cnt <= 13'd0;
        end
    end

endmodule
```

### 4.4 PWM 生成模板

```verilog
// =================================================
//  pwm_gen.v — PWM 波形生成 (精度 8-bit)
// =================================================
module pwm_gen (
    input  wire       clk,        // 50MHz
    input  wire       rst_n,
    input  wire [7:0] duty,       // 占空比 0-255
    output reg        pwm_out
);

    reg [7:0] cnt;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 8'd0;
        else
            cnt <= cnt + 1'b1;
    end
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pwm_out <= 1'b0;
        else
            pwm_out <= (cnt < duty);
    end

endmodule
// PWM 频率 = 50MHz / 256 ≈ 195kHz
```

### 4.5 SPI 驱动 OLED 模板

```verilog
// =================================================
//  spi_oled.v — SPI 驱动 0.96" OLED (SSD1306)
//  时钟: 4MHz
// =================================================
module spi_oled (
    input  wire       clk,
    input  wire       rst_n,
    output reg        oled_scl,   // SPI Clock
    output reg        oled_sda,   // SPI Data (MOSI)
    output reg        oled_rst,   // OLED Reset
    output reg        oled_dc,    // Data/Command
    input  wire       start,
    output reg        done
);

    // SPI 状态机 + OLED 初始化序列
    // ... (完整代码省略，见 nuedc 代码模板)

endmodule
```

---

## ⏱️ 五、时序约束 (SDC)

### 5.1 基础 SDC 文件

```tcl
# timing.sdc — 时序约束文件
# EP4CE6E22C8, 50MHz 基准时钟

# ===== 创建时钟约束 =====
create_clock -name clk_50m -period 20.000 [get_ports {clk_50m}]

# PLL 生成时钟
derive_pll_clocks
derive_clock_uncertainty

# ===== 输入延迟约束 =====
# 假设外部芯片 tco_max=5ns, tco_min=1.5ns, 走线延迟=1ns
set_input_delay -clock clk_50m -max 6.0 [get_ports {rx}]
set_input_delay -clock clk_50m -min 2.5 [get_ports {rx}]

# ===== 输出延迟约束 =====
set_output_delay -clock clk_50m -max 4.0 [get_ports {tx}]
set_output_delay -clock clk_50m -min 1.0 [get_ports {tx}]

# ===== 异步信号 (false path) =====
set_false_path -from [get_ports {rst_n}]

# ===== 多周期路径 =====
# (如果跨越多个时钟域)
# set_multicycle_path -setup 2 -from [get_clocks {clk_a}] -to [get_clocks {clk_b}]
```

### 5.2 时序报告解读

```
时序分析报告关键指标:
┌──────────────────────────────────────────────────────┐
│  Fmax (最大运行频率):         120.5 MHz ✅ (>50MHz)   │
│  Setup Slack (最小建立时间余量): +8.2 ns   ✅ (>0ns)  │
│  Hold Slack (最小保持时间余量):  +0.3 ns   ✅ (>0ns)  │
│  Recovery Slack (复位恢复):     +12.1 ns  ✅         │
│  Removal Slack (复位撤离):      +2.5 ns   ✅         │
└──────────────────────────────────────────────────────┘

⚠️ 如果 Slack < 0 (红色): 时序违例！需优化设计或降频。
```

---

## 🔍 六、SignalTap II 逻辑分析仪

### 6.1 创建 SignalTap 调试

```tcl
# signalTap_setup.tcl — 自动化 SignalTap 配置
# 用法: quartus_stp -t signalTap_setup.tcl

# 创建 SignalTap 文件
create_stp_file -name "debug"

# 添加时钟
add_stp_clock -name "clk_50m" -period 20ns

# 添加观测信号
add_stp_signal -name "led"        -width 4 -trigger_basic "Rising Edge"
add_stp_signal -name "cnt[25:0]"  -width 26
add_stp_signal -name "pwm_out"    -width 1
add_stp_signal -name "tx"         -width 1
add_stp_signal -name "rx"         -width 1

# 设置采样深度
set_stp_sample_depth 4096

# 设置触发条件
add_stp_trigger -name "led[0]" -pattern "1"  # LED[0] 上升沿触发

# 保存
save_stp_file -name "debug.stp"
```

### 6.2 SignalTap 操作流程

```
操作步骤:
1. 在项目中创建 SignalTap II Logic Analyzer File (.stp)
2. 添加观测信号 (拖拽或右键 → Add Nodes)
3. 设置采样时钟和深度
4. 设置触发条件
5. 保存 .stp 文件
6. 重新编译 (Processing → Start Compilation)
7. 连接 USB-Blaster
8. 下载 .sof 文件 (带 SignalTap 调试信息)
9. 点击 "Run Analysis" 开始采集
10. 查看波形，验证设计
```

---

## 🔥 七、烧录/编程

### 7.1 JTAG 方式 (.sof)

```batch
:: JTAG 烧录 SRAM (掉电丢失，调试用)
quartus_pgm -c "USB-Blaster" -m JTAG -o "p;output.sof"

:: 或通过 Tcl:
quartus_pgm -t program.tcl
```

```tcl
# program.tcl
set cable_name "USB-Blaster"
set device @1
set sof_file  "output.sof"
programmer -c $cable_name -m jtag -o "p;$sof_file"
```

### 7.2 AS 方式 (.pof / .jic)

```batch
:: 第一步: .sof → .jic (需配合 EPCS Flash)
quartus_cpf -c -d EPCS16 -s EP4CE6 output.sof output.jic

:: 第二步: 烧录 .jic 到 EPCS Flash
quartus_pgm -c "USB-Blaster" -m JTAG -o "p;output.jic"
```

### 7.3 通过 OpenOCD

```bash
# OpenOCD 烧录 Cyclone IV
openocd -f interface/altera-usb-blaster.cfg \
        -f board/altera_cycloneiv.cfg \
        -c "init; svf output.svf; exit"
```

---

## 🧰 八、电赛 FPGA 应用场景

### 8.1 高速数据采集 (ADC + FPGA)

```
场景: 示波器/频谱分析仪/失真度测量
架构: AD9280 (8-bit 32MSPS) → FPGA → FIFO → UART/USB

FPGA 核心模块:
┌─────────────────────────────────────┐
│  clk_50m                            │
│    │                                 │
│    ├── PLL ── clk_adc (32MHz)      │
│    │                                 │
│    ├── adc_ctrl (AD9280 时序)      │
│    │     └── data[7:0]              │
│    │                                 │
│    ├── fifo (8×1024)               │
│    │     └── buffer[7:0]            │
│    │                                 │
│    ├── fft_core (256点 FFT)        │
│    │     └── spectrum[15:0]         │
│    │                                 │
│    └── uart_tx (串口上传)          │
│          └── TX → 上位机             │
└─────────────────────────────────────┘
```

### 8.2 DDS 信号发生器

```verilog
// =================================================
//  dds_core.v — DDS 正弦波发生器 (频率可调)
// =================================================
module dds_core (
    input  wire        clk,        // 100MHz
    input  wire        rst_n,
    input  wire [31:0] freq_word,  // 频率控制字
    output reg  [7:0]  dac_out     // 8-bit DAC 输出
);

    reg [31:0] phase_acc;
    
    // 相位累加器
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            phase_acc <= 32'd0;
        else
            phase_acc <= phase_acc + freq_word;
    end
    
    // 相位 → 正弦波 (查表简化为计算)
    // fout = freq_word × fclk / 2^32
    
    // 正弦查找表 (256点 × 8-bit)
    wire [7:0] addr = phase_acc[31:24];
    // ... ROM 查找表省略，用 IP 核替代
    
endmodule
// 例: fclk=100MHz, freq_word=42949673 → fout≈1MHz
```

### 8.3 电机控制 (PWM 编码器)

```
场景: 智能小车/无人机电调
架构: 正交编码器 → FPGA 解码 → PID 控制 → 6路 PWM

FPGA 模块:
  encoder_decode.v  — 正交编码器 A/B 相 → 速度+方向
  pid_controller.v  — PID 控制算法
  pwm_6ch.v         — 6路互补 PWM 输出 (带死区)
  hall_sensor.v     — 霍尔传感器换相逻辑
```

---

## 🔧 九、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| JTAG 找不到器件 | USB-Blaster 驱动未装 | 设备管理器更新驱动 |
| "Can't find design entity" | 顶层模块名与项目名不一致 | 确保 top-level entity 与文件名一致 |
| 综合后逻辑单元超出 | 设计太大 | 优化代码/换大器件 |
| 时序违例 (红色) | 关键路径延迟太大 | 插入流水线/降频/优化布局 |
| SignalTap 无波形 | 触发条件没满足 | 改用 Always Trigger 先验证 |
| .jic 烧录失败 | EPCS Flash ID 不匹配 | 检查 quartus_cpf 的 -d 参数 |
| PLL 不锁定 | 输入时钟频率不对 | 检查 inclk0 频率与 PLL 设置 |

---

## 📌 技能信息

- **版本**: v1.0
- **适用**: Quartus II 13.1 SP1 ~ Quartus Prime 24.x
- **电赛 FPGA 题目**: 信号采集 / DDS 发生器 / 电机控制 / 数字滤波器
- **配合**: `nuedc` 技能 (赛题拆解) + `modelsim` 技能 (HDL 仿真)

---

> **用法**: 告诉 agent "用 Quartus 创建一个 Cyclone IV 的 LED 闪烁项目，50MHz 时钟，4 个 LED 依次点亮"，agent 会：
> 1. 生成完整 Verilog 代码
> 2. 生成 Tcl 脚本 (创建项目 + 引脚分配 + 编译)
> 3. 设置时序约束
> 4. 生成 SignalTap 调试配置
> 5. 指导烧录步骤
