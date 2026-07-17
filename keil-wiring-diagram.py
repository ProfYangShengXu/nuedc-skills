#!/usr/bin/env python3
"""
keil-wiring-diagram.py — 动态 Keil 硬件接线图生成器

根据 MCU 型号、外设、调试接口等参数，动态生成 SVG 接线图。
兼容 Reasonix / Claude Code / Codex / Cursor 等 AI 代理调用。

用法:
    python keil-wiring-diagram.py --help                          # 帮助
    python keil-wiring-diagram.py --list-mcus                     # 列出支持的 MCU
    python keil-wiring-diagram.py --list-peripherals              # 列出支持的外设
    
    # 基本用法
    python keil-wiring-diagram.py --mcu STM32F103C8               # 调试器接线图
    python keil-wiring-diagram.py --mcu STM32F103C8 --peripherals "LED:PB0"  # + LED
    
    # 多外设
    python keil-wiring-diagram.py --mcu STM32F407VG ^
        --peripherals "LED:PE0,OLED:I2C1,Servo:PA0,Button:PE4"
    
    # 指定调试接口
    python keil-wiring-diagram.py --mcu STM32F103C8 --debug jtag
    
    # 中英双语
    python keil-wiring-diagram.py --mcu STM32F103C8 --lang en
    
    # 自动从 Keil 项目文件读取 MCU
    python keil-wiring-diagram.py --project my_project.uvprojx ^
        --peripherals "LED:PC13"
    
    # 输出到指定路径
    python keil-wiring-diagram.py --mcu STM32F103C8 -o output.svg
    
    # 批量生成所有组合
    python keil-wiring-diagram.py --all
"""

import sys
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════
# 1. MCU 引脚数据库
# ═══════════════════════════════════════════════

@dataclass
class PinInfo:
    """单个引脚信息"""
    name: str        # 如 PA0, PB1, PC13
    function: str    # 默认功能描述
    x: float         # SVG 上的 X 坐标
    y: float         # SVG 上的 Y 坐标
    side: str = "left"   # left / right
    swd: bool = False    # 是否 SWD 引脚
    jtag: bool = False   # 是否 JTAG 引脚

@dataclass
class MCUInfo:
    """MCU 信息"""
    model: str            # 型号
    core: str             # 内核
    package: str          # 封装
    swd_pins: dict        # SWD 引脚映射
    jtag_pins: dict       # JTAG 引脚映射
    uart_pins: dict       # UART 引脚映射
    i2c_pins: dict        # I2C 引脚映射
    spi_pins: dict        # SPI 引脚映射
    led_onboard: str      # 板载 LED 引脚
    button_onboard: str   # 板载按钮引脚
    adc_pins: list        # ADC 引脚列表
    pwm_pins: list        # 支持 PWM 的引脚
    pinout_svg: str = ""  # 引脚 SVG 子图

# ── MCU 数据库 ─────────────────────────────────
MCU_DB = {}

MCU_DB["STM32F103C8"] = MCUInfo(
    model="STM32F103C8T6",
    core="Cortex-M3",
    package="LQFP48",
    swd_pins={"SWDIO": "PA13", "SWCLK": "PA14", "SWO": "PB3"},
    jtag_pins={"TMS": "PA13", "TCK": "PA14", "TDI": "PA15", "TDO": "PB3", "nTRST": "PB4"},
    uart_pins={"USART1_TX": "PA9", "USART1_RX": "PA10", "USART2_TX": "PA2", "USART2_RX": "PA3"},
    i2c_pins={"I2C1_SCL": "PB6", "I2C1_SDA": "PB7", "I2C2_SCL": "PB10", "I2C2_SDA": "PB11"},
    spi_pins={"SPI1_NSS": "PA4", "SPI1_SCK": "PA5", "SPI1_MISO": "PA6", "SPI1_MOSI": "PA7"},
    led_onboard="PC13",
    button_onboard="PA0",
    adc_pins=["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1"],
    pwm_pins=["PA0","PA1","PA2","PA3","PA6","PA7","PB0","PB1"],
    pinout_svg="""
    <g transform="translate(0,0)">
      <!-- LQFP48 双排引脚 -->
      <text x="5" y="25" font-size="10" fill="#333">左排:</text>
      <text x="5" y="40" font-size="8" fill="#666">PA0  PA1  PA2  PA3  PA4  PA5  PA6  PA7</text>
      <text x="5" y="55" font-size="8" fill="#666">PB0  PB1  PB10 PB11 VUSB 3.3V GND</text>
      <text x="5" y="70" font-size="10" fill="#333">右排:</text>
      <text x="5" y="85" font-size="8" fill="#666">PB12 PB13 PB14 PB15 PC13 PD2</text>
      <text x="5" y="100" font-size="8" fill="#666">5V  GND</text>
      <text x="5" y="118" font-size="9" font-weight="bold" fill="#2e7d32">关键调试引脚:</text>
      <text x="5" y="133" font-size="8" fill="#4caf50">  PA13 (SWDIO)  PA14 (SWCLK)</text>
      <text x="5" y="148" font-size="8" fill="#f44336">  3.3V   GND</text>
    </g>
    """
)

MCU_DB["STM32F103VE"] = MCUInfo(
    model="STM32F103VET6",
    core="Cortex-M3",
    package="LQFP100",
    swd_pins={"SWDIO": "PA13", "SWCLK": "PA14", "SWO": "PB3"},
    jtag_pins={"TMS": "PA13", "TCK": "PA14", "TDI": "PA15", "TDO": "PB3", "nTRST": "PB4"},
    uart_pins={"USART1_TX": "PA9", "USART1_RX": "PA10", "USART2_TX": "PA2", "USART2_RX": "PA3",
               "USART3_TX": "PB10", "USART3_RX": "PB11"},
    i2c_pins={"I2C1_SCL": "PB6", "I2C1_SDA": "PB7", "I2C2_SCL": "PB10", "I2C2_SDA": "PB11"},
    spi_pins={"SPI1_NSS": "PA4", "SPI1_SCK": "PA5", "SPI1_MISO": "PA6", "SPI1_MOSI": "PA7"},
    led_onboard="PE2",
    button_onboard="PA0",
    adc_pins=["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1","PC0","PC1","PC2","PC3","PC4","PC5"],
    pwm_pins=["PA0","PA1","PA2","PA3","PA6","PA7","PB0","PB1","PE9","PE11","PE13","PE14"],
    pinout_svg="""
    <g transform="translate(0,0)">
      <text x="5" y="25" font-size="10" fill="#333">LQFP100 封装引脚众多</text>
      <text x="5" y="40" font-size="9" fill="#2e7d32">关键调试引脚:</text>
      <text x="5" y="55" font-size="8" fill="#4caf50">  PA13 (SWDIO)  PA14 (SWCLK)</text>
      <text x="5" y="70" font-size="8" fill="#f44336">  3.3V(若干)  GND(若干)</text>
      <text x="5" y="88" font-size="9" fill="#2e7d32">板载外设:</text>
      <text x="5" y="103" font-size="8" fill="#666">  LED: PE2  Button: PA0</text>
    </g>
    """
)

