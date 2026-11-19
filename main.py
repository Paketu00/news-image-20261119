"""The World in One Page - Thursday, November 19, 2026.

A standard-library-only Python program that draws a newspaper front
page summarising the world news of Thursday 19 November 2026 into a
single 1024x1024 PNG image. It ships its own PNG encoder and its own
5x7 bitmap typeface, so it needs no third-party packages, no network
and no model calls, and it is fully deterministic.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 242, 230)
INK = (22, 20, 18)
RED = (163, 32, 26)
BLUE = (28, 54, 108)
GREY = (96, 92, 84)
BOXBG = (240, 233, 216)
RULE = (22, 20, 18)


def _chunk(tag, data):
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(
        ">I", zlib.crc32(body) & 0xFFFFFFFF
    )


def encode_png(width, height, pixels):
    """Encode an RGB bytearray as a PNG file (bytes)."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


class Canvas:
    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.px = bytearray(bytes(colour) * (width * height))

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            if 0 <= yy < self.h:
                start = max(0, x)
                end = min(self.w, x + w)
                if start < end:
                    i = (yy * self.w + start) * 3
                    self.px[i:i + (end - start) * 3] = bytes(colour) * (end - start)

    def hline(self, x, y, w, colour, thick=1):
        self.rect(x, y, w, thick, colour)

    def vline(self, x, y, h, colour, thick=1):
        self.rect(x, y, thick, h, colour)

    def frame(self, x, y, w, h, colour, thick=2):
        self.hline(x, y, w, colour, thick)
        self.hline(x, y + h - thick, w, colour, thick)
        self.vline(x, y, h, colour, thick)
        self.vline(x + w - thick, y, h, colour, thick)


# ---------------------------------------------------------------------------
# 5x7 bitmap typeface. Each glyph is seven rows of five pixels.
# ---------------------------------------------------------------------------

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),

    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),

    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": (".##..", "...#.", "....#", "....#", "....#", "...#.", ".##.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
}


