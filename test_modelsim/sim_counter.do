# ====================================================
#  sim_counter.do — ModelSim 自动化仿真脚本
#  用法: vsim -c -do sim_counter.do
# ====================================================

# 创建/清空 work 库
if {[file exists work]} { vdel -all }
vlib work
vmap work work

# 编译 RTL + Testbench
vlog -sv +acc -work work ../src/counter.v
vlog -sv +acc -work work ../tb/tb_counter.v

# 加载仿真 (命令行模式, 无GUI)
vsim -voptargs="+acc" -c work.tb_counter

# 添加波形信号
add wave -position insertpoint sim:/tb_counter/*
add wave -divider "Counter Internal"
add wave -position insertpoint sim:/tb_counter/uut/*

# 记录所有信号
log -r /*

# 运行仿真
run -all

# 退出
quit -sim
