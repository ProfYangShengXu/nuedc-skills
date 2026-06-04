---
name: modelsim
description: ModelSim/QuestaSim HDL 仿真技能 — Verilog/VHDL 编译→波形查看→代码覆盖率→时序仿真，与 Quartus 配套，兼容 Reasonix/Claude Code/Codex/Cursor
run_as: inline
---

# ModelSim / QuestaSim HDL 仿真全能技能

> **ModelSim SE/DE / QuestaSim / ModelSim-Altera** — FPGA 开发的"逻辑万用表"
> 写 Verilog/VHDL → 仿真验证 → 波形分析 → 代码覆盖率 → 门级时序仿真

---

## 📦 一、版本与安装

### 1.1 版本对照

| 版本 | 来源 | 限制 | 推荐场景 |
|------|------|------|----------|
| **ModelSim-Altera Starter** | Quartus 自带 | 免费，性能有限 (10K行RTL) | 电赛首选 ✅ |
| **ModelSim PE** | Siemens | 付费，性能中等 | 中小项目 |
| **ModelSim DE** | Siemens | 付费，高性能 | 大型项目 |
| **QuestaSim** | Siemens | 付费，支持 UVM/SystemVerilog | 专业验证 |

> **电赛推荐**: ModelSim-Altera Starter Edition (随 Quartus II 安装)，免费且够用。

### 1.2 独立安装 ModelSim

```
下载 (ModelSim PE Student Edition — 免费):
https://www.siemens.com/eda/modelsim-student

安装步骤:
1. 运行 setup.exe → 选择安装路径
2. 选择版本: PE (Personal Edition)
3. 等待安装 (5-10 分钟)
4. 首次运行弹出 License 设置 → 选 "Student Edition"
5. ✔ 完成
```

### 1.3 验证安装

```batch
:: 检查版本
"C:\modeltech64_10.7\win64\vsim.exe" -version

:: 或 ModelSim-Altera
"C:\intelFPGA\13.1\modelsim_ase\win32aloem\vsim.exe" -version

:: GUI 启动
"C:\intelFPGA\13.1\modelsim_ase\win32aloem\vsim.exe" -gui
```

---

## 🛠 二、CLI 命令速查表

### 2.1 核心命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `vlib work` | 创建 work 库 | 每次新项目第一步 |
| `vmap work work` | 映射逻辑库到物理目录 | — |
| `vlog file.v` | 编译 Verilog 文件 | 支持 `*.v` 通配符 |
| `vcom file.vhd` | 编译 VHDL 文件 | 支持 `*.vhd` 通配符 |
| `vsim work.module` | 加载顶层模块仿真 | 进入仿真模式 |
| `vsim -c` | 命令行模式 (无 GUI) | CI/批量使用 |
| `vsim -do script.do` | 加载 DO 脚本运行 | 自动化 |
| `run 10 us` | 运行仿真 10μs | 在仿真模式下执行 |
| `run -all` | 运行直到 $finish | — |
| `quit -sim` | 退出仿真 | 返回命令行 |
| `vcover report` | 覆盖率报告 | 需启用覆盖率 |

### 2.2 一键命令行仿真

```batch
:: test_counter.bat — 完整编译仿真脚本
@echo off
set MODELSIM=C:\intelFPGA\13.1\modelsim_ase\win32aloem

:: 1. 创建库
if exist work rmdir /s /q work
%MODELSIM%\vlib.exe work
%MODELSIM%\vmap.exe work work

:: 2. 编译源文件
%MODELSIM%\vlog.exe +acc -work work ../src/counter.v
%MODELSIM%\vlog.exe +acc -work work ../tb/tb_counter.v

:: 3. 仿真 (命令行模式)
%MODELSIM%\vsim.exe -c -do "run -all; quit" work.tb_counter

:: 4. 检查结果 (通过 $display 输出)
echo [OK] Simulation complete
```

### 2.3 DO 脚本自动化

```tcl
# sim_counter.do — ModelSim 自动化仿真脚本
# 用法: vsim -do sim_counter.do

# 创建库
vlib work
vmap work work

# 编译 RTL
vlog -sv +acc -work work ../src/counter.v
vlog -sv +acc -work work ../tb/tb_counter.v

# 加载仿真
vsim -voptargs="+acc" work.tb_counter

# 添加波形
add wave -position insertpoint sim:/tb_counter/*
add wave -divider "Counter Internal"
add wave -position insertpoint sim:/tb_counter/uut/*

# 配置波形
configure wave -signalnamewidth 1
configure wave -timelineunits ns

# 运行仿真
run 10 us

# 缩放波形
wave zoom full
```

