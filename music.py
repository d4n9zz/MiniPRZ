import pygame
import settings


def play_menu():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(settings.MUSIC_MENU)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
    except Exception:
        pass


def play_game():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(settings.MUSIC_GAME)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
    except Exception:
        pass


def fade_music_volume(target_volume):
    try:
        base_volume = settings.MUSIC_VOLUME
        actual_volume = base_volume * target_volume
        pygame.mixer.music.set_volume(actual_volume)
    except Exception:
        pass