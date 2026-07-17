// ====================================================
//  counter.v — 可预置双向计数器 (电赛常用模块)
// ====================================================
module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    input  wire             dir,          // 0=加计数, 1=减计数
    input  wire [WIDTH-1:0] preset,
    input  wire             load,
    output reg  [WIDTH-1:0] count,
    output reg              overflow,     // 加计数溢出
    output reg              underflow     // 减计数下溢
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count     <= 0;
            overflow  <= 0;
            underflow <= 0;
        end else if (load) begin
            count     <= preset;
            overflow  <= 0;
            underflow <= 0;
        end else if (en) begin
            if (!dir) begin  // 加计数
                if (count == {WIDTH{1'b1}}) begin  // 全 1 → 溢出
                    count    <= 0;
                    overflow <= 1;
                end else begin
                    count    <= count + 1;
                    overflow <= 0;
                end
                underflow <= 0;
            end else begin   // 减计数
                if (count == 0) begin
                    count     <= {WIDTH{1'b1}};  // 0 → 全 1 (下溢)
                    underflow <= 1;
                end else begin
                    count     <= count - 1;
                    underflow <= 0;
                end
                overflow <= 0;
            end
        end else begin
            overflow  <= 0;
            underflow <= 0;
        end
    end

endmodule