---

## 📐 三、Testbench 编写规范

### 3.1 基础 Testbench 模板

```verilog
// =================================================
//  tb_counter.v — 计数器模块 Testbench
// =================================================
`timescale 1ns / 1ps

module tb_counter;

    // ===== 端口声明 =====
    reg        clk;
    reg        rst_n;
    reg        en;
    wire [7:0] count;
    wire       overflow;
    
    // ===== 待测模块 (DUT) 例化 =====
    counter #(.WIDTH(8)) uut (
        .clk      (clk),
        .rst_n    (rst_n),
        .en       (en),
        .count    (count),
        .overflow (overflow)
    );
    
    // ===== 时钟生成 =====
    initial clk = 0;
    always #10 clk = ~clk;  // 50MHz (周期 20ns)
    
    // ===== 测试激励 =====
    initial begin
        // 初始化
        rst_n = 0;
        en    = 0;
        #100;                   // 100ns 复位
        
        // 释放复位
        rst_n = 1;
        #50;
        
        // 测试1: 基本计数
        en = 1;
        #5000;                  // 计数 250 个周期
        
        // 测试2: 暂停
        en = 0;
        #200;
        $display("Count after pause: %d (should stay at ~250)", count);
        
        // 测试3: 溢出
        en = 1;
        #6000;                  // 继续计数到溢出
        if (overflow)
            $display("[PASS] Overflow detected at count=%d", count);
        else
            $display("[FAIL] Overflow NOT detected");
        
        // 结束
        #200;
        $display("=== Simulation Complete ===");
        $finish;
    end
    
    // ===== 自动检查 =====
    reg [7:0] expected;
    always @(posedge clk) begin
        if (!rst_n) expected <= 0;
        else if (en) expected <= expected + 1;
    end
    
    // 断言
    always @(posedge clk) begin
        if (rst_n && en) begin
            #1;  // 延迟一个时间单位等待稳定
            if (count !== expected) begin
                $display("[ERROR] Time=%0t: count=%d, expected=%d",
                         $time, count, expected);
            end
        end
    end

endmodule
```

### 3.2 带文件 I/O 的 Testbench

```verilog
// =================================================
//  tb_fir.v — FIR 滤波器 Testbench (文件输入/黄金对比)
// =================================================
`timescale 1ns / 1ps

module tb_fir;

    reg        clk;
    reg        rst_n;
    reg [15:0] data_in;
    wire [15:0] data_out;
    wire        data_valid;
    
    // DUT
    fir_filter uut (
        .clk(clk), .rst_n(rst_n),
        .data_in(data_in), .data_out(data_out), .data_valid(data_valid)
    );
    
    // 时钟
    initial clk = 0;
    always #5 clk = ~clk;  // 100MHz
    
    // 文件句柄
    integer input_file, golden_file, output_file;
    integer status_in, status_golden;
    reg [15:0] golden_val;
    integer test_cnt, err_cnt;
    
    initial begin
        // 打开文件
        input_file   = $fopen("../testdata/input.txt",   "r");
        golden_file  = $fopen("../testdata/golden.txt",  "r");
        output_file  = $fopen("../testdata/output.txt",  "w");
        
        test_cnt = 0;
        err_cnt  = 0;
        
        // 初始化
        rst_n = 0;
        data_in = 0;
        #50 rst_n = 1;
        
        // 读入测试数据
        while (!$feof(input_file)) begin
            @(posedge clk);
            status_in = $fscanf(input_file, "%d\n", data_in);
            test_cnt = test_cnt + 1;
            
            // 等待输出
            @(posedge clk iff data_valid);
            status_golden = $fscanf(golden_file, "%d\n", golden_val);
            
            // 对比
            $fwrite(output_file, "%d\n", data_out);
            if (data_out !== golden_val) begin
                $display("[ERROR] Test#%0d: got %d, expected %d",
                         test_cnt, data_out, golden_val);
                err_cnt = err_cnt + 1;
            end
        end
        
        // 报告
        $display("=== Test Report ===");
        $display("Total tests: %0d", test_cnt);
        $display("Errors:      %0d", err_cnt);
        if (err_cnt == 0)
            $display("[PASS] All tests passed!");
        else
            $display("[FAIL] %0d errors found", err_cnt);
        
        $fclose(input_file);
        $fclose(golden_file);
        $fclose(output_file);
        $finish;
    end

endmodule
```

