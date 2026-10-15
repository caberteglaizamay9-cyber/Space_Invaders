import pygame
from db import register_player, login_player
import theme


class LoginManager:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.page = "login"
        self.username = ""
        self.password = ""
        self.confirm = ""
        self.active = "username"
        self.message = ""
        self.logged_in_player = None
        self.show_password = False
        self.clicked = False

        cx = w // 2
        top = 178
        bw = 340
        bx = cx - bw // 2

        self.login_panel = pygame.Rect(cx - 200, top, 400, 300)
        self.register_panel = pygame.Rect(cx - 200, top, 400, 366)

        self.tab_bar = pygame.Rect(bx, top + 20, bw, 42)
        self.login_tab, self.register_tab = theme.tab_rects(self.tab_bar, 2)

        self.login_user_box = pygame.Rect(bx, top + 82, bw, 48)
        self.login_pass_box = pygame.Rect(bx, top + 142, bw, 48)
        self.login_btn = pygame.Rect(bx, top + 206, bw, 48)
        self.login_link = pygame.Rect(cx - 160, top + 262, 320, 26)

        self.register_user_box = pygame.Rect(bx, top + 82, bw, 48)
        self.register_pass_box = pygame.Rect(bx, top + 142, bw, 48)
        self.register_confirm_box = pygame.Rect(bx, top + 202, bw, 48)
        self.register_btn = pygame.Rect(bx, top + 266, bw, 48)
        self.register_link = pygame.Rect(cx - 160, top + 326, 320, 26)


    def draw_title(self):
        theme.title_logo(self.screen, self.w // 2, 92, 46)

    def draw_eye(self, rect):
        x = rect.right - 28
        y = rect.centery
        color = (225, 170, 176)

        pygame.draw.ellipse(
            self.screen, color, (x - 11, y - 7, 22, 14), 2
        )

        if self.show_password:
            pygame.draw.circle(self.screen, color, (x, y), 4)
        else:
            pygame.draw.line(
                self.screen, color, (x - 10, y - 9), (x + 10, y + 9), 2
            )

    def draw_password_box(self, rect, label, value, active):
        display = (
            value if self.show_password else "*" * len(value)
        )

        theme.text_input(
            self.screen,
            rect,
            label,
            value,
            active,
            display=display,
            right_pad=52,
            icon="lock"
        )

        self.draw_eye(rect)

    def draw_message(self, y):
        if self.message:
            theme.pill_text(
                self.screen,
                self.message,
                13,
                (self.w // 2, y),
                alpha=220,
                pad=(16, 6)
            )

    def draw_link(self, rect, question, link):
        f = theme.font(14)
        a = f.render(question + " ", True, theme.MUTED)
        b = theme.font(14, True).render(link, True, theme.RED_BRIGHT)

        x = rect.centerx - (a.get_width() + b.get_width()) // 2
        y = rect.centery - a.get_height() // 2

        self.screen.blit(a, (x, y))
        self.screen.blit(b, (x + a.get_width(), y))

    def draw_login(self):
        theme.text_input(
            self.screen,
            self.login_user_box,
            "Username",
            self.username,
            self.active == "username",
            icon="user"
        )

        self.draw_password_box(
            self.login_pass_box,
            "Password",
            self.password,
            self.active == "password"
        )

        theme.button(self.screen, self.login_btn, "LOGIN", 20)

        self.draw_link(
            self.login_link, "Don't have an account?", "Create one"
        )

        self.draw_message(self.login_panel.bottom + 30)

    def draw_register(self):
        theme.text_input(
            self.screen,
            self.register_user_box,
            "Username",
            self.username,
            self.active == "username",
            icon="user"
        )

        self.draw_password_box(
            self.register_pass_box,
            "Password",
            self.password,
            self.active == "password"
        )

        self.draw_password_box(
            self.register_confirm_box,
            "Confirm password",
            self.confirm,
            self.active == "confirm"
        )

        theme.button(self.screen, self.register_btn, "CREATE ACCOUNT", 19)

        self.draw_link(
            self.register_link, "Already have an account?", "Login"
        )

        self.draw_message(self.register_panel.bottom + 30)

    def draw(self):
        theme.draw_image_background(
            self.screen, self.w, self.h, "glaback.png"
        )
        self.draw_title()

        panel = (
            self.login_panel
            if self.page == "login"
            else self.register_panel
        )

        theme.panel(self.screen, panel, alpha=215, cut=18)

        theme.tabs(
            self.screen,
            self.tab_bar,
            ["LOGIN", "CREATE ACCOUNT"],
            0 if self.page == "login" else 1
        )

        if self.page == "login":
            self.draw_login()
        else:
            self.draw_register()


    def switch_page(self, page):
        self.page = page
        self.username = ""
        self.password = ""
        self.confirm = ""
        self.active = "username"
        self.message = ""
        self.show_password = False

    def handle_events(self, events):
        self.clicked = False

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_click(event.pos)

            elif event.type == pygame.KEYDOWN:
                self.keyboard_input(event)

    def eye_clicked(self, box, pos):
        eye_area = pygame.Rect(box.right - 55, box.y, 55, box.height)
        return eye_area.collidepoint(pos)

    def mouse_click(self, pos):
        if self.login_tab.collidepoint(pos):
            self.clicked = True
            if self.page != "login":
                self.switch_page("login")
            return

        if self.register_tab.collidepoint(pos):
            self.clicked = True
            if self.page != "register":
                self.switch_page("register")
            return

        if self.page == "login":
            if self.login_user_box.collidepoint(pos):
                self.active = "username"

            elif self.login_pass_box.collidepoint(pos):
                if self.eye_clicked(self.login_pass_box, pos):
                    self.clicked = True
                    self.show_password = not self.show_password
                else:
                    self.active = "password"

            elif self.login_btn.collidepoint(pos):
                self.clicked = True
                self.login()

            elif self.login_link.collidepoint(pos):
                self.clicked = True
                self.switch_page("register")

        else:
            if self.register_user_box.collidepoint(pos):
                self.active = "username"

            elif self.register_pass_box.collidepoint(pos):
                if self.eye_clicked(self.register_pass_box, pos):
                    self.clicked = True
                    self.show_password = not self.show_password
                else:
                    self.active = "password"

            elif self.register_confirm_box.collidepoint(pos):
                if self.eye_clicked(self.register_confirm_box, pos):
                    self.clicked = True
                    self.show_password = not self.show_password
                else:
                    self.active = "confirm"

            elif self.register_btn.collidepoint(pos):
                self.clicked = True
                self.register()

            elif self.register_link.collidepoint(pos):
                self.clicked = True
                self.switch_page("login")

    def keyboard_input(self, event):
        if event.key == pygame.K_TAB:
            if self.page == "login":
                self.active = (
                    "password"
                    if self.active == "username"
                    else "username"
                )
            else:
                order = ["username", "password", "confirm"]
                index = order.index(self.active)
                self.active = order[(index + 1) % 3]

        elif event.key == pygame.K_BACKSPACE:
            if self.active == "username":
                self.username = self.username[:-1]
            elif self.active == "password":
                self.password = self.password[:-1]
            elif self.active == "confirm":
                self.confirm = self.confirm[:-1]

        elif event.key == pygame.K_RETURN:
            if self.page == "login":
                self.login()
            else:
                self.register()

        elif event.unicode and event.unicode.isprintable():
            if self.active == "username":
                if len(self.username) < 30:
                    self.username += event.unicode

            elif self.active == "password":
                if len(self.password) < 30:
                    self.password += event.unicode

            elif self.active == "confirm":
                if len(self.confirm) < 30:
                    self.confirm += event.unicode


    def login(self):
        if not self.username or not self.password:
            self.message = "PLEASE ENTER ALL FIELDS"
            return

        player = login_player(
            self.username.strip(),
            self.password
        )

        if player:
            self.logged_in_player = player
            self.message = ""
        else:
            self.message = "INVALID USERNAME OR PASSWORD"

    def register(self):
        if not self.username or not self.password or not self.confirm:
            self.message = "PLEASE ENTER ALL FIELDS"
            return

        username = self.username.strip()

        if len(username) < 3:
            self.message = "USERNAME MUST BE AT LEAST 3 CHARACTERS"
            return

        if len(self.password) < 3:
            self.message = "PASSWORD MUST BE AT LEAST 3 CHARACTERS"
            return

        if self.password != self.confirm:
            self.message = "PASSWORDS DO NOT MATCH"
            return

        success, result = register_player(
            username,
            self.password
        )

        if success:
            self.switch_page("login")
            self.message = "ACCOUNT CREATED - PLEASE LOGIN"
        else:
            self.message = result