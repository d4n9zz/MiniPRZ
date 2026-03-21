import pygame
import settings

def play_menu():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(settings.MUSIC_MENU)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
    except Exception as e:
        print(f"Music error: {e}")

def play_game():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(settings.MUSIC_GAME)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
    except Exception as e:
        print(f"Music error: {e}")