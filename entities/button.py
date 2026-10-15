import math
import pygame
import theme


class MobileButtons:
    """Three on-screen buttons: LEFT, RIGHT and FIRE.
    Works with mouse and with real touch (multi-finger)."""

    def __init__(self, w=800, h=600):
        self.w = w
        self.h = h

        self.buttons = {
            "left": (56, h - 52, 28),
            "right": (118, h - 52, 28),
            "fire": (w - 62, h - 58, 36),
        }

        self.fingers = {}
        self.pressed = {"left": False, "right": False, "fire": False}

    def read_points(self, events):
        finger_down = getattr(pygame, "FINGERDOWN", None)
        finger_move = getattr(pygame, "FINGERMOTION", None)
        finger_up = getattr(pygame, "FINGERUP", None)

        for event in events:
            if finger_down is not None and event.type in (finger_down, finger_move):
                self.fingers[event.finger_id] = (
                    event.x * self.w,
                    event.y * self.h
                )

            elif finger_up is not None and event.type == finger_up:
                self.fingers.pop(event.finger_id, None)

        points = list(self.fingers.values())

        if pygame.mouse.get_pressed()[0]:
            points.append(pygame.mouse.get_pos())

        return points

    def handle_mouse(self, player, events):
        points = self.read_points(events)

        for name in self.pressed:
            self.pressed[name] = False

        for px, py in points:
            for name, (cx, cy, r) in self.buttons.items():
                if math.hypot(px - cx, py - cy) <= r + 8:
                    self.pressed[name] = True

        if self.pressed["left"]:
            player.move_left()

        if self.pressed["right"]:
            player.move_right()

        return self.pressed["fire"]

    def draw_button(self, screen, name):
        cx, cy, r = self.buttons[name]
        down = self.pressed[name]

        surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        c = surf.get_width() // 2

        if down:
            fill = (235, 40, 58, 215)
        else:
            fill = (170, 15, 30, 130)

        pygame.draw.circle(surf, fill, (c, c), r)
        pygame.draw.circle(surf, (255, 255, 255, 255 if down else 200), (c, c), r, 2)
        pygame.draw.circle(surf, (255, 255, 255, 60), (c, c), r - 6, 1)

        screen.blit(surf, (cx - c, cy - c))

        white = theme.WHITE

        def sc(value, k):
            return int(round(value * k))

        if name == "left":
            k = r / 40
            pygame.draw.polygon(
                screen, white,
                [(cx + sc(11, k), cy - sc(17, k)),
                 (cx - sc(13, k), cy),
                 (cx + sc(11, k), cy + sc(17, k))]
            )

        elif name == "right":
            k = r / 40
            pygame.draw.polygon(
                screen, white,
                [(cx - sc(11, k), cy - sc(17, k)),
                 (cx + sc(13, k), cy),
                 (cx - sc(11, k), cy + sc(17, k))]
            )

        else:
            k = r / 52
            pygame.draw.circle(screen, white, (cx, cy), sc(13, k))
            pygame.draw.circle(screen, white, (cx, cy), sc(28, k), 2)

            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                pygame.draw.line(
                    screen, white,
                    (cx + dx * sc(22, k), cy + dy * sc(22, k)),
                    (cx + dx * sc(34, k), cy + dy * sc(34, k)),
                    2
                )

    def draw(self, screen):
        for name in ("left", "right", "fire"):
            self.draw_button(screen, name)