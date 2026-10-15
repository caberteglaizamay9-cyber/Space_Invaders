import pygame
from db import load_leaderboard
import theme


class Leader:
    PERIODS = ("all", "weekly", "daily")
    LABELS = ["ALL TIME", "WEEKLY", "DAILY"]

    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None
        self.clicked = False

        self.panel = pygame.Rect(100, 92, 600, 412)
        self.tab_bar = pygame.Rect(125, 108, 550, 38)
        self.tab_rects = theme.tab_rects(self.tab_bar, 3)
        self.back_btn = pygame.Rect(45, h - 62, 140, 44)

        self.period = 0
        self.rows = []
        self.scroll = 0
        self.visible_rows = 8
        self.load_data()

    def load_data(self):
        self.rows = load_leaderboard(100, self.PERIODS[self.period])
        self.scroll = 0

    def my_id(self):
        if isinstance(self.player, dict):
            return self.player.get("player_id")

        return None

    def draw_table(self):
        left = self.panel.x + 22
        right = self.panel.right - 22
        table_w = right - left

        head = pygame.Rect(left, 158, table_w, 30)

        theme.glass(
            self.screen, head, alpha=235, radius=7,
            color=(40, 6, 13), border=(150, 26, 40), border_w=1, glow=False
        )

        col_rank = left + 16
        col_name = left + 82
        col_score = left + 370
        col_level = left + 480

        for label, x in (
            ("#", col_rank), ("PLAYER", col_name),
            ("SCORE", col_score), ("LEVEL", col_level)
        ):
            surface = theme.font(13, True).render(label, True, theme.MUTED)
            self.screen.blit(
                surface, (x, head.centery - surface.get_height() // 2)
            )

        if not self.rows:
            theme.text(
                self.screen, "NO SCORES YET", 20,
                (self.w // 2, 320), center=True, color=theme.MUTED
            )
            return

        row_h = 38
        list_top = head.bottom + 8
        visible = self.visible_rows
        max_scroll = max(0, len(self.rows) - visible)
        self.scroll = max(0, min(self.scroll, max_scroll))

        if max_scroll > 0:
            track = pygame.Rect(
                self.panel.right - 14, list_top, 5, visible * row_h - 4
            )
            pygame.draw.rect(
                self.screen, theme.GREY_BORDER, track, border_radius=3
            )

            thumb_h = max(30, int(track.height * visible / len(self.rows)))
            thumb_y = track.y + int(
                (track.height - thumb_h) * self.scroll / max_scroll
            )
            pygame.draw.rect(
                self.screen,
                theme.RED_BRIGHT,
                (track.x, thumb_y, track.width, thumb_h),
                border_radius=3
            )

        for index, row in enumerate(self.rows, start=1):
            if index - 1 < self.scroll or index - 1 >= self.scroll + visible:
                continue

            y = list_top + (index - 1 - self.scroll) * row_h
            rect = pygame.Rect(left, y, table_w, row_h - 5)
            mine = row.get("player_id") == self.my_id()

            if mine:
                theme.fill_red(self.screen, rect, radius=7)
            else:
                theme.glass(
                    self.screen, rect, alpha=220, radius=7,
                    color=(18, 5, 10), border=(95, 16, 28),
                    border_w=1, glow=False
                )

            cy = rect.centery
            bold = index <= 3 or mine

            def put(value, x, color=theme.WHITE):
                surface = theme.font(16, bold).render(value, True, color)
                self.screen.blit(surface, (x, cy - surface.get_height() // 2))

            put(str(index), col_rank, theme.WHITE if mine or index > 3 else theme.RED_BRIGHT)

            pygame.draw.circle(self.screen, (24, 4, 9), (col_name - 20, cy), 13)
            pygame.draw.circle(self.screen, theme.RED, (col_name - 20, cy), 13, 2)
            theme.invader_logo(self.screen, col_name - 20, cy, 11)

            name = str(row.get("username", "PLAYER"))
            f = theme.font(16, bold)

            while f.size(name)[0] > 240 and len(name) > 1:
                name = name[:-1]

            put(name, col_name)
            put(str(row.get("score", 0)), col_score)
            put(str(row.get("level") or "-"), col_level)

    def draw(self):
        theme.draw_background(self.screen, self.w, self.h)

        theme.heading(
            self.screen, "LEADERBOARD", (self.w // 2, 50), 32
        )

        theme.panel(self.screen, self.panel, alpha=225, cut=18)
        theme.tabs(self.screen, self.tab_bar, self.LABELS, self.period)
        self.draw_table()

        theme.icon_button(
            self.screen, self.back_btn, "BACK", "back",
            size=17, radius=8
        )

    def handle_events(self, events):
        self.action = None
        self.clicked = False

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self.scroll -= event.y

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.scroll -= 1
                elif event.key == pygame.K_DOWN:
                    self.scroll += 1
                elif event.key == pygame.K_ESCAPE:
                    self.action = "back"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.back_btn.collidepoint(event.pos):
                        self.action = "back"
                        self.clicked = True
                        continue

                    for i, rect in enumerate(self.tab_rects):
                        if rect.collidepoint(event.pos):
                            self.clicked = True

                            if i != self.period:
                                self.period = i
                                self.load_data()