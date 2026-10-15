import importlib
import math
import random
import pygame

import theme
from db import save_score, get_player_highest_score
try:
    from settings_manager import load_settings
except ImportError:
    from managers.settings_manager import load_settings


def _load_class(module, cls):
    """Find player.py / enemy.py / bullet.py / button.py whether they sit
    next to main.py or inside a sub folder (entities, classes, ...)."""
    for prefix in ("", "entities.", "classes.", "models.", "objects.", "managers."):
        try:
            return getattr(importlib.import_module(prefix + module), cls)
        except (ImportError, AttributeError):
            continue

    raise ImportError(f"Cannot find class {cls} in module {module}")


Player = _load_class("player", "Player")
Enemy = _load_class("enemy", "Enemy")
Bullet = _load_class("bullet", "Bullet")
MobileButtons = _load_class("button", "MobileButtons")
Boss = _load_class("boss", "Boss")


class GameManager:
    START_SCORE = 1
    SCORE_PER_KILL = 1
    MAX_LIVES = 3
    FIRE_DELAY = 12
    INVULN_FRAMES = 60
    BOSS_EVERY = 5
    BOSS_KILL_SCORE = 20
    ROUNDS_BASE = 3

    FX_AMOUNT = {"low": 0.35, "medium": 0.7, "high": 1.0}

    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.current_player_id = None
        self.player_name = "PLAYER"
        self.game_state = "playing"
        self.settings = {}

        self.pause_btn = pygame.Rect(w - 42, 10, 32, 32)

        self.fx = 1.0

        self.stars = []
        for _ in range(70):
            self.stars.append([
                random.randint(0, w),
                random.randint(0, h),
                random.uniform(0.4, 2.4),
                random.choice((1, 1, 2))
            ])

        self.music_path = theme.find_asset("glamusic.mp3")
        self.shoot_sound = self.load_sound("glaizallet.mp3")
        self.click_sound = self.load_sound("glabutton.mp3")
        self.music_on = True
        self.sound_on = True

        self.reset()


    def load_sound(self, name):
        path = theme.find_asset(name)

        if not path:
            return None

        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            return None

    def apply_audio(self):
        try:
            volume = int(self.settings.get("sound_volume", 80))
        except (TypeError, ValueError):
            volume = 80

        volume = max(0, min(100, volume)) / 100

        self.music_on = bool(self.settings.get("music_enabled", True))
        self.sound_on = bool(self.settings.get("sound_enabled", True))

        for sound in (self.shoot_sound, self.click_sound):
            if sound:
                sound.set_volume(volume)

        try:
            pygame.mixer.music.set_volume(volume * 0.6)
        except pygame.error:
            pass

    def play_music(self):
        if not (self.music_on and self.music_path):
            self.stop_music()
            return

        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def play(self, sound):
        if self.sound_on and sound:
            sound.play()


    def start_again(self):
        self.settings = load_settings()
        self.apply_audio()
        self.fx = self.FX_AMOUNT.get(
            str(self.settings.get("graphics", "high")).lower(), 1.0
        )
        self.reset()

        if self.current_player_id:
            self.prev_best = get_player_highest_score(self.current_player_id)
            self.best = self.prev_best

        self.play_music()

    def reset(self):
        self.game_state = "playing"
        self.score = self.START_SCORE
        self.lives = self.MAX_LIVES
        self.wave = 1
        self.best = 0
        self.prev_best = 0
        self.score_saved = False
        self.boss = None
        self.boss_bullets = []

        self.player = Player(self.w, self.h)

        if self.settings.get("mobile_controls", False):
            self.mobile = MobileButtons(self.w, self.h)
            self.player.y = self.h - 160
        else:
            self.mobile = None

        self.bullets = []
        self.particles = []
        self.fire_cd = 0

        self.spawn_wave()

    def spawn_wave(self):
        self.boss_bullets = []
        self.banner_timer = 90

        if self.wave % self.BOSS_EVERY == 0:
            self.boss = Boss(self.wave, self.w)
            self.enemies = []
            self.round = 1
            self.rounds_total = 1
            self.drop_interval = 60
            self.drop_timer = 60
            return

        self.boss = None
        self.round = 1

        self.rounds_total = min(self.ROUNDS_BASE + self.wave // 2, 8)

        self.spawn_round()

    def spawn_round(self):
        count = min(4 + self.wave, 8)

        self.enemies = [
            Enemy(i, count, self.w) for i in range(count)
        ]

        speed = min(3 + self.wave * 0.5 + (self.round - 1) * 0.3, 9)

        for enemy in self.enemies:
            enemy.speed = speed

        self.drop_interval = max(25, 100 - self.wave * 8 - self.round * 3)
        self.drop_timer = self.drop_interval + 60
        self.banner_timer = 90

    def finish_score(self):
        if self.score_saved or not self.current_player_id:
            return

        self.score_saved = True
        save_score(self.current_player_id, self.score, self.wave)
        self.best = get_player_highest_score(self.current_player_id)

    def go_home(self):
        if self.game_state in ("game_over", "level_complete"):
            self.finish_score()

        self.stop_music()
        self.game_state = "back_home"


    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if self.game_state == "playing":
                        self.game_state = "paused"
                    elif self.game_state == "paused":
                        self.game_state = "playing"

                elif event.key == pygame.K_RETURN:
                    if self.game_state == "game_over":
                        self.start_again()
                    elif self.game_state == "level_complete":
                        self.next_level()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

        self.update_stars()
        self.update_particles()

        if self.game_state != "playing":
            return

        self.update_play(events)

    def next_level(self):
        self.wave += 1
        self.game_state = "playing"
        self.spawn_wave()

    def overlay_buttons(self):
        """(key, label, icon, rect) for the window that is open now."""
        cx = self.w // 2

        if self.game_state == "paused":
            items = [
                ("resume", "RESUME", "play"),
                ("restart", "RESTART", "restart"),
                ("home", "MAIN MENU", "home"),
            ]
            top = 292

        elif self.game_state == "level_complete":
            items = [
                ("next", "NEXT LEVEL", "play"),
                ("home", "MAIN MENU", "home"),
            ]
            top = 372

        elif self.game_state == "game_over":
            items = [
                ("restart", "PLAY AGAIN", "restart"),
                ("home", "MAIN MENU", "home"),
            ]
            top = 372

        else:
            return []

        return [
            (key, label, icon, pygame.Rect(cx - 140, top + i * 58, 280, 46))
            for i, (key, label, icon) in enumerate(items)
        ]

    def click(self, pos):
        if self.game_state == "playing":
            if self.pause_btn.collidepoint(pos):
                self.play(self.click_sound)
                self.game_state = "paused"

            return

        for key, _label, _icon, rect in self.overlay_buttons():
            if not rect.collidepoint(pos):
                continue

            self.play(self.click_sound)

            if key == "resume":
                self.game_state = "playing"
            elif key == "restart":
                self.start_again()
            elif key == "next":
                self.next_level()
            elif key == "home":
                self.go_home()

            return

    def update_stars(self):
        for star in self.stars:
            star[1] += star[2]

            if star[1] > self.h:
                star[1] = 0
                star[0] = random.randint(0, self.w)

    def update_particles(self):
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1

        self.particles = [p for p in self.particles if p[4] > 0]

    def explode(self, x, y, amount=18):
        colors = [
            (255, 255, 255),
            (255, 90, 100),
            (230, 35, 50),
            (255, 160, 70)
        ]

        amount = max(2, int(amount * self.fx))

        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1, 5)

            self.particles.append([
                x,
                y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.randint(18, 34),
                random.choice(colors)
            ])

    def update_play(self, events):
        player = self.player
        fire = pygame.key.get_pressed()[pygame.K_SPACE]

        if self.mobile and self.mobile.handle_mouse(player, events):
            fire = True

        player.update()

        if self.fire_cd > 0:
            self.fire_cd -= 1

        if fire and self.fire_cd == 0:
            self.bullets.append(
                Bullet(
                    player.x + player.width // 2 - 16,
                    player.y - 20
                )
            )
            self.fire_cd = self.FIRE_DELAY
            self.play(self.shoot_sound)

        if player.is_blinking and player.blink_timer >= self.INVULN_FRAMES:
            player.is_blinking = False
            player.blink_timer = 0
            player.visible = True

        for bullet in self.bullets:
            bullet.update()

        for enemy in self.enemies:
            enemy.update()

        if self.boss:
            self.boss_bullets.extend(self.boss.update())

        for bb in self.boss_bullets:
            bb.update()

        self.update_drops()
        self.check_bullet_hits()
        self.check_boss_hits()
        self.check_player_hits()
        self.check_boss_bullet_hits()

        self.bullets = [b for b in self.bullets if b.is_active]
        self.enemies = [e for e in self.enemies if e.active]
        self.boss_bullets = [b for b in self.boss_bullets if b.active]

        if self.banner_timer > 0:
            self.banner_timer -= 1

        if not self.enemies and self.boss is None and self.game_state == "playing":
            self.bullets = []
            self.boss_bullets = []

            if self.round < self.rounds_total:
                self.round += 1
                self.spawn_round()
            else:
                self.game_state = "level_complete"

    def update_drops(self):
        self.drop_timer -= 1

        if self.drop_timer > 0:
            return

        waiting = [e for e in self.enemies if e.state == "waiting"]
        dropping = sum(1 for e in self.enemies if e.state == "dropping")

        if waiting and dropping < min(1 + self.wave // 2, 4):
            enemy = random.choice(waiting)
            player = self.player

            enemy.start_drop(
                player.x + (player.width - enemy.width) / 2,
                player.y + (player.height - enemy.height) / 2
            )

            self.drop_timer = self.drop_interval
        else:
            self.drop_timer = 10

    def check_bullet_hits(self):
        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            bullet_rect = bullet.get_rect().inflate(-14, -6)

            for enemy in self.enemies:
                if not enemy.active:
                    continue

                if bullet_rect.colliderect(enemy.get_rect().inflate(-16, -16)):
                    enemy.active = False
                    bullet.is_active = False
                    self.score += self.SCORE_PER_KILL

                    self.explode(
                        enemy.x + enemy.width / 2,
                        enemy.y + enemy.height / 2
                    )
                    break

    def check_boss_hits(self):
        boss = self.boss

        if not boss or boss.state != "fighting":
            return

        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            if bullet.get_rect().inflate(-14, -6).colliderect(
                boss.get_rect().inflate(-20, -20)
            ):
                bullet.is_active = False
                boss.hit()
                self.score += self.SCORE_PER_KILL
                self.explode(bullet.x + bullet.width / 2, bullet.y, 5)

                if not boss.active:
                    self.score += self.BOSS_KILL_SCORE
                    self.explode(
                        boss.x + boss.width / 2,
                        boss.y + boss.height / 2,
                        60
                    )
                    self.boss = None
                    self.boss_bullets = []
                    return

    def check_boss_bullet_hits(self):
        player = self.player

        if player.is_blinking or self.game_state != "playing":
            return

        player_rect = player.get_rect().inflate(-30, -30)

        for bb in self.boss_bullets:
            if not bb.active:
                continue

            if player_rect.colliderect(bb.get_rect()):
                bb.active = False
                self.lives -= 1

                self.explode(
                    player.x + player.width / 2,
                    player.y + player.height / 2,
                    14
                )

                if self.lives <= 0:
                    self.explode(
                        player.x + player.width / 2,
                        player.y + player.height / 2,
                        40
                    )
                    self.game_state = "game_over"
                    self.finish_score()
                else:
                    player.is_blinking = True
                    player.blink_timer = 0

                break

    def check_player_hits(self):
        player = self.player

        if player.is_blinking:
            return

        player_rect = player.get_rect().inflate(-30, -30)

        for enemy in self.enemies:
            if not enemy.active:
                continue

            if player_rect.colliderect(enemy.get_rect().inflate(-16, -16)):
                enemy.active = False
                self.lives -= 1

                self.explode(
                    enemy.x + enemy.width / 2,
                    enemy.y + enemy.height / 2
                )

                if self.lives <= 0:
                    self.explode(
                        player.x + player.width / 2,
                        player.y + player.height / 2,
                        40
                    )
                    self.game_state = "game_over"
                    self.finish_score()
                else:
                    player.is_blinking = True
                    player.blink_timer = 0

                break


    def draw(self):
        self.screen.blit(theme.game_background(self.w, self.h), (0, 0))

        self.draw_stars()

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        if self.boss:
            self.boss.draw(self.screen)

        for bb in self.boss_bullets:
            bb.draw(self.screen)

        if self.game_state != "game_over":
            self.player.draw(self.screen)

        self.draw_particles()
        self.draw_hud()

        if self.boss and self.banner_timer <= 0:
            self.boss.draw_hp_bar(self.screen, self.w)

        if self.mobile:
            self.mobile.draw(self.screen)

        if self.game_state == "paused":
            self.draw_pause()

        elif self.game_state == "level_complete":
            self.draw_result("LEVEL COMPLETE")

        elif self.game_state == "game_over":
            self.draw_result("GAME OVER")

    def draw_stars(self):
        for x, y, speed, size in self.stars:
            shade = int(110 + speed * 55)
            pygame.draw.circle(
                self.screen,
                (min(255, shade + 20), int(shade * 0.55), int(shade * 0.6)),
                (int(x), int(y)),
                size
            )

    def draw_particles(self):
        for x, y, _vx, _vy, life, color in self.particles:
            pygame.draw.circle(
                self.screen,
                color,
                (int(x), int(y)),
                max(1, life // 8)
            )

    def draw_hud(self):
        box = dict(alpha=230, radius=8, border=theme.RED, glow=True)

        score_box = pygame.Rect(12, 10, 150, 34)
        theme.glass(self.screen, score_box, **box)

        theme.text(
            self.screen, "SCORE", 12,
            (score_box.x + 14, score_box.centery),
            bold=True, color=theme.MUTED
        )
        surface = theme.font(18, True).render(
            str(self.score), True, theme.WHITE
        )
        self.screen.blit(
            surface,
            (score_box.right - 14 - surface.get_width(),
             score_box.centery - surface.get_height() // 2)
        )

        level_box = pygame.Rect(self.w // 2 - 70, 10, 140, 34)
        theme.glass(self.screen, level_box, **box)

        theme.text(
            self.screen, "LEVEL", 12,
            (level_box.x + 14, level_box.centery),
            bold=True, color=theme.MUTED
        )
        surface = theme.font(18, True).render(
            str(self.wave), True, theme.WHITE
        )
        self.screen.blit(
            surface,
            (level_box.right - 14 - surface.get_width(),
             level_box.centery - surface.get_height() // 2)
        )

        hearts_box = pygame.Rect(self.w - 42 - 8 - 96, 10, 96, 34)
        theme.glass(self.screen, hearts_box, **box)

        for i in range(self.MAX_LIVES):
            theme.draw_heart(
                self.screen,
                hearts_box.x + 22 + i * 26,
                hearts_box.centery,
                17,
                filled=(i < self.lives)
            )

        hover = self.pause_btn.collidepoint(pygame.mouse.get_pos())

        theme.glass(
            self.screen,
            self.pause_btn,
            alpha=240 if hover else 230,
            radius=8,
            color=(60, 8, 16) if hover else theme.BLACK_PANEL,
            border=theme.WHITE if hover else theme.RED,
            glow=True
        )

        theme.draw_icon(
            self.screen,
            "pause",
            self.pause_btn.centerx,
            self.pause_btn.centery
        )

    def draw_buttons(self):
        for i, (_key, label, icon, rect) in enumerate(self.overlay_buttons()):
            theme.icon_button(
                self.screen, rect, label, icon,
                size=17, radius=10, primary=(i == 0)
            )

    def draw_pause(self):
        cx = self.w // 2

        theme.overlay(self.screen, 175)
        theme.panel(
            self.screen, pygame.Rect(cx - 170, 120, 340, 360), alpha=240, cut=18
        )

        pygame.draw.circle(self.screen, (24, 4, 9), (cx, 178), 28)
        pygame.draw.circle(self.screen, theme.RED_BRIGHT, (cx, 178), 28, 3)
        theme.draw_icon(self.screen, "pause", cx, 178)

        theme.glow_text(self.screen, "PAUSED", 36, (cx, 238))
        self.draw_buttons()

    def draw_result(self, title):
        cx = self.w // 2
        new_record = self.score > self.prev_best

        theme.overlay(self.screen, 175)
        theme.panel(
            self.screen, pygame.Rect(cx - 190, 100, 380, 392), alpha=240, cut=18
        )

        for side in (-1, 1):
            for k in range(3):
                y = 150 + k * 9
                pygame.draw.line(
                    self.screen, theme.RED,
                    (cx + side * 26, y - 4),
                    (cx + side * (82 - k * 12), y - 18 + k * 4),
                    3
                )

        theme.draw_icon(self.screen, "star", cx, 150, theme.WHITE)
        theme.draw_icon(self.screen, "star", cx, 150, theme.RED_BRIGHT)

        theme.glow_text(self.screen, title, 30, (cx, 204))

        rows = [
            ("SCORE", str(self.score)),
            ("LEVEL", str(self.wave)),
        ]

        for i, (label, value) in enumerate(rows):
            y = 250 + i * 32

            theme.text(
                self.screen, label, 16, (cx - 120, y),
                bold=True, color=theme.MUTED
            )

            surface = theme.font(20, True).render(value, True, theme.WHITE)
            self.screen.blit(surface, (cx + 120 - surface.get_width(), y - 2))

            pygame.draw.line(
                self.screen, (80, 12, 22),
                (cx - 120, y + 26), (cx + 120, y + 26), 1
            )

        if new_record:
            theme.draw_icon(self.screen, "crown", cx - 92, 338, theme.RED_BRIGHT)
            theme.glow_text(
                self.screen, "NEW HIGH SCORE!", 17, (cx + 10, 338),
                color=theme.SOFT_WHITE
            )
        else:
            theme.text(
                self.screen, f"BEST  {max(self.best, self.prev_best)}", 16,
                (cx, 338), bold=True, center=True, color=theme.MUTED
            )

        self.draw_buttons()