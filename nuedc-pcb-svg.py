# SVG schematic engine
SVG_W, SVG_H = 1000, 700

def svg_header(title):
    return '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">\n<rect width="%d" height="%d" fill="#fafafa"/>\n<text x="%d" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#333">%s</text>\n' % (SVG_W, SVG_H, SVG_W, SVG_H, SVG_W, SVG_H, SVG_W//2, title)

def svg_footer():
    return '</svg>'

def res_sym(x, y, label="R", val="10k"):
    s = '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y-8, x, y-4)
    for i in range(5):
        s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x-8, y-4+i*4, x+8, y-4+(i+1)*4)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y+4, x, y+8)
    s += '<text x="%d" y="%d" font-size="11" fill="#333">%s</text>' % (x+15, y, label)
    if val: s += '<text x="%d" y="%d" font-size="9" fill="#666">%s</text>' % (x+15, y+14, val)
    return s

def cap_sym(x, y, label="C", val="10uF"):
    s = '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y-15, x, y)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x-10, y, x+10, y)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x-10, y+3, x+10, y+3)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y+3, x, y+18)
    s += '<text x="%d" y="%d" font-size="11" fill="#e53935">+</text>' % (x+12, y+10)
    s += '<text x="%d" y="%d" font-size="11" fill="#333">%s</text>' % (x+15, y-5, label)
    if val: s += '<text x="%d" y="%d" font-size="9" fill="#666">%s</text>' % (x+15, y+9, val)
    return s

def inductor_sym(x, y, label="L", val="10uH"):
    s = '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y-15, x, y-10)
    for i in range(4):
        ry = y-10+i*7
        s += '<path d="M %d %d Q %d %d %d %d" fill="none" stroke="#333" stroke-width="2"/>' % (x-6, ry, x+6, ry-4, x+6, ry)
        s += '<path d="M %d %d Q %d %d %d %d" fill="none" stroke="#333" stroke-width="2"/>' % (x+6, ry, x-6, ry+4, x-6, ry)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y+18, x, y+23)
    s += '<text x="%d" y="%d" font-size="11" fill="#333">%s</text>' % (x+15, y, label)
    if val: s += '<text x="%d" y="%d" font-size="9" fill="#666">%s</text>' % (x+15, y+14, val)
    return s

def diode_sym(x, y, label="D", val="SS34"):
    s = '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y-15, x, y-3)
    s += '<polygon points="%d,%d %d,%d %d,%d" fill="none" stroke="#333" stroke-width="2"/>' % (x-8,y-3, x+8,y-8, x+8,y+2)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x+8, y-8, x+8, y+2)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y+2, x, y+18)
    s += '<text x="%d" y="%d" font-size="11" fill="#333">%s</text>' % (x+15, y, label)
    if val: s += '<text x="%d" y="%d" font-size="9" fill="#666">%s</text>' % (x+15, y+14, val)
    return s

