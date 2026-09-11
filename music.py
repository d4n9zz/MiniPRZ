import pygame
import settings


def play_menu():
    try:
        if pygame.mixer is None:
            return
        pygame.mixer.music.stop()
        pygame.mixer.music.load(settings.MUSIC_MENU)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
    except Exception:
        pass


def play_game():
    try:
        if pygame.mixer is None:
            return
        pygame.mixer.music.stop()
        pygame.mixer.music.load(settings.MUSIC_GAME)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
    except Exception:
        pass


def fade_music_volume(target_volume):
    try:
        if pygame.mixer is None:
            return
        volume = max(0.0, min(1.0, float(target_volume)))
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME * volume)
    except Exception:
        pass


def pause_music():
    try:
        if pygame.mixer is not None and pygame.mixer.get_init():
            pygame.mixer.music.pause()
    except Exception:
        pass


def resume_music():
    try:
        if pygame.mixer is not None and pygame.mixer.get_init():
            pygame.mixer.music.unpause()
    except Exception:
        pass