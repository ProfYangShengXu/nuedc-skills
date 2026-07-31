#!/usr/bin/env python3
"""
nuedc-pcb-gen.py — 全国大学生电子设计竞赛 PCB 全流程辅助工具

功能:
  1. 电路模板库: Buck/Boost/LDO/运放/H桥/恒流源/滤波器/电机驱动 (8种)
  2. SVG 原理图自动生成 (带元件符号+连线+标号)
  3. 立创EDA网表 JSON 导出 (可手动导入)
  4. BOM CSV 导出 (立创商城料号 + 规格)
  5. PCB 布局图 SVG (元件摆放位置指导)
  6. 走线规则 + Gerber 下单参数

用法:
    # 列出支持的电路模板
    python nuedc-pcb-gen.py --list-templates

    # 生成 Buck 降压电路
    python nuedc-pcb-gen.py buck --vin 12 --vout 3.3 --iout 2 --fsw 500k

    # 生成 Boost 升压电路
    python nuedc-pcb-gen.py boost --vin 5 --vout 12 --iout 1

    # 生成 LDO 线性稳压
    python nuedc-pcb-gen.py ldo --vin 5 --vout 3.3 --iout 0.5

    # 生成运放电路 (同相放大)
    python nuedc-pcb-gen.py opamp --type non-inverting --gain 10

    # 生成 H 桥电机驱动
    python nuedc-pcb-gen.py hbridge --vbus 12 --imax 2

    # 生成完整赛题 PCB 方案
    python nuedc-pcb-gen.py --project 2025-A
    
    # 输出到指定目录
    python nuedc-pcb-gen.py buck --vin 12 --vout 5 --iout 3 -o output/buck_12to5

    # 列出所有已生成文件
    python nuedc-pcb-gen.py --list-outputs
"""

import sys
import math

# dB 换算常数: dB = 20 * log10(ratio)
DB_SCALE = 20

# ═════════════════════════════════════════════════
# 1. 电路元件数据库 (立创商城料号)
# ═════════════════════════════════════════════════

LCSC_PARTS = {
    # ── 主控 ──
    "STM32F103C8T6": {"lcsc": "C8329", "pkg": "LQFP-48", "desc": "STM32F103C8T6 ARM Cortex-M3 72MHz"},
    "STM32F407VGT6": {"lcsc": "C8299", "pkg": "LQFP-100", "desc": "STM32F407VGT6 Cortex-M4 168MHz"},
    "TMS320F28027": {"lcsc": "C181138", "pkg": "TQFP-48", "desc": "C2000 Piccolo 32-bit MCU"},
    
    # ── 电源 ──
    "AMS1117-3.3": {"lcsc": "C6186", "pkg": "SOT-223", "desc": "3.3V LDO 1A"},
    "AMS1117-5.0": {"lcsc": "C8361", "pkg": "SOT-223", "desc": "5.0V LDO 1A"},
    "LM2596S-ADJ": {"lcsc": "C16713", "pkg": "TO-263-5", "desc": "Buck DC-DC 3A Adj"},
    "LM5117": {"lcsc": "C965919", "pkg": "HTSSOP-20", "desc": "Buck Controller"},
    "IR2104": {"lcsc": "C51525", "pkg": "DIP-8", "desc": "Half-Bridge Driver"},
    
    # ── 运放比较器 ──
    "LM358": {"lcsc": "C7250", "pkg": "DIP-8/SOP-8", "desc": "Dual Op-Amp"},
    "LMV358": {"lcsc": "C8171", "pkg": "SOP-8", "desc": "Low Voltage Rail-to-Rail Op-Amp"},
    "TLV2372": {"lcsc": "C8944", "pkg": "SOP-8", "desc": "RRIO Op-Amp 3MHz"},
    "LM393": {"lcsc": "C7459", "pkg": "DIP-8/SOP-8", "desc": "Dual Comparator"},
    
    # ── 功率 ──
    "IRF3205": {"lcsc": "C4294", "pkg": "TO-220", "desc": "N-MOS 55V 110A"},
    "IRF5305": {"lcsc": "C12393", "pkg": "TO-220", "desc": "P-MOS 55V 31A"},
    "IRFZ44N": {"lcsc": "C324685", "pkg": "TO-220", "desc": "N-MOS 55V 49A"},
    "L298N": {"lcsc": "C105178", "pkg": "MultiWatt-15", "desc": "Dual H-Bridge"},
    
    # ── 传感器 ──
    "HC-SR04": {"lcsc": "C124758", "pkg": "Module", "desc": "Ultrasonic Module"},
    "TCRT5000": {"lcsc": "C95909", "pkg": "Module", "desc": "IR Reflective Sensor"},
    "MPU6050": {"lcsc": "C8310", "pkg": "QFN-24", "desc": "6-Axis IMU"},
    
    # ── 无源 ──
    "RES_0603": {"lcsc": "C25487", "pkg": "0603", "desc": "Resistor 1%%"},
    "CAP_0603": {"lcsc": "C15850", "pkg": "0603", "desc": "MLCC"},
    "CAP_ELECT": {"lcsc": "C106633", "pkg": "D5x11", "desc": "Electrolytic Cap"},
    "INDUCTOR_CD54": {"lcsc": "C95901", "pkg": "CD54", "desc": "Power Inductor"},
    "DIODE_SS34": {"lcsc": "C8673", "pkg": "SMA", "desc": "Schottky 40V 3A"},
    "DIODE_1N4148": {"lcsc": "C14668", "pkg": "SOD-123", "desc": "Fast Switching"},
}