MCU_DB["STM32F407VG"] = MCUInfo(
    model="STM32F407VGT6",
    core="Cortex-M4 (FPU)",
    package="LQFP100",
    swd_pins={"SWDIO": "PA13", "SWCLK": "PA14", "SWO": "PB3"},
    jtag_pins={"TMS": "PA13", "TCK": "PA14", "TDI": "PA15", "TDO": "PB3", "nTRST": "PB4"},
    uart_pins={"USART1_TX": "PA9", "USART1_RX": "PA10", "USART2_TX": "PA2", "USART2_RX": "PA3",
               "USART3_TX": "PB10", "USART3_RX": "PB11","UART4_TX": "PC10","UART4_RX": "PC11"},
    i2c_pins={"I2C1_SCL": "PB6", "I2C1_SDA": "PB7", "I2C2_SCL": "PB10", "I2C2_SDA": "PB11",
              "I2C3_SCL": "PA8", "I2C3_SDA": "PC9"},
    spi_pins={"SPI1_NSS": "PA4", "SPI1_SCK": "PA5", "SPI1_MISO": "PA6", "SPI1_MOSI": "PA7",
              "SPI2_NSS": "PB12", "SPI2_SCK": "PB13", "SPI2_MISO": "PB14", "SPI2_MOSI": "PB15"},
    led_onboard="PE0",
    button_onboard="PA0",
    adc_pins=["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1","PC0","PC1","PC2","PC3","PC4","PC5"],
    pwm_pins=["PA0","PA1","PA2","PA3","PA6","PA7","PB0","PB1","PE9","PE11","PE13","PE14"],
    pinout_svg="""
    <g transform="translate(0,0)">
      <text x="5" y="25" font-size="10" fill="#333">STM32F407VGT6 — LQFP100</text>
      <text x="5" y="40" font-size="8" fill="#666">Cortex-M4F @168MHz, 1MB Flash, 192KB RAM</text>
      <text x="5" y="58" font-size="9" font-weight="bold" fill="#2e7d32">关键调试引脚:</text>
      <text x="5" y="73" font-size="8" fill="#4caf50">  PA13 (SWDIO)  PA14 (SWCLK)</text>
      <text x="5" y="88" font-size="8" fill="#f44336">  3.3V(多个)  GND(多个)</text>
    </g>
    """
)

MCU_DB["STM32F103R6"] = MCUInfo(
    model="STM32F103R6T6",
    core="Cortex-M3",
    package="LQFP64",
    swd_pins={"SWDIO": "PA13", "SWCLK": "PA14"},
    jtag_pins={"TMS": "PA13", "TCK": "PA14", "TDI": "PA15", "TDO": "PB3", "nTRST": "PB4"},
    uart_pins={"USART1_TX": "PA9", "USART1_RX": "PA10"},
    i2c_pins={"I2C1_SCL": "PB6", "I2C1_SDA": "PB7"},
    spi_pins={"SPI1_NSS": "PA4", "SPI1_SCK": "PA5", "SPI1_MISO": "PA6", "SPI1_MOSI": "PA7"},
    led_onboard="PC13",
    button_onboard="PA0",
    adc_pins=["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1"],
    pwm_pins=["PA0","PA1","PA2","PA3","PA6","PA7","PB0","PB1"],
    pinout_svg="""
    <g transform="translate(0,0)">
      <text x="5" y="25" font-size="10" fill="#333">LQFP64</text>
      <text x="5" y="42" font-size="9" fill="#2e7d32">调试: PA13(SWDIO) PA14(SWCLK)</text>
    </g>
    """
)

MCU_DB["STM32F411CE"] = MCUInfo(
    model="STM32F411CEU6",
    core="Cortex-M4 (FPU)",
    package="UFQFPN48",
    swd_pins={"SWDIO": "PA13", "SWCLK": "PA14"},
    jtag_pins={"TMS": "PA13", "TCK": "PA14"},
    uart_pins={"USART1_TX": "PA9", "USART1_RX": "PA10", "USART2_TX": "PA2", "USART2_RX": "PA3"},
    i2c_pins={"I2C1_SCL": "PB6", "I2C1_SDA": "PB7", "I2C2_SCL": "PB10", "I2C2_SDA": "PB11"},
    spi_pins={"SPI1_NSS": "PA4", "SPI1_SCK": "PA5", "SPI1_MISO": "PA6", "SPI1_MOSI": "PA7"},
    led_onboard="PC13",
    button_onboard="PA0",
    adc_pins=["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1"],
    pwm_pins=["PA0","PA1","PA2","PA3","PA6","PA7","PB0","PB1"],
    pinout_svg="""
    <g transform="translate(0,0)">
      <text x="5" y="25" font-size="10" fill="#333">STM32F411CEU6 (Black Pill)</text>
      <text x="5" y="40" font-size="8" fill="#666">Cortex-M4F @100MHz, 512KB Flash</text>
      <text x="5" y="58" font-size="9" fill="#2e7d32">调试: PA13(SWDIO) PA14(SWCLK)</text>
    </g>
    """
)

MCU_DB["STM32G030F6"] = MCUInfo(
    model="STM32G030F6P6",
    core="Cortex-M0+",
    package="TSSOP20",
    swd_pins={"SWDIO": "PA13", "SWCLK": "PA14"},
    jtag_pins={},
    uart_pins={"USART1_TX": "PA9", "USART1_RX": "PA10", "USART2_TX": "PA2", "USART2_RX": "PA3"},
    i2c_pins={"I2C1_SCL": "PB6", "I2C1_SDA": "PB7"},
    spi_pins={"SPI1_NSS": "PA4", "SPI1_SCK": "PA5", "SPI1_MISO": "PA6", "SPI1_MOSI": "PA7"},
    led_onboard="PA0",
    button_onboard="PA1",
    adc_pins=["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7"],
    pwm_pins=["PA0","PA1","PA2","PA3","PA6","PA7"],
    pinout_svg="""
    <g transform="translate(0,0)">
      <text x="5" y="25" font-size="10" fill="#333">STM32G030F6P6 — TSSOP20</text>
      <text x="5" y="40" font-size="8" fill="#666">Cortex-M0+ @64MHz, 32KB Flash</text>
      <text x="5" y="58" font-size="9" fill="#2e7d32">调试: PA13(SWDIO) PA14(SWCLK)</text>
    </g>
    """
)


# ═══════════════════════════════════════════════
# 2. 文本资源（中英双语）
# ═══════════════════════════════════════════════

