import pygame
import sys
import os
import settings
from settings import WIDTH, HEIGHT
from utils import load_font, load_unit_image
from menu import main_menu
from game import Game


class ResourceManager:
    __slots__ = ['fonts', 'images']

    def __init__(self):
        self.fonts = {}
        self.images = {}

    def load_fonts(self):
        self.fonts['normal'] = load_font(28)
        self.fonts['big'] = load_font(60)
        self.fonts['small'] = load_font(20)
        self.fonts['card'] = load_font(16)
        self.fonts['damage'] = load_font(32)
        settings.font = self.fonts['normal']
        settings.big_font = self.fonts['big']
        settings.small_font = self.fonts['small']
        settings.card_font = self.fonts['card']
        settings.damage_font = self.fonts['damage']

    @staticmethod
    def load_unit_images():
        unit_types = ['pawn', 'knight', 'archer', 'mage']
        for utype in unit_types:
            settings.player_unit_imgs[utype] = load_unit_image(f"resources/paws_png/player_{utype}.png")
            settings.bot_unit_imgs[utype] = load_unit_image(f"resources/paws_png/bot_{utype}.png")

    @staticmethod
    def load_ui_images():
        if os.path.exists(settings.GITHUB_ICON_PATH):
            try:
                img = pygame.image.load(settings.GITHUB_ICON_PATH).convert_alpha()
                settings.github_icon_img = pygame.transform.smoothscale(img, (64, 64))
            except pygame.error:
                settings.github_icon_img = None


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MiniPRZ")
    clock = pygame.time.Clock()
    resources = ResourceManager()
    resources.load_fonts()
    ResourceManager.load_unit_images()
    ResourceManager.load_ui_images()
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