"""Flat side-view pixel office panorama in the colours of the current Kantor Agent loft.
Drawn at half resolution (PW x PH) then scaled x2 (nearest) -> base 2800 x 960."""
from PIL import Image, ImageDraw
import random
random.seed(3)
PW, PH = 1400, 480
FLOOR = 190          # wall/floor line (half res)
GND = 236            # furniture standing line (half res)

C = dict(
    wall=(237, 234, 228), wall2=(228, 224, 216), pil=(207, 202, 194), pil2=(189, 184, 175), pil3=(170, 165, 156),
    base=(156, 151, 143), frame=(30, 30, 34), sill=(214, 209, 200),
    wood=(200, 148, 95), wood2=(212, 162, 110), seam=(168, 122, 76), conc=(167, 163, 156), conc2=(156, 152, 146), tile=(220, 214, 204), tile2=(206, 200, 190),
    oak=(210, 154, 90), oak2=(176, 122, 64), blk=(38, 38, 42), blk2=(58, 58, 64),
    rug=(238, 233, 222), rug2=(74, 74, 80), green=(110, 154, 106), green2=(86, 128, 84),
    leaf=(78, 138, 79), leaf2=(111, 174, 99), leaf3=(56, 104, 60), pot=(188, 184, 176), pot2=(160, 156, 148),
    sofa=(194, 88, 46), sofa2=(217, 112, 63), sofa3=(142, 59, 29), cream=(236, 226, 205),
    steel=(184, 188, 194), steel2=(140, 144, 150), glass=(207, 232, 238), bottle=(127, 195, 232), white=(250, 250, 248),
)
BOOK = [(110, 139, 116), (194, 85, 63), (224, 192, 122), (74, 90, 120), (236, 226, 205), (120, 90, 70)]


def R(d, x0, y0, x1, y1, c): d.rectangle([x0, y0, x1, y1], fill=c)


def window(d, x0, y0, x1, y1, cols=4, rows=3):
    R(d, x0 - 3, y0 - 3, x1 + 3, y1 + 3, C['frame'])
    R(d, x0, y0, x1, y1, (0, 0, 0, 0))  # pane hole (transparent)
    cw = (x1 - x0) / cols; rh = (y1 - y0) / rows
    for i in range(1, cols): xx = int(x0 + i * cw); R(d, xx - 1, y0, xx, y1, C['frame'])
    for j in range(1, rows): yy = int(y0 + j * rh); R(d, x0, yy - 1, x1, yy, C['frame'])
    R(d, x0 - 5, y1 + 3, x1 + 5, y1 + 6, C['sill'])
    return (x0, y0, x1, y1)


def pillar(d, x0, x1):
    R(d, x0, 0, x1, FLOOR, C['pil']); R(d, x1 - 4, 0, x1, FLOOR, C['pil2']); R(d, x0, 0, x0 + 1, FLOOR, C['pil3'])
    for y in range(18, FLOOR, 46): R(d, x0 + 2, y, x1 - 5, y, C['pil2'])