T = {
    "zh": {
        "title_wiring": "接线图",
        "title_debug": "调试器接线图",
        "title_peripherals": "外设接线图",
        "title_components": "器材选购指南",
        "stlink": "ST-Link V2 调试器",
        "jlink": "J-Link 调试器",
        "ulink": "ULINK2 调试器",
        "insert_usb": "← 插入电脑 USB 口",
        "pin_top_view": "引脚排列 (俯视图)",
        "usb_port": "USB 口",
        "usb_up": "USB口朝上",
        "key_pins": "关键引脚",
        "warning_title": "⚠️ 重要提醒",
        "warning_1": "1. 不要接反 3.3V 和 GND（会烧板子！）",
        "warning_2": "2. 先断开 USB 再拔插线",
        "warning_3": "3. 线要插实，不能松动",
        "component_title": "入门必备器材（总预算约 ¥30-100）",
        "component_col1": "器材",
        "component_col2": "说明 / 选购建议",
        "core_equipment": "🔑 核心装备只需前三样: 开发板 + 调试器 + 杜邦线 = ¥27-50",
        "tips_title": "💡 选购小贴士",
        "tips": [
            "▸ 初学者首选 STM32F103C8T6（资料最多，教程最丰富）",
            "▸ ST-Link V2 建议买带防反接保护版本",
            "▸ 杜邦线买 20cm 长的更好操作",
            "▸ 初次玩可以先买最小系统板 + ST-Link 套餐",
            "▸ 别买太便宜的 ST-Link（容易掉固件）",
            "▸ 面包板买带电源轨道的更方便",
        ],
        "warning_buy": "⚠️ 千万别买错",
        "warning_buy_detail": "x STM32 要买 ARM Cortex-M 系列 | x 杜邦线买母对母（不是公对公）",
        "mcu_model": "MCU 型号",
        "core": "内核",
        "package": "封装",
        "debug_mode": "调试接口",
        "peripheral_list": "外设列表",
        "wiring_steps": "接线步骤（初学者请看仔细！）",
        "step_1": "☝️ 第一步：准备杜邦线",
        "step_1_detail": "红(3.3V) 黑(GND) 黄(SWDIO) 绿(SWCLK) — 母对母",
        "step_2": "✌️ 第二步：插入调试器到电脑 USB",
        "step_3": "🤟 第三步：按颜色一一对应接线",
        "step_4": "🖐️ 第四步：给开发板供电（ST-Link 可供电）",
        "step_5": "🖐️ 第五步：检查指示灯",
        "checklist": ["☑ ST-Link 红灯亮", "☑ STM32 板电源灯亮", "☑ 四根线都接实了"],
        "peripheral_label": "外设",
        "pin_label": "引脚",
        "connect_to": "→",
        "gnd": "GND",
        "vcc": "3.3V",
        "resistor": "限流电阻",
        "led_long": "长脚(+)",
        "code_hint": "示例代码",
        "generated_by": "Generated by keil-wiring-diagram.py",
    },
    "en": {
        "title_wiring": "Wiring Diagram",
        "title_debug": "Debugger Wiring Diagram",
        "title_peripherals": "Peripheral Wiring Diagram",
        "title_components": "Component Shopping Guide",
        "stlink": "ST-Link V2 Debugger",
        "jlink": "J-Link Debugger",
        "ulink": "ULINK2 Debugger",
        "insert_usb": "← Plug into Computer USB",
        "pin_top_view": "Pin Layout (Top View)",
        "usb_port": "USB Port",
        "usb_up": "USB up",
        "key_pins": "Key Pins",
        "warning_title": "⚠️ Important",
        "warning_1": "1. NEVER reverse 3.3V and GND!",
        "warning_2": "2. Disconnect USB before replugging wires",
        "warning_3": "3. Push wires firmly",
        "component_title": "Essential Components (Budget ~$5-15 USD)",
        "component_col1": "Component",
        "component_col2": "Description / Buying Tips",
        "core_equipment": "🔑 Core: Dev Board + Debugger + Dupont Wires = $4-8",
        "tips_title": "💡 Shopping Tips",
        "tips": [
            "▸ Beginners: STM32F103C8T6 (most tutorials)",
            "▸ ST-Link V2: buy reverse-polarity protected",
            "▸ Dupont wires: 20cm length recommended",
            "▸ Starter pack: board + ST-Link bundle saves money",
            "▸ Avoid ultra-cheap ST-Link clones (firmware issues)",
            "▸ Breadboard with power rails recommended",
        ],
        "warning_buy": "⚠️ Common Mistakes",
        "warning_buy_detail": "x Buy Cortex-M series STM32 | x Buy female-to-female dupont wires",
        "mcu_model": "MCU Model",
        "core": "Core",
        "package": "Package",
        "debug_mode": "Debug Interface",
        "peripheral_list": "Peripherals",
        "wiring_steps": "Wiring Steps",
        "step_1": "☝️ Step 1: Prepare wires",
        "step_1_detail": "Red(3.3V) Black(GND) Yellow(SWDIO) Green(SWCLK) — F/F",
        "step_2": "✌️ Step 2: Plug debugger into USB",
        "step_3": "🤟 Step 3: Connect wires (match colors)",
        "step_4": "🖐️ Step 4: Power the board (ST-Link can supply power)",
        "step_5": "🖐️ Step 5: Check indicator lights",
        "checklist": ["☑ ST-Link red LED on", "☑ Board power LED on", "☑ All wires secure"],
        "peripheral_label": "Peripheral",
        "pin_label": "Pin",
        "connect_to": "→",
        "gnd": "GND",
        "vcc": "3.3V",
        "resistor": "Resistor",
        "led_long": "Anode(+)",
        "code_hint": "Example Code",
        "generated_by": "Generated by keil-wiring-diagram.py",
    }
}


# ═══════════════════════════════════════════════
# 3. SVG 基础组件
# ═══════════════════════════════════════════════

COMPONENTS = []  # 器材列表

def svg_header(title, w, h, lang="zh"):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <rect width="{w}" height="{h}" fill="#fafafa"/>
  <text x="{w//2}" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#333">{title}</text>
