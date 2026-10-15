import os
import math
import random
import pygame


WHITE = (255, 255, 255)
SOFT_WHITE = (255, 225, 228)
MUTED = (190, 150, 156)
RED = (230, 35, 50)
RED_BRIGHT = (255, 70, 85)
RED_DARK = (110, 8, 20)

RED_GLASS = (12, 4, 8)
RED_DEEP = (18, 6, 11)
BLACK_PANEL = RED_GLASS
GREY_BORDER = (105, 38, 46)

_font_cache = {}
_bg_cache = {}
_img_cache = {}
_fx_cache = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SEARCH_DIRS = [
    "",
    "assets",
    os.path.join("assets", "images"),
    os.path.join("assets", "sounds"),
    os.path.join("assets", "audio"),
    os.path.join("assets", "fonts"),
    "images",
    "sounds",
    "audio",
]


UI_FONTS = "bahnschrift,segoeui,verdana,arial"


def font(size, bold=False):
    key = (size, bold)

    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(
            UI_FONTS, size, bold=bold
        )

    return _font_cache[key]


TITLE_FONTS = "impact,haettenschweiler,arialblack,bahnschrift,arial"
_title_cache = {}


def title_font(size):
    if size in _title_cache:
        return _title_cache[size]

    f = None
    path = find_asset("glatitle.ttf", "glatitle.otf")

    if path:
        try:
            f = pygame.font.Font(path, size)
        except (pygame.error, OSError):
            f = None

    if f is None:
        f = pygame.font.SysFont(TITLE_FONTS, size)

    _title_cache[size] = f
    return f


def _italic_font(size):
    key = ("italic", size)

    if key not in _font_cache:
        f = None
        path = find_asset("glatitle.ttf", "glatitle.otf")

        if path:
            try:
                f = pygame.font.Font(path, size)
            except (pygame.error, OSError):
                f = None

        if f is None:
            f = pygame.font.SysFont(
                TITLE_FONTS, size, bold=False, italic=True
            )

        _font_cache[key] = f

    return _font_cache[key]


def find_asset(*names):
    for root in (os.getcwd(), BASE_DIR):
        for folder in SEARCH_DIRS:
            for name in names:
                path = os.path.join(root, folder, name)

                if os.path.isfile(path):
                    return path

    return None


def load_image(names, size=None):
    if isinstance(names, str):
        names = (names,)

    key = (tuple(names), size)

    if key in _img_cache:
        return _img_cache[key]

    image = None
    path = find_asset(*names)

    if path:
        try:
            image = pygame.image.load(path).convert_alpha()

            if size:
                image = pygame.transform.smoothscale(image, size)

        except pygame.error:
            image = None

    _img_cache[key] = image
    return image


