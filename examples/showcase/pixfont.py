"""A small monospaced pixel font for the showcase pictures: 5x7 capitals and digits, lowercase with 2-row descenders,
on a 6x9 cell. Drawn by hand for this repo (no font file needed), so the pictures come out the same on every
machine and stay on the pixel grid when scaled.

    import pixfont
    pixfont.draw(img, x, y, "beast: 0 fault(s)", (240, 230, 210), scale=3)   # img: a PIL RGB or RGBA image
    pixfont.width("text", scale=3)
"""
from PIL import ImageDraw

CELL_W, CELL_H = 6, 9                                     # advance and line height, in font pixels

_G = {
    "A": ".XXX./X...X/X...X/XXXXX/X...X/X...X/X...X",
    "B": "XXXX./X...X/X...X/XXXX./X...X/X...X/XXXX.",
    "C": ".XXX./X...X/X..../X..../X..../X...X/.XXX.",
    "D": "XXXX./X...X/X...X/X...X/X...X/X...X/XXXX.",
    "E": "XXXXX/X..../X..../XXXX./X..../X..../XXXXX",
    "F": "XXXXX/X..../X..../XXXX./X..../X..../X....",
    "G": ".XXX./X...X/X..../X.XXX/X...X/X...X/.XXXX",
    "H": "X...X/X...X/X...X/XXXXX/X...X/X...X/X...X",
    "I": ".XXX./..X../..X../..X../..X../..X../.XXX.",
    "J": "..XXX/...X./...X./...X./...X./X..X./.XX..",
    "K": "X...X/X..X./X.X../XX.../X.X../X..X./X...X",
    "L": "X..../X..../X..../X..../X..../X..../XXXXX",
    "M": "X...X/XX.XX/X.X.X/X.X.X/X...X/X...X/X...X",
    "N": "X...X/X...X/XX..X/X.X.X/X..XX/X...X/X...X",
    "O": ".XXX./X...X/X...X/X...X/X...X/X...X/.XXX.",
    "P": "XXXX./X...X/X...X/XXXX./X..../X..../X....",
    "Q": ".XXX./X...X/X...X/X...X/X.X.X/X..X./.XX.X",
    "R": "XXXX./X...X/X...X/XXXX./X.X../X..X./X...X",
    "S": ".XXXX/X..../X..../.XXX./....X/....X/XXXX.",
    "T": "XXXXX/..X../..X../..X../..X../..X../..X..",
    "U": "X...X/X...X/X...X/X...X/X...X/X...X/.XXX.",
    "V": "X...X/X...X/X...X/X...X/X...X/.X.X./..X..",
    "W": "X...X/X...X/X...X/X.X.X/X.X.X/X.X.X/.X.X.",
    "X": "X...X/X...X/.X.X./..X../.X.X./X...X/X...X",
    "Y": "X...X/X...X/.X.X./..X../..X../..X../..X..",
    "Z": "XXXXX/....X/...X./..X../.X.../X..../XXXXX",
    "a": "...../...../.XXX./....X/.XXXX/X...X/.XXXX",
    "b": "X..../X..../XXXX./X...X/X...X/X...X/XXXX.",
    "c": "...../...../.XXX./X..../X..../X...X/.XXX.",
    "d": "....X/....X/.XXXX/X...X/X...X/X...X/.XXXX",
    "e": "...../...../.XXX./X...X/XXXXX/X..../.XXX.",
    "f": "..XX./.X..X/.X.../XXX../.X.../.X.../.X...",
    "g": "...../...../.XXXX/X...X/X...X/X...X/.XXXX/....X/.XXX.",
    "h": "X..../X..../XXXX./X...X/X...X/X...X/X...X",
    "i": "..X../...../.XX../..X../..X../..X../.XXX.",
    "j": "...X./...../..XX./...X./...X./...X./...X./X..X./.XX..",
    "k": "X..../X..../X..X./X.X../XX.../X.X../X..X.",
    "l": ".XX../..X../..X../..X../..X../..X../.XXX.",
    "m": "...../...../XX.X./X.X.X/X.X.X/X.X.X/X.X.X",
    "n": "...../...../XXXX./X...X/X...X/X...X/X...X",
    "o": "...../...../.XXX./X...X/X...X/X...X/.XXX.",
    "p": "...../...../XXXX./X...X/X...X/X...X/XXXX./X..../X....",
    "q": "...../...../.XXXX/X...X/X...X/X...X/.XXXX/....X/....X",
    "r": "...../...../X.XX./XX..X/X..../X..../X....",
    "s": "...../...../.XXXX/X..../.XXX./....X/XXXX.",
    "t": ".X.../.X.../XXX../.X.../.X.../.X..X/..XX.",
    "u": "...../...../X...X/X...X/X...X/X..XX/.XX.X",
    "v": "...../...../X...X/X...X/X...X/.X.X./..X..",
    "w": "...../...../X...X/X...X/X.X.X/X.X.X/.X.X.",
    "x": "...../...../X...X/.X.X./..X../.X.X./X...X",
    "y": "...../...../X...X/X...X/X...X/X...X/.XXXX/....X/.XXX.",
    "z": "...../...../XXXXX/...X./..X../.X.../XXXXX",
    "0": ".XXX./X...X/X..XX/X.X.X/XX..X/X...X/.XXX.",
    "1": "..X../.XX../..X../..X../..X../..X../.XXX.",
    "2": ".XXX./X...X/....X/...X./..X../.X.../XXXXX",
    "3": "XXXXX/...X./..X../...X./....X/X...X/.XXX.",
    "4": "...X./..XX./.X.X./X..X./XXXXX/...X./...X.",
    "5": "XXXXX/X..../XXXX./....X/....X/X...X/.XXX.",
    "6": "..XX./.X.../X..../XXXX./X...X/X...X/.XXX.",
    "7": "XXXXX/....X/...X./..X../.X.../.X.../.X...",
    "8": ".XXX./X...X/X...X/.XXX./X...X/X...X/.XXX.",
    "9": ".XXX./X...X/X...X/.XXXX/....X/...X./.XX..",
    " ": "",
    ".": "...../...../...../...../...../.XX../.XX..",
    ",": "...../...../...../...../...../.XX../..X../.X...",
    ":": "...../.XX../.XX../...../.XX../.XX..",
    ";": "...../.XX../.XX../...../.XX../..X../.X...",
    "(": "...X./..X../.X.../.X.../.X.../..X../...X.",
    ")": ".X.../..X../...X./...X./...X./..X../.X...",
    "[": ".XXX./.X.../.X.../.X.../.X.../.X.../.XXX.",
    "]": ".XXX./...X./...X./...X./...X./...X./.XXX.",
    "-": "...../...../...../.XXX.",
    "_": "...../...../...../...../...../...../XXXXX",
    "/": "....X/....X/...X./..X../.X.../X..../X....",
    "%": "XX..X/XX..X/...X./..X../.X.../X..XX/X..XX",
    "'": "..X../..X../.X...",
    '"': ".X.X./.X.X.",
    "#": ".X.X./.X.X./XXXXX/.X.X./XXXXX/.X.X./.X.X.",
    "=": "...../...../XXXXX/...../XXXXX",
    "+": "...../..X../..X../XXXXX/..X../..X..",
    ">": ".X.../..X../...X./....X/...X./..X../.X...",
    "<": "...X./..X../.X.../X..../.X.../..X../...X.",
    "!": "..X../..X../..X../..X../..X../...../..X..",
    "?": ".XXX./X...X/....X/...X./..X../...../..X..",
    "$": "..X../.XXXX/X.X../.XXX./..X.X/XXXX./..X..",
    "*": "...../..X../X.X.X/.XXX./X.X.X/..X..",
    "|": "..X../..X../..X../..X../..X../..X../..X..",
    "~": "...../...../.X..X/X.XX./X....",
}
GLYPHS = {ch: [r for r in rows.split("/")] if rows else [] for ch, rows in _G.items()}


def width(text, scale=1):
    """The width of a line of text, in image pixels (no trailing gap)."""
    return max(0, (len(text) * CELL_W - 1) * scale)


def draw(img, x, y, text, colour, scale=1):
    """Draw one line of text with its top-left at (x, y); each font pixel is a scale x scale square."""
    d = ImageDraw.Draw(img)
    for i, ch in enumerate(text):
        if ch not in GLYPHS:
            raise ValueError(f"pixfont has no glyph for {ch!r}")
        for r, row in enumerate(GLYPHS[ch]):
            for c, v in enumerate(row):
                if v == "X":
                    X, Y = x + (i * CELL_W + c) * scale, y + r * scale
                    d.rectangle((X, Y, X + scale - 1, Y + scale - 1), fill=colour)