'''

def svg_footer():
    return '</svg>\n'

def draw_warning_box(x, y, w, h, lines, lang="zh"):
    """绘制警告框"""
    t = T[lang]
    svg = f'''
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff3e0" stroke="#ff9800" stroke-width="1.5"/>
    <text x="{x+10}" y="{y+20}" font-size="11" font-weight="bold" fill="#e65100">{t["warning_title"]}</text>'''
    for i, line in enumerate(lines):
        svg += f'''
    <text x="{x+10}" y="{y+38+i*16}" font-size="10" fill="#e65100">{line}</text>'''
    return svg

def draw_debugger_box(x, y, name, pin_map, lang="zh"):
    """绘制调试器框图"""
    t = T[lang]
    pin_labels = {"SWCLK": t["pin_top_view"], "SWDIO": "", "GND": "", "3.3V": ""}
    
    h = 60 + len(pin_map) * 30 + 20
    svg = f'''
    <rect x="{x}" y="{y}" width="220" height="{h}" rx="10" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/>
    <text x="{x+110}" y="{y+25}" text-anchor="middle" font-size="14" font-weight="bold" fill="#1565c0">{name}</text>
    <rect x="{x+15}" y="{y+35}" width="190" height="22" rx="4" fill="#ffcdd2"/>
    <text x="{x+110}" y="{y+51}" text-anchor="middle" font-size="10" fill="#c62828">{t["insert_usb"]}</text>
    <rect x="{x+30}" y="{y+65}" width="160" height="{h-80}" rx="6" fill="white" stroke="#333" stroke-width="1"/>
    <text x="{x+110}" y="{y+82}" text-anchor="middle" font-size="10" font-weight="bold" fill="#333">{t["pin_top_view"]}</text>'''
    
    colors = {"SWCLK": "#4caf50", "SWDIO": "#2196f3", "GND": "#000", "3.3V": "#f44336",
              "TMS": "#2196f3", "TCK": "#4caf50", "TDI": "#9c27b0", "TDO": "#ff9800",
              "nTRST": "#795548", "TX": "#00bcd4", "RX": "#ff5722"}
    
    for i, (pin_name, pin_color_name) in enumerate(pin_map.items()):
        color = colors.get(pin_name, "#666")
        cy = y + 100 + i * 28
        svg += f'''
    <circle cx="{x+50}" cy="{cy}" r="9" fill="{color}"/>
    <text x="{x+50}" y="{cy+4}" text-anchor="middle" font-size="7" fill="white" font-weight="bold">{i+1}</text>
    <text x="{x+68}" y="{cy+4}" font-size="10" fill="#333">{pin_name}</text>
    <text x="{x+160}" y="{cy+4}" text-anchor="end" font-size="9" fill="{color}">● {pin_color_name}</text>'''
    
    svg += f'''
    <rect x="{x+30}" y="{y+h-20}" width="160" height="14" rx="3" fill="#eee"/>
    <text x="{x+110}" y="{y+h-10}" text-anchor="middle" font-size="8" fill="#666">{t["usb_up"]}</text>'''
    return svg, h


# ═══════════════════════════════════════════════
# 4. 外设渲染器
# ═══════════════════════════════════════════════

def parse_peripherals(periph_str: str) -> list:
    """解析外设参数字符串，返回 [(type, pin), ...]
    支持格式: "LED:PB0" "LED:PB0,OLED:I2C1,Servo:PA0,Button:PE4,UART:PA9-PA10"
    """
    if not periph_str:
        return []
    result = []
    for item in periph_str.split(","):
        item = item.strip()
        if ":" in item:
            parts = item.split(":")
            ptype = parts[0].strip().upper()
            pin = parts[1].strip() if len(parts) > 1 else ""
            result.append((ptype, pin))
        else:
            result.append((item.strip().upper(), ""))
    return result

def draw_peripheral(svg, ptype, pin, x, y, lang="zh"):
    """在 SVG 上绘制一个外设"""
    t = T[lang]
    pin_color = "#ffc107"
    
    if ptype == "LED":
        # LED + 电阻
        svg += f'''
    <!-- LED -->
    <rect x="{x}" y="{y}" width="55" height="30" rx="4" fill="#ffebee" stroke="#c62828" stroke-width="1.5"/>
    <polygon points="{x+10},{y+15} {x+35},{y+5} {x+35},{y+25}" fill="#e53935"/>
    <text x="{x+27}" y="{y-5}" text-anchor="middle" font-size="9" font-weight="bold" fill="#c62828">LED</text>
    <text x="{x+27}" y="{y+40}" text-anchor="middle" font-size="7" fill="#c62828">{t["led_long"]}</text>
    <!-- 电阻 -->
    <rect x="{x-35}" y="{y+5}" width="30" height="20" rx="3" fill="#fff9c4" stroke="#f9a825" stroke-width="1.5"/>
    <text x="{x-20}" y="{y+18}" text-anchor="middle" font-size="7" font-weight="bold" fill="#f57f17">220Ω</text>
    <!-- 标注引脚 -->
    <rect x="{x-70}" y="{y-12}" width="60" height="16" rx="3" fill="{pin_color}" stroke="#f57f17" stroke-width="1"/>
    <text x="{x-40}" y="{y-1}" text-anchor="middle" font-size="8" font-weight="bold" fill="#333">{pin}</text>'''
        # 导线
        svg += f'''
    <line x1="{x-35}" y1="{y+15}" x2="{x-10}" y2="{y+15}" stroke="#f44336" stroke-width="2"/>
    <line x1="{x-70}" y1="{y-4}" x2="{x-35}" y2="{y-4}" stroke="#ffc107" stroke-width="2"/>
    <line x1="{x-70}" y1="{y-4}" x2="{x-70}" y2="{y+15}" stroke="#ffc107" stroke-width="2"/>
    <line x1="{x-70}" y1="{y+15}" x2="{x-35}" y2="{y+15}" stroke="#ffc107" stroke-width="2"/>'''
        # 接地
        svg += f'''
    <line x1="{x+55}" y1="{y+15}" x2="{x+75}" y2="{y+15}" stroke="#000" stroke-width="2"/>
    <text x="{x+65}" y="{y+30}" text-anchor="middle" font-size="7" fill="#000">{t["gnd"]}</text>'''
    
    elif ptype == "BUTTON":
        svg += f'''
    <!-- Button -->
    <rect x="{x}" y="{y}" width="40" height="40" rx="4" fill="#e8eaf6" stroke="#283593" stroke-width="1.5"/>
    <rect x="{x+8}" y="{y+8}" width="24" height="24" rx="2" fill="#5c6bc0"/>
    <text x="{x+20}" y="{y+23}" text-anchor="middle" font-size="8" fill="white" font-weight="bold">BTN</text>
    <text x="{x+20}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#283593">Button</text>
    <rect x="{x-55}" y="{y+10}" width="50" height="16" rx="3" fill="{pin_color}" stroke="#f57f17" stroke-width="1"/>
    <text x="{x-30}" y="{y+22}" text-anchor="middle" font-size="8" font-weight="bold" fill="#333">{pin}</text>
    <line x1="{x-5}" y1="{y+18}" x2="{x-55}" y2="{y+18}" stroke="#ffc107" stroke-width="2"/>
    <line x1="{x+40}" y1="{y+18}" x2="{x+55}" y2="{y+18}" stroke="#f44336" stroke-width="2"/>
    <text x="{x+50}" y="{y+33}" text-anchor="middle" font-size="7" fill="#f44336">{t["vcc"]}</text>
    <line x1="{x-55}" y1="{y+30}" x2="{x-70}" y2="{y+30}" stroke="#000" stroke-width="1.5"/>
    <text x="{x-62}" y="{y+45}" text-anchor="middle" font-size="7" fill="#000">{t["gnd"]}</text>'''
    
    elif ptype == "SERVO":
        svg += f'''
    <!-- Servo -->
    <rect x="{x}" y="{y}" width="50" height="32" rx="5" fill="#fff3e0" stroke="#e65100" stroke-width="1.5"/>
    <text x="{x+25}" y="{y+14}" text-anchor="middle" font-size="7" fill="#e65100">SERVO</text>
    <text x="{x+25}" y="{y+26}" text-anchor="middle" font-size="6" fill="#bf360c">PWM</text>
    <text x="{x+25}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#e65100">Servo</text>
    <rect x="{x-55}" y="{y+6}" width="50" height="16" rx="3" fill="{pin_color}" stroke="#f57f17" stroke-width="1"/>
    <text x="{x-30}" y="{y+18}" text-anchor="middle" font-size="8" font-weight="bold" fill="#333">{pin}</text>
    <line x1="{x-5}" y1="{y+14}" x2="{x-55}" y2="{y+14}" stroke="#ffc107" stroke-width="2"/>
    <line x1="{x+50}" y1="{y+14}" x2="{x+65}" y2="{y+14}" stroke="#f44336" stroke-width="2"/>
    <text x="{x+55}" y="{y+28}" text-anchor="middle" font-size="7" fill="#f44336">{t["vcc"]}</text>
    <line x1="{x-55}" y1="{y+28}" x2="{x-70}" y2="{y+28}" stroke="#000" stroke-width="1.5"/>
    <text x="{x-62}" y="{y+42}" text-anchor="middle" font-size="7" fill="#000">{t["gnd"]}</text>'''
    
    elif ptype in ("BUZZER", "BEEP"):
        svg += f'''
    <!-- Buzzer -->
    <rect x="{x}" y="{y+5}" width="40" height="30" rx="5" fill="#fce4ec" stroke="#880e4f" stroke-width="1.5"/>
    <text x="{x+20}" y="{y+24}" text-anchor="middle" font-size="8" font-weight="bold" fill="#880e4f">BZ</text>
    <text x="{x+20}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#880e4f">Buzzer</text>
    <rect x="{x-55}" y="{y+10}" width="50" height="16" rx="3" fill="{pin_color}" stroke="#f57f17" stroke-width="1"/>
    <text x="{x-30}" y="{y+22}" text-anchor="middle" font-size="8" font-weight="bold" fill="#333">{pin}</text>
    <line x1="{x-5}" y1="{y+20}" x2="{x-55}" y2="{y+20}" stroke="#ffc107" stroke-width="2"/>
    <line x1="{x+40}" y1="{y+20}" x2="{x+55}" y2="{y+20}" stroke="#000" stroke-width="1.5"/>
    <text x="{x+50}" y="{y+34}" text-anchor="middle" font-size="7" fill="#000">{t["gnd"]}</text>'''
    
    elif ptype == "OLED":
        svg += f'''
    <!-- OLED I2C -->
    <rect x="{x}" y="{y}" width="50" height="40" rx="4" fill="#e8f5e9" stroke="#1b5e20" stroke-width="1.5"/>
    <text x="{x+25}" y="{y+15}" text-anchor="middle" font-size="7" font-weight="bold" fill="#1b5e20">OLED</text>
    <text x="{x+25}" y="{y+28}" text-anchor="middle" font-size="6" fill="#2e7d32">I²C</text>
    <text x="{x+25}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#1b5e20">OLED 屏</text>
    <text x="{x+25}" y="{y+48}" text-anchor="middle" font-size="7" fill="#4caf50">{pin}: SCL/SDA</text>
    <rect x="{x-55}" y="{y+10}" width="50" height="16" rx="3" fill="#9c27b0" stroke="#7b1fa2" stroke-width="1"/>
    <text x="{x-30}" y="{y+22}" text-anchor="middle" font-size="7" font-weight="bold" fill="white">SCL</text>
    <line x1="{x-5}" y1="{y+10}" x2="{x-55}" y2="{y+18}" stroke="#9c27b0" stroke-width="2"/>
    <line x1="{x+50}" y1="{y+10}" x2="{x+65}" y2="{y+10}" stroke="#f44336" stroke-width="1.5"/>
    <text x="{x+55}" y="{y+24}" text-anchor="middle" font-size="7" fill="#f44336">{t["vcc"]}</text>
    <line x1="{x-55}" y1="{y+30}" x2="{x-70}" y2="{y+30}" stroke="#000" stroke-width="1.5"/>
    <text x="{x-62}" y="{y+44}" text-anchor="middle" font-size="7" fill="#000">{t["gnd"]}</text>'''
    
    elif ptype in ("I2C", "I2C1", "I2C2", "I2C3"):
        svg += f'''
    <!-- I2C 总线 -->
    <rect x="{x}" y="{y}" width="70" height="40" rx="5" fill="#f3e5f5" stroke="#7b1fa2" stroke-width="1.5"/>
    <text x="{x+35}" y="{y+16}" text-anchor="middle" font-size="8" font-weight="bold" fill="#7b1fa2">I²C Bus</text>
    <text x="{x+35}" y="{y+32}" text-anchor="middle" font-size="7" fill="#9c27b0">{pin}</text>
    <text x="{x+35}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#7b1fa2">{pin}</text>'''
        # SCL + SDA 线
        svg += f'''
    <line x1="{x-30}" y1="{y+10}" x2="{x}" y2="{y+10}" stroke="#9c27b0" stroke-width="2"/>
    <line x1="{x-30}" y1="{y+25}" x2="{x}" y2="{y+25}" stroke="#9c27b0" stroke-width="2" stroke-dasharray="3,3"/>
    <text x="{x-45}" y="{y+14}" text-anchor="middle" font-size="7" fill="#9c27b0">SCL</text>
    <text x="{x-45}" y="{y+29}" text-anchor="middle" font-size="7" fill="#9c27b0">SDA</text>'''
    
    elif ptype in ("SPI", "SPI1", "SPI2"):
        svg += f'''
    <!-- SPI 总线 -->
    <rect x="{x}" y="{y}" width="70" height="50" rx="5" fill="#e1f5fe" stroke="#0277bd" stroke-width="1.5"/>
    <text x="{x+35}" y="{y+16}" text-anchor="middle" font-size="8" font-weight="bold" fill="#0277bd">SPI Bus</text>
    <text x="{x+35}" y="{y+32}" text-anchor="middle" font-size="7" fill="#0288d1">{pin}</text>
    <text x="{x+35}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#0277bd">{pin}</text>
    <text x="{x+35}" y="{y+44}" text-anchor="middle" font-size="7" fill="#666">CS/SCK/MOSI/MISO</text>'''
    
    elif ptype in ("UART", "USART1", "USART2", "USART3", "UART4"):
        svg += f'''
    <!-- UART -->
    <rect x="{x}" y="{y}" width="60" height="45" rx="4" fill="#fff8e1" stroke="#f57f17" stroke-width="1.5"/>
    <text x="{x+30}" y="{y+15}" text-anchor="middle" font-size="8" font-weight="bold" fill="#e65100">{ptype}</text>
    <text x="{x+30}" y="{y+28}" text-anchor="middle" font-size="7" fill="#f57f17">{pin}</text>
    <text x="{x+30}" y="{y+40}" text-anchor="middle" font-size="7" fill="#666">TX / RX</text>
    <text x="{x+30}" y="{y-5}" text-anchor="middle" font-size="8" font-weight="bold" fill="#e65100">{pin}</text>'''
        # 交叉线
        svg += f'''
    <line x1="{x-30}" y1="{y+15}" x2="{x}" y2="{y+15}" stroke="#00bcd4" stroke-width="2"/>
    <line x1="{x-30}" y1="{y+30}" x2="{x}" y2="{y+30}" stroke="#ff5722" stroke-width="2"/>
    <text x="{x-45}" y="{y+19}" text-anchor="middle" font-size="7" fill="#00bcd4">TX</text>
    <text x="{x-45}" y="{y+34}" text-anchor="middle" font-size="7" fill="#ff5722">RX</text>'''
    
    return svg


# ═══════════════════════════════════════════════
# 5. 调试模式渲染器
# ═══════════════════════════════════════════════

DEBUGGER_PINS = {
    "stlink": {"SWCLK": "SWCLK", "SWDIO": "SWDIO", "GND": "GND", "3.3V": "3.3V"},
    "jlink_swd": {"SWCLK": "SWCLK", "SWDIO": "SWDIO", "GND": "GND", "3.3V": "3.3V"},
    "jlink_jtag": {"TMS": "TMS", "TCK": "TCK", "TDI": "TDI", "TDO": "TDO", "nTRST": "nTRST", "GND": "GND", "3.3V": "3.3V"},
    "ulink": {"SWCLK": "SWCLK", "SWDIO": "SWDIO", "GND": "GND", "3.3V": "3.3V"},
}

def draw_debug_wiring(svg, mcu_info, debug_mode, x, y, lang):
    """绘制调试器接线"""
    t = T[lang]
    
    if debug_mode == "swd":
        pins = {"SWCLK": "SWCLK", "SWDIO": "SWDIO", "GND": "GND", "3.3V": "3.3V"}
        dbg_name = t["stlink"]
    elif debug_mode == "jtag":
        pins = {"TMS": "TMS", "TCK": "TCK", "TDI": "TDI", "TDO": "TDO", "GND": "GND", "3.3V": "3.3V"}
        dbg_name = t["jlink"]
    elif debug_mode == "uart":
        pins = {"TX": "TX", "RX": "RX", "GND": "GND", "3.3V": "3.3V"}
        dbg_name = "USB-UART"
    else:
        pins = {"SWCLK": "SWCLK", "SWDIO": "SWDIO", "GND": "GND", "3.3V": "3.3V"}
        dbg_name = t["stlink"]
    
    # 绘制调试器
    dbg_svg, dbg_h = draw_debugger_box(x, y, dbg_name, pins, lang)
    svg += dbg_svg
    
    # 计算目标板位置
    target_x = x + 280
    target_y = y
    
    # 提取 MCU 的调试引脚
    if debug_mode == "swd":
        mcu_swd = mcu_info.swd_pins
        wire_pins = [
            ("SWCLK", mcu_swd.get("SWCLK", "?"), "#4caf50"),
            ("SWDIO", mcu_swd.get("SWDIO", "?"), "#2196f3"),
            ("GND", "GND", "#000"),
            ("3.3V", "3.3V", "#f44336"),
        ]
    elif debug_mode == "jtag":
        mcu_jtag = mcu_info.jtag_pins
        wire_pins = [
            ("TCK", mcu_jtag.get("TCK", "?"), "#4caf50"),
            ("TMS", mcu_jtag.get("TMS", "?"), "#2196f3"),
            ("TDI", mcu_jtag.get("TDI", "?"), "#9c27b0"),
            ("TDO", mcu_jtag.get("TDO", "?"), "#ff9800"),
            ("GND", "GND", "#000"),
            ("3.3V", "3.3V", "#f44336"),
        ]
    else:  # uart
        wire_pins = [
            ("TX", mcu_info.uart_pins.get(list(mcu_info.uart_pins.keys())[0], "?"), "#00bcd4"),
            ("RX", mcu_info.uart_pins.get(list(mcu_info.uart_pins.keys())[1], "?"), "#ff5722"),
            ("GND", "GND", "#000"),
            ("3.3V", "3.3V", "#f44336"),
        ]
    
    # 目标板区域
    target_h = max(dbg_h, 80 + len(wire_pins) * 28)
    wire_colors = [c for (_, _, c) in wire_pins]
    wire_labels = [f"{s} ({p})" for (s, p, _) in wire_pins]
    
    svg += f'''
    <rect x="{target_x}" y="{target_y}" width="200" height="{target_h}" rx="10" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
    <text x="{target_x+100}" y="{target_y+25}" text-anchor="middle" font-size="14" font-weight="bold" fill="#2e7d32">{mcu_info.model}</text>
    <text x="{target_x+100}" y="{target_y+45}" text-anchor="middle" font-size="9" fill="#555">{mcu_info.core} | {mcu_info.package}</text>
    <text x="{target_x+100}" y="{target_y+62}" text-anchor="middle" font-size="10" font-weight="bold" fill="#333">{t["key_pins"]}</text>'''
    
    for i, (sname, mpin, color) in enumerate(wire_pins):
        cy = target_y + 78 + i * 26
        svg += f'''
    <circle cx="{target_x+50}" cy="{cy}" r="8" fill="{color}"/>
    <text x="{target_x+65}" y="{cy+4}" font-size="9" fill="#333">{mpin}</text>
    <text x="{target_x+175}" y="{cy+4}" text-anchor="end" font-size="8" fill="{color}">{sname}</text>'''
    
    # 导线（从调试器到目标板）
    for i, (sname, mpin, color) in enumerate(wire_pins):
        src_y = y + 100 + i * 28
        dst_y = target_y + 78 + i * 26
        # 根据信号的顺序决定交错路径
        offset = (i % 2) * 30
        svg += f'''
    <line x1="{x+220}" y1="{src_y}" x2="{x+250}" y2="{src_y + offset}" stroke="{color}" stroke-width="2.5" stroke-dasharray="6,3"/>
    <line x1="{x+250}" y1="{src_y + offset}" x2="{x+270}" y2="{dst_y}" stroke="{color}" stroke-width="2.5" stroke-dasharray="6,3"/>
    <line x1="{x+270}" y1="{dst_y}" x2="{target_x+50}" y2="{dst_y}" stroke="{color}" stroke-width="2.5" stroke-dasharray="6,3"/>'''
    
    return svg, max(dbg_h, target_h)


# ═══════════════════════════════════════════════
# 6. 页面布局引擎（主生成函数）
# ═══════════════════════════════════════════════

def generate_wiring_diagram(mcu_model: str, peripherals_str: str = "",
                            debug_mode: str = "swd", lang: str = "zh",
                            output_path: Optional[str] = None) -> str:
    """生成完整接线图 SVG"""
    t = T[lang]
    
    # 查找 MCU
    mcu = MCU_DB.get(mcu_model)
    if not mcu:
        # 尝试近似匹配
        for key in MCU_DB:
            if mcu_model.upper() in key.upper():
                mcu = MCU_DB[key]
                break
        if not mcu:
            mcu = MCU_DB["STM32F103C8"]  # 默认
    
    periphs = parse_peripherals(peripherals_str)
    
    # 计算画布大小（动态）
    base_w = 650
    base_h = 200
    
    # 调试器区域高度
    pin_count = 4 if debug_mode in ("swd", "uart") else 6
    debug_h = 120 + pin_count * 28
    
    # 外设区域
    periph_h = 0
    if periphs:
        periph_h = 80 + (len(periphs) * 80)
    
    canvas_w = max(base_w, 800)
    canvas_h = base_h + debug_h + periph_h
    
    # 标题
    title = f"{mcu.model} — {t['title_debug']}"
    if periphs:
        title += f" + {t['title_peripherals']}"
    
    svg = svg_header(title, canvas_w, canvas_h, lang)
    
    # 1. 调试器接线图
    y_offset = 50
    svg, dbg_height = draw_debug_wiring(svg, mcu, debug_mode, 30, y_offset, lang)
    
    # 2. 警告框
    y_offset += dbg_height + 20
    svg += draw_warning_box(30, y_offset, canvas_w - 60, 70, 
                           [t["warning_1"], t["warning_2"], t["warning_3"]], lang)
    
    # 3. 外设接线
    if periphs:
        y_offset += 90
        svg += f'''
    <rect x="30" y="{y_offset}" width="{canvas_w-60}" height="30" rx="5" fill="#1565c0"/>
    <text x="{canvas_w//2}" y="{y_offset+20}" text-anchor="middle" font-size="13" font-weight="bold" fill="white">{t["peripheral_list"]} ({len(periphs)})</text>'''
        
        y_offset += 45
        per_x = 80
        for ptype, pin in periphs:
            svg = draw_peripheral(svg, ptype, pin, per_x, y_offset, lang)
            per_x += 120
        
        # 外设总体说明
        y_offset += max(80, len(periphs) * 80) + 10
        svg += f'''
    <rect x="30" y="{y_offset}" width="{canvas_w-60}" height="30" rx="5" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
    <text x="{canvas_w//2}" y="{y_offset+20}" text-anchor="middle" font-size="10" fill="#1565c0">
      {t["peripheral_label"]} → {t["pin_label"]} → {mcu.model}
    </text>'''
        y_offset += 45
    
    # 4. MCU 引脚图
    if mcu.pinout_svg:
        y_offset += 10
        svg += f'''
    <rect x="30" y="{y_offset}" width="{canvas_w-60}" height="170" rx="8" fill="#f9fbe7" stroke="#827717" stroke-width="1"/>
    <text x="{canvas_w//2}" y="{y_offset+20}" text-anchor="middle" font-size="12" font-weight="bold" fill="#827717">{mcu.model} — Pinout</text>'''
        # 嵌入 MCU 引脚子图
        for line in mcu.pinout_svg.split('\n'):
            if '<g' in line or '<text' in line or '<rect' in line:
                # 调整坐标偏移
                adjusted = line
                if 'x=' in line and 'transform' not in line:
                    svg += f'    {adjusted}\n'
                else:
                    svg += f'    {line}\n'
    
    # 底部信息
    svg += f'''
    <text x="{canvas_w//2}" y="{canvas_h-10}" text-anchor="middle" font-size="8" fill="#999">{t["generated_by"]}</text>'''
    
    svg += svg_footer()
    
    # 写文件
    if output_path:
        Path(output_path).write_text(svg, encoding="utf-8")
        print(f"[✓] 已生成: {output_path}  ({len(svg)//1024} KB)")
    else:
        out_dir = Path(__file__).parent / "wiring-diagrams"
        out_dir.mkdir(exist_ok=True)
        
        # 构造文件名
        fname = f"wiring_{mcu_model}"
        if debug_mode != "swd":
            fname += f"_{debug_mode}"
        if periphs:
            per_suffix = "_".join([f"{p[0]}_{p[1]}" for p in periphs[:3]])
            fname += f"_{per_suffix}"
        if lang != "zh":
            fname += f"_{lang}"
        fname += ".svg"
        
        path = out_dir / fname
        path.write_text(svg, encoding="utf-8")
        print(f"[✓] 已生成: {path}  ({len(svg)//1024} KB)")
    
    return svg


# ═══════════════════════════════════════════════
# 7. 器材选购指南
# ═══════════════════════════════════════════════

def generate_component_guide(lang="zh", output_path=None):
    """生成器材选购 SVG"""
    t = T[lang]
    w, h = 700, 600
    
    svg = svg_header(t["title_components"], w, h, lang)
    
    # 标题栏
    svg += f'''
    <rect x="30" y="50" width="{w-60}" height="35" rx="5" fill="#1565c0"/>
    <text x="{w//2}" y="73" text-anchor="middle" font-size="14" font-weight="bold" fill="white">{t["component_title"]}</text>'''
    
    # 表头
    svg += f'''
    <rect x="30" y="85" width="280" height="25" rx="3" fill="#e3f2fd"/>
    <text x="170" y="103" text-anchor="middle" font-size="11" font-weight="bold" fill="#1565c0">{t["component_col1"]}</text>
    <rect x="310" y="85" width="{w-340}" height="25" rx="3" fill="#e3f2fd"/>
    <text x="{170+280}" y="103" text-anchor="middle" font-size="11" font-weight="bold" fill="#1565c0">{t["component_col2"]}</text>'''
    
    if lang == "zh":
        rows = [
            ("① STM32 最小系统板", "¥15-25 | STM32F103C8T6 蓝色药丸板 | 推荐买带排针的"),
            ("② ST-Link V2 调试器", "¥10-20 | SWD 接口 | 注意买正版兼容版"),
            ("③ 杜邦线 (母对母)", "¥2-5  | 至少 4 根: 红/黑/黄/绿各一根"),
            ("④ USB 数据线", "¥5-10  | Micro-USB 或 Type-C | 要能传数据的"),
            ("⑤ 面包板 830孔", "¥5-10  | 可选，做复杂电路时用"),
            ("⑥ LED + 电阻套装", "¥2-5   | 5mm LED × 若干 + 220Ω/1kΩ 电阻"),
            ("⑦ 跳线 (公对公)", "¥3-5   | 面包板使用时需要"),
        ]
    else:
        rows = [
            ("① STM32 Dev Board", "$2-4 | STM32F103C8T6 Blue Pill | Pre-soldered headers"),
            ("② ST-Link V2 Debugger", "$1.5-3 | SWD interface | Get genuine-compatible"),
            ("③ Dupont Wires (F/F)", "$0.5-1 | At least 4: Red/Black/Yellow/Green"),
            ("④ USB Data Cable", "$1-2 | Micro-USB or Type-C | Data-capable"),
            ("⑤ Breadboard 830pt", "$1-2 | Optional, for complex circuits"),
            ("⑥ LED + Resistor kit", "$0.5-1 | 5mm LEDs + 220Ω/1kΩ resistors"),
            ("⑦ Jumper Wires (M/M)", "$0.5-1 | Needed with breadboard"),
        ]
    
    y = 125
    for i, (item, desc) in enumerate(rows):
        fill = "#fff" if i % 2 == 0 else "#f5f5f5"
        svg += f'''
    <rect x="30" y="{y}" width="280" height="28" fill="{fill}"/>
    <text x="170" y="{y+18}" text-anchor="middle" font-size="10" fill="#333">{item}</text>
    <rect x="310" y="{y}" width="{w-340}" height="28" fill="{fill}"/>
    <text x="{170+280}" y="{y+18}" text-anchor="middle" font-size="9" fill="#666">{desc}</text>'''
        y += 28
    
    # 核心提示
    y += 10
    svg += f'''
    <rect x="30" y="{y}" width="{w-60}" height="30" rx="5" fill="#e8f5e9"/>
    <text x="{w//2}" y="{y+20}" text-anchor="middle" font-size="11" font-weight="bold" fill="#2e7d32">{t["core_equipment"]}</text>'''
    
    # 选购贴士
    y += 50
    tips_h = 30 + len(t["tips"]) * 22
    svg += f'''
    <rect x="30" y="{y}" width="{w-60}" height="{tips_h}" rx="8" fill="#fff3e0" stroke="#ff9800" stroke-width="1.5"/>
    <text x="50" y="{y+22}" font-size="13" font-weight="bold" fill="#e65100">{t["tips_title"]}</text>'''
    for i, tip in enumerate(t["tips"]):
        svg += f'''
    <text x="50" y="{y+45+i*22}" font-size="10" fill="#795548">{tip}</text>'''
    
    # 警告
    y += tips_h + 10
    svg += f'''
    <rect x="30" y="{y}" width="{w-60}" height="45" rx="8" fill="#ffebee" stroke="#c62828" stroke-width="1.5"/>
    <text x="50" y="{y+20}" font-size="12" font-weight="bold" fill="#c62828">{t["warning_buy"]}</text>
    <text x="50" y="{y+38}" font-size="10" fill="#c62828">{t["warning_buy_detail"]}</text>'''
    
    svg += svg_footer()
    
    if output_path:
        Path(output_path).write_text(svg, encoding="utf-8")
        print(f"[✓] 已生成: {output_path}")
    else:
        out_dir = Path(__file__).parent / "wiring-diagrams"
        out_dir.mkdir(exist_ok=True)
        path = out_dir / f"component-guide_{lang}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"[✓] 已生成: {path}")
    
    return svg


# ═══════════════════════════════════════════════
# 8. .uvprojx 解析器（自动探测 MCU）
# ═══════════════════════════════════════════════

def detect_mcu_from_project(project_path: str) -> Optional[str]:
    """从 .uvprojx 文件中提取 MCU 型号"""
    try:
        tree = ET.parse(project_path)
        root = tree.getroot()
        # 搜索 Device 标签
        for elem in root.iter():
            if elem.tag == "Device" and elem.text:
                return elem.text.strip()
            # 搜索 TDeviceTypeName
            if elem.tag == "TDeviceTypeName" and elem.text:
                return elem.text.strip()
    except Exception as e:
        print(f"[!] 解析项目文件失败: {e}")
    return None


# ═══════════════════════════════════════════════
# 9. CLI 入口
# ═══════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Keil 动态接线图生成器 — 支持 6+ MCU / 10+ 外设 / 中英双语",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python keil-wiring-diagram.py --mcu STM32F103C8 --peripherals "LED:PB0"
  python keil-wiring-diagram.py --mcu STM32F407VG --peripherals "LED:PE0,OLED:I2C1,Servo:PA0"
  python keil-wiring-diagram.py --mcu STM32F103C8 --debug jtag --lang en
  python keil-wiring-diagram.py --project my_project.uvprojx --peripherals "LED:PC13"
  python keil-wiring-diagram.py --list-mcus
  python keil-wiring-diagram.py --all
        """
    )
    
    parser.add_argument("--mcu", help="MCU 型号 (支持: " + ", ".join(MCU_DB.keys()) + ")")
    parser.add_argument("--peripherals", help="外设列表, 格式: TYPE:PIN,TYPE:PIN (如 LED:PB0,OLED:I2C1)")
    parser.add_argument("--debug", choices=["swd", "jtag", "uart"], default="swd", help="调试接口 (默认: swd)")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="语言 (默认: zh)")
    parser.add_argument("-o", "--output", help="输出 SVG 文件路径")
    parser.add_argument("--project", help="从 .uvprojx 文件读取 MCU 型号")
    parser.add_argument("--list-mcus", action="store_true", help="列出支持的 MCU")
    parser.add_argument("--list-peripherals", action="store_true", help="列出支持的外设")
    parser.add_argument("--all", action="store_true", help="生成所有组合")
    parser.add_argument("--guide", action="store_true", help="生成器材选购指南")
    
    args = parser.parse_args()
    
    # 列表模式
    if args.list_mcus:
        print("支持的 MCU 型号:")
        for key, mcu in MCU_DB.items():
            print(f"  {key:15s} → {mcu.model:20s} {mcu.core:15s} {mcu.package}")
        return
    
    if args.list_peripherals:
        print("支持的外设类型:")
        for pt in ["LED", "BUTTON", "SERVO", "BUZZER", "OLED", "I2C", "SPI", "UART"]:
            print(f"  {pt} — ", end="")
            if pt == "LED": print("引脚→220Ω→LED→GND")
            elif pt == "BUTTON": print("引脚→按钮→3.3V/GND")
            elif pt == "SERVO": print("PWM引脚控制舵机")
            elif pt == "BUZZER": print("引脚驱动蜂鸣器")
            elif pt == "OLED": print("I2C 接口 OLED 屏")
            elif pt == "I2C": print("I2C 总线 (SCL/SDA)")
            elif pt == "SPI": print("SPI 总线 (CS/SCK/MOSI/MISO)")
            elif pt == "UART": print("串口 (TX/RX)")
        return
    
    # 自动探测 MCU
    mcu_model = args.mcu
    if args.project:
        detected = detect_mcu_from_project(args.project)
        if detected:
            print(f"[→] 从项目文件 {args.project} 检测到 MCU: {detected}")
            mcu_model = detected
        else:
            print(f"[!] 未从项目文件中检测到 MCU，使用 --mcu 参数指定")
    
    if not mcu_model and not args.all and not args.guide:
        print("[!] 请指定 --mcu 型号 或 --project 项目文件")
        print("    可用型号:", ", ".join(MCU_DB.keys()))
        parser.print_help()
        return
    
    # ── 器材选购指南 ──
    if args.guide:
        generate_component_guide(args.lang, args.output)
        return
    
    # ── 全生成模式 ──
    if args.all:
        out_dir = Path(__file__).parent / "wiring-diagrams"
        out_dir.mkdir(exist_ok=True)
        
        # 每个 MCU 生成默认接线图
        for mcu_key in MCU_DB:
            generate_wiring_diagram(mcu_key, "", "swd", "zh")
            generate_wiring_diagram(mcu_key, "", "swd", "en")
        
        # 生成器材指南
        generate_component_guide("zh")
        generate_component_guide("en")
        
        # 生成带外设的示例
        generate_wiring_diagram("STM32F103C8", "LED:PB0", "swd", "zh")
        generate_wiring_diagram("STM32F103C8", "LED:PB0,BUTTON:PA0", "swd", "zh")
        generate_wiring_diagram("STM32F407VG", "LED:PE0,OLED:I2C1", "swd", "zh")
        generate_wiring_diagram("STM32F411CE", "LED:PC13,SERVO:PA0", "swd", "zh")
        generate_wiring_diagram("STM32F103C8", "UART:PA9-PA10", "uart", "zh")
        
        print(f"\n✅ 全部生成完毕，文件位于: {out_dir}")
        print(f"   共 {len(list(out_dir.glob('*.svg')))} 个 SVG 文件")
        return
    
    # ── 单次生成 ──
    # 匹配 MCU
    matched_mcu = None
    for key in MCU_DB:
        if mcu_model.upper() in key.upper():
            matched_mcu = key
            break
    if not matched_mcu and mcu_model in MCU_DB:
        matched_mcu = mcu_model
    
    if not matched_mcu:
        print(f"[!] 未找到 MCU 型号 '{mcu_model}'")
        print("    可用型号:", ", ".join(MCU_DB.keys()))
        return
    
    generate_wiring_diagram(matched_mcu, args.peripherals or "", 
                           args.debug, args.lang, args.output)


if __name__ == "__main__":
    main()