def _remember(key, value):
    if len(_fx_cache) > 700:
        _fx_cache.clear()

    _fx_cache[key] = value
    return value


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def _blur(surf, k=4):
    w, h = surf.get_size()

    small = pygame.transform.smoothscale(
        surf, (max(1, w // k), max(1, h // k))
    )

    return pygame.transform.smoothscale(small, (w, h))


def _chamfer(w, h, cut):
    cut = max(0, min(cut, w // 2, h // 2))

    return [
        (cut, 0), (w - cut, 0), (w, cut), (w, h - cut),
        (w - cut, h), (cut, h), (0, h - cut), (0, cut)
    ]


def _segment(a, b, length):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    d = math.hypot(dx, dy) or 1

    return a, (a[0] + dx / d * length, a[1] + dy / d * length)


def _terrain(surf, w, h, base, edge, edge_w, heights):
    step = w / (len(heights) - 1)

    points = [(0, h)]

    for i, up in enumerate(heights):
        points.append((int(i * step), h - up))

    points.append((w, h))

    pygame.draw.polygon(surf, base, points)
    pygame.draw.lines(surf, edge, False, points[1:-1], edge_w)


def _planet(surf, cx, cy, radius):
    glow = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(glow, (230, 35, 50, 200), (cx, cy), radius + 4, 8)
    glow = _blur(glow, 3)
    surf.blit(glow, (0, 0))
    surf.blit(glow, (0, 0))

    for i in range(radius, 0, -2):
        k = 1 - i / radius

        color = (
            int(40 + 175 * k),
            int(4 + 22 * k),
            int(10 + 34 * k)
        )

        pygame.draw.circle(
            surf,
            color,
            (int(cx - k * radius * 0.45), int(cy - k * radius * 0.35)),
            i
        )


def _vignette(w, h):
    key = ("vignette", w, h)

    if key in _bg_cache:
        return _bg_cache[key]

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    for i in range(70):
        a = int(150 * (1 - i / 70) ** 2)
        pygame.draw.rect(
            surf, (0, 0, 0, a), (i, i, w - i * 2, h - i * 2), 1
        )

    _bg_cache[key] = surf
    return surf


def background(w, h, scene=True):
    key = (w, h, scene)

    if key in _bg_cache:
        return _bg_cache[key]

    surf = pygame.Surface((w, h))

    for y in range(h):
        t = y / h
        color = (
            int(3 + 26 * t * t),
            int(2 + 1 * t),
            int(7 + 5 * t)
        )
        pygame.draw.line(surf, color, (0, y), (w, y))

    if scene:
        _planet(surf, int(w * 0.10), int(h * 0.22), 95)

        glow = pygame.Surface((w, 170), pygame.SRCALPHA)

        for gy in range(170):
            a = int(80 * (gy / 170) ** 2)
            pygame.draw.line(glow, (200, 20, 35, a), (0, gy), (w, gy))

        surf.blit(glow, (0, h - 170))

        _terrain(
            surf, w, h,
            (28, 4, 9), (150, 18, 32), 1,
            [70, 100, 60, 95, 55, 85, 50, 90, 60, 80, 105, 70]
        )

        _terrain(
            surf, w, h,
            (14, 2, 6), (225, 30, 48), 2,
            [45, 70, 35, 60, 28, 50, 24, 55, 38, 62, 40, 52]
        )

    surf.blit(_vignette(w, h), (0, 0))

    _bg_cache[key] = surf
    return surf


_stars = {}


def _star_field(w, h):
    key = (w, h)

    if key not in _stars:
        rnd = random.Random(7)

        _stars[key] = [
            [
                rnd.uniform(0, w),
                rnd.uniform(0, h - 70),
                rnd.uniform(0.04, 0.3),
                rnd.choice((1, 1, 1, 2)),
                rnd.uniform(0, 6.28)
            ]
            for _ in range(90)
        ]

    return _stars[key]


def draw_stars(screen, w, h, strength=1.0):
    t = pygame.time.get_ticks() / 1000.0

    for star in _star_field(w, h):
        star[1] += star[2]

        if star[1] > h - 70:
            star[1] = 0
            star[0] = random.uniform(0, w)

        b = int((150 + 100 * math.sin(t * 2.2 + star[4])) * strength)
        b = max(50, min(255, b))

        pygame.draw.circle(
            screen,
            (b, int(b * 0.62), int(b * 0.65)),
            (int(star[0]), int(star[1])),
            star[3]
        )


def draw_background(screen, w, h):
    screen.blit(background(w, h, True), (0, 0))
    draw_stars(screen, w, h)


def image_background(name, w, h):
    """Load a full-screen background image (cached). None if missing."""
    key = ("bgimg", name, w, h)

    if key in _bg_cache:
        return _bg_cache[key]

    image = None
    path = find_asset(name)

    if path:
        try:
            image = pygame.image.load(path).convert()
            image = pygame.transform.smoothscale(image, (w, h))

            dim = pygame.Surface((w, h), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 70))
            image.blit(dim, (0, 0))
            image.blit(_vignette(w, h), (0, 0))

        except pygame.error:
            image = None

    _bg_cache[key] = image
    return image


def draw_image_background(screen, w, h, name):
    """Draw the image; fall back to the default space background."""
    image = image_background(name, w, h)

    if image:
        screen.blit(image, (0, 0))
        draw_stars(screen, w, h, 0.7)
    else:
        draw_background(screen, w, h)


def game_background(w, h):
    """In-game background: dark sky with a big red planet at the bottom."""
    key = ("game", w, h)

    if key in _bg_cache:
        return _bg_cache[key]

    surf = pygame.Surface((w, h))

    for y in range(h):
        t = y / h
        pygame.draw.line(
            surf,
            (int(3 + 14 * t * t), 2, int(7 + 4 * t)),
            (0, y),
            (w, y)
        )

    cx, cy, radius = w // 2, h + 330, 500

    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(glow, (230, 35, 50, 220), (cx, cy), radius + 2, 10)
    glow = _blur(glow, 3)
    surf.blit(glow, (0, 0))
    surf.blit(glow, (0, 0))

    pygame.draw.circle(surf, (230, 40, 55), (cx, cy), radius)

    for k in range(0, 90):
        pygame.draw.circle(
            surf,
            _lerp((120, 12, 26), (12, 2, 6), k / 90),
            (cx, cy),
            radius - 3 - k
        )

    pygame.draw.circle(surf, (12, 2, 6), (cx, cy), radius - 93)

    surf.blit(_vignette(w, h), (0, 0))

    _bg_cache[key] = surf
    return surf


def panel(
    screen,
    rect,
    alpha=235,
    cut=16,
    fill=BLACK_PANEL,
    border=RED,
    border_w=2,
    glow=True
):
    """Big dark panel with chamfered corners and a glowing red border."""
    rect = pygame.Rect(rect)
    key = ("panel", rect.w, rect.h, alpha, cut, fill, border, border_w, glow)
    entry = _fx_cache.get(key)

    if entry is None:
        w, h = rect.size
        pad = 16 if glow else 0

        surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        pts = [(x + pad, y + pad) for x, y in _chamfer(w, h, cut)]

        if glow:
            g = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(g, (*border, 255), pts, 5)
            g = _blur(g, 3)
            surf.blit(g, (0, 0))
            surf.blit(g, (0, 0))

        pygame.draw.polygon(surf, (*fill, alpha), pts)

        tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

        for yy in range(h):
            a = int(46 * (yy / max(1, h)) ** 2)
            pygame.draw.line(
                tint, (150, 12, 26, a),
                (0, yy + pad), (w + pad * 2, yy + pad)
            )

        mask = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), pts)
        tint.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(tint, (0, 0))

        pygame.draw.polygon(surf, border, pts, border_w)

        if w > 60 and h > 60:
            inner = [
                (x + pad + 6, y + pad + 6)
                for x, y in _chamfer(w - 12, h - 12, max(0, cut - 4))
            ]
            pygame.draw.polygon(surf, (*border, 55), inner, 1)

        for a, b in (
            (pts[0], pts[1]), (pts[1], pts[0]),
            (pts[2], pts[3]), (pts[3], pts[2]),
            (pts[4], pts[5]), (pts[5], pts[4]),
            (pts[6], pts[7]), (pts[7], pts[6]),
        ):
            p1, p2 = _segment(a, b, 28)
            pygame.draw.line(surf, RED_BRIGHT, p1, p2, border_w + 1)

        for a, b in (
            (pts[7], pts[0]), (pts[1], pts[2]),
            (pts[3], pts[4]), (pts[5], pts[6])
        ):
            pygame.draw.line(surf, RED_BRIGHT, a, b, border_w + 1)

        entry = _remember(key, (surf, pad))

    surf, pad = entry
    screen.blit(surf, (rect.x - pad, rect.y - pad))


def glass(
    screen,
    rect,
    alpha=140,
    radius=10,
    color=BLACK_PANEL,
    border=RED,
    border_w=2,
    glow=None
):
    """Rounded dark box with a red border (small boxes, HUD, rows)."""
    rect = pygame.Rect(rect)

    if glow is None:
        glow = bool(border_w) and rect.width >= 300 and rect.height >= 150

    if sum(color) < 150:
        alpha = max(alpha, 225)

    key = ("glass", rect.w, rect.h, alpha, radius, color, border, border_w, glow)
    entry = _fx_cache.get(key)

    if entry is None:
        w, h = rect.size
        pad = 10 if glow else 0

        surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

        if glow:
            g = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(
                g, (*border, 255), (pad, pad, w, h), 4,
                border_radius=radius + 2
            )
            g = _blur(g, 3)
            surf.blit(g, (0, 0))
            surf.blit(g, (0, 0))

        pygame.draw.rect(
            surf, (*color, alpha), (pad, pad, w, h),
            border_radius=radius
        )

        if border_w:
            pygame.draw.rect(
                surf, border, (pad, pad, w, h), border_w,
                border_radius=radius
            )

        entry = _remember(key, (surf, pad))

    surf, pad = entry
    screen.blit(surf, (rect.x - pad, rect.y - pad))


def _gbutton(w, h, top, bottom, border, radius, glow, border_w):
    key = ("gbtn", w, h, top, bottom, border, radius, glow, border_w)
    entry = _fx_cache.get(key)

    if entry is not None:
        return entry

    pad = 10 if glow else 0
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    if glow:
        g = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(
            g, (*border, 255), (pad, pad, w, h), 4,
            border_radius=radius + 2
        )
        g = _blur(g, 3)
        surf.blit(g, (0, 0))

    body = pygame.Surface((w, h), pygame.SRCALPHA)

    for yy in range(h):
        pygame.draw.line(
            body,
            _lerp(top, bottom, yy / max(1, h - 1)),
            (0, yy),
            (w, yy)
        )

    gloss = pygame.Surface((w, max(1, h // 2)), pygame.SRCALPHA)
    gloss.fill((255, 255, 255, 26))
    body.blit(gloss, (0, 0))

    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(
        mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius
    )
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    surf.blit(body, (pad, pad))

    pygame.draw.rect(
        surf, border, (pad, pad, w, h), border_w, border_radius=radius
    )

    if w > radius * 2 + 4:
        pygame.draw.line(
            surf, (255, 200, 205, 90),
            (pad + radius, pad + 2), (pad + w - radius, pad + 2), 1
        )

    return _remember(key, (surf, pad))


def _blit_gbutton(
    screen, rect, top, bottom, border, radius, glow=True, border_w=2
):
    rect = pygame.Rect(rect)
    surf, pad = _gbutton(
        rect.w, rect.h, top, bottom, border, radius, glow, border_w
    )
    screen.blit(surf, (rect.x - pad, rect.y - pad))


def fill_red(screen, rect, radius=6):
    """Solid red gradient bar (used for the highlighted leaderboard row)."""
    _blit_gbutton(
        screen, rect, (225, 35, 50), (160, 10, 24),
        (255, 110, 120), radius, False, 1
    )


def text(
    screen,
    string,
    size,
    pos,
    bold=False,
    center=False,
    color=WHITE
):
    surface = font(size, bold).render(string, True, color)

    if center:
        rect = surface.get_rect(center=pos)
    else:
        rect = surface.get_rect(topleft=pos)

    screen.blit(surface, rect)
    return rect


def glow_text(
    screen,
    string,
    size,
    pos,
    color=WHITE,
    center=True,
    glow=RED,
    bold=True,
    fnt=None,
    strength=2
):
    """Text with a soft red glow (use for fixed labels, not for scores)."""
    key = ("gtext", string, size, color, glow, bold, id(fnt), strength)
    entry = _fx_cache.get(key)

    if entry is None:
        f = fnt or font(size, bold)
        txt = f.render(string, True, color)
        w, h = txt.get_size()
        pad = int(size * 0.6) + 6

        surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        g = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        g.blit(f.render(string, True, glow), (pad, pad))
        g = _blur(g, 3)

        for _ in range(strength):
            surf.blit(g, (0, 0))

        surf.blit(txt, (pad, pad))
        entry = _remember(key, (surf, pad, w, h))

    surf, pad, w, h = entry
    rect = pygame.Rect(0, 0, w, h)

    if center:
        rect.center = pos
    else:
        rect.topleft = pos

    screen.blit(surf, (rect.x - pad, rect.y - pad))
    return rect


def spaced_text(screen, string, size, center, spacing=3, color=SOFT_WHITE, bold=True):
    f = font(size, bold)
    glyphs = [f.render(ch, True, color) for ch in string]
    total = sum(g.get_width() for g in glyphs) + spacing * (len(glyphs) - 1)

    x = center[0] - total // 2

    for g in glyphs:
        screen.blit(g, (x, center[1] - g.get_height() // 2))
        x += g.get_width() + spacing


def heading(screen, string, center, size=32):
    """Screen title with glow and red lines on both sides."""
    rect = glow_text(screen, string, size, center)

    y = rect.centery

    for side in (-1, 1):
        x0 = rect.left - 22 if side < 0 else rect.right + 22
        x1 = x0 + side * 120

        pygame.draw.line(screen, RED, (x0, y), (x1, y), 2)
        pygame.draw.polygon(
            screen, RED_BRIGHT,
            [(x0, y - 5), (x0 - side * 7, y), (x0, y + 5)]
        )

    return rect


def overlay(screen, alpha=170):
    key = ("overlay", screen.get_size(), alpha)
    dim = _fx_cache.get(key)

    if dim is None:
        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((8, 0, 3, alpha))
        _remember(key, dim)

    screen.blit(dim, (0, 0))


def pill_text(
    screen,
    string,
    size,
    center,
    bold=True,
    alpha=140,
    pad=(22, 8),
    color=WHITE,
    fnt=None
):
    surface = (fnt or font(size, bold)).render(string, True, color)
    rect = surface.get_rect(center=center)
    bg = rect.inflate(pad[0] * 2, pad[1] * 2)

    glass(
        screen,
        bg,
        alpha=alpha,
        radius=min(14, bg.height // 2),
        border=(150, 24, 38),
        border_w=1,
        glow=False
    )

    screen.blit(surface, rect)
    return bg


def button(
    screen,
    rect,
    string,
    size=20,
    active=False,
    radius=9
):
    """Red gradient button (like the LOGIN button in the design)."""
    rect = pygame.Rect(rect)
    hover = rect.collidepoint(pygame.mouse.get_pos())

    if active or hover:
        top, bottom = (255, 85, 95), (205, 20, 38)
        border = WHITE if active else (255, 150, 158)
    else:
        top, bottom = (245, 55, 68), (175, 12, 28)
        border = (255, 120, 130)

    _blit_gbutton(screen, rect, top, bottom, border, radius, True)

    label = font(size, True).render(string, True, WHITE)
    screen.blit(label, label.get_rect(center=rect.center))


def icon_button(
    screen,
    rect,
    string,
    icon,
    size=19,
    radius=10,
    accent=None,
    accent_dark=None,
    primary=False
):
    """Red gradient button with an icon + label.
    primary=True -> brighter (use it for PLAY)."""
    rect = pygame.Rect(rect)
    hover = rect.collidepoint(pygame.mouse.get_pos())

    if primary:
        if hover:
            top, bottom, border = (255, 90, 100), (210, 22, 40), WHITE
        else:
            top, bottom, border = (248, 58, 70), (180, 12, 28), (255, 120, 130)
    else:
        if hover:
            top, bottom, border = (195, 32, 48), (105, 10, 24), WHITE
        else:
            top, bottom, border = (135, 17, 32), (64, 6, 15), (235, 60, 76)

    _blit_gbutton(screen, rect, top, bottom, border, radius, True)

    label = font(size, True).render(string, True, WHITE)
    icon_w = 28 if icon else 0
    start = rect.centerx - (icon_w + label.get_width()) // 2

    if icon:
        draw_icon(screen, icon, start + 11, rect.centery)

    screen.blit(
        label,
        (start + icon_w, rect.centery - label.get_height() // 2)
    )


def icon_tile(screen, rect, icon):
    """Small dark square with an icon (settings rows, profile stats)."""
    rect = pygame.Rect(rect)

    glass(
        screen, rect, alpha=240, radius=9, color=(34, 6, 12),
        border=(160, 28, 42), border_w=2, glow=False
    )

    draw_icon(screen, icon, rect.centerx, rect.centery, RED_BRIGHT)


def text_input(
    screen,
    rect,
    label,
    value,
    active,
    display=None,
    right_pad=15,
    icon=None
):
    """Dark input box. 'label' is shown as the placeholder text."""
    rect = pygame.Rect(rect)

    glass(
        screen,
        rect,
        alpha=240,
        radius=9,
        color=RED_DEEP,
        border=RED_BRIGHT if active else (140, 26, 38),
        border_w=2,
        glow=active
    )

    left = rect.x + (52 if icon else 16)

    if icon:
        draw_icon(
            screen, icon, rect.x + 26, rect.centery, (225, 170, 176)
        )

    shown = value if display is None else display
    f = font(19)

    if not shown:
        surface = f.render(label, True, (150, 112, 118))
    else:
        surface = f.render(shown, True, WHITE)
        max_w = rect.right - right_pad - left

        while surface.get_width() > max_w and shown:
            shown = shown[1:]
            surface = f.render(shown, True, WHITE)

    screen.blit(
        surface,
        (left, rect.centery - surface.get_height() // 2)
    )

    if active and (pygame.time.get_ticks() // 500) % 2:
        cx = left + (surface.get_width() if shown else 0) + 2

        pygame.draw.line(
            screen,
            WHITE,
            (cx, rect.y + 12),
            (cx, rect.bottom - 12),
            2
        )


def tab_rects(rect, count):
    rect = pygame.Rect(rect)
    width = rect.width / count

    return [
        pygame.Rect(rect.x + int(i * width), rect.y, int(width), rect.height)
        for i in range(count)
    ]


def tabs(screen, rect, labels, active, size=15):
    """Segmented tabs (LOGIN | CREATE ACCOUNT, ALL TIME | WEEKLY | DAILY)."""
    rect = pygame.Rect(rect)

    glass(
        screen, rect, alpha=240, radius=9, color=RED_DEEP,
        border=(140, 26, 38), border_w=2, glow=False
    )

    mouse = pygame.mouse.get_pos()

    for i, (r, label) in enumerate(zip(tab_rects(rect, len(labels)), labels)):
        inner = r.inflate(-6, -6)

        if i == active:
            _blit_gbutton(
                screen, inner, (250, 60, 72), (185, 14, 30),
                (255, 120, 130), 8, True
            )

        lit = i == active or inner.collidepoint(mouse)

        surface = font(size, True).render(
            label, True, WHITE if lit else MUTED
        )
        screen.blit(surface, surface.get_rect(center=r.center))


def toggle(screen, rect, on):
    rect = pygame.Rect(rect)
    hover = rect.collidepoint(pygame.mouse.get_pos())
    r = rect.height // 2

    if on:
        _blit_gbutton(
            screen, rect, (255, 72, 84), (190, 14, 30),
            WHITE if hover else (255, 120, 130), r, True
        )
        knob_x = rect.right - r
        label_x = rect.centerx - 12
    else:
        glass(
            screen, rect, alpha=240, radius=r, color=RED_DEEP,
            border=WHITE if hover else GREY_BORDER, border_w=2, glow=False
        )
        knob_x = rect.x + r
        label_x = rect.centerx + 12

    text(
        screen, "ON" if on else "OFF", 15,
        (label_x, rect.centery), bold=True, center=True,
        color=WHITE if on else MUTED
    )

    pygame.draw.circle(
        screen, WHITE, (knob_x, rect.centery), max(4, r - 6)
    )


def draw_icon(screen, name, x, y, color=WHITE):
    x = int(x)
    y = int(y)

    if name in ("profile", "user"):
        pygame.draw.circle(screen, color, (x, y - 5), 5, 2)
        pygame.draw.arc(
            screen, color, (x - 9, y + 2, 18, 14), 0, math.pi, 2
        )

    elif name == "lock":
        pygame.draw.rect(screen, color, (x - 7, y - 1, 14, 10), 2, border_radius=2)
        pygame.draw.arc(screen, color, (x - 5, y - 10, 10, 12), 0, math.pi, 2)

    elif name == "leaderboard":
        pygame.draw.rect(screen, color, (x - 10, y - 1, 5, 9), 2)
        pygame.draw.rect(screen, color, (x - 3, y - 8, 5, 16), 2)
        pygame.draw.rect(screen, color, (x + 4, y - 4, 5, 12), 2)

    elif name == "trophy":
        pygame.draw.polygon(
            screen, color,
            [(x - 7, y - 9), (x + 7, y - 9), (x + 5, y + 1), (x - 5, y + 1)],
            2
        )
        pygame.draw.arc(screen, color, (x - 13, y - 8, 9, 9), math.pi / 2, 3 * math.pi / 2, 2)
        pygame.draw.arc(screen, color, (x + 4, y - 8, 9, 9), -math.pi / 2, math.pi / 2, 2)
        pygame.draw.line(screen, color, (x, y + 1), (x, y + 6), 2)
        pygame.draw.line(screen, color, (x - 5, y + 8), (x + 5, y + 8), 3)

    elif name in ("speaker", "speaker_off"):
        pygame.draw.polygon(
            screen, color,
            [(x - 10, y - 3), (x - 5, y - 3), (x + 1, y - 8),
             (x + 1, y + 8), (x - 5, y + 3), (x - 10, y + 3)]
        )

        if name == "speaker":
            pygame.draw.arc(screen, color, (x - 2, y - 6, 10, 12), -1.0, 1.0, 2)
            pygame.draw.arc(screen, color, (x - 1, y - 10, 15, 20), -1.0, 1.0, 2)
        else:
            pygame.draw.line(screen, color, (x + 4, y - 5), (x + 12, y + 5), 2)
            pygame.draw.line(screen, color, (x + 12, y - 5), (x + 4, y + 5), 2)

    elif name == "exit":
        pygame.draw.lines(
            screen, color, False,
            [(x - 3, y - 9), (x - 10, y - 9), (x - 10, y + 9), (x - 3, y + 9)], 2
        )
        pygame.draw.line(screen, color, (x - 4, y), (x + 9, y), 2)
        pygame.draw.line(screen, color, (x + 9, y), (x + 3, y - 5), 2)
        pygame.draw.line(screen, color, (x + 9, y), (x + 3, y + 5), 2)

    elif name == "logout":
        pygame.draw.line(screen, color, (x - 9, y), (x + 7, y), 2)
        pygame.draw.line(screen, color, (x + 1, y - 6), (x + 7, y), 2)
        pygame.draw.line(screen, color, (x + 1, y + 6), (x + 7, y), 2)

    elif name == "star":
        pts = []

        for i in range(10):
            r = 10 if i % 2 == 0 else 4.5
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((x + math.cos(a) * r, y + math.sin(a) * r))

        pygame.draw.polygon(screen, color, pts)

    elif name == "crown":
        pygame.draw.polygon(
            screen, color,
            [(x - 9, y + 6), (x - 9, y - 4), (x - 4, y + 1), (x, y - 7),
             (x + 4, y + 1), (x + 9, y - 4), (x + 9, y + 6)]
        )

    elif name == "pencil":
        pygame.draw.line(screen, color, (x - 6, y + 6), (x + 5, y - 5), 4)
        pygame.draw.polygon(
            screen, color, [(x - 9, y + 9), (x - 9, y + 3), (x - 3, y + 9)]
        )

    elif name == "restart":
        pygame.draw.arc(screen, color, (x - 8, y - 8, 16, 16), 0.9, 6.0, 2)
        px = x + 5
        py = y - 6
        pygame.draw.polygon(
            screen, color, [(px + 3, py - 5), (px + 5, py + 3), (px - 4, py + 1)]
        )

    elif name == "home":
        pygame.draw.polygon(
            screen, color, [(x - 10, y), (x, y - 9), (x + 10, y)], 2
        )
        pygame.draw.rect(screen, color, (x - 7, y, 14, 9), 2)

    elif name == "games":
        pygame.draw.rect(screen, color, (x - 10, y - 6, 20, 12), 2, border_radius=5)
        pygame.draw.line(screen, color, (x - 6, y), (x - 2, y), 2)
        pygame.draw.line(screen, color, (x - 4, y - 2), (x - 4, y + 2), 2)
        pygame.draw.circle(screen, color, (x + 4, y - 1), 1)
        pygame.draw.circle(screen, color, (x + 7, y + 1), 1)

    elif name == "play":
        pygame.draw.polygon(
            screen, color,
            [(x - 6, y - 9), (x - 6, y + 9), (x + 9, y)]
        )

    elif name == "back":
        pygame.draw.line(screen, color, (x + 9, y), (x - 8, y), 2)
        pygame.draw.line(screen, color, (x - 8, y), (x, y - 7), 2)
        pygame.draw.line(screen, color, (x - 8, y), (x, y + 7), 2)

    elif name == "pause":
        pygame.draw.rect(screen, color, (x - 7, y - 9, 5, 18))
        pygame.draw.rect(screen, color, (x + 2, y - 9, 5, 18))

    elif name == "login":
        pygame.draw.polygon(
            screen, color,
            [
                (x - 8, y - 3), (x + 1, y - 3), (x + 1, y - 9),
                (x + 10, y), (x + 1, y + 9), (x + 1, y + 3),
                (x - 8, y + 3)
            ]
        )

    elif name == "settings":
        pygame.draw.circle(screen, color, (x, y), 7, 2)

        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.line(
                screen, color,
                (int(x + math.cos(a) * 9), int(y + math.sin(a) * 9)),
                (int(x + math.cos(a) * 12), int(y + math.sin(a) * 12)),
                2
            )

    elif name == "mobile":
        pygame.draw.rect(screen, color, (x - 6, y - 10, 12, 20), 2, border_radius=3)
        pygame.draw.circle(screen, color, (x, y + 6), 1)

    elif name == "graphics":
        pygame.draw.rect(screen, color, (x - 10, y - 7, 20, 14), 2, border_radius=2)
        pygame.draw.line(screen, color, (x - 6, y + 4), (x - 1, y - 2), 2)
        pygame.draw.line(screen, color, (x - 1, y - 2), (x + 3, y + 2), 2)
        pygame.draw.line(screen, color, (x + 3, y + 2), (x + 7, y - 3), 2)

    elif name == "music":
        pygame.draw.circle(screen, color, (x - 4, y + 6), 4)
        pygame.draw.line(screen, color, (x, y + 6), (x, y - 9), 2)
        pygame.draw.line(screen, color, (x, y - 9), (x + 8, y - 6), 3)

    elif name == "register":
        pygame.draw.circle(screen, color, (x - 3, y - 5), 5, 2)
        pygame.draw.arc(screen, color, (x - 12, y + 1, 18, 14), 0, math.pi, 2)
        pygame.draw.line(screen, color, (x + 6, y - 2), (x + 6, y + 8), 2)
        pygame.draw.line(screen, color, (x + 1, y + 3), (x + 11, y + 3), 2)


def draw_heart(screen, cx, cy, size, filled=True):
    color = (255, 70, 85) if filled else (70, 20, 28)
    r = max(3, int(size * 0.27))
    off = size * 0.24

    pygame.draw.circle(
        screen, color, (int(cx - off), int(cy - size * 0.1)), r
    )
    pygame.draw.circle(
        screen, color, (int(cx + off), int(cy - size * 0.1)), r
    )
    pygame.draw.polygon(
        screen,
        color,
        [
            (cx - size * 0.48, cy - size * 0.02),
            (cx + size * 0.48, cy - size * 0.02),
            (cx, cy + size * 0.5)
        ]
    )


_INVADER = [
    "..#.....#..",
    "...#...#...",
    "..#######..",
    ".##.###.##.",
    "###########",
    "#.#######.#",
    "#.#.....#.#",
    "...##.##...",
]


def invader_logo(screen, cx, cy, size, color=(235, 30, 45)):
    cell = max(2, size // 11)
    total_w = cell * 11
    total_h = cell * len(_INVADER)

    x0 = cx - total_w // 2
    y0 = cy - total_h // 2

    for row, line in enumerate(_INVADER):
        for col, ch in enumerate(line):
            if ch == "#":
                pygame.draw.rect(
                    screen,
                    color,
                    (x0 + col * cell, y0 + row * cell, cell, cell)
                )


def logo(screen, x, y, size=80, color=(235, 30, 45)):
    image = load_image(("spaceship.png", "logo.png"), (size, size))

    if image:
        screen.blit(image, image.get_rect(center=(x, y)))
        return

    invader_logo(screen, x, y, size, color)


def title_logo(screen, cx, cy, size=64, icon=True):
    """Big glowing 'SPACE INVADERS' title (two lines, red gradient,
    white outline) with the little invader on top."""
    key = ("title", size, icon)
    canvas = _fx_cache.get(key)

    if canvas is None:
        f = _italic_font(size)
        lines = ["SPACE", "INVADERS"]
        rendered = [f.render(s, True, WHITE) for s in lines]

        gap = -int(size * 0.14)
        cell = max(2, int(size * 0.7) // 11)
        icon_h = cell * 8 if icon else 0
        text_w = max(r.get_width() for r in rendered)
        text_h = sum(r.get_height() for r in rendered) + gap

        pad = int(size * 0.5)
        w = text_w + pad * 2 + 10
        h = icon_h + (10 if icon else 0) + text_h + pad * 2

        canvas = pygame.Surface((w, h), pygame.SRCALPHA)
        glow = pygame.Surface((w, h), pygame.SRCALPHA)

        y = pad

        if icon:
            invader_logo(glow, w // 2, y + icon_h // 2, cell * 11)
            invader_logo(canvas, w // 2, y + icon_h // 2, cell * 11)
            y += icon_h + 10

        for s, r in zip(lines, rendered):
            x = (w - r.get_width()) // 2
            rw, rh = r.get_size()

            red_text = f.render(s, True, (235, 30, 45))
            glow.blit(red_text, (x, y))

            dark = f.render(s, True, (150, 10, 25))
            white = f.render(s, True, (255, 238, 238))

            for k in range(16):
                a = k * math.pi / 8
                canvas.blit(
                    dark,
                    (x + int(math.cos(a) * 5), y + int(math.sin(a) * 5))
                )

            for k in range(12):
                a = k * math.pi / 6
                canvas.blit(
                    white,
                    (x + int(math.cos(a) * 3), y + int(math.sin(a) * 3))
                )

            grad = pygame.Surface((rw, rh), pygame.SRCALPHA)

            for yy in range(rh):
                pygame.draw.line(
                    grad,
                    _lerp((255, 120, 120), (205, 14, 30), yy / max(1, rh - 1)),
                    (0, yy),
                    (rw, yy)
                )

            grad.blit(r, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            canvas.blit(grad, (x, y))

            y += rh + gap

        glow = _blur(glow, 3)

        out = pygame.Surface((w, h), pygame.SRCALPHA)
        out.blit(glow, (0, 0))
        out.blit(glow, (0, 0))
        out.blit(canvas, (0, 0))

        canvas = _remember(key, out)

    screen.blit(canvas, canvas.get_rect(center=(cx, cy)))


def draw_avatar(screen, cx, cy, radius=30):
    """Round avatar with the red invader logo inside."""
    key = ("avatar", radius)
    entry = _fx_cache.get(key)

    if entry is None:
        pad = 10
        size = radius * 2 + pad * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2

        g = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(g, (*RED, 255), (c, c), radius, 4)
        g = _blur(g, 3)
        surf.blit(g, (0, 0))
        surf.blit(g, (0, 0))

        pygame.draw.circle(surf, (24, 4, 9), (c, c), radius)
        pygame.draw.circle(surf, RED, (c, c), radius, 3)
        invader_logo(surf, c, c, int(radius * 1.2))

        entry = _remember(key, (surf, pad))

    surf, _ = entry
    screen.blit(surf, surf.get_rect(center=(cx, cy)))


def ship_sprite(size):
    f = size / 80
    s = pygame.Surface((size, size), pygame.SRCALPHA)

    pts = [
        (40, 4), (50, 34), (74, 62), (52, 56), (46, 74),
        (34, 74), (28, 56), (6, 62), (30, 34)
    ]
    pts = [(px * f, py * f) for px, py in pts]

    pygame.draw.polygon(s, (230, 35, 50), pts)
    pygame.draw.polygon(s, WHITE, pts, max(1, int(2 * f)))
    pygame.draw.circle(s, WHITE, (int(40 * f), int(34 * f)), max(2, int(6 * f)))

    return s


def enemy_sprite(size):
    """Glowing red pixel invader (used when the enemy image is missing)."""
    key = ("enemy", size)
    sprite = _fx_cache.get(key)

    if sprite is not None:
        return sprite

    cell = max(2, size // 11)
    ox = (size - cell * 11) // 2
    oy = (size - cell * 8) // 2

    body = pygame.Surface((size, size), pygame.SRCALPHA)
    glow = pygame.Surface((size, size), pygame.SRCALPHA)

    for row, line in enumerate(_INVADER):
        for col, ch in enumerate(line):
            if ch == "#":
                rect = (ox + col * cell, oy + row * cell, cell, cell)
                pygame.draw.rect(body, (235, 35, 50), rect)
                pygame.draw.rect(glow, (255, 70, 85, 255), rect)

    glow = _blur(glow, 3)

    sprite = pygame.Surface((size, size), pygame.SRCALPHA)
    sprite.blit(glow, (0, 0))
    sprite.blit(glow, (0, 0))
    sprite.blit(body, (0, 0))

    return _remember(key, sprite)


def bullet_sprite(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    pygame.draw.rect(
        s, (255, 70, 85),
        (cx - 4, 4, 8, h - 8),
        border_radius=4
    )
    pygame.draw.rect(
        s, WHITE,
        (cx - 1, 6, 3, h - 12),
        border_radius=2
    )

    return s