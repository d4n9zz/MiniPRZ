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
        # Хранилище шрифтов и изображений, чтобы не грузить их повторно
        self.fonts = {}
        self.images = {}

    def load_fonts(self):
        # Загружаем шрифты разных размеров для меню, интерфейса и эффектов
        self.fonts['normal'] = load_font(28)
        self.fonts['big'] = load_font(60)
        self.fonts['small'] = load_font(20)
        self.fonts['card'] = load_font(16)
        self.fonts['damage'] = load_font(32)

        # Сохраняем шрифты в глобальные настройки, чтобы ими пользовались другие модули
        settings.font = self.fonts['normal']
        settings.big_font = self.fonts['big']
        settings.small_font = self.fonts['small']
        settings.card_font = self.fonts['card']
        settings.damage_font = self.fonts['damage']

    @staticmethod
    def load_unit_images():
        # Загружаем спрайты всех типов юнитов для игрока и ботов
        unit_types = ['pawn', 'knight', 'archer', 'mage']
        settings.player_unit_imgs = {}
        settings.bot_unit_imgs = {}

        for utype in unit_types:
            settings.player_unit_imgs[utype] = load_unit_image(
                os.path.join("resources", "paws", "player", f"player_{utype}.png")
            )

        bot_folders = []
        bot_root = os.path.join("resources", "paws", "bot")
        if os.path.isdir(bot_root):
            bot_folders = sorted(
                entry for entry in os.listdir(bot_root)
                if os.path.isdir(os.path.join(bot_root, entry))
            )
        if not bot_folders:
            bot_folders = ["bot0", "bot1", "bot2"]

        for bot_folder in bot_folders:
            bot_index = 0
            try:
                bot_index = int(bot_folder.replace("bot", ""))
            except ValueError:
                bot_index = 0

            settings.bot_unit_imgs[bot_index] = {}
            for utype in unit_types:
                bot_img_path = os.path.join(
                    "resources", "paws", "bot", bot_folder, f"bot_{utype}{bot_index}.png"
                )
                settings.bot_unit_imgs[bot_index][utype] = load_unit_image(bot_img_path)
                if settings.bot_unit_imgs[bot_index][utype] is None:
                    fallback_path = os.path.join(
                        "resources", "paws", "bot", bot_folder, f"bot_{utype}.png"
                    )
                    settings.bot_unit_imgs[bot_index][utype] = load_unit_image(fallback_path)

    @staticmethod
    def load_ui_images():
        # Загружаем иконку GitHub, если файл существует
        if os.path.exists(settings.GITHUB_ICON_PATH):
            try:
                img = pygame.image.load(settings.GITHUB_ICON_PATH).convert_alpha()
                settings.github_icon_img = pygame.transform.smoothscale(img, (64, 64))
            except pygame.error:
                settings.github_icon_img = None


def main():
    # Настройка аудио перед инициализацией Pygame
    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.init()

    try:
        # Пробуем запустить музыку/эффекты
        pygame.mixer.init()
    except pygame.error:
        print("Warning: Audio not available, running without sound")
        pygame.mixer = None

    # Создаём окно игры и главный таймер кадров
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MiniPRZ")
    clock = pygame.time.Clock()

    # Подгружаем всё, что нужно для стартового экрана и игровой логики
    resources = ResourceManager()
    resources.load_fonts()
    ResourceManager.load_unit_images()
    ResourceManager.load_ui_images()

    # Главный цикл: меню -> игра -> выход
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