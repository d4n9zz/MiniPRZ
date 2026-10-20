import pygame

from config import get_field_size

WIDTH = 1920                        # ширина окна (всегда фиксированная)
HEIGHT = 1080                       # высота окна (всегда фиксированная)
TILE_SIZE = 50                      # размер клетки сетки
INTERFACE_HEIGHT = 80               # высота нижней панели интерфейса
FIELD_HEIGHT = HEIGHT - INTERFACE_HEIGHT  # область окна, в которой стоит карта

# Размеры карты в клетках (колонки, строки). Окно всегда 1920x1080,
# карта выбранного размера ставится по центру. Числа можно менять в любой момент.
# Максимум, который поместится: 38 x 20.
FIELD_PRESETS = {
    'small':  (30, 15),
    'medium': (34, 18),
    'large':  (38, 20),
}
DEFAULT_FIELD_PRESET = 'large'
FIELD_PRESET_KEYS = list(FIELD_PRESETS.keys())  # порядок кнопки выбора карты
MAP_OUTSIDE_COLOR = (18, 24, 38)                # цвет рамки вокруг карты

# Эти значения заполняет apply_field_preset() — их нельзя импортировать
# через "from settings import COLS", только читать как settings.COLS
FIELD_PRESET = DEFAULT_FIELD_PRESET
COLS = ROWS = 0                     # размер карты в клетках
MAP_WIDTH = MAP_HEIGHT = 0          # размер карты в пикселях
MAP_OFFSET_X = MAP_OFFSET_Y = 0     # положение левого верхнего угла карты в окне