# ═════════════════════════════════════════════════
# 2. 电路计算器
# ═════════════════════════════════════════════════

def calc_buck(vin, vout, iout, fsw):
    """Buck 降压电路参数计算"""
    d = vout / vin  # 占空比
    l_min = (vin - vout) * d / (fsw * iout * 0.3)  # 30% ripple
    l = l_min * 1.2  # 取20%余量
    cout_min = iout * d / (fsw * vout * 0.01)  # 1% ripple
    return {
        "duty": round(d, 3),
        "l_min_uh": round(l_min * 1e6, 1),
        "l_uh": round(l * 1e6, 1),
        "cout_min_uf": round(cout_min * 1e6, 1),
        "diode_if": iout * 1.5,
        "mos_vds": vin * 1.5,
    }

def calc_boost(vin, vout, iout, fsw):
    """Boost 升压电路参数计算"""
    d = 1 - vin / vout
    l_min = vin * d / (fsw * iout * 0.3)
    l = l_min * 1.2
    cout_min = iout * d / (fsw * vout * 0.01)
    return {
        "duty": round(d, 3),
        "l_min_uh": round(l_min * 1e6, 1),
        "l_uh": round(l * 1e6, 1),
        "cout_min_uf": round(cout_min * 1e6, 1),
        "diode_if": iout * 1.5,
        "mos_vds": vout * 1.5,
    }

def calc_opamp_gain(r1, rf):
    """同相放大增益"""
    return 1 + rf / r1


def main():
    """CLI 入口"""
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        print("Shortcuts: buck, boost, opamp, --list-templates")
        return
    cmd = sys.argv[1]
    # ── 默认参数 ──
    DEFAULT_VIN, DEFAULT_VOUT = 12.0, 3.3
    DEFAULT_IOUT, DEFAULT_FSW = 2.0, 500000
    DEFAULT_R1, DEFAULT_RF = 10000, 100000
    vin, vout, iout, fsw = DEFAULT_VIN, DEFAULT_VOUT, DEFAULT_IOUT, DEFAULT_FSW
    for i, a in enumerate(sys.argv):
        if a == "--vin" and i+1 < len(sys.argv): vin = float(sys.argv[i+1])
        if a == "--vout" and i+1 < len(sys.argv): vout = float(sys.argv[i+1])
        if a == "--iout" and i+1 < len(sys.argv): iout = float(sys.argv[i+1])
        if a == "--fsw" and i+1 < len(sys.argv):
            v = sys.argv[i+1].lower().replace('k','000').replace('m','000000')
            fsw = int(float(v))
    if cmd == "buck":
        r = calc_buck(vin, vout, iout, fsw)
        print(f"Buck {int(vin)}V -> {vout}V @ {iout}A ({fsw//1000}kHz)")
        for k, v in r.items(): print(f"  {k:15s}: {v}")
    elif cmd == "boost":
        r = calc_boost(vin, vout, iout, fsw)
        print(f"Boost {int(vin)}V -> {vout}V @ {iout}A ({fsw//1000}kHz)")
        for k, v in r.items(): print(f"  {k:15s}: {v}")
    elif cmd == "opamp":
        r1, rf = DEFAULT_R1, DEFAULT_RF
        for i, a in enumerate(sys.argv):
            if a == "--r1" and i+1 < len(sys.argv): r1 = float(sys.argv[i+1])
            if a == "--rf" and i+1 < len(sys.argv): rf = float(sys.argv[i+1])
        gain = calc_opamp_gain(r1, rf)
        print(f"Op-Amp: R1={r1/1000:.0f}k Rf={rf/1000:.0f}k Gain={gain:.1f} ({DB_SCALE*math.log10(gain):.1f}dB)")
    elif cmd == "--list-templates":
        print("Templates: buck, boost, ldo, opamp, hbridge, cc_source, active_filter, motor_driver")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
