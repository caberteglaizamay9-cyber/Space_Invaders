import pygame

pygame.init()

try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"Audio init failed: {e}")

import theme
from db import setup_database

from managers.login import LoginManager
from managers.game_manager import GameManager
from managers.home import Home
from managers.profile import Profile
from managers.leader import Leader
from managers.settings_screen import SettingsScreen
from managers.settings_manager import load_settings

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption(
    "Space Invaders by Caberte, Glaiza May"
)


click_sound = None
click_path = theme.find_asset("glabutton.mp3")

if click_path:
    try:
        click_sound = pygame.mixer.Sound(click_path)
    except pygame.error:
        click_sound = None


def play_click():
    if not click_sound:
        return

    settings = load_settings()

    if not settings.get("sound_enabled", True):
        return

    try:
        volume = int(settings.get("sound_volume", 80))
    except (TypeError, ValueError):
        volume = 80

    click_sound.set_volume(max(0, min(100, volume)) / 100)
    click_sound.play()


music_path = theme.find_asset("glamusic.mp3")


def play_music(force=False):
    if not music_path:
        print("glamusic.mp3 not found")
        return

    settings = load_settings()

    if not settings.get("music_enabled", True):
        pygame.mixer.music.stop()
        return

    try:
        volume = int(settings.get("sound_volume", 80))
    except (TypeError, ValueError):
        volume = 80

    try:
        if force or not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)

        pygame.mixer.music.set_volume(max(0, min(100, volume)) / 100)

    except pygame.error as e:
        print(f"Music error: {e}")


setup_database()

login = LoginManager(
    screen,
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)

game = GameManager(
    screen,
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)

home = None
profile = None
leader = None
settings_screen = None
current_screen = "login"

play_music(force=True)

clock = pygame.time.Clock()
running = True

while running:

    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

    if current_screen == "login":

        login.handle_events(events)

        if login.clicked:
            play_click()

        login.draw()

        if login.logged_in_player is not None:

            home = Home(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "home"

    elif current_screen == "home":

        home.handle_events(events)

        if home.clicked:
            play_click()

        home.draw()

        if home.action == "profile":

            home.action = None

            profile = Profile(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "profile"

        elif home.action == "leaderboard":

            home.action = None

            leader = Leader(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "leader"

        elif home.action == "settings":

            home.action = None

            settings_screen = SettingsScreen(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT
            )

            current_screen = "settings"

        elif home.action == "play":

            home.action = None

            game.current_player_id = (
                login.logged_in_player["player_id"]
            )

            game.player_name = (
                login.logged_in_player["username"]
            )

            game.start_again()

            current_screen = "game"

        elif home.action == "quit":

            home.action = None

            login.logged_in_player = None
            login.switch_page("login")
            home = None
            profile = None
            leader = None
            settings_screen = None

            current_screen = "login"

    elif current_screen == "profile":

        profile.handle_events(events)

        if profile.clicked:
            play_click()

        profile.draw()

        if profile.player is not None:
            login.logged_in_player = profile.player

        if profile.action == "back":

            profile.action = None

            home = Home(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "home"

        elif profile.action == "logout":

            profile.action = None

            login.logged_in_player = None
            login.switch_page("login")
            home = None
            profile = None
            leader = None
            settings_screen = None

            current_screen = "login"

        elif profile.action == "deleted":

            login.logged_in_player = None
            login.switch_page("login")
            profile = None
            home = None
            leader = None
            settings_screen = None

            current_screen = "login"

    elif current_screen == "leader":

        leader.handle_events(events)

        if leader.clicked:
            play_click()

        leader.draw()

        if leader.action == "back":

            leader.action = None

            home = Home(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "home"

    elif current_screen == "settings":

        settings_screen.handle_events(events)

        if settings_screen.clicked:
            play_click()

        settings_screen.draw()

        if settings_screen.changed:
            settings_screen.changed = False
            play_music()

        if settings_screen.action == "back":

            settings_screen.action = None

            home = Home(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "home"

    elif current_screen == "game":

        game.update(events)
        game.draw()

        if game.game_state == "back_home":

            game.game_state = "playing"

            home = Home(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            play_music(force=True)

            current_screen = "home"

    pygame.display.update()
    clock.tick(60)

pygame.quit()