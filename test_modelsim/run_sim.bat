@echo off
REM ==============================================
REM  run_sim.bat — 一键运行 ModelSim 仿真
REM  使用 ModelSim-Altera 17.0 (随 Quartus 安装)
REM ==============================================

set MODELSIM=C:\intelFPGA\17.0\modelsim_ase\win32aloem

echo ==========================================
echo   Counter Simulation Test
echo   ModelSim: %MODELSIM%
echo ==========================================

REM 清空旧 work 库
if exist work rmdir /s /q work

REM Step 1: 创建 work 库
echo [1/4] Creating work library...
%MODELSIM%\vlib.exe work
%MODELSIM%\vmap.exe work work

REM Step 2: 编译 Verilog 源文件
echo [2/4] Compiling Verilog sources...
%MODELSIM%\vlog.exe -sv +acc -work work src\counter.v
if errorlevel 1 goto :error
%MODELSIM%\vlog.exe -sv +acc -work work tb\tb_counter.v
if errorlevel 1 goto :error

REM Step 3: 运行仿真
echo [3/4] Running simulation...
%MODELSIM%\vsim.exe -c -voptargs="+acc" -do "run -all; quit" work.tb_counter > sim_output.txt 2>&1

REM Step 4: 输出结果
echo [4/4] Done! Results:
echo ==========================================
findstr /C:"FINAL" /C:"Test Report" /C:"Total" /C:"Passed" /C:"Failed" /C:"PASS" /C:"FAIL" sim_output.txt
echo ==========================================
echo Full log saved to sim_output.txt
goto :end

:error
echo [ERROR] Compilation failed! Check output above.
exit /b 1

:end
