WIDTH, HEIGHT = 800, 600
TILE_SIZE = 50
INTERFACE_HEIGHT = 80
FIELD_HEIGHT = HEIGHT - INTERFACE_HEIGHT
COLS, ROWS = WIDTH // TILE_SIZE, FIELD_HEIGHT // TILE_SIZE

VISIBILITY_RADIUS = 2
TURN_TIME = 30000

BG_TOP, BG_BOTTOM = (34, 139, 34), (144, 238, 144)
MENU_BG_TOP, MENU_BG_BOTTOM = (25, 32, 50), (45, 52, 70)

GRID_COLOR, GRID_BORDER = (25, 100, 25, 120), (18, 72, 18)

PLAYER_COLOR, PLAYER_GLOW, PLAYER_HIGHLIGHT = (255, 107, 107), (255, 150, 150), (255, 214, 107)
BOT_COLOR, BOT_GLOW = (106, 184, 255), (135, 206, 255)

UI_BG, UI_BORDER, UI_TEXT = (45, 52, 70), (100, 149, 237), (240, 248, 255)
UI_BUTTON_NORMAL, UI_BUTTON_HOVER, UI_BUTTON_SHADOW = (70, 130, 180), (100, 180, 255), (20, 25, 40)

MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER = (100, 149, 237), (135, 206, 250)
MENU_BTN_RED, MENU_BTN_RED_HOVER = (255, 99, 71), (255, 130, 102)

HIT_EFFECT_COLORS = [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 105, 180), (138, 43, 226)]
FOG_UNEXPLORED, FOG_EXPLORED_NO_VIS = (15, 20, 35, 230), (30, 40, 60, 90)
TIMER_SAFE, TIMER_WARNING, TIMER_DANGER = (50, 205, 50), (255, 165, 0), (255, 69, 0)

FONT_SIZES = {'normal': 28, 'big': 60, 'small': 20, 'card': 16, 'damage': 32}
FONT_FALLBACKS = ["segoeuisymbol", "segoe ui", "arial", "dejavusans", "freesansbold", None]

font = None
big_font = None
small_font = None
card_font = None
damage_font = None
player_unit_img = None
bot_unit_img = None

MUSIC_MENU = "menu_music.mp3"
MUSIC_GAME = "game_music.mp3"
MUSIC_VOLUME = 0.5