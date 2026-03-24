import pygame
import sys
import settings
from settings import WIDTH, HEIGHT
from utils import load_font, load_unit_image
from menu import main_menu
from game import Game


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MiniPRZ")
    clock = pygame.time.Clock()
    settings.font = load_font(28)
    settings.big_font = load_font(60)
    settings.small_font = load_font(20)
    settings.card_font = load_font(16)
    settings.damage_font = load_font(32)
    unit_types = ['pawn', 'knight', 'archer', 'mage']
    for utype in unit_types:
        settings.player_unit_imgs[utype] = load_unit_image(f"paws_png/player_{utype}.png")
        settings.bot_unit_imgs[utype] = load_unit_image(f"paws_png/bot_{utype}.png")
    while True:
        if not main_menu(screen, clock):
            break
        game = Game(screen, clock)
        if not game.run():
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()