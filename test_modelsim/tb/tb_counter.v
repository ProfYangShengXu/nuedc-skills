// ====================================================
//  tb_counter.v — 计数器 Testbench (带自检)
// ====================================================
`timescale 1ns / 1ps

module tb_counter;

    // === 参数 ===
    localparam WIDTH = 8;
    localparam CLK_PERIOD = 20;  // 50MHz

    // === 信号 ===
    reg             clk;
    reg             rst_n;
    reg             en;
    reg             dir;
    reg  [WIDTH-1:0] preset;
    reg             load;
    wire [WIDTH-1:0] count;
    wire            overflow;
    wire            underflow;

    // === DUT ===
    counter #(.WIDTH(WIDTH)) uut (
        .clk      (clk),
        .rst_n    (rst_n),
        .en       (en),
        .dir      (dir),
        .preset   (preset),
        .load     (load),
        .count    (count),
        .overflow (overflow),
        .underflow(underflow)
    );

    // === 时钟 ===
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // === 测试统计 ===
    integer test_cnt, pass_cnt, fail_cnt;

    // === 事件锁存 (捕捉单周期脉冲) ===
    reg overflow_seen, underflow_seen;
    always @(posedge clk) begin
        if (overflow)  overflow_seen  <= 1;
        if (underflow) underflow_seen <= 1;
    end

    // === 预期值模型 (黄金参考) ===
    reg [WIDTH-1:0] expected;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            expected <= 0;
        else if (load)
            expected <= preset;
        else if (en) begin
            if (!dir)
                expected <= expected + 1;
            else
                expected <= expected - 1;
        end
    end

    // === 自动比对 ===
    always @(negedge clk) begin
        if (rst_n && en && !load) begin
            #1;
            if (count !== expected) begin
                $display("[FAIL] t=%0t: count=%d, expected=%d", $time, count, expected);
                fail_cnt = fail_cnt + 1;
            end else begin
                pass_cnt = pass_cnt + 1;
            end
            test_cnt = test_cnt + 1;
        end
    end

    // === 主测试流程 ===
    initial begin
        test_cnt  = 0;
        pass_cnt  = 0;
        fail_cnt  = 0;

        // ---- 初始化 ----
        $display("=== Counter Testbench Start ===");
        rst_n  = 0;
        en     = 0;
        dir    = 0;
        preset = 0;
        load   = 0;
        overflow_seen  = 0;
        underflow_seen = 0;
        #100;
        rst_n  = 1;
        #50;

        // ---- 测试1: 基本加计数 (0→255→0 溢出) ----
        $display("[TEST 1] Basic up-count + overflow");
        en  = 1;
        dir = 0;
        #5500;  // 跑 275 个周期, 覆盖从0到溢出后
        if (overflow_seen)
            $display("  [PASS] Overflow detected at count=%d", count);
        else
            $display("  [FAIL] Overflow NOT detected");

        // ---- 测试2: 暂停 ----
        $display("[TEST 2] Pause and resume");
        en = 0;
        #100;
        if (count === expected)
            $display("  [PASS] Count stable during pause");
        else
            $display("  [FAIL] Count changed during pause");
        en = 1;
        #200;

        // ---- 测试3: 预置加载 ----
        $display("[TEST 3] Preset load (load=100)");
        en     = 0;
        preset = 100;
        load   = 1;
        #20;
        load   = 0;
        #5;
        if (count == 100)
            $display("  [PASS] Loaded 100 successfully");
        else
            $display("  [FAIL] Load failed: expected 100, got %d", count);
        en = 1;
        #200;

        // ---- 测试4: 减计数 + 下溢 ----
        $display("[TEST 4] Down-count + underflow");
        en  = 1;
        dir = 1;  // 减计数
        #6000;
        if (underflow_seen)
            $display("  [PASS] Underflow detected at count=%d", count);
        else
            $display("  [FAIL] Underflow NOT detected");

        // ---- 测试5: 异步复位 ----
        $display("[TEST 5] Async reset");
        rst_n = 0;
        #30;
        if (count == 0)
            $display("  [PASS] Reset to zero");
        else
            $display("  [FAIL] Reset failed: count=%d", count);
        rst_n = 1;
        #50;

        // ---- 报告 ----
        $display("======================================");
        $display("  Test Report");
        $display("  Total checks: %0d", test_cnt);
        $display("  Passed:       %0d", pass_cnt);
        $display("  Failed:       %0d", fail_cnt);
        if (fail_cnt == 0)
            $display("  [FINAL: PASS] All checks passed!");
        else
            $display("  [FINAL: FAIL] %0d failures", fail_cnt);
        $display("======================================");

        $finish;
    end

endmodule
