import pygame
import theme


class Player:
    def __init__(self, screen_width, screen_height):
        self.width = 80
        self.height = 80
        self.speed = 5

        self.image = theme.load_image(
            ("glaship.png", "shanship.png", "spaceship.png"),
            (self.width, self.height)
        )

        if self.image is None:
            self.image = theme.ship_sprite(self.width)

        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - 100
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.is_blinking = False
        self.blink_timer = 0
        self.visible = True

    def move_left(self):
        if not self.is_blinking:
            self.x -= self.speed

    def move_right(self):
        if not self.is_blinking:
            self.x += self.speed

    def keep_inside_screen(self):
        self.x = max(0, min(self.x, self.screen_width - self.width))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update_blink(self):
        if self.is_blinking:
            self.blink_timer += 1

            if self.blink_timer % 6 == 0:
                self.visible = not self.visible
        else:
            self.visible = True

    def update(self):
        keys = pygame.key.get_pressed()

        if not self.is_blinking:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.move_left()

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.move_right()

        self.keep_inside_screen()
        self.update_blink()

    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, (self.x, self.y))