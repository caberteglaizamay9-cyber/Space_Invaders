import pygame
import theme


class Bullet:
    _image = None

    def __init__(self, x, y):
        self.width = 32
        self.height = 32

        if Bullet._image is None:
            image = theme.load_image(
                ("glabullet.png",),
                (self.width, self.height)
            )

            if image is None:
                image = theme.bullet_sprite(self.width, self.height)

            Bullet._image = image

        self.image = Bullet._image
        self.x = x
        self.y = y
        self.speed = 9
        self.is_active = True

    def update(self):
        self.y -= self.speed

        if self.y < -self.height:
            self.is_active = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, (self.x, self.y))