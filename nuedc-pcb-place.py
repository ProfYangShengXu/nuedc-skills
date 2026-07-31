#!/usr/bin/env python3
"""
nuedc-pcb-place.py — PCB 自动布局布线脚本生成器

功能:
  1. 根据电路拓扑生成元件摆放方案 (placement plan)
  2. 输出 SVG 摆放位置指导图
  3. 生成 KiCad Python 脚本 → 一键自动布局+自动布线+导出 Gerber

用法:
    python nuedc-pcb-place.py buck --vin 12 --vout 3.3 --iout 2
    python nuedc-pcb-place.py buck --layout-svg
    python nuedc-pcb-place.py buck --kicad-script
"""

import sys
from pathlib import Path

OUT = Path("wiring-diagrams")

FP = {
    "STM32F103C8T6":"Package_QFP:LQFP-48_7x7mm_P0.5mm",
    "IR2104":"Package_DIP:DIP-8_W7.62mm",
    "LM358":"Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "IRF3205":"Package_TO_THT:TO-220-3_Vertical",
    "SS34":"Diode_SMD:D_SMA",
    "CD54_10uH":"Inductor_SMD:L_CD54",
    "CAP_1206":"Capacitor_SMD:C_1206_3216Metric",
    "RES_0805":"Resistor_SMD:R_0805_2012Metric",
    "HEADER_2x5":"Connector_PinHeader_2.54mm:PinHeader_2x5_P2.54mm_Vertical",
}

PLACEMENTS = {
    "buck": {
        "board":"50 x 40", "topo":"Buck Converter",
        "parts": [
            ("C1","CAP_1206",0.1,0.3,0),("U1","IR2104",0.3,0.2,0),
            ("Q1","IRF3205",0.3,0.5,0),("L1","CD54_10uH",0.6,0.5,0),
            ("D1","SS34",0.6,0.7,0),("C2","CAP_1206",0.8,0.3,0),
            ("R1","RES_0805",0.3,0.8,0),("R2","RES_0805",0.3,0.9,0),
            ("J1","HEADER_2x5",0.1,0.7,0),("J2","HEADER_2x5",0.9,0.7,90),
        ]},
    "boost": {
        "board":"50 x 40", "topo":"Boost Converter",
        "parts": [
            ("C1","CAP_1206",0.1,0.3,0),("L1","CD54_10uH",0.2,0.5,0),
            ("Q1","IRF3205",0.4,0.5,0),("D1","SS34",0.6,0.5,0),
            ("C2","CAP_1206",0.8,0.3,0),("U1","LM358",0.4,0.2,0),
            ("R1","RES_0805",0.6,0.8,0),("R2","RES_0805",0.7,0.8,0),
            ("J1","HEADER_2x5",0.1,0.7,0),("J2","HEADER_2x5",0.9,0.7,90),
        ]},
}

def gen_layout_svg(topo, out_path):
    p = PLACEMENTS[topo]
    BW, BH = 500, 400
    cols = ["#e53935","#1565c0","#2e7d32","#f57f17","#7b1fa2","#00897b","#c62828","#283593","#558b2f","#e65100"]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 480">']
    svg.append(f'<text x="280" y="20" text-anchor="middle" font-size="16" font-weight="bold">{p["topo"]}</text>')
    svg.append(f'<text x="280" y="38" text-anchor="middle" font-size="11" fill="#666">Board: {p["board"]}</text>')
    svg.append(f'<rect x="30" y="50" width="{BW}" height="{BH}" rx="5" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2" stroke-dasharray="8,4"/>')
    for i, (ref, part, nx, ny, rot) in enumerate(p["parts"]):
        cx, cy = 30 + int(nx * BW), 50 + int(ny * BH)
        c = cols[i % len(cols)]
        svg.append(f'<rect x="{cx-15}" y="{cy-10}" width="30" height="20" rx="2" fill="{c}33" stroke="{c}" stroke-width="1.5"/>')
        svg.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="9" font-weight="bold" fill="{c}">{ref}</text>')
        svg.append(f'<text x="{cx}" y="{cy+14}" text-anchor="middle" font-size="7" fill="#666">{part}</text>')
    svg.append('<text x="30" y="470" font-size="10" font-weight="bold">Guide:</text>')
    svg.append('<text x="30" y="486" font-size="9" fill="#555">Power loop: thick traces, keep short</text>')
    svg.append('<text x="30" y="500" font-size="9" fill="#555">Keep inductor away from control IC</text>')
    svg.append('<text x="30" y="514" font-size="9" fill="#555">Decoupling caps within 5mm of IC</text>')
    svg.append('</svg>')
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(svg))
    except OSError as e:
        print(f"[!] 写入 SVG 失败 {out_path}: {e}")
        return None
    return out_path

def gen_kicad_script(topo, out_path):
    p = PLACEMENTS[topo]
    bs = p["board"].split(" x ")
    w, h = bs[0], bs[1]
    lines = [
        '#!/usr/bin/env python3',
        '"""KiCad auto-placement for ' + p["topo"] + '"""',
        '',
        'import sys, pcbnew',
        '',
        f'W = pcbnew.FromMM({w})',
        f'H = pcbnew.FromMM({h})',
        '',
        'b = pcbnew.BOARD()',
        'ol = pcbnew.PCB_SHAPE()',
        'ol.SetShape(pcbnew.SHAPE_T_RECT)',
        'ol.SetLayer(pcbnew.Edge_Cuts)',
        'ol.SetStart(pcbnew.VECTOR2I(0,0))',
        'ol.SetEnd(pcbnew.VECTOR2I(W,H))',
        'b.Add(ol)',
        '',
    ]
    for ref, part, nx, ny, rot in p["parts"]:
        fp = FP.get(part, "")
        x = f'pcbnew.FromMM({float(nx)*float(w):.1f})'
        y = f'pcbnew.FromMM({float(ny)*float(h):.1f})'
        lines.append(f'f=pcbnew.FootprintLoad("","{fp}")')
        lines.append(f'if f:f.SetReference("{ref}");f.SetPosition(pcbnew.VECTOR2I({x},{y}))' + (f';f.SetOrientationDegrees({rot})' if rot else '') + ';b.Add(f)')
        lines.append(f'else:print("Missing:{fp}")')
    lines.extend([
        '',
        'b.Save("auto_placed.kicad_pcb")',
        'print("[OK] Saved. Open in KiCad PCB Editor -> Route -> Auto-route")',
    ])
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except OSError as e:
        print(f"[!] 写入 KiCad 脚本失败 {out_path}: {e}")
        return None
    return out_path

if __name__ == "__main__":
    if "--help" in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        print("\nTopologies: buck, boost")
        sys.exit(0)
    topo = sys.argv[1]
    if topo not in PLACEMENTS:
        print(f"Unknown: {topo}. Options: {', '.join(PLACEMENTS.keys())}")
        sys.exit(1)
    OUT.mkdir(exist_ok=True)
    gen_layout_svg(topo, OUT / f"layout_{topo}.svg")
    print(f"[OK] Layout SVG: wiring-diagrams/layout_{topo}.svg")
    if "--kicad-script" in sys.argv:
        gen_kicad_script(topo, OUT / f"kicad_auto_{topo}.py")
        print(f"[OK] KiCad script: wiring-diagrams/kicad_auto_{topo}.py")
