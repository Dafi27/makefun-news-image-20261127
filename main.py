#!/usr/bin/env python3
"""News-image-20261127: draw a one-page newspaper front page summing up
Friday 27 November 2026 in world news, and write it to /output/entry.png.

Pure Python 3 standard library only: the canvas is a plain RGB bytearray,
text is drawn with a small built-in 5x7 bitmap font, and the PNG is encoded
by hand (zlib + struct). No network, no files read, no timestamps, no
randomness -- the two runs the grader makes write byte-identical output.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)
INK = (26, 26, 26)
NAVY = (20, 33, 61)
NAVY_LT = (31, 78, 121)
RED = (176, 42, 42)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
GREY = (90, 86, 78)
CARD = (255, 255, 255)
BLUE = (31, 78, 121)
TEAL = (18, 110, 105)
ORANGE = (214, 106, 28)
SKY = (176, 205, 224)
CLOUD = (96, 104, 112)
YELLOW = (242, 201, 76)

# ---------------------------------------------------------------- canvas
px = bytearray(PAPER[0:1] * 0)  # placeholder, replaced below
canvas = bytearray(W * H * 3)
for _i in range(W * H):
    canvas[_i * 3:_i * 3 + 3] = bytes(PAPER)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        canvas[o:o + 3] = bytes(c)


def rect(x, y, w, h, c):
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        o = (yy * W + x0) * 3
        canvas[o:o + len(row)] = row


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def circle(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_px(xx, yy, c)


def disc(cx, cy, r, c):
    circle(cx, cy, r, c)


def ring(cx, cy, r, c, t=3):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - t) ** 2 <= d2 <= r * r:
                set_px(xx, yy, c)


def line(x0, y0, x1, y1, c, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        rect(x - t // 2, y - t // 2, t, t, c)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def triangle(p1, p2, p3, c):
    # scanline fill
    pts = sorted([p1, p2, p3], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    for y in range(ay, cy + 1):
        xs = []
        for (x0, y0), (x1, y1) in (((ax, ay), (bx, by)),
                                   ((bx, by), (cx, cy)),
                                   ((ax, ay), (cx, cy))):
            if y0 == y1:
                continue
            if min(y0, y1) <= y <= max(y0, y1):
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
        if len(xs) >= 2:
            rect(int(min(xs)), y, int(max(xs)) - int(min(xs)) + 1, 1, c)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '#' = ink.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}

CHAR_W = 6  # 5 px glyph + 1 px gap, times scale


def text_w(s, scale):
    return len(s) * CHAR_W * scale - scale


def draw_char(x, y, ch, scale, c):
    g = FONT.get(ch, FONT['?'])
    for r, row in enumerate(g):
        for col, bit in enumerate(row):
            if bit == '1':
                rect(x + col * scale, y + r * scale, scale, scale, c)


def draw_text(x, y, s, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        if ch == '\n':
            continue
        draw_char(cx, y, ch, scale, c)
        cx += CHAR_W * scale
    return cx


def wrap_lines(s, scale, max_w):
    """Word-wrap an uppercased string to lines fitting max_w pixels."""
    words = s.upper().split(' ')
    lines, cur = [], ''
    for w_ in words:
        trial = (cur + ' ' + w_).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, scale, c, max_w, leading=None):
    """Draw wrapped paragraph; return y just below the last line."""
    lh = leading if leading is not None else 7 * scale + 4 * scale
    for ln in wrap_lines(s, scale, max_w):
        draw_text(x, y, ln, scale, c)
        y += lh
    return y

# ---------------------------------------------------------------- pictures
def icon_ballot(x, y):
    # ballot box with a paper going in and a red tick
    rect(x + 8, y + 58, 168, 92, NAVY)
    rect(x + 8, y + 58, 168, 12, NAVY_LT)
    rect(x, y + 44, 184, 16, (58, 74, 102))
    rect(x + 62, y + 48, 60, 8, INK)
    rect(x + 58, y - 6, 68, 56, WHITE)
    rect(x + 58, y - 6, 68, 56, INK)  # border via outline below
    rect(x + 60, y - 4, 64, 52, WHITE)
    line(x + 68, y + 22, x + 80, y + 38, RED, 5)
    line(x + 80, y + 38, x + 106, y + 2, RED, 5)
    disc(x + 150, y + 130, 10, GOLD)
    disc(x + 22, y + 130, 10, GOLD)


def icon_storm(x, y):
    # dark cloud, rain, lightning bolt
    disc(x + 40, y + 55, 34, CLOUD)
    disc(x + 85, y + 45, 40, CLOUD)
    disc(x + 125, y + 58, 30, CLOUD)
    rect(x + 12, y + 55, 140, 30, CLOUD)
    for i, rx in enumerate((30, 62, 94, 126)):
        line(x + rx, y + 100, x + rx - 8, y + 128, BLUE, 4)
    bolt = [(x + 88, y + 78), (x + 66, y + 128), (x + 82, y + 128),
            (x + 72, y + 158), (x + 102, y + 104), (x + 86, y + 104)]
    for i in range(len(bolt)):
        p, q = bolt[i], bolt[(i + 1) % len(bolt)]
        line(p[0], p[1], q[0], q[1], YELLOW, 3)
    # fill bolt roughly with two triangles
    triangle((x + 88, y + 78), (x + 66, y + 128), (x + 102, y + 104), YELLOW)
    triangle((x + 66, y + 128), (x + 72, y + 158), (x + 102, y + 104), YELLOW)


def icon_drone(x, y):
    # quadcopter drone over a burst
    rect(x + 55, y + 60, 70, 26, INK)
    disc(x + 90, y + 73, 8, RED)
    for ax, ay in ((35, 55), (145, 55), (35, 95), (145, 95)):
        line(x + 90, y + 73, x + ax, y + ay, INK, 4)
        rect(x + ax - 22, y + ay - 3, 44, 6, INK)
    for i in range(8):
        ang = i * 3.14159 / 4
        x2 = int(x + 90 + 34 * math.cos(ang))
        y2 = int(y + 128 + 14 * math.sin(ang))
        line(x + 90, y + 128, x2, y2, ORANGE, 4)
    disc(x + 90, y + 128, 16, ORANGE)
    disc(x + 90, y + 128, 8, YELLOW)


def icon_flags(x, y):
    # US flag and Russian tricolour on poles
    # US flag
    fx, fy = x + 8, y + 30
    rect(fx, fy, 74, 46, WHITE)
    for i in range(4):
        rect(fx, fy + i * 12, 74, 6, RED)
    rect(fx, fy, 30, 24, NAVY)
    for r_ in range(3):
        for c_ in range(4):
            disc(fx + 5 + c_ * 7, fy + 5 + r_ * 7, 1, WHITE)
    # Russian flag
    gx, gy = x + 96, y + 30
    rect(gx, gy, 74, 46, WHITE)
    rect(gx, gy + 15, 74, 16, BLUE)
    rect(gx, gy + 31, 74, 15, RED)
    rect(gx, gy, 74, 46, INK)  # outline pass
    rect(gx + 2, gy + 2, 70, 42, WHITE)
    rect(gx + 2, gy + 16, 70, 14, BLUE)
    rect(gx + 2, gy + 30, 70, 14, RED)
    # poles
    vline(x + 4, y + 14, 96, INK, 3)
    vline(x + 92, y + 14, 96, INK, 3)
    disc(x + 5, y + 12, 4, GOLD)
    disc(x + 93, y + 12, 4, GOLD)
    # handshake bar below
    rect(x + 30, y + 96, 120, 10, GOLD)


def icon_afp(x, y):
    # laptop screen with warning triangle
    triangle((x + 90, y + 6), (x + 52, y + 72), (x + 128, y + 72), RED)
    triangle((x + 90, y + 18), (x + 62, y + 66), (x + 118, y + 66), YELLOW)
    rect(x + 86, y + 30, 8, 22, INK)
    rect(x + 86, y + 56, 8, 8, INK)
    rect(x + 30, y + 86, 120, 62, NAVY)
    rect(x + 36, y + 92, 108, 50, WHITE)
    draw_text(x + 78, y + 100, "!", 4, RED)
    rect(x + 18, y + 148, 144, 10, INK)


def icon_coin(x, y):
    disc(x + 14, y + 14, 13, GOLD)
    ring(x + 14, y + 14, 13, (160, 120, 20), 2)
    draw_text(x + 10, y + 5, "E", 2, INK)


def icon_arrow(x, y):
    line(x + 14, y + 26, x + 14, y + 6, TEAL, 4)
    triangle((x + 14, y + 0), (x + 4, y + 12), (x + 24, y + 12), TEAL)
    line(x + 2, y + 26, x + 26, y + 26, TEAL, 3)


def icon_pawn(x, y):
    disc(x + 14, y + 8, 6, INK)
    triangle((x + 14, y + 12), (x + 4, y + 26), (x + 24, y + 26), INK)
    rect(x + 2, y + 26, 24, 4, INK)


# ---------------------------------------------------------------- layout
def card(x, y, w, h):
    rect(x, y, w, h, CARD)
    rect(x, y, w, 2, INK)
    rect(x, y + h - 2, w, 2, INK)
    rect(x, y, 2, h, INK)
    rect(x + w - 2, y, 2, h, INK)


def kicker(x, y, s, c=RED):
    draw_text(x, y, s, 2, c)


def build():
    # ---- masthead
    rect(0, 0, W, 104, NAVY)
    title = "THE WORLD IN ONE DAY"
    draw_text((W - text_w(title, 5)) // 2, 18, title, 5, WHITE)
    date = "FRIDAY, 27 NOVEMBER 2026"
    draw_text((W - text_w(date, 3)) // 2, 66, date, 3, GOLD)
    hline(0, 104, W, GOLD, 4)

    # ---- lead story: New Zealand election
    card(16, 116, 992, 236)
    kicker(36, 130, "LEAD STORY  -  WELLINGTON")
    icon_ballot(52, 168)
    draw_para(320, 158,
              "NEW ZEALAND COALITION ONE SEAT SHORT OF MAJORITY",
              4, INK, 660, leading=36)
    draw_para(320, 240,
              "OFFICIAL RESULTS LEAVE PM LUXON'S RULING BLOC A SINGLE "
              "SEAT SHORT OF A MAJORITY. COALITION TALKS - OR A FRESH "
              "VOTE - NOW LOOM.",
              2, GREY, 660, leading=19)

    # ---- grid of four stories
    panels = [
        (16, 364, "UNITED STATES  -  WEATHER", icon_storm,
         "THANKSGIVING STORM BATTERS US EAST",
         "MORE THAN 724,000 HOMES LOSE POWER; NYC POSTPONES THE "
         "100TH MACY'S PARADE."),
        (516, 364, "MIDDLE EAST  -  KUWAIT", icon_drone,
         "DRONE STRIKE IN KUWAIT KILLS TWO ITALIANS",
         "TWO ITALIAN TECHNICIANS DEAD AFTER A DRONE HIT A KUWAITI "
         "FACILITY. IRAN DENIES A ROLE."),
        (16, 580, "UKRAINE WAR  -  DIPLOMACY", icon_flags,
         "TRUMP: PUTIN 'WOULD LIKE A DEAL'",
         "AFTER TALKS IN CHINA, THE US PRESIDENT SAYS PUTIN WANTS AN "
         "END TO THE UKRAINE WAR."),
        (516, 580, "EUROPE  -  MEDIA", icon_afp,
         "CYBERATTACK HITS NEWS AGENCY AFP",
         "FRANCE'S AFP TAKES ITS FORUM PLATFORM OFFLINE AFTER AN "
         "OVERNIGHT INTRUSION."),
    ]
    for (px_, py_, kick, icon, head, body) in panels:
        card(px_, py_, 492, 204)
        kicker(px_ + 20, py_ + 14, kick)
        icon(px_ + 16, py_ + 42)
        tx = px_ + 196
        draw_para(tx, py_ + 40, head, 3, INK, 276, leading=26)
        draw_para(tx, py_ + 122, body, 2, GREY, 276, leading=18)

    # ---- briefs strip
    briefs = [
        ("EUROPE  -  ECONOMY", icon_coin,
         "EU NAMES SPAIN'S DE COS TO LEAD THE ECB",
         "SUCCEEDS LAGARDE IN FEBRUARY 2027."),
        ("ASIA  -  SOCIETY", icon_arrow,
         "SOUTH KOREA BIRTHS JUMP 14.3%",
         "RECORD RISE IN THE FIRST NINE MONTHS OF 2026."),
        ("SPORT  -  CHESS", icon_pawn,
         "GUKESH, SINDAROV DRAW GAME 3",
         "MARATHON GAME ENDS LEVEL AFTER THREE GAMES."),
    ]
    for i, (kick, icon, head, body) in enumerate(briefs):
        bx = 16 + i * 336
        card(bx, 796, 320, 152)
        rect(bx, 796, 320, 6, NAVY)
        icon(bx + 16, 814)
        kicker(bx + 56, 816, kick)
        draw_para(bx + 16, 852, head, 2, INK, 288, leading=19)
        draw_para(bx + 16, 900, body, 2, GREY, 288, leading=18)

    # ---- footer
    foot = ("ALL STORIES FIRST REPORTED FRIDAY 27 NOVEMBER 2026  -  "
            "BBC, AFP, AL JAZEERA, REUTERS")
    draw_text((W - text_w(foot, 2)) // 2, 972, foot, 2, GREY)

# ---------------------------------------------------------------- PNG out
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png():
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += canvas[y * W * 3:(y + 1) * W * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    # Clear only the children of the output directory, never the dir itself.
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
    build()
    data = encode_png()
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
