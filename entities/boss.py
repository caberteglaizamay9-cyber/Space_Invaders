import pygame
import theme


class BossBullet:
    def __init__(self, x, y, dx=0, speed=6):
        self.width = 14
        self.height = 30
        self.x = x - self.width // 2
        self.y = y
        self.dx = dx
        self.speed = speed
        self.active = True

    def update(self):
        self.x += self.dx
        self.y += self.speed

        if self.y > 640 or self.x < -40 or self.x > 840:
            self.active = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if not self.active:
            return

        rect = self.get_rect()
        pygame.draw.rect(screen, (230, 35, 50), rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=6)
        pygame.draw.rect(
            screen,
            (255, 200, 120),
            (rect.centerx - 2, rect.y + 6, 4, rect.height - 12),
            border_radius=2
        )


class Boss:
    """Big enemy that shows up every 5th level.
    Slides left/right, shoots down at the player and has an HP bar."""

    def __init__(self, level, screen_width):
        self.width = 150
        self.height = 150
        self.level = level
        self.screen_width = screen_width

        self.image = theme.load_image(
            ("glamy.png", "glaboss.png", "boss.png"),
            (self.width, self.height)
        )

        if self.image is None:
            self.image = theme.enemy_sprite(self.width)

        tier = max(1, level // 5)

        self.max_hp = 45 + (tier - 1) * 25
        self.hp = self.max_hp

        self.x = screen_width / 2 - self.width / 2
        self.y = -self.height
        self.target_y = 90

        self.state = "entering"
        self.direction = 1
        self.speed = min(3 + tier * 0.7, 7)

        self.shoot_interval = max(22, 55 - tier * 8)
        self.bullet_speed = min(7 + tier * 0.6, 11)
        self.shoot_timer = self.shoot_interval + 30
        self.five_way = tier >= 2

        self.hit_flash = 0
        self.active = True

    def update(self):
        """Move the boss. Returns a list of new BossBullet objects."""
        new_bullets = []

        if not self.active:
            return new_bullets

        if self.hit_flash > 0:
            self.hit_flash -= 1

        if self.state == "entering":
            self.y += 2

            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "fighting"

            return new_bullets

        self.x += self.direction * self.speed

        if self.x <= 20:
            self.x = 20
            self.direction = 1

        elif self.x >= self.screen_width - self.width - 20:
            self.x = self.screen_width - self.width - 20
            self.direction = -1

        self.shoot_timer -= 1

        if self.shoot_timer <= 0:
            if self.hp <= self.max_hp / 2:
                self.shoot_timer = int(self.shoot_interval * 0.65)
            else:
                self.shoot_timer = self.shoot_interval

            cx = self.x + self.width / 2
            cy = self.y + self.height - 25

            spread = (-4, -2, 0, 2, 4) if self.five_way else (-2, 0, 2)

            for dx in spread:
                new_bullets.append(BossBullet(cx, cy, dx, self.bullet_speed))

        return new_bullets

    def hit(self):
        self.hp -= 1
        self.hit_flash = 4

        if self.hp <= 0:
            self.hp = 0
            self.active = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if not self.active:
            return

        if self.hit_flash > 0:
            flash = self.image.copy()
            flash.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(flash, (self.x, self.y))
        else:
            screen.blit(self.image, (self.x, self.y))

    def draw_hp_bar(self, screen, screen_width=None):
        """Small HP bar right under the boss, moves with it, shows HP count."""
        if not self.active:
            return

        bar_w = 110
        bar_h = 8
        x = int(self.x + self.width / 2 - bar_w / 2)
        y = int(self.y + self.height + 4)

        pygame.draw.rect(screen, (60, 8, 16), (x, y, bar_w, bar_h), border_radius=4)

        fill_w = int(bar_w * self.hp / self.max_hp)

        if fill_w > 0:
            pygame.draw.rect(
                screen, (230, 35, 50), (x, y, fill_w, bar_h), border_radius=4
            )

        pygame.draw.rect(
            screen, (255, 255, 255), (x, y, bar_w, bar_h), 1, border_radius=4
        )

        theme.text(
            screen,
            f"{self.hp}/{self.max_hp}",
            13,
            (x + bar_w // 2, y + bar_h + 10),
            bold=True,
            center=True
        )