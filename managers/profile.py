import pygame
from db import update_player_profile, delete_player, get_player_stats
import theme

XP_PER_LEVEL = 50


class Profile:
    def __init__(self, screen, w, h, player):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None
        self.clicked = False
        self.editing = False
        self.confirm_delete = False
        self.message = ""
        self.delete_success_time = 0

        self.player_id = self.get_player_id()
        self.username = self.get_username()

        self.panel = pygame.Rect(140, 92, 520, 414)

        self.username_box = pygame.Rect(270, 122, 340, 46)
        self.save_btn = pygame.Rect(270, 184, 165, 40)
        self.cancel_btn = pygame.Rect(445, 184, 165, 40)

        self.edit_btn = pygame.Rect(170, 396, 460, 40)
        self.logout_btn = pygame.Rect(170, 446, 460, 40)
        self.delete_btn = pygame.Rect(170, 446, 460, 40)

        self.back_btn = pygame.Rect(30, 540, 140, 44)

        self.confirm_panel = pygame.Rect(200, 190, 400, 200)
        self.confirm_no = pygame.Rect(225, 322, 170, 44)
        self.confirm_yes = pygame.Rect(405, 322, 170, 44)

        self.pencil_rect = pygame.Rect(0, 0, 0, 0)

        stats = get_player_stats(self.player_id)

        self.highest_score = stats["highest_score"]
        self.total_games = stats["total_games"]
        self.best_level = stats["best_level"]

        total = stats["total_score"]
        self.level = total // XP_PER_LEVEL + 1
        self.xp = total % XP_PER_LEVEL

    def get_player_id(self):
        if isinstance(self.player, dict):
            return self.player.get("player_id")

        if isinstance(self.player, (tuple, list)):
            return self.player[0]

        return None

    def get_username(self):
        if isinstance(self.player, dict):
            return self.player.get("username", "")

        if isinstance(self.player, (tuple, list)):
            if len(self.player) > 1:
                return self.player[1]

        return ""


    def draw(self):
        theme.draw_background(self.screen, self.w, self.h)

        if self.action == "delete_success":
            theme.heading(
                self.screen, "ACCOUNT DELETED", (self.w // 2, 250), 38
            )

            theme.pill_text(
                self.screen,
                self.message,
                18,
                (self.w // 2, 315),
                bold=False,
                alpha=200,
                pad=(18, 8)
            )

            return

        theme.heading(
            self.screen, "PLAYER PROFILE", (self.w // 2, 50), 32
        )

        theme.panel(self.screen, self.panel, alpha=225, cut=18)

        theme.draw_avatar(self.screen, 215, 160, 38)

        if self.editing:
            self.draw_edit()
        else:
            self.draw_profile()

        theme.icon_button(
            self.screen, self.back_btn, "BACK", "back",
            size=17, radius=8
        )

        if self.confirm_delete:
            self.draw_confirm()

    def draw_xp_bar(self):
        track = pygame.Rect(270, 200, 340, 12)

        theme.glass(
            self.screen, track, alpha=240, radius=6,
            color=theme.RED_DEEP, border=(140, 26, 38), border_w=1,
            glow=False
        )

        fill_w = int((track.width - 4) * self.xp / XP_PER_LEVEL)

        if fill_w > 4:
            theme.fill_red(
                self.screen,
                pygame.Rect(track.x + 2, track.y + 2, fill_w, track.height - 4),
                radius=4
            )

        label = theme.font(12).render(
            f"{self.xp} / {XP_PER_LEVEL} XP", True, theme.MUTED
        )
        self.screen.blit(label, (track.right - label.get_width(), track.bottom + 6))

    def draw_stats(self):
        theme.text(
            self.screen, "STATS", 16, (170, 246),
            bold=True, color=theme.RED_BRIGHT
        )

        box = pygame.Rect(165, 272, 470, 112)

        theme.glass(
            self.screen, box, alpha=235, radius=10,
            color=(14, 4, 8), border=(120, 20, 32), border_w=1, glow=False
        )

        rows = [
            ("star", "Highest Score", str(self.highest_score)),
            ("games", "Total Games", str(self.total_games)),
            ("trophy", "Best Level", str(self.best_level or "-")),
        ]

        for i, (icon, label, value) in enumerate(rows):
            cy = box.y + 19 + i * 37

            theme.draw_icon(self.screen, icon, box.x + 26, cy, theme.RED_BRIGHT)
            theme.text(self.screen, label, 16, (box.x + 52, cy - 10), color=theme.SOFT_WHITE)

            v = theme.font(18, True).render(value, True, theme.WHITE)
            self.screen.blit(v, (box.right - 22 - v.get_width(), cy - v.get_height() // 2))

            if i < len(rows) - 1:
                pygame.draw.line(
                    self.screen, (70, 12, 22),
                    (box.x + 14, cy + 18), (box.right - 14, cy + 18), 1
                )

    def draw_profile(self):
        name = theme.text(
            self.screen, self.username, 28, (270, 122), bold=True
        )

        self.pencil_rect = pygame.Rect(name.right + 8, name.y + 2, 28, 28)
        theme.draw_icon(
            self.screen, "pencil",
            self.pencil_rect.centerx, self.pencil_rect.centery,
            theme.RED_BRIGHT
        )

        theme.text(
            self.screen, f"Level {self.level}", 17, (270, 168),
            color=theme.SOFT_WHITE
        )

        self.draw_xp_bar()
        self.draw_stats()

        theme.icon_button(
            self.screen, self.edit_btn, "EDIT PROFILE", "pencil", size=17
        )
        theme.icon_button(
            self.screen, self.logout_btn, "LOG OUT", "logout", size=17
        )

    def draw_edit(self):
        theme.text_input(
            self.screen,
            self.username_box,
            "Username",
            self.username,
            True,
            icon="user"
        )

        theme.button(self.screen, self.save_btn, "SAVE", 17)
        theme.icon_button(self.screen, self.cancel_btn, "CANCEL", None, size=17)

        if self.message:
            theme.pill_text(
                self.screen,
                self.message,
                14,
                (self.w // 2, 262),
                alpha=230,
                pad=(14, 5)
            )

        theme.icon_button(
            self.screen, self.delete_btn, "DELETE ACCOUNT", "exit", size=17
        )

    def draw_confirm(self):
        theme.overlay(self.screen, 190)
        theme.panel(self.screen, self.confirm_panel, alpha=245, cut=16)

        theme.glow_text(
            self.screen, "DELETE ACCOUNT?", 26,
            (self.w // 2, 232)
        )

        theme.text(
            self.screen, "This cannot be undone.", 15,
            (self.w // 2, 276), center=True, color=theme.SOFT_WHITE
        )

        theme.icon_button(self.screen, self.confirm_no, "CANCEL", None, size=16)
        theme.button(self.screen, self.confirm_yes, "DELETE", 16)


    def handle_events(self, events):
        self.clicked = False

        if self.action == "delete_success":
            if pygame.time.get_ticks() - self.delete_success_time >= 2000:
                self.action = "deleted"
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_click(event.pos)

            elif event.type == pygame.KEYDOWN:
                if self.confirm_delete:
                    if event.key == pygame.K_ESCAPE:
                        self.confirm_delete = False

                elif self.editing:
                    self.keyboard_input(event)

    def start_edit(self):
        self.clicked = True
        self.editing = True
        self.username = self.get_username()
        self.message = ""

    def mouse_click(self, pos):
        if self.confirm_delete:
            if self.confirm_no.collidepoint(pos):
                self.clicked = True
                self.confirm_delete = False

            elif self.confirm_yes.collidepoint(pos):
                self.clicked = True
                self.confirm_delete = False
                self.delete_account()

            return

        if self.back_btn.collidepoint(pos):
            self.clicked = True
            self.action = "back"
            return

        if not self.editing:
            if self.edit_btn.collidepoint(pos) or self.pencil_rect.collidepoint(pos):
                self.start_edit()

            elif self.logout_btn.collidepoint(pos):
                self.clicked = True
                self.action = "logout"

        else:
            if self.save_btn.collidepoint(pos):
                self.clicked = True
                self.save_profile()

            elif self.cancel_btn.collidepoint(pos):
                self.clicked = True
                self.editing = False
                self.username = self.get_username()
                self.message = ""

            elif self.delete_btn.collidepoint(pos):
                self.clicked = True
                self.confirm_delete = True

    def keyboard_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.username = self.username[:-1]

        elif event.key == pygame.K_RETURN:
            self.save_profile()

        elif event.unicode and event.unicode.isprintable():
            if len(self.username) < 30:
                self.username += event.unicode


    def save_profile(self):
        username = self.username.strip()

        if not username:
            self.message = "PLEASE ENTER A USERNAME"
            return

        if len(username) < 3:
            self.message = "USERNAME MUST BE AT LEAST 3 CHARACTERS"
            return

        success = update_player_profile(
            self.player_id,
            username
        )

        if success:
            self.username = username

            if isinstance(self.player, dict):
                self.player["username"] = username

            self.editing = False
            self.message = ""
        else:
            self.message = "USERNAME ALREADY EXISTS"

    def delete_account(self):
        player_name = self.get_username()

        success = delete_player(self.player_id)

        if success:
            self.message = f"{player_name} SUCCESSFULLY DELETED"
            self.delete_success_time = pygame.time.get_ticks()
            self.action = "delete_success"
        else:
            self.message = "DELETE ACCOUNT FAILED"