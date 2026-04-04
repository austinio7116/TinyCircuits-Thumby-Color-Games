"""Process Galaga spritesheet into RGB565 BMP assets for Thumbalaga.

Source: /tmp/Arcade - Galaga - Miscellaneous - General Sprites.png (458x216)

Generates:
  player.bmp          — 12x12 player ship (S1 row 0 col 6, facing down)
  player_captured.bmp  — 12x12 red captured player (S1 row 1 col 6)
  life_icon.bmp        — 6x6 small player ship for lives display
  enemies.bmp          — 96x240 (8 frames x 20 rows) full enemy sprite sheet
  explosion.bmp        — 60x12 (5 frames x 12x12) enemy explosions (S3 top)
  player_explosion.bmp — 48x12 (4 frames x 12x12) player explosions (S2 top)
  badge_narrow.bmp     — 10x10 (2 frames x 5x10) stage markers: 1-flag, 5-badge
  badge_shields.bmp    — 32x8 (4 frames x 8x8) stage shields: 10, 20, 30, 50
  icon.bmp             — 64x64 launcher icon (from logo PNG if available)

Enemy sheet row order (matches constants.py):
  0=Bee, 1=Butterfly, 2=Boss, 3=BossHit,
  4=Scorpion, 5=Bosconian, 6=Galaxian,
  7=Dragonfly, 8=Satellite, 9=Enterprise,
  10=Boss dying, 11=Bee dying, 12=Butterfly dying,
  13=Scorpion dying, 14=Bosconian dying, 15=Galaxian dying,
  16=Dragonfly dying, 17=Enterprise dying,
  18=Bee pre-transform pulsating, 19=Butterfly pre-transform pulsating
  (Satellite dying = frames 3-5 of row 8, no separate row needed)

Spritesheet source mapping:
  Section 1 (x=1-142, 18px grid): rows 0-11
    Row 0: Player (white), Row 1: Player captured (red)
    Row 2: Boss normal, Row 3: Boss hit
    Row 4: Butterfly/Goei, Row 5: Bee/Zako
    Row 6: Scorpion, Row 7: Bosconian, Row 8: Galaxian
    Row 9: Dragonfly, Row 10: Satellite, Row 11: Enterprise

  Section 2 (x=145-286, 18px grid, y starts at 37): rows 0-9
    Row 0: Boss dying, Row 1: Butterfly dying, Row 2: Bee dying
    Row 3: Scorpion dying, Row 4: Bosconian dying, Row 5: Galaxian dying
    Row 6: Dragonfly dying, Row 7: Enterprise dying
    Row 8: Bee pre-transform pulsating, Row 9: Butterfly pre-transform pulsating

  Section 2 top (y=1-32): 4x 32x32 player explosions (white/cyan/red)
  Section 3 top (y=1-32, x=289+): 5x 32x32 enemy explosions (yellow/red)
  Section 3 bottom (y=170+): stage badges
"""

import struct
import os
from PIL import Image

SRC = '/tmp/Arcade - Galaga - Miscellaneous - General Sprites.png'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
BG = (64, 64, 64)
S = 12  # main sprite size
MAGENTA_565 = ((0xF8) << 8) | ((0x00) << 3) | (0x1F)


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def convert_pixel(r, g, b, a):
    if (r, g, b) == BG or (r, g, b) == (0, 0, 0) or a == 0:
        return MAGENTA_565
    return rgb565(r, g, b)


def write_bmp(filename, width, height, pixels):
    """Write 16-bit RGB565 BMP with BI_BITFIELDS, bottom-up."""
    row_size = width * 2
    padding = (4 - (row_size % 4)) % 4
    padded_row_size = row_size + padding
    pixel_data_size = padded_row_size * height
    header_size = 14 + 40 + 12
    file_size = header_size + pixel_data_size
    data = bytearray()
    data += struct.pack('<2sIHHI', b'BM', file_size, 0, 0, header_size)
    data += struct.pack('<IiiHHIIiiII',
        40, width, height, 1, 16, 3, pixel_data_size, 0, 0, 0, 0)
    data += struct.pack('<III', 0xF800, 0x07E0, 0x001F)
    for row in range(height - 1, -1, -1):
        for col in range(width):
            data += struct.pack('<H', pixels[row * width + col] & 0xFFFF)
        data += b'\x00' * padding
    with open(filename, 'wb') as f:
        f.write(data)


def extract_scaled(img, x, y, src_w, src_h, dst_w, dst_h):
    """Extract region, scale, convert bg/black to magenta."""
    cell = img.crop((x, y, x + src_w, y + src_h))
    scaled = cell.resize((dst_w, dst_h), Image.NEAREST)
    return [convert_pixel(*scaled.getpixel((px, py)))
            for py in range(dst_h) for px in range(dst_w)]