### 3.3 总线功能模型 (BFM)

```verilog
// =================================================
//  uart_bfm.v — UART BFM (Bus Functional Model)
//  模拟 MCU 通过 UART 与 FPGA 通信
// =================================================
module uart_bfm #(parameter BAUD_DIV = 434) (  // 115200 @ 50MHz
    output reg       tx,
    output reg [7:0] data,
    output reg       send
);

    task send_byte(input [7:0] byte_data);
        integer i;
        begin
            // 起始位
            tx = 1'b0;
            repeat(BAUD_DIV) @(posedge tb_clk);
            
            // 数据位 (LSB first)
            for (i = 0; i < 8; i = i + 1) begin
                tx = byte_data[i];
                repeat(BAUD_DIV) @(posedge tb_clk);
            end
            
            // 停止位
            tx = 1'b1;
            repeat(BAUD_DIV) @(posedge tb_clk);
        end
    endtask
    
    // 发送命令序列
    task send_command(input [7:0] cmd, input [7:0] arg);
        begin
            $display("[BFM] Sending cmd=0x%02h, arg=0x%02h", cmd, arg);
            send_byte(8'hAA);    // 帧头
            send_byte(cmd);      // 命令
            send_byte(arg);      // 参数
            send_byte(8'h55);    // 帧尾
        end
    endtask

endmodule
```

---

## 🔬 四、波形查看技巧

### 4.1 波形窗口操作

```
ModelSim 波形 (Wave) 窗口常用操作:

快捷键:
  Ctrl+W        — 添加信号到波形
  F             — 缩放到全屏 (Zoom Full)
  Z             — 放大 (Zoom In)
  Shift+Z       — 缩小 (Zoom Out)
  C             — 添加游标 (Cursor)
  Ctrl+G        — 跳转到指定时间

显示设置:
  右键 → Radix → Binary/Hex/Decimal/Unsigned  — 切换数值进制
  右键 → Format → Analog (Step/Interpolated)  — 模拟波形显示
  右键 → Properties → Color                    — 改变颜色

分组与分隔:
  add wave -divider "===== Group Name ====="
  波形窗口 → 右键 → Insert Divider
```

### 4.2 保存/恢复波形配置

```tcl
# 保存当前波形设置
write format wave -output wave_format.do

# 下次仿真时恢复
do wave_format.do
```

### 4.3 波形比较

```batch
:: 比较两次仿真的波形
vsim -view wave1.wlf -do "add wave *"
add wave -view wave2.wlf *
compare start wave1 wave2
compare options -wave
```

---

## 📊 五、代码覆盖率

### 5.1 启用覆盖率

```tcl
# 编译时启用覆盖率
vlog -cover bcest +acc -work work ../src/counter.v

# 仿真
vsim -coverage work.tb_counter
run -all

# 查看覆盖率报告
coverage report -file coverage_report.txt

# GUI 查看
coverage report -detail -output coverage_detail.txt

# 覆盖率指标:
#   b = branch    (分支覆盖率)
#   c = condition (条件覆盖率)
#   e = expression(表达式覆盖率)
#   s = statement (语句覆盖率)
#   t = toggle    (翻转覆盖率)
```

### 5.2 覆盖率合并

```tcl
# 合并多个测试的覆盖率
vcover merge merged_coverage test1.ucdb test2.ucdb test3.ucdb
vcover report -html merged_coverage -output coverage_html/
```

---

## ⏱️ 六、时序仿真 (Gate-Level)

### 6.1 时序仿真流程

```
步骤:
1. Quartus 编译生成网表 + SDF (标准延迟格式)
2. 在 ModelSim 中编译网表 + SDF
3. 运行仿真，观察延迟影响

关键文件:
  project_name.vo          — Verilog 门级网表
  project_name_v.sdo       — SDF 延迟文件
  cycloneive_atoms.v       — Cyclone IV 原语库
```

### 6.2 时序仿真 DO 脚本