def apply_field_preset(key):
    """Применяет размер карты по ключу ('small', 'medium', 'large') и центрует её в окне."""
    global FIELD_PRESET, COLS, ROWS, MAP_WIDTH, MAP_HEIGHT, MAP_OFFSET_X, MAP_OFFSET_Y
    if key not in FIELD_PRESETS:
        key = DEFAULT_FIELD_PRESET
    cols, rows = FIELD_PRESETS[key]
    # карта не может быть больше области под неё
    cols = max(1, min(cols, WIDTH // TILE_SIZE))
    rows = max(1, min(rows, FIELD_HEIGHT // TILE_SIZE))
    FIELD_PRESET = key
    COLS, ROWS = cols, rows
    MAP_WIDTH, MAP_HEIGHT = cols * TILE_SIZE, rows * TILE_SIZE
    MAP_OFFSET_X = (WIDTH - MAP_WIDTH) // 2
    MAP_OFFSET_Y = (FIELD_HEIGHT - MAP_HEIGHT) // 2


apply_field_preset(get_field_size())    # размер карты из config.json

VISIBILITY_RADIUS = 4               # радиус обзора юнитов игрока (в клетках)
TURN_TIME = 25000                   # время на ход игрока (мс)
GAME_VERSION = "0.1.3"              # версия игры

SHAKE_DURATION = 10                 # длительность тряски юнита при ударе (в кадрах)
SHAKE_INTENSITY = 4                 # сила тряски (смещение в пикселях)

MENU_BG_TOP, MENU_BG_BOTTOM = (25, 32, 50), (45, 52, 70)  # градиент фона меню
BG_TOP, BG_BOTTOM = (34, 139, 34), (144, 238, 144)        # градиент фона игрового поля (трава)

GRID_COLOR, GRID_BORDER = (25, 100, 25, 120), (18, 72, 18)  # цвет клеток и их обводка
PLAYER_COLOR, PLAYER_GLOW, PLAYER_HIGHLIGHT = (255, 107, 107), (255, 150, 150), (255, 214, 107)  # цвета игрока
BOT_COLOR, BOT_GLOW = (106, 184, 255), (135, 206, 255)       # цвета первого бота
BOT2_COLOR, BOT2_GLOW = (255, 105, 180), (255, 182, 193)     # цвета второго бота

UI_BG, UI_BORDER, UI_TEXT = (45, 52, 70), (100, 149, 237), (240, 248, 255)  # цвета интерфейса
UI_BUTTON_NORMAL, UI_BUTTON_HOVER, UI_BUTTON_SHADOW = (70, 130, 180), (100, 180, 255), (20, 25, 40)  # состояния кнопок UI
MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER = (100, 149, 237), (135, 206, 250)  # синие кнопки меню
MENU_BTN_RED, MENU_BTN_RED_HOVER = (255, 99, 71), (255, 130, 102)      # красные кнопки меню

HIT_EFFECT_COLORS = [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 105, 180), (138, 43, 226)]  # цвета эффекта удара
DEATH_EFFECT_COLORS = [(255, 0, 0), (255, 69, 0), (139, 0, 0), (255, 140, 0), (100, 0, 0)]        # цвета эффекта смерти

FOG_UNEXPLORED, FOG_EXPLORED_NO_VIS = (15, 20, 35, 230), (30, 40, 60, 90)  # туман: невидимый и виденный ранее
FOG_FADE_TILES = 2  # ширина плавного перехода тумана за пределами радиуса обзора

TIMER_SAFE, TIMER_WARNING, TIMER_DANGER = (50, 205, 50), (255, 165, 0), (255, 69, 0)  # цвета таймера хода
ATTACK_RANGE_COLOR = (255, 69, 0, 150)  # подсветка клеток, которые можно атаковать

UNIT_TYPES = {
    'pawn':   {'name': 'PAWN',   'hp': 11, 'damage': (2, 5), 'color': (255, 255, 255), 'speed': 5},  # базовый юнит
    'knight': {'name': 'KNIGHT', 'hp': 17, 'damage': (2, 4), 'color': (255, 215, 0),   'speed': 5},  # танк
    'archer': {'name': 'ARCHER', 'hp': 9,  'damage': (3, 6), 'color': (144, 238, 144), 'speed': 5},  # хрупкий, сильный урон
    'mage':   {'name': 'MAGE',   'hp': 8,  'damage': (4, 6), 'color': (138, 43, 226),  'speed': 5},  # самый сильный урон
}

FONT_SIZES = {'normal': 28, 'big': 60, 'small': 20, 'card': 16, 'damage': 32}  # размеры шрифтов
FONT_REGULAR = "resources/fonts/Nunito-SemiBold.ttf"  # основной шрифт (текст, кнопки, подсказки)
FONT_BOLD = "resources/fonts/Nunito-Bold.ttf"         # жирный шрифт (заголовки, цифры урона)
FONT_FALLBACKS = ["segoeuisymbol", "arial", "dejavusans"]  # запасные системные шрифты, если файл шрифта не найден

font = None         # обычный шрифт
big_font = None     # большой шрифт (заголовки)
small_font = None   # мелкий шрифт
card_font = None    # шрифт карточек юнитов
damage_font = None  # шрифт цифр урона

player_unit_imgs = {}   # картинки юнитов игрока
bot_unit_imgs = {}      # картинки юнитов ботов
github_icon_img = None  # иконка GitHub в меню

MUSIC_MENU = "resources/music/menu_music.mp3"  # трек меню
MUSIC_GAME = "resources/music/game_music.mp3"  # трек игры

GITHUB_URL = "https://github.com/d4n9zz/MiniPRZ"
GITHUB_ICON_PATH = "resources/ui/github_icon.png"

from config import get_music_volume, get_background, get_snow_enabled

MUSIC_VOLUME = get_music_volume()           # громкость музыки (0.0 — 1.0)
BG_OVERLAY_ALPHA = 180                      # прозрачность затемнения поверх фона меню
CURRENT_BACKGROUND = get_background()       # текущий фон меню
SNOW_ENABLED = get_snow_enabled()           # включён ли снег в меню

CUSTOM_BACKGROUNDS = {
    'bg1': 'resources/backgrounds/menu_bg1',
    'bg2': 'resources/backgrounds/menu_bg2',
    'bg3': 'resources/backgrounds/menu_bg3',
    'bg4': 'resources/backgrounds/menu_bg4',
}
BACKGROUND_KEYS = list(CUSTOM_BACKGROUNDS.keys())  # список ключей фонов для переключения

PLAYER_AURA_SYMBOLS = [ "✦  ",  "✧  ",  "⚝  ",  "✦  ",  "✧  ",  "⚝  ",  "✦  ",  "✧  "]  # символы ауры города
PLAYER_AURA_RADIUS = 90                 # радиус вращения ауры
PLAYER_AURA_ROTATION_SPEED = 0.0005     # скорость вращения ауры
PLAYER_AURA_COLOR = (255, 214, 107, 180)  # цвет ауры

SHOP_ANIM_DURATION = 250                # длительность анимации магазина (мс)

UI_ANIM_DURATION = 400                  # длительность анимации появления UI (мс)
UI_STAGGER_DELAY = 40                   # задержка между появлением соседних элементов (мс)
UI_SLIDE_DISTANCE = 10                  # расстояние выезда панели снизу (пиксели)