# ---------------------------------------------------------------------------
# Text drawing helpers.
# ---------------------------------------------------------------------------


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, colour):
    """Draw one line of text; returns the x just past the last glyph."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            line = glyph[row]
            for col in range(5):
                if line[col] == "#":
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, colour)
        cx += 6 * scale
    return cx


def draw_centered(cv, y, text, scale, colour):
    w = text_width(text, scale)
    draw_text(cv, (WIDTH - w) // 2, y, text, scale, colour)


def draw_right(cv, right_x, y, text, scale, colour):
    w = text_width(text, scale)
    draw_text(cv, right_x - w, y, text, scale, colour)


def wrap(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    lines = []
    current = ""
    for word in text.split(" "):
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_para(cv, x, y, text, scale, colour, max_chars, line_gap):
    """Draw a wrapped paragraph; returns the y below its last line."""
    for line in wrap(text, max_chars):
        draw_text(cv, x, y, line, scale, colour)
        y += 7 * scale + line_gap
    return y


def split_columns(text, ncols, max_chars):
    """Wrap text, then deal the lines round-robin into balanced columns."""
    lines = wrap(text, max_chars)
    per = (len(lines) + ncols - 1) // ncols
    return [lines[i * per:(i + 1) * per] for i in range(ncols)]


def draw_story(cv, x, y, width, kicker, headline, body):
    """A small news item: red kicker, bold headline, body copy."""
    draw_text(cv, x, y, kicker, 2, RED)
    y += 22
    y = draw_para(cv, x, y, headline, 3, INK, width // 18, 5)
    y += 4
    draw_para(cv, x, y, body, 2, INK, width // 12, 2)


def draw_box_story(cv, x, y, width, height, kicker, headline_lines, body):
    """A framed feature box used for the day's two second leads."""
    cv.rect(x, y, width, height, BOXBG)
    cv.frame(x, y, width, height, INK, 2)
    inner = x + 16
    cy = y + 14
    draw_text(cv, inner, cy, kicker, 2, RED)
    cy += 24
    for line in headline_lines:
        draw_text(cv, inner, cy, line, 4, INK)
        cy += 36
    cy += 4
    draw_para(cv, inner, cy, body, 2, INK, (width - 32) // 12, 3)


# ---------------------------------------------------------------------------
# The front page itself: Thursday, November 19, 2026.
# ---------------------------------------------------------------------------

LEFT = 34
RIGHT = 990
PAGE_W = RIGHT - LEFT

LEAD_BODY = (
    "SHENZHEN - THE PRESIDENTS OF THE UNITED STATES, CHINA AND RUSSIA "
    "MET ON THE SIDELINES OF THE APEC FORUM, THE FIRST TIME THE THREE "
    "HAVE HELD TALKS TOGETHER. TRUMP SAID HE EXPECTED WONDERFUL THINGS "
    "FROM HIS TALKS WITH PUTIN, AND XI GREETED BOTH MEN. ONE HOUR WAS "
    "SET ASIDE AFTER THE APEC PLENARY. THE AGENDA REPORTEDLY COVERS "
    "THE WARS IN UKRAINE AND IRAN, NUCLEAR WEAPONS, TRADE AND "
    "ARTIFICIAL INTELLIGENCE. ANALYSTS EXPECT FEW CONCRETE RESULTS, "
    "BUT TALKS AMONG THE THREE POWERS COULD SHAPE BOTH WARS, TRADE "
    "RULES AND ARMS CONTROL WORLDWIDE."
)


def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    # Masthead.
    cv.hline(LEFT, 24, PAGE_W, RULE, 4)
    cv.hline(LEFT, 32, PAGE_W, RULE, 1)
    draw_centered(cv, 44, "THE WORLD IN ONE PAGE", 6, INK)
    draw_centered(
        cv, 94,
        "THURSDAY, NOVEMBER 19, 2026 - VOL. II - NO. 19 - THE WHOLE PLANET, ONE IMAGE",
        2, GREY,
    )
    cv.hline(LEFT, 118, PAGE_W, RULE, 3)
    cv.hline(LEFT, 124, PAGE_W, RULE, 1)
    draw_centered(
        cv, 132,
        "SHENZHEN 21C - THE HAGUE 10C - NEW YORK 7C - SYDNEY 24C - NAIROBI 26C",
        2, GREY,
    )
    cv.hline(LEFT, 154, PAGE_W, RULE, 1)

    # Lead story: the Shenzhen trilateral.
    draw_text(cv, LEFT, 164, "APEC SUMMIT - SHENZHEN, CHINA", 2, RED)
    draw_right(cv, RIGHT, 164, "REPORTED BY 13 OUTLETS", 2, GREY)
    for i, line in enumerate(
        ("TRUMP, XI AND PUTIN", "HOLD FIRST THREE-WAY", "SUMMIT IN SHENZHEN")
    ):
        draw_text(cv, LEFT, 186 + i * 54, line, 7, INK)
    draw_text(cv, LEFT, 356, "THE THREE NUCLEAR POWERS SIT DOWN TOGETHER FOR THE", 3, BLUE)
    draw_text(cv, LEFT, 384, "FIRST TIME - WARS, TRADE AND AI ON THE TABLE.", 3, BLUE)

    cols = split_columns(LEAD_BODY, 3, 25)
    for i, col_lines in enumerate(cols):
        cx = LEFT + i * 326
        cy = 424
        for line in col_lines:
            draw_text(cv, cx, cy, line, 2, INK)
            cy += 17
        if i:
            cv.vline(cx - 11, 424, 136, GREY, 1)
    cv.hline(LEFT, 574, PAGE_W, RULE, 2)

    # Second leads: GTA VI launch day and the Anthropic debut.
    draw_box_story(
        cv, LEFT, 586, 467, 188,
        "CULTURE - LAUNCH DAY, VICE CITY",
        ("GTA VI IS HERE", "AFTER 13 YEARS"),
        "ROCKSTAR'S SEQUEL LAUNCHED AT MIDNIGHT ON PS5 AND XBOX. "
        "REVIEWS AVERAGE 99/100, WITH 2.3 MILLION PEOPLE "
        "WATCHING LIVE STREAMS.",
    )
    draw_box_story(
        cv, 523, 586, 467, 188,
        "MARKETS - NASDAQ DEBUT TODAY",
        ("ANTHROPIC'S $81BN", "RECORD IPO LANDS"),
        "THE CLAUDE MAKER PRICED 980M SHARES AT $83, ABOVE ITS "
        "RANGE - NEAR $1.5 TRILLION IN VALUE. IT TRADES TODAY "
        "AS ANT, A HISTORY-MAKING DEBUT.",
    )
    cv.hline(LEFT, 786, PAGE_W, RULE, 2)

    # Lower grid: justice, the Middle East, Europe.
    draw_story(
        cv, LEFT, 798, 304,
        "JUSTICE - THE HAGUE",
        "ROHINGYA GENOCIDE RULING",
        "THE ICJ DECIDES TODAY IF MYANMAR COMMITTED GENOCIDE "
        "AGAINST THE ROHINGYA. GAMBIA FILED THE CASE IN 2019.",
    )
    draw_story(
        cv, 360, 798, 304,
        "MIDDLE EAST - GULF",
        "IRAN STRIKES GULF STATES",
        "TEHRAN HIT GULF STATES AFTER US STRIKES ON QESHM "
        "ISLAND. IRAN ALSO OPENS BUSHEHR TO IAEA INSPECTORS.",
    )
    draw_story(
        cv, 686, 798, 304,
        "EUROPE - BRUSSELS",
        "CRIMEAN BRIDGE HIT A THIRD TIME",
        "UKRAINE STRUCK THE BRIDGE FOR THE THIRD TIME IN A "
        "WEEK. THE EU BACKED AN INDONESIA PACT AND A LOAN.",
    )
    cv.vline(349, 798, 150, GREY, 1)
    cv.vline(675, 798, 150, GREY, 1)

    # Briefs strip and colophon.
    cv.hline(LEFT, 962, PAGE_W, RULE, 1)
    draw_centered(
        cv, 970,
        "ALSO: VOYAGER 1 A FULL LIGHT-DAY AWAY - CYCLONE AQWAN NEARS INDIA - HANG SENG -2.78%",
        2, GREY,
    )
    draw_centered(
        cv, 996,
        "DRAWN BY A PYTHON PROGRAM - STANDARD LIBRARY ONLY - SOURCES: BBC, REUTERS, LE MONDE, CBS",
        1, GREY,
    )
    return cv


def main():
    cv = build_page()
    data = encode_png(WIDTH, HEIGHT, cv.px)
    here = os.path.dirname(os.path.abspath(__file__))
    targets = [os.path.join(here, "entry.png"), os.path.abspath("entry.png")]
    if os.path.isdir("/output"):
        targets.append("/output/entry.png")
    written = []
    for path in targets:
        if path not in written:
            with open(path, "wb") as fh:
                fh.write(data)
            written.append(path)
    print("wrote", len(data), "bytes to", ", ".join(written))


if __name__ == "__main__":
    main()
