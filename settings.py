import pygame

WIDTH = 1920
HEIGHT = 1080
TILE_SIZE = 50
INTERFACE_HEIGHT = 80
FIELD_HEIGHT = HEIGHT - INTERFACE_HEIGHT
COLS, ROWS = WIDTH // TILE_SIZE, FIELD_HEIGHT // TILE_SIZE
VISIBILITY_RADIUS = 5
TURN_TIME = 25000
GAME_VERSION = "0.1"
SHAKE_DURATION = 10
SHAKE_INTENSITY = 4
MENU_BG_TOP, MENU_BG_BOTTOM = (25, 32, 50), (45, 52, 70)
BG_TOP, BG_BOTTOM = (34, 139, 34), (144, 238, 144)
GRID_COLOR, GRID_BORDER = (25, 100, 25, 120), (18, 72, 18)
PLAYER_COLOR, PLAYER_GLOW, PLAYER_HIGHLIGHT = (255, 107, 107), (255, 150, 150), (255, 214, 107)
BOT_COLOR, BOT_GLOW = (106, 184, 255), (135, 206, 255)
BOT2_COLOR, BOT2_GLOW = (255, 105, 180), (255, 182, 193)
UI_BG, UI_BORDER, UI_TEXT = (45, 52, 70), (100, 149, 237), (240, 248, 255)
UI_BUTTON_NORMAL, UI_BUTTON_HOVER, UI_BUTTON_SHADOW = (70, 130, 180), (100, 180, 255), (20, 25, 40)
MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER = (100, 149, 237), (135, 206, 250)
MENU_BTN_RED, MENU_BTN_RED_HOVER = (255, 99, 71), (255, 130, 102)
HIT_EFFECT_COLORS = [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 105, 180), (138, 43, 226)]
DEATH_EFFECT_COLORS = [(255, 0, 0), (255, 69, 0), (139, 0, 0), (255, 140, 0), (100, 0, 0)]
FOG_UNEXPLORED, FOG_EXPLORED_NO_VIS = (15, 20, 35, 230), (30, 40, 60, 90)
TIMER_SAFE, TIMER_WARNING, TIMER_DANGER = (50, 205, 50), (255, 165, 0), (255, 69, 0)
ATTACK_RANGE_COLOR = (255, 69, 0, 150)
UNIT_TYPES = {
    'pawn': {'name': 'PAWN', 'hp': 11, 'damage': (2, 5), 'color': (255, 255, 255), 'speed': 5},
    'knight': {'name': 'KNIGHT', 'hp': 17, 'damage': (2, 4), 'color': (255, 215, 0), 'speed': 5},
    'archer': {'name': 'ARCHER', 'hp': 9, 'damage': (3, 6), 'color': (144, 238, 144), 'speed': 5},
    'mage': {'name': 'MAGE', 'hp': 8, 'damage': (4, 6), 'color': (138, 43, 226), 'speed': 5},
}
FONT_SIZES = {'normal': 28, 'big': 60, 'small': 20, 'card': 16, 'damage': 32}
FONT_FALLBACKS = ["segoeuisymbol", "arial", "dejavusans"]
font = None
big_font = None
small_font = None
card_font = None
damage_font = None
player_unit_imgs = {}
bot_unit_imgs = {}
github_icon_img = None
MUSIC_MENU = "resources/music/menu_music.mp3"
MUSIC_GAME = "resources/music/game_music.mp3"
GITHUB_URL = "https://github.com/d4n9zz/MiniPRZ"
GITHUB_ICON_PATH = "resources/ui/github_icon.png"
from config import get_music_volume, get_background, get_snow_enabled

MUSIC_VOLUME = get_music_volume()
BG_OVERLAY_ALPHA = 180
CURRENT_BACKGROUND = get_background()
SNOW_ENABLED = get_snow_enabled()
CUSTOM_BACKGROUNDS = {
    'bg1': 'resources/backgrounds/menu_bg1',
    'bg2': 'resources/backgrounds/menu_bg2',
    'bg3': 'resources/backgrounds/menu_bg3',
    'bg4': 'resources/backgrounds/menu_bg4',
}
BACKGROUND_KEYS = list(CUSTOM_BACKGROUNDS.keys())
DEBUG_FOG_KEY = pygame.K_F4
DEBUG_HEAL_KEY = pygame.K_F5
DEBUG_INSTANT_WIN_KEY = pygame.K_F6
DEBUG_SKIP_TURN_KEY = pygame.K_F7
DEBUG_TEXT_COLOR = (0, 255, 0)
DEBUG_BG_COLOR = (0, 0, 0, 180)