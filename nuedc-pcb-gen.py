#!/usr/bin/env python3
"""
nuedc-pcb-gen.py — 全国大学生电子设计竞赛 PCB 参数计算工具

已实现（本脚本只做参数计算，不出图/不导出）:
  1. Buck 降压变换器参数计算（占空比 / 电感 / 输出电容 / 器件耐压）
  2. Boost 升压变换器参数计算
  3. 同相运放增益与 dB 换算

元件库 LCSC_PARTS 仅供查料号参考，未与计算流程耦合。
原理图/布局 SVG 见 nuedc-pcb-svg.py 与 nuedc-pcb-place.py。

用法:
    # 列出支持的电路模板
    python nuedc-pcb-gen.py --list-templates

    # 生成 Buck 降压电路
    python nuedc-pcb-gen.py buck --vin 12 --vout 3.3 --iout 2 --fsw 500k

    # 生成 Boost 升压电路
    python nuedc-pcb-gen.py boost --vin 5 --vout 12 --iout 1

    # 运放增益计算 (同相放大)
    python nuedc-pcb-gen.py opamp --r1 10000 --rf 100000
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


# 已实现的计算/生成器: 模板名 -> 说明
IMPLEMENTED_TEMPLATES = {
    "buck": "降压变换器参数计算",
    "boost": "升压变换器参数计算",
    "opamp": "同相放大增益计算",
}


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
        if vin <= 0 or vout <= 0 or iout <= 0 or fsw <= 0:
            print("[!] 参数必须为正数 (--vin/--vout/--iout/--fsw)")
            return
        if vout >= vin:
            print(f"[!] Buck 需满足 vout < vin (当前 {vout}V >= {vin}V)，请用 boost")
            return
        r = calc_buck(vin, vout, iout, fsw)
        print(f"Buck {int(vin)}V -> {vout}V @ {iout}A ({fsw//1000}kHz)")
        for k, v in r.items(): print(f"  {k:15s}: {v}")
    elif cmd == "boost":
        if vin <= 0 or vout <= 0 or iout <= 0 or fsw <= 0:
            print("[!] 参数必须为正数 (--vin/--vout/--iout/--fsw)")
            return
        if vout <= vin:
            print(f"[!] Boost 需满足 vout > vin (当前 {vout}V <= {vin}V)，请用 buck")
            return
        r = calc_boost(vin, vout, iout, fsw)
        print(f"Boost {int(vin)}V -> {vout}V @ {iout}A ({fsw//1000}kHz)")
        for k, v in r.items(): print(f"  {k:15s}: {v}")
    elif cmd == "opamp":
        r1, rf = DEFAULT_R1, DEFAULT_RF
        for i, a in enumerate(sys.argv):
            if a == "--r1" and i+1 < len(sys.argv): r1 = float(sys.argv[i+1])
            if a == "--rf" and i+1 < len(sys.argv): rf = float(sys.argv[i+1])
        if r1 <= 0 or rf < 0:
            print("[!] 电阻必须为正数 (--r1/--rf)")
            return
        gain = calc_opamp_gain(r1, rf)
        print(f"Op-Amp: R1={r1/1000:.0f}k Rf={rf/1000:.0f}k"
              f" Gain={gain:.1f} ({DB_SCALE*math.log10(gain):.1f}dB)")
    elif cmd == "--list-templates":
        print("已实现的计算模板:")
        for name, desc in IMPLEMENTED_TEMPLATES.items():
            print(f"  {name:12s} — {desc}")
    else:
        print(f"Unknown: {cmd}")
        print(f"Available: {', '.join(IMPLEMENTED_TEMPLATES)}")


if __name__ == "__main__":
    main()