```tcl
# gate_sim.do — 门级时序仿真脚本
# 用法: vsim -do gate_sim.do

# 编译 Quartus 库 (第一次运行需要)
# vlog +acc C:/intelFPGA/13.1/quartus/eda/sim_lib/cycloneive_atoms.v

# 编译门级网表
vlog +acc +no_opt -work work ../output_files/counter.vo

# 编译 Testbench
vlog +acc -work work ../tb/tb_counter.v

# 加载仿真
vsim -L cycloneive_ver -sdftyp /tb_counter/uut=../output_files/counter_v.sdo work.tb_counter

# 添加波形
add wave *
add wave -divider "Timing Check"
add wave /tb_counter/uut/count*

# 运行
run 10 us

# 检查时序违例
check_timing -verbose
```

---

## 🧰 七、电赛仿真典型场景

### 7.1 FPGA 逻辑功能验证

```
场景: 验证 PWM 生成模块
步骤:
  1. 编写 Testbench 模拟不同占空比
  2. ModelSim 中观察 PWM 波形
  3. 测量周期和脉宽是否与设计一致
  4. 覆盖 0%/25%/50%/75%/100% 占空比
```

### 7.2 ADC 数据采集验证

```verilog
// tb_adc.v — ADC 接口仿真
module tb_adc;

    reg        clk;
    reg        rst_n;
    reg  [7:0] adc_data_sim;  // 模拟 ADC 数据
    reg        adc_clk;
    wire       adc_oe;
    
    // ADC 仿真模型 — 产生正弦波数据
    reg [7:0] sine_table [0:255];
    reg [7:0] index;
    
    initial begin
        // 初始化正弦查找表
        $readmemh("../data/sine_8bit_256.hex", sine_table);
    end
    
    always @(posedge adc_clk) begin
        index <= index + 1;
        adc_data_sim <= sine_table[index];
    end
    
    // DUT 例化
    adc_reader uut (
        .clk(clk), .rst_n(rst_n),
        .adc_data(adc_data_sim), .adc_clk(adc_clk), .adc_oe(adc_oe)
    );
    
endmodule
```

### 7.3 UART 通信验证

```
验证步骤:
1. 编写 UART BFM 模拟上位机发送指令
2. FPGA 接收 → 解析 → 返回响应
3. BFM 检查响应是否正确
4. 验证不同波特率的稳定性
```

---

## 🔧 八、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `Error: cannot find work library` | 未创建 work 库 | 先执行 `vlib work && vmap work work` |
| 仿真结果全 `x` | 未初始化 | 检查 reset 信号是否有效 |
| 波形窗口无信号 | 未添加信号到波形 | 选中信号 → Ctrl+W |
| `# ** Error: (vopt-2189)` | 优化导致信号不可见 | 加 `+acc` 编译选项 |
| SDF 反标失败 | 信号名不匹配 | 检查 `-sdftyp` 路径是否正确 |
| 门级仿真时序违例 | 时序约束不够 | 检查 SDC 约束是否正确 |
| ModelSim 闪退 | 内存不足/版本bug | 用 64-bit 版本 / 增大虚拟内存 |

---

## 🔗 九、与 Quartus 集成

### 9.1 从 Quartus 启动 ModelSim

```
Quartus 中:
  Assignments → Settings → EDA Tool Settings → Simulation
    Tool name: ModelSim-Altera
    Format: Verilog HDL
    勾选: ☑ Run gate-level simulation automatically after compilation

  然后: Tools → Run Simulation Tool → RTL Simulation
```

### 9.2 生成 ModelSim 脚本

```batch
:: Quartus 自动生成 ModelSim 脚本
:: 位置: <project>/simulation/modelsim/

:: 手动运行:
cd simulation/modelsim
vsim -do msim_setup.tcl
```

---

## 📌 技能信息

- **版本**: v1.0
- **适用**: ModelSim SE/DE 10.x / ModelSim-Altera / QuestaSim
- **配合**: `quartus` 技能 (FPGA 开发) + `nuedc` 技能 (赛题拆解)
- **电赛场景**: FPGA 逻辑验证 / 时序验证 / 接口调试

---

> **用法**: 告诉 agent "写一个 UART 接收模块的 Testbench，用 ModelSim 验证 115200bps"，agent 会：
> 1. 生成完整 Testbench (含 BFM)
> 2. 生成 .do 编译仿真脚本
> 3. 给出波形关键检查点
> 4. 添加自动比对断言