def ic_box(x, y, w, h, label, pins_left=None, pins_right=None):
    s = '<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="white" stroke="#333" stroke-width="2"/>' % (x, y, w, h)
    s += '<text x="%d" y="%d" text-anchor="middle" font-size="11" fill="#333">%s</text>' % (x+w//2, y+h//2+4, label)
    if pins_left:
        for name, py in pins_left:
            s += '<rect x="%d" y="%d" width="6" height="8" fill="#ccc"/>' % (x-6, y+py-4)
            s += '<text x="%d" y="%d" text-anchor="end" font-size="8" fill="#333">%s</text>' % (x-12, y+py+4, name)
    if pins_right:
        for name, py in pins_right:
            s += '<rect x="%d" y="%d" width="6" height="8" fill="#ccc"/>' % (x+w, y+py-4)
            s += '<text x="%d" y="%d" font-size="8" fill="#333">%s</text>' % (x+w+12, y+py+4, name)
    return s

def wire(x1, y1, x2, y2, color="#333"):
    return '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (x1, y1, x2, y2, color)

def dot(x, y):
    return '<circle cx="%d" cy="%d" r="3" fill="#333"/>' % (x, y)

def gnd_sym(x, y):
    s = '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x, y, x, y+8)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="2"/>' % (x-12, y+8, x+12, y+8)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.5"/>' % (x-8, y+12, x+8, y+12)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1"/>' % (x-4, y+16, x+4, y+16)
    return s

def vcc_label(x, y, val="3.3V"):
    return '<text x="%d" y="%d" font-size="10" fill="#e53935" font-weight="bold">VCC(%s)</text>' % (x, y, val)

def net_label(x, y, text):
    return '<text x="%d" y="%d" font-size="10" fill="#1565c0" font-weight="bold">%s</text>' % (x, y, text)

def gen_buck_schematic(vin, vout, iout, fsw, output_path):
    """Generate full Buck converter schematic SVG"""
    import importlib.util as _iu
    _s = _iu.spec_from_file_location('_pg', __file__.replace('-svg','-gen'))
    _m = _iu.module_from_spec(_s); _s.loader.exec_module(_m); calc_buck = _m.calc_buck
    params = calc_buck(vin, vout, iout, fsw)
    
    svg = svg_header('Buck Converter: %dV → %dV @ %dA (%dkHz)' % (vin, vout, iout, fsw//1000))
    
    # Input section
    svg += vcc_label(80, 80, '%dV' % vin)
    svg += cap_sym(80, 120, 'Cin', '%duF' % int(params['cout_min_uf']*3))
    svg += gnd_sym(80, 180)
    
    # MOSFET + PWM driver
    svg += ic_box(200, 100, 120, 80, 'IR2104\nDriver', 
                  pins_left=[('VCC',20),('HIN',40),('LIN',60)], 
                  pins_right=[('HO',20),('VS',40),('LO',60)])
    svg += wire(80, 130, 180, 120)
    svg += dot(80, 130)
    
    # Output inductor
    svg += inductor_sym(400, 130, 'L1', '%duH' % params['l_uh'])
    
    # Freewheeling diode
    svg += diode_sym(300, 300, 'D1', 'SS34')
    svg += gnd_sym(300, 370)
    
    # Output cap
    svg += cap_sym(500, 220, 'Cout', '%duF' % int(params['cout_min_uf']))
    svg += gnd_sym(500, 320)
    svg += net_label(500, 165, 'VOUT=%dV' % vout)
    
    # Feedback divider
    svg += res_sym(400, 450, 'R1', '10k')
    svg += gnd_sym(400, 520)
    svg += res_sym(500, 450, 'R2', '47k')
    
    # Parameters table
    table_y = 570
    svg += '<rect x="50" y="%d" width="900" height="90" rx="5" fill="#f5f5f5" stroke="#ddd" stroke-width="1"/>' % table_y
    svg += '<text x="60" y="%d" font-size="12" font-weight="bold" fill="#333">Design Parameters:</text>' % (table_y+20)
    y = table_y + 40
    for k, v in params.items():
        svg += '<text x="60" y="%d" font-size="10" fill="#555">%s: %s</text>' % (y, k, str(v))
        y += 16
    
    svg += svg_footer()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)
    return output_path


def gen_boost_schematic(vin, vout, iout, fsw, output_path):
    """Generate full Boost converter schematic SVG"""
    import importlib.util as _iu
    _s = _iu.spec_from_file_location('_pg2', __file__.replace('-svg','-gen'))
    _m = _iu.module_from_spec(_s); _s.loader.exec_module(_m); calc_boost = _m.calc_boost
    params = calc_boost(vin, vout, iout, fsw)
    
    svg = svg_header('Boost Converter: %dV → %dV @ %dA (%dkHz)' % (vin, vout, iout, fsw//1000))
    
    # Input
    svg += vcc_label(80, 80, '%dV' % vin)
    svg += cap_sym(80, 120, 'Cin', '%duF' % int(params['cout_min_uf']*3))
    svg += gnd_sym(80, 180)
    
    # Inductor
    svg += inductor_sym(200, 130, 'L1', '%duH' % params['l_uh'])
    
    # MOSFET + diode
    svg += diode_sym(350, 130, 'D1', 'SS34')
    svg += cap_sym(500, 220, 'Cout', '%duF' % int(params['cout_min_uf']))
    svg += gnd_sym(500, 320)
    svg += net_label(500, 165, 'VOUT=%dV' % vout)
    
    # GND
    svg += gnd_sym(300, 350)
    
    svg += svg_footer()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)
    return output_path


if __name__ == '__main__':
    from pathlib import Path
    Path('wiring-diagrams').mkdir(exist_ok=True)
    gen_buck_schematic(12, 3.3, 2, 500000, 'wiring-diagrams/buck_12to3v3.svg')
    gen_boost_schematic(5, 12, 1, 400000, 'wiring-diagrams/boost_5to12.svg')
    print('[OK] Generated Buck + Boost schematics in wiring-diagrams/')
