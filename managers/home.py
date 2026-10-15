import pygame
import theme


class Home:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None
        self.clicked = False

        cx = w // 2
        btn_w = 300

        self.play_btn = pygame.Rect(cx - btn_w // 2, 276, btn_w, 58)
        self.leaderboard_btn = pygame.Rect(cx - btn_w // 2, 348, btn_w, 48)
        self.settings_btn = pygame.Rect(cx - btn_w // 2, 408, btn_w, 48)
        self.quit_btn = pygame.Rect(cx - btn_w // 2, 468, btn_w, 48)

        self.profile_btn = pygame.Rect(w - 220 - 14, 14, 220, 48)

    def get_username(self):
        if isinstance(self.player, dict):
            return self.player.get("username", "PLAYER")

        if self.player:
            return str(self.player)

        return "PLAYER"

    def draw_profile_chip(self):
        rect = self.profile_btn
        hover = rect.collidepoint(pygame.mouse.get_pos())

        theme.glass(
            self.screen,
            rect,
            alpha=235,
            radius=12,
            color=(40, 6, 13) if hover else theme.BLACK_PANEL,
            border=theme.WHITE if hover else theme.RED,
            border_w=2,
            glow=hover
        )

        theme.draw_avatar(self.screen, rect.x + 27, rect.centery, 17)

        name = self.get_username().upper()
        f = theme.font(15, True)

        while f.size(name)[0] > 140 and len(name) > 1:
            name = name[:-1]

        self.screen.blit(
            f.render(name, True, theme.WHITE),
            (rect.x + 54, rect.y + 7)
        )

        theme.text(
            self.screen,
            "VIEW PROFILE",
            10,
            (rect.x + 54, rect.y + 27),
            bold=True,
            color=theme.RED_BRIGHT
        )

    def draw(self):
        theme.draw_image_background(
            self.screen, self.w, self.h, "glamenu.png"
        )

        theme.title_logo(self.screen, self.w // 2, 128, 72)

        theme.spaced_text(
            self.screen,
            "DEFEND EARTH  \u2022  SURVIVE  \u2022  BE THE BEST",
            12,
            (self.w // 2, 246),
            spacing=3
        )

        theme.icon_button(
            self.screen, self.play_btn, "PLAY", "play",
            size=24, radius=12, primary=True
        )

        theme.icon_button(
            self.screen, self.leaderboard_btn, "LEADERBOARD", "trophy",
            size=18
        )

        theme.icon_button(
            self.screen, self.settings_btn, "SETTINGS", "settings",
            size=18
        )

        theme.icon_button(
            self.screen, self.quit_btn, "QUIT", "exit",
            size=18
        )

        self.draw_profile_chip()

    def handle_events(self, events):
        self.action = None
        self.clicked = False

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_click(event.pos)

                    if self.action:
                        self.clicked = True

    def mouse_click(self, pos):
        if self.play_btn.collidepoint(pos):
            self.action = "play"

        elif self.leaderboard_btn.collidepoint(pos):
            self.action = "leaderboard"

        elif self.settings_btn.collidepoint(pos):
            self.action = "settings"

        elif self.quit_btn.collidepoint(pos):
            self.action = "quit"

        elif self.profile_btn.collidepoint(pos):
            self.action = "profile"