def plant(d, x, big=1.0):
    h = int(34 * big)
    R(d, x - 9, GND - 16, x + 9, GND, C['pot']); R(d, x + 5, GND - 16, x + 9, GND, C['pot2'])
    for k, (dx, dy, r, c) in enumerate([(-8, -h, 9, C['leaf3']), (6, -h - 4, 10, C['leaf']), (-2, -h - 14, 9, C['leaf2']), (-10, -h + 10, 8, C['leaf']), (9, -h + 8, 8, C['leaf2'])]):
        d.ellipse([x + dx - r, GND - 16 + dy + h // 2 - r, x + dx + r, GND - 16 + dy + h // 2 + r], fill=c)
    R(d, x - 1, GND - 30, x, GND - 16, C['leaf3'])


def desk(d, x0, x1, top=196, divider=False, monitors=1, mug=True):
    R(d, x0, top, x1, top + 4, C['oak']); R(d, x0, top + 4, x1, top + 6, C['oak2'])
    R(d, x0 + 3, top + 6, x0 + 6, GND, C['blk']); R(d, x1 - 6, top + 6, x1 - 3, GND, C['blk'])
    R(d, x0 + 3, GND - 2, x0 + 14, GND, C['blk']); R(d, x1 - 14, GND - 2, x1 - 3, GND, C['blk'])
    if divider: R(d, x0 + 10, top - 22, x1 - 10, top - 1, C['green']); R(d, x0 + 10, top - 22, x1 - 10, top - 20, C['green2'])
    mons = []
    for k in range(monitors):
        mx = x0 + 18 + k * 44
        R(d, mx, top - 30, mx + 34, top - 10, C['blk']); R(d, mx + 2, top - 28, mx + 32, top - 12, (43, 74, 107))
        mons.append((mx + 2, top - 28, mx + 32, top - 12))
        R(d, mx + 15, top - 10, mx + 18, top - 1, C['blk2']); R(d, mx + 10, top - 2, mx + 24, top - 1, C['blk2'])
        R(d, mx + 4, top - 2, mx + 2 + 28, top - 1, C['blk2'])
    if mug: R(d, x1 - 22, top - 7, x1 - 16, top - 1, C['white']); R(d, x1 - 16, top - 5, x1 - 14, top - 3, C['white'])
    R(d, x1 - 40, top - 3, x1 - 28, top - 1, C['blk2'])
    return mons


def chair(d, x, facing=1):
    R(d, x - 8, GND - 34, x + 8, GND - 30, C['blk']); R(d, x - 7 * facing - (1 if facing < 0 else 0), GND - 54, x - 5 * facing + (2 if facing > 0 else 0), GND - 34, C['blk2'])
    R(d, x - 1, GND - 30, x + 1, GND - 8, C['blk']); R(d, x - 10, GND - 4, x + 10, GND - 2, C['blk'])
    for dx in (-10, 0, 10): R(d, x + dx - 1, GND - 2, x + dx + 1, GND, C['blk2'])


def bookshelf(d, x0, x1, top):
    R(d, x0, top, x0 + 2, GND, C['blk']); R(d, x1 - 2, top, x1, GND, C['blk'])
    shelves = list(range(top, GND, 26))
    for y in shelves:
        R(d, x0, y, x1, y + 2, C['oak'])
        bx = x0 + 4
        while bx < x1 - 8 and y + 2 < GND - 4:
            w = random.randint(3, 6); h = random.randint(12, 20); col = random.choice(BOOK)
            if random.random() < .15: R(d, bx, y + 24 - 8, bx + 8, y + 24, col); bx += 10; continue
            R(d, bx, y + 26 - h - 2, bx + w, y + 24, col); bx += w + 1
            if random.random() < .1: bx += 5


def dispenser(d, x):
    R(d, x - 11, GND - 52, x + 11, GND, C['white']); R(d, x + 7, GND - 52, x + 11, GND, (220, 220, 222))
    R(d, x - 9, GND - 46, x + 9, GND - 44, C['blk2']); R(d, x - 3, GND - 40, x - 1, GND - 36, (200, 60, 60)); R(d, x + 2, GND - 40, x + 4, GND - 36, (60, 110, 200))
    d.ellipse([x - 10, GND - 82, x + 10, GND - 52], fill=C['bottle']); R(d, x - 3, GND - 86, x + 3, GND - 80, C['bottle'])
    R(d, x - 6, GND - 76, x - 4, GND - 58, (190, 228, 246))


def coffeebar(d, x0, x1):
    top = 168
    R(d, x0, top, x1, top + 4, C['oak']); R(d, x0, top + 4, x1, GND, C['blk']); R(d, x0 + 4, top + 10, x1 - 4, top + 12, C['blk2'])
    R(d, x0 + 4, top + 30, x1 - 4, top + 32, C['blk2'])
    for k in range(4): R(d, x0 + 8 + k * 18, top + 36, x0 + 20 + k * 18, top + 52, [C['cream'], C['oak2'], C['white'], C['green']][k])
    # espresso machine
    R(d, x0 + 10, top - 26, x0 + 44, top, C['steel']); R(d, x0 + 10, top - 26, x0 + 44, top - 23, C['steel2'])
    R(d, x0 + 18, top - 14, x0 + 24, top - 8, C['blk']); R(d, x0 + 30, top - 14, x0 + 36, top - 8, C['blk']); R(d, x0 + 20, top - 4, x0 + 24, top - 1, C['white'])
    # grinder
    R(d, x0 + 52, top - 22, x0 + 62, top, C['blk']); d.polygon([(x0 + 50, top - 22), (x0 + 64, top - 22), (x0 + 60, top - 34), (x0 + 54, top - 34)], fill=(120, 80, 50))
    for k in range(3): R(d, x0 + 70 + k * 8, top - 6, x0 + 75 + k * 8, top - 1, C['white'])
    # shelf above
    R(d, x0 + 6, top - 60, x1 - 6, top - 58, C['oak'])
    for k in range(5): R(d, x0 + 12 + k * 16, top - 72, x0 + 22 + k * 16, top - 60, [C['white'], (120, 80, 50), C['cream'], C['green'], C['white']][k])
    return (x0 + 20, top - 4)  # steam point


def railing(d, x0, x1):
    R(d, x0, 150, x0 + 2, GND, (140, 144, 150)); R(d, x1 - 2, 150, x1, GND, (140, 144, 150)); R(d, x0, 150, x1, 152, (140, 144, 150))
    for x in range(x0 + 2, x1 - 2):
        for y in range(152, GND):
            if (x + y) % 2 == 0: d.point((x, y), fill=C['glass'])
    for k in range(3): d.line([x0 + 6 + k * 10, 200, x0 + 16 + k * 10, 160], fill=(240, 250, 252))


def sofa(d, x0, x1):
    R(d, x0, 170, x1, 196, C['sofa']); R(d, x0, 170, x1, 174, C['sofa2'])
    R(d, x0 - 8, 186, x0 + 8, GND - 10, C['sofa3']); R(d, x1 - 8, 186, x1 + 8, GND - 10, C['sofa3'])
    R(d, x0 + 6, 196, x1 - 6, 216, C['sofa2']); R(d, x0 + 6, 212, x1 - 6, GND - 10, C['sofa'])
    for k in range(3): R(d, x0 + 10 + k * (x1 - x0 - 20) // 3, 196, x0 + 11 + k * (x1 - x0 - 20) // 3, 216, C['sofa3'])
    R(d, x0 + 14, 180, x0 + 34, 198, C['cream']); R(d, x1 - 34, 180, x1 - 14, 198, (170, 196, 168))
    R(d, x0 - 4, GND - 10, x0, GND, C['blk']); R(d, x1, GND - 10, x1 + 4, GND, C['blk'])


def frame_pic(d, x0, y0, w, h, night=False):
    R(d, x0, y0, x0 + w, y0 + h, C['blk']); R(d, x0 + 3, y0 + 3, x0 + w - 3, y0 + h - 3, (198, 196, 190))
    for k in range(4):
        bh = random.randint(10, h - 12); bx = x0 + 5 + k * (w - 10) // 4
        R(d, bx, y0 + h - 4 - bh, bx + (w - 10) // 4 - 1, y0 + h - 4, (90 + k * 15, 92 + k * 12, 100 + k * 10))


def lamp(d, x, y=46):
    R(d, x, 0, x, y, C['blk']); d.polygon([(x - 9, y + 10), (x + 9, y + 10), (x + 4, y), (x - 4, y)], fill=C['blk']); R(d, x - 3, y + 10, x + 3, y + 12, (255, 220, 140))
    return (x, y + 12)


def floor_lamp(d, x):
    R(d, x, 120, x + 1, GND, C['blk']); R(d, x - 6, GND - 2, x + 7, GND, C['blk'])
    d.polygon([(x - 10, 132), (x + 11, 132), (x + 6, 116), (x - 5, 116)], fill=C['cream'])
    return (x, 128)


def build():
    im = Image.new('RGBA', (PW, PH), C['wall']); d = ImageDraw.Draw(im)
    # wall texture (subtle concrete speckle)
    for _ in range(2600):
        x, y = random.randint(0, PW - 1), random.randint(0, FLOOR - 1); d.point((x, y), fill=C['wall2'])
    R(d, 0, 0, PW, 6, C['pil2'])  # ceiling beam
    wins = []
    wins.append(window(d, 48, 22, 236, 140, 4, 3))
    wins.append(window(d, 290, 22, 545, 140, 5, 3))
    wins.append(window(d, 598, 22, 708, 100, 2, 2))
    wins.append(window(d, 785, 22, 1048, 140, 5, 3))
    wins.append(window(d, 1095, 22, 1385, 60, 6, 1))
    for x0, x1 in [(0, 22), (252, 276), (560, 584), (722, 746), (1062, 1086)]: pillar(d, x0, x1)
    # floors
    for x in range(0, PW):
        pass
    R(d, 0, FLOOR, 760, PH, C['wood'])
    for y in range(FLOOR, PH, 9):
        R(d, 0, y, 760, y, C['seam'])
        off = (y // 9) * 37 % 90
        for x in range(off, 760, 90): R(d, x, y, x, y + 8, C['seam'])
        if (y // 9) % 3 == 0: R(d, 0, y + 1, 760, y + 2, C['wood2'])
    R(d, 760, FLOOR, 1080, PH, C['conc'])
    for _ in range(3000):
        x, y = random.randint(760, 1079), random.randint(FLOOR, PH - 1); d.point((x, y), fill=C['conc2'])
    for y in range(FLOOR, PH, 20):
        for x in range(1080, PW, 20): R(d, x, y, x + 19, y + 19, C['tile'] if ((x // 20 + y // 20) % 2) else C['tile2'])
    R(d, 0, FLOOR - 3, PW, FLOOR, C['base'])
    # rugs
    R(d, 286, 226, 424, 250, C['rug2']); R(d, 289, 228, 421, 248, C['rug'])
    R(d, 430, 226, 560, 250, C['rug2']); R(d, 433, 228, 557, 248, C['rug'])
    d.ellipse([1110, 232, 1320, 268], fill=(150, 112, 70)); d.ellipse([1120, 236, 1310, 264], fill=(196, 160, 112)); d.ellipse([1150, 242, 1280, 258], fill=(178, 140, 94))
    # furniture
    bookshelf(d, 60, 122, 66)
    dispenser(d, 140)
    plant(d, 222, 1.1)
    m1 = desk(d, 300, 412, monitors=2)
    chair(d, 330, 1)
    m2 = desk(d, 442, 552, monitors=2, mug=False)
    chair(d, 470, 1)
    steam = coffeebar(d, 600, 706)
    railing(d, 748, 790)
    m3 = desk(d, 806, 970, divider=True, monitors=3)
    plant(d, 1004, 1.2)
    frame_pic(d, 1120, 74, 44, 56); frame_pic(d, 1176, 74, 44, 56)
    sofa(d, 1120, 1300)
    R(d, 1170, 222, 1262, 226, (60, 60, 66)); R(d, 1172, 226, 1176, 246, C['blk']); R(d, 1256, 226, 1260, 246, C['blk']); R(d, 1174, 218, 1200, 222, (200, 220, 230))
    plant(d, 1330, 1.3)
    fl = floor_lamp(d, 1362)
    lamps = [lamp(d, x) for x in (360, 500, 880, 960, 1210)]
    return im, dict(wins=wins, mons=m1 + m2 + m3, steam=steam, lamps=lamps + [fl])


if __name__ == '__main__':
    im, meta = build()
    im.resize((PW * 2, PH * 2), Image.NEAREST).save('/tmp/claude-0/w/vid/pano_test.png')
    print(meta)
