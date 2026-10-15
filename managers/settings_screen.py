import pygame
import theme

try:
    from settings_manager import load_settings, save_settings
except ImportError:
    from managers.settings_manager import load_settings, save_settings


GRAPHICS_LEVELS = ["low", "medium", "high"]


class SettingsScreen:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h
        self.action = None
        self.clicked = False

        self.changed = False

        self.settings = load_settings()
        self.dragging = False

        self.panel = pygame.Rect(140, 100, 520, 372)
        self.back_btn = pygame.Rect(45, h - 62, 140, 44)

        self.row_music = 120
        self.row_sound = 188
        self.row_volume = 256
        self.row_mobile = 324
        self.row_graphics = 392

        self.music_toggle = pygame.Rect(550, self.row_music + 4, 86, 38)
        self.sound_toggle = pygame.Rect(550, self.row_sound + 4, 86, 38)
        self.mobile_toggle = pygame.Rect(550, self.row_mobile + 4, 86, 38)

        self.slider_track = pygame.Rect(370, self.row_volume + 19, 170, 8)
        self.slider_area = pygame.Rect(355, self.row_volume, 200, 46)

        self.gfx_left = pygame.Rect(500, self.row_graphics + 5, 34, 36)
        self.gfx_right = pygame.Rect(608, self.row_graphics + 5, 34, 36)


    def get_bool(self, key, default=True):
        return bool(self.settings.get(key, default))

    def get_volume(self):
        try:
            value = int(self.settings.get("sound_volume", 80))
        except (TypeError, ValueError):
            value = 80

        return max(0, min(100, value))

    def get_graphics(self):
        value = str(self.settings.get("graphics", "high")).lower()

        return value if value in GRAPHICS_LEVELS else "high"

    def set_value(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)
        self.changed = True

    def toggle(self, key, default=True):
        self.set_value(key, not self.get_bool(key, default))

    def step_graphics(self, step):
        index = GRAPHICS_LEVELS.index(self.get_graphics())
        index = max(0, min(len(GRAPHICS_LEVELS) - 1, index + step))
        self.set_value("graphics", GRAPHICS_LEVELS[index])

    def set_volume_from_mouse(self, mouse_x):
        ratio = (mouse_x - self.slider_track.x) / self.slider_track.width
        value = int(round(max(0, min(1, ratio)) * 100))

        if value != self.get_volume():
            self.set_value("sound_volume", value)


    def draw_row_label(self, y, icon, title, sub):
        theme.icon_tile(self.screen, (162, y, 46, 46), icon)
        theme.text(self.screen, title, 19, (222, y + 2), bold=True)
        theme.text(
            self.screen, sub, 12, (222, y + 28), color=theme.MUTED
        )

    def draw_separator(self, y):
        pygame.draw.line(
            self.screen, (80, 12, 22), (162, y + 57), (638, y + 57), 1
        )

    def draw_slider(self):
        track = self.slider_track
        volume = self.get_volume()
        knob_x = track.x + int(track.width * volume / 100)

        pygame.draw.rect(
            self.screen, (60, 14, 22), track, border_radius=4
        )

        fill = pygame.Rect(track.x, track.y, knob_x - track.x, track.height)

        if fill.width > 0:
            pygame.draw.rect(
                self.screen, theme.RED_BRIGHT, fill, border_radius=4
            )

        pygame.draw.circle(
            self.screen, theme.WHITE, (knob_x, track.centery), 11
        )
        pygame.draw.circle(
            self.screen, theme.RED, (knob_x, track.centery), 11, 2
        )

        theme.text(
            self.screen,
            f"{volume}%",
            17,
            (610, track.centery),
            bold=True,
            center=True
        )

    def draw_arrow(self, rect, direction, enabled):
        hover = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        color = (
            theme.WHITE if hover
            else theme.RED_BRIGHT if enabled
            else (90, 30, 38)
        )

        cx, cy = rect.center
        d = -1 if direction == "left" else 1

        pygame.draw.polygon(
            self.screen,
            color,
            [(cx - d * 6, cy - 9), (cx - d * 6, cy + 9), (cx + d * 7, cy)]
        )

    def draw_graphics(self):
        level = self.get_graphics()
        index = GRAPHICS_LEVELS.index(level)

        self.draw_arrow(self.gfx_left, "left", index > 0)
        self.draw_arrow(self.gfx_right, "right", index < 2)

        theme.text(
            self.screen,
            level.upper(),
            16,
            ((self.gfx_left.right + self.gfx_right.x) // 2,
             self.row_graphics + 23),
            bold=True,
            center=True
        )

    def draw(self):
        theme.draw_background(self.screen, self.w, self.h)

        theme.heading(self.screen, "SETTINGS", (self.w // 2, 55), 32)

        theme.panel(self.screen, self.panel, alpha=230, cut=18)

        self.draw_row_label(
            self.row_music, "music", "MUSIC", "Background music"
        )
        theme.toggle(self.screen, self.music_toggle, self.get_bool("music_enabled"))
        self.draw_separator(self.row_music)

        self.draw_row_label(
            self.row_sound, "speaker", "SOUND", "Button + game sounds"
        )
        theme.toggle(self.screen, self.sound_toggle, self.get_bool("sound_enabled"))
        self.draw_separator(self.row_sound)

        self.draw_row_label(
            self.row_volume, "speaker", "VOLUME", "Music + sounds"
        )
        self.draw_slider()
        self.draw_separator(self.row_volume)

        self.draw_row_label(
            self.row_mobile, "mobile", "MOBILE", "On-screen buttons"
        )
        theme.toggle(
            self.screen,
            self.mobile_toggle,
            self.get_bool("mobile_controls", False)
        )
        self.draw_separator(self.row_mobile)

        self.draw_row_label(
            self.row_graphics, "graphics", "GRAPHICS", "Effects quality"
        )
        self.draw_graphics()

        theme.icon_button(
            self.screen, self.back_btn, "BACK", "back",
            size=17, radius=8
        )


    def handle_events(self, events):
        self.action = None
        self.clicked = False

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_down(event.pos)

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.set_volume_from_mouse(event.pos[0])

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.action = "back"

    def mouse_down(self, pos):
        if self.back_btn.collidepoint(pos):
            self.clicked = True
            self.action = "back"

        elif self.music_toggle.collidepoint(pos):
            self.clicked = True
            self.toggle("music_enabled", True)

        elif self.sound_toggle.collidepoint(pos):
            self.clicked = True
            self.toggle("sound_enabled", True)

        elif self.mobile_toggle.collidepoint(pos):
            self.clicked = True
            self.toggle("mobile_controls", False)

        elif self.gfx_left.collidepoint(pos):
            self.clicked = True
            self.step_graphics(-1)

        elif self.gfx_right.collidepoint(pos):
            self.clicked = True
            self.step_graphics(1)

        elif self.slider_area.collidepoint(pos):
            self.dragging = True
            self.set_volume_from_mouse(pos[0])