def preview(name, w, h, data):
    pimg = Image.new('RGBA', (w, h))
    for py in range(h):
        for px in range(w):
            v = data[py * w + px]
            if v == MAGENTA_565:
                pimg.putpixel((px, py), (255, 0, 255, 0))
            else:
                r = ((v >> 11) & 0x1F) << 3
                g = ((v >> 5) & 0x3F) << 2
                b = (v & 0x1F) << 3
                pimg.putpixel((px, py), (r, g, b, 255))
    big = pimg.resize((w * 4, h * 4), Image.NEAREST)
    big.save(f"/tmp/preview_{name}.png")


# Grid helpers
def s1(col, row):
    """Section 1 sprite position (16x16, 18px grid from x=1, y=1)."""
    return (1 + col * 18, 1 + row * 18)

def s2(col, row):
    """Section 2 sprite position (16x16, 18px grid from x=145, y=37)."""
    return (145 + col * 18, 37 + row * 18)


# ====================================================================
img = Image.open(SRC).convert('RGBA')
print(f"Loaded {SRC}: {img.size}")
os.makedirs(OUT, exist_ok=True)

# ====================================================================
# PLAYER SHIP — S1 row 0, col 6 (facing down), 12x12
# ====================================================================
px, py = s1(6, 0)
player_px = extract_scaled(img, px, py, 16, 16, S, S)
write_bmp(f"{OUT}/player.bmp", S, S, player_px)
preview("player", S, S, player_px)
print("player.bmp (12x12)")

# ====================================================================
# PLAYER CAPTURED (red) — S1 row 1, col 6, 12x12
# ====================================================================
px, py = s1(6, 1)
captured_px = extract_scaled(img, px, py, 16, 16, S, S)
write_bmp(f"{OUT}/player_captured.bmp", S, S, captured_px)
print("player_captured.bmp (12x12)")

# ====================================================================
# LIFE ICON — S1 row 0, col 6, scaled to 6x6
# ====================================================================
px, py = s1(6, 0)
life_px = extract_scaled(img, px, py, 16, 16, 6, 6)
write_bmp(f"{OUT}/life_icon.bmp", 6, 6, life_px)
print("life_icon.bmp (6x6)")

# ====================================================================
# ENEMIES — 8 frames x 20 types = 96x240
# ====================================================================
FRAMES = 8

sprite_defs = [
    # Normal sprites
    (s1, 5, 8, "Bee"),              # 0: S1 Row 5 = Bee/Zako (blue/yellow)
    (s1, 4, 8, "Butterfly"),        # 1: S1 Row 4 = Butterfly/Goei (red/white)
    (s1, 2, 8, "Boss"),             # 2: S1 Row 2 = Boss normal (teal)
    (s1, 3, 8, "BossHit"),          # 3: S1 Row 3 = Boss hit (purple)
    (s1, 6, 7, "Scorpion"),         # 4: S1 Row 6
    (s1, 7, 7, "Bosconian"),        # 5: S1 Row 7
    (s1, 8, 7, "Galaxian"),         # 6: S1 Row 8
    (s1, 9, 7, "Dragonfly"),        # 7: S1 Row 9 (challenge)
    (s1, 10, 6, "Satellite"),       # 8: S1 Row 10 (challenge, frames 0-2 alive, 3-5 dying)
    (s1, 11, 7, "Enterprise"),      # 9: S1 Row 11 (challenge)
    # Hit/dying palettes
    (s2, 0, 8, "Boss dying"),       # 10: S2 Row 0
    (s2, 2, 8, "Bee dying"),        # 11: S2 Row 2 (matches S1 R5)
    (s2, 1, 8, "Butterfly dying"),  # 12: S2 Row 1 (matches S1 R4)
    (s2, 3, 7, "Scorpion dying"),   # 13: S2 Row 3
    (s2, 4, 7, "Bosconian dying"),  # 14: S2 Row 4
    (s2, 5, 7, "Galaxian dying"),   # 15: S2 Row 5
    (s2, 6, 7, "Dragonfly dying"),  # 16: S2 Row 6
    (s2, 7, 7, "Enterprise dying"), # 17: S2 Row 7
    # Pre-transform pulsating (one row per enemy type that can morph)
    (s2, 8, 6, "Bee pre-transform"),       # 18: S2 Row 8 (bee pulsation colors)
    (s2, 9, 6, "Butterfly pre-transform"), # 19: S2 Row 9 (butterfly pulsation colors)
]

sheet_w = FRAMES * S  # 96
sheet_h = len(sprite_defs) * S  # 240

enemy_pixels = []
for src_fn, src_row, ncols, name in sprite_defs:
    for py_idx in range(S):
        for col in range(FRAMES):
            actual_col = min(col, ncols - 1)
            x, y = src_fn(actual_col, src_row)
            cell = img.crop((x, y, x + 16, y + 16))
            scaled = cell.resize((S, S), Image.NEAREST)
            for px_idx in range(S):
                enemy_pixels.append(convert_pixel(*scaled.getpixel((px_idx, py_idx))))
    print(f"  {name}: row {src_row}, {ncols} frames")

write_bmp(f"{OUT}/enemies.bmp", sheet_w, sheet_h, enemy_pixels)
preview("enemies", sheet_w, sheet_h, enemy_pixels)
print(f"enemies.bmp ({sheet_w}x{sheet_h}) — {FRAMES} frames x {len(sprite_defs)} types")

# ====================================================================
# ENEMY EXPLOSIONS — 5 frames from S3 top (32x32 → 12x12)
# ====================================================================
exp_positions = [(289, 1), (323, 1), (357, 1), (391, 1), (425, 1)]
exp_strip = []
for py_idx in range(S):
    for ex, ey in exp_positions:
        cell = img.crop((ex, ey, ex + 32, ey + 32))
        scaled = cell.resize((S, S), Image.NEAREST)
        for px_idx in range(S):
            exp_strip.append(convert_pixel(*scaled.getpixel((px_idx, py_idx))))

exp_w = S * len(exp_positions)
write_bmp(f"{OUT}/explosion.bmp", exp_w, S, exp_strip)
preview("explosion", exp_w, S, exp_strip)
print(f"explosion.bmp ({exp_w}x{S}) — 5 frames")

# ====================================================================
# PLAYER EXPLOSIONS — 4 frames from S2 top (32x32 → 12x12, white/cyan/red)
# ====================================================================
pexp_positions = [(145, 1), (179, 1), (213, 1), (247, 1)]
pexp_strip = []
for py_idx in range(S):
    for ex, ey in pexp_positions:
        cell = img.crop((ex, ey, ex + 32, ey + 32))
        scaled = cell.resize((S, S), Image.NEAREST)
        for px_idx in range(S):
            pexp_strip.append(convert_pixel(*scaled.getpixel((px_idx, py_idx))))

pexp_w = S * len(pexp_positions)
write_bmp(f"{OUT}/player_explosion.bmp", pexp_w, S, pexp_strip)
preview("player_explosion", pexp_w, S, pexp_strip)
print(f"player_explosion.bmp ({pexp_w}x{S}) — 4 frames")

# ====================================================================
# STAGE BADGES — narrow markers (1-flag, 5-badge) and shields (10, 20, 30, 50)
# ====================================================================
# Narrow markers: 1-flag at x=307, 5-badge at x=317, both y=168-185
SW, SH = 5, 10
f1 = img.crop((307, 168, 314, 186)).resize((SW, SH), Image.NEAREST)
f5 = img.crop((317, 168, 326, 186)).resize((SW, SH), Image.NEAREST)

narrow_pixels = []
for py_idx in range(SH):
    for frame in [f1, f5]:
        for px_idx in range(SW):
            narrow_pixels.append(convert_pixel(*frame.getpixel((px_idx, py_idx))))

write_bmp(f"{OUT}/badge_narrow.bmp", SW * 2, SH, narrow_pixels)
print(f"badge_narrow.bmp ({SW*2}x{SH}) — 1-flag + 5-badge")

# Shields: 10, 20, 30, 50 at x=328, 346, 364, 382, y=170-185, 16x16 each → 8x8
SS = 8
shield_positions = [(328, 170), (346, 170), (364, 170), (382, 170)]
shield_pixels = []
for py_idx in range(SS):
    for sx, sy in shield_positions:
        cell = img.crop((sx, sy, sx + 16, sy + 16))
        scaled = cell.resize((SS, SS), Image.NEAREST)
        for px_idx in range(SS):
            shield_pixels.append(convert_pixel(*scaled.getpixel((px_idx, py_idx))))

write_bmp(f"{OUT}/badge_shields.bmp", SS * 4, SS, shield_pixels)
print(f"badge_shields.bmp ({SS*4}x{SS}) — 10, 20, 30, 50 shields")

# ====================================================================
# LAUNCHER ICON — 64x64 from logo PNG if available
# ====================================================================
logo_path = '/tmp/thumbalaga.png'
if os.path.exists(logo_path):
    logo = Image.open(logo_path).convert('RGBA')
    logo = logo.resize((64, 64), Image.LANCZOS)
    icon_pixels = []
    for y in range(64):
        for x in range(64):
            r, g, b, a = logo.getpixel((x, y))
            if a < 128:
                icon_pixels.append(0x0000)
            else:
                icon_pixels.append(rgb565(r, g, b))
    write_bmp(f"{OUT}/../icon.bmp", 64, 64, icon_pixels)
    print("icon.bmp (64x64)")
else:
    print(f"Skipping icon.bmp — {logo_path} not found")

print("\n=== DONE ===")
