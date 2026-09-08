import pygame
import random
import math
from settings import (
WIDTH,
HEIGHT,
TILE_SIZE,
FIELD_HEIGHT,
VISIBILITY_RADIUS,
TURN_TIME,
BG_TOP,
BG_BOTTOM,
GRID_COLOR,
GRID_BORDER,
FOG_UNEXPLORED,
FOG_EXPLORED_NO_VIS,
PLAYER_HIGHLIGHT,
COLS,
ROWS,
BOT_GLOW,
BOT2_GLOW,
DEBUG_FOG_KEY,
DEBUG_HEAL_KEY,
DEBUG_INSTANT_WIN_KEY,
DEBUG_SKIP_TURN_KEY,
ATTACK_RANGE_COLOR,
UNIT_TYPES,
MENU_BTN_RED,
MENU_BTN_RED_HOVER,
PLAYER_AURA_SYMBOLS,
PLAYER_AURA_RADIUS,
PLAYER_AURA_ROTATION_SPEED,
PLAYER_AURA_COLOR,
SHOP_ANIM_DURATION,
UI_ANIM_DURATION,
)
from entities import create_units, bot_step, smart_bot_buy, Unit
from effects import DamageNumber, BattleEffect, DeathEffect
from ui import (
draw_interface,
draw_menu_button,
draw_pause_menu,
draw_debug_overlay,
draw_top_interface,
)
from music import play_game, fade_music_volume
from menu import settings_menu
from animation import UIAnimation

GAME_CONFIG = {
'num_bots': 3,
'bot_colors': [BOT_GLOW, BOT2_GLOW, (100, 255, 100), (255, 100, 255), (255, 165, 0)],
'bot_personalities': ['aggressive', 'defensive', 'balanced', 'aggressive', 'defensive'],
}

def _get_random_spawn_position(is_player, bot_index=None, total_bots=None):
    """Генерирует случайную позицию спавна.
    Для игрока — нижняя часть карты.
    Для ботов — верхняя половина с распределением по ширине."""
    if is_player:
        min_y = ROWS - 8
        max_y = ROWS - 4
        min_x = 0
        max_x = COLS - 3
    else:
        min_y = 1
        max_y = ROWS // 2
        min_x = 0
        max_x = COLS - 3
        # Распределяем ботов по ширине карты
        if bot_index is not None and total_bots is not None and total_bots > 0:
            zone_width = max(4, COLS // total_bots)
            min_x = bot_index * zone_width
            max_x = min(min_x + zone_width - 3, COLS - 3)
            if max_x < min_x + 2:
                max_x = min_x + 2
            min_x = max(0, min_x)
    spawn_x = random.randint(min_x, max_x)
    spawn_y = random.randint(min_y, max_y)
    return [spawn_x, spawn_y]

def _get_distance_between_spawns(spawn1, spawn2):
    city1_x = spawn1[0] + 1
    city1_y = spawn1[1] + 1
    city2_x = spawn2[0] + 1
    city2_y = spawn2[1] + 1
    return abs(city1_x - city2_x) + abs(city1_y - city2_y)

def _is_city_visible(city_center_pos, visible):
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            check_pos = (city_center_pos[0] + dx, city_center_pos[1] + dy)
            if check_pos in visible:
                return True
    return False

def _get_attackable_tiles(unit, enemy_units):
    attackable = []
    x, y = unit.pos
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                for enemy in enemy_units:
                    if enemy.pos == [nx, ny]:
                        attackable.append((nx, ny))
    return attackable

class Game:
    return_to_menu: bool
    __slots__ = [
        "screen", "clock", "player_units", "enemy_teams",
        "selected_unit", "current_turn", "game_over", "winner",
        "explored_tiles", "turn_timer_start", "damage_numbers",
        "battle_effects", "death_effects", "current_bot_index",
        "bot_wait_until",
        "return_to_menu", "paused", "pause_resume_btn",
        "pause_settings_btn", "pause_menu_btn", "total_paused_time",
        "pause_start_time", "music_fade_target", "music_fade_current",
        "music_fade_speed", "fog_unexplored_surf", "fog_explored_surf",
        "debug_mode", "debug_fog_override", "bg_surface", "grid_surface",
        "player_spawn", "player_city_img",
        "bot_city_img", "player_gold",
        "shop_open", "shop_city_pos", "shop_buttons", "shop_close_btn",
        "shop_open_time", "context_tooltip_unit",
        "pause_anim",
    ]

    def __init__(self, screen, clock, num_bots=None):
        self.screen = screen
        self.clock = clock
        if num_bots is not None:
            GAME_CONFIG['num_bots'] = num_bots
        play_game()
        self._create_static_surfaces()
        self._load_city_images()
        self._reset_game()

    def _create_static_surfaces(self):
        self.grid_surface = pygame.Surface((WIDTH, FIELD_HEIGHT), pygame.SRCALPHA)
        self._draw_grid_static()
        self.bg_surface = pygame.Surface((WIDTH, FIELD_HEIGHT))
        self._draw_background_static()

    def _load_city_images(self):
        self.player_city_img = None
        self.bot_city_img = None
        try:
            player_city = pygame.image.load("resources/ui/player_city.png").convert_alpha()
            self.player_city_img = pygame.transform.smoothscale(
                player_city, (TILE_SIZE, TILE_SIZE)
            )
        except pygame.error:
            pass
        try:
            bot_city = pygame.image.load("resources/ui/bot_city.png").convert_alpha()
            self.bot_city_img = pygame.transform.smoothscale(bot_city, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            pass

    def _draw_grid_static(self):
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.grid_surface, GRID_COLOR, rect)
                pygame.draw.rect(self.grid_surface, GRID_BORDER, rect, 1)

    def _draw_background_static(self):
        for y in range(FIELD_HEIGHT):
            ratio = y / FIELD_HEIGHT
            r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
            g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
            b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
            pygame.draw.line(self.bg_surface, (r, g, b), (0, y), (WIDTH, y))

    def _reset_game(self):
        min_distance = 5
        num_bots = GAME_CONFIG['num_bots']
        # Спавн игрока (всегда снизу)
        self.player_spawn = _get_random_spawn_position(is_player=True)
        # Спавн ботов с распределением по ширине
        self.enemy_teams = []
        bot_spawns = []
        for i in range(num_bots):
            attempts = 0
            while attempts < 50:
                new_spawn = _get_random_spawn_position(
                    is_player=False,
                    bot_index=i,
                    total_bots=num_bots
                )
                # Проверяем расстояние до игрока
                valid = _get_distance_between_spawns(new_spawn, self.player_spawn) >= min_distance
                # Проверяем расстояние до других ботов
                for existing_spawn in bot_spawns:
                    if _get_distance_between_spawns(new_spawn, existing_spawn) < min_distance:
                        valid = False
                        break
                if valid:
                    bot_spawns.append(new_spawn)
                    break
                attempts += 1
            # Если не нашли валидную позицию — используем последнюю попытку
            if attempts >= 50:
                new_spawn = _get_random_spawn_position(
                    is_player=False,
                    bot_index=i,
                    total_bots=num_bots
                )
                bot_spawns.append(new_spawn)
            color = GAME_CONFIG['bot_colors'][i % len(GAME_CONFIG['bot_colors'])]
            personality = GAME_CONFIG['bot_personalities'][i % len(GAME_CONFIG['bot_personalities'])]
            all_existing_units = []
            for team in self.enemy_teams:
                all_existing_units.extend(team['units'])
            self.enemy_teams.append({
                'units': create_units(
                    2,
                    all_existing_units,
                    is_player=False,
                    spawn_zone=new_spawn
                ),
                'color': color,
                'personality': personality,
                'spawn': new_spawn,
                'gold': 15,
                'action_index': 0,
                'wait_until': 0,
            })
        self.player_units = create_units(2, [], is_player=True, spawn_zone=self.player_spawn)
        self.selected_unit = None
        self.current_turn = "player"
        self.game_over = False
        self.winner = None
        self.explored_tiles = set()
        self.turn_timer_start = pygame.time.get_ticks()
        self.damage_numbers = []
        self.battle_effects = []
        self.death_effects = []
        self.current_bot_index = 0
        self.bot_wait_until = 0
        self.return_to_menu = False
        self.paused = False
        self.pause_resume_btn = None
        self.pause_settings_btn = None
        self.pause_menu_btn = None
        self.total_paused_time = 0
        self.pause_start_time = 0
        self.music_fade_target = 1.0
        self.music_fade_current = 1.0
        self.music_fade_speed = 0.03
        self.fog_unexplored_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.fog_unexplored_surf.fill(FOG_UNEXPLORED)
        self.fog_explored_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.fog_explored_surf.fill(FOG_EXPLORED_NO_VIS)
        self.debug_mode = False
        self.debug_fog_override = False
        self.player_gold = 15
        self.shop_open = False
        self.shop_city_pos = None
        self.shop_buttons = []
        self.shop_close_btn = None
        self.shop_open_time = 0
        self.context_tooltip_unit = None
        # === АНИМАЦИЯ МЕНЮ ПАУЗЫ ===
        self.pause_anim = UIAnimation(duration=UI_ANIM_DURATION)

    def _set_pause_state(self, state):
        if state == self.paused:
            return
        if state:
            self.pause_start_time = pygame.time.get_ticks()
            self.music_fade_target = 0.0
            self.pause_anim.restart()  # ← перезапуск анимации при открытии
        else:
            self.total_paused_time += pygame.time.get_ticks() - self.pause_start_time
            self.music_fade_target = 1.0
        self.paused = state

    def _update_music_fade(self):
        if self.music_fade_current < self.music_fade_target:
            self.music_fade_current = min(
                self.music_fade_target, self.music_fade_current + self.music_fade_speed
            )
        elif self.music_fade_current > self.music_fade_target:
            self.music_fade_current = max(
                self.music_fade_target, self.music_fade_current - self.music_fade_speed
            )
        fade_music_volume(self.music_fade_current)

    def _get_visible_tiles(self):
        visible = set()
        for unit in self.player_units:
            x, y = unit.pos
            for dx in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
                for dy in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
                    if dx * dx + dy * dy <= VISIBILITY_RADIUS * VISIBILITY_RADIUS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < COLS and 0 <= ny < ROWS:
                            visible.add((nx, ny))
        player_city_x = self.player_spawn[0]
        player_city_y = self.player_spawn[1]
        for dx in range(3):
            for dy in range(3):
                city_tile = (player_city_x + dx, player_city_y + dy)
                if 0 <= city_tile[0] < COLS and 0 <= city_tile[1] < ROWS:
                    visible.add(city_tile)
                    self.explored_tiles.add(city_tile)
        return visible

    def _draw_city(self, pos, is_player, team_color=None):
        city_x = pos[0] * TILE_SIZE
        city_y = pos[1] * TILE_SIZE
        city_img = self.player_city_img if is_player else self.bot_city_img
        if city_img:
            self.screen.blit(city_img, (city_x, city_y))
        else:
            if is_player:
                city_color = PLAYER_HIGHLIGHT
            else:
                city_color = team_color if team_color else BOT_GLOW
            center_x = city_x + TILE_SIZE // 2
            center_y = city_y + TILE_SIZE // 2
            pygame.draw.rect(
                self.screen, city_color, (city_x + 5, city_y + 15, TILE_SIZE - 10, TILE_SIZE - 20),
                border_radius=3,
            )
            pygame.draw.polygon(
                self.screen,
                (139, 69, 19),
                [(center_x - 15, city_y + 15), (center_x + 15, city_y + 15), (center_x, city_y + 5)],
            )
            pygame.draw.rect(self.screen, (139, 69, 19), (city_x + 18, city_y + 25, 6, 15))
            pygame.draw.rect(self.screen, (139, 69, 19), (city_x + 26, city_y + 25, 6, 15))
            tower_h = 12
            pygame.draw.rect(
                self.screen, city_color, (city_x + 2, city_y + 10, 8, tower_h), border_radius=2
            )
            pygame.draw.rect(
                self.screen,
                city_color,
                (city_x + TILE_SIZE - 10, city_y + 10, 8, tower_h),
                border_radius=2,
            )
            pygame.draw.circle(self.screen, (255, 255, 255), (city_x + 6, city_y + 10), 3)
            pygame.draw.circle(
                self.screen, (255, 255, 255), (city_x + TILE_SIZE - 6, city_y + 10), 3
            )

    def _draw_player_aura(self, city_center_pos):
        cx = city_center_pos[0] * TILE_SIZE + TILE_SIZE // 2
        cy = city_center_pos[1] * TILE_SIZE + TILE_SIZE // 2
        t = pygame.time.get_ticks()
        base_angle = t * PLAYER_AURA_ROTATION_SPEED
        pulse = int(40 * abs(math.sin(t * 0.002)))
        aura_alpha = min(255, PLAYER_AURA_COLOR[3] + pulse)
        ring_surf = pygame.Surface((PLAYER_AURA_RADIUS * 2 + 20, PLAYER_AURA_RADIUS * 2 + 20), pygame.SRCALPHA)
        ring_center = PLAYER_AURA_RADIUS + 10
        pygame.draw.circle(
            ring_surf,
            (*PLAYER_AURA_COLOR[:3], aura_alpha // 3),
            (ring_center, ring_center),
            PLAYER_AURA_RADIUS,
            1,
        )
        self.screen.blit(ring_surf, (cx - ring_center, cy - ring_center))
        from settings import small_font
        if small_font:
            num_symbols = len(PLAYER_AURA_SYMBOLS)
            for i, symbol in enumerate(PLAYER_AURA_SYMBOLS):
                angle = base_angle + (i * 2 * math.pi / num_symbols)
                sx = cx + int(PLAYER_AURA_RADIUS * math.cos(angle))
                sy = cy + int(PLAYER_AURA_RADIUS * math.sin(angle))
                symbol_alpha = int(aura_alpha * (0.6 + 0.4 * abs(math.sin(t * 0.003 + i))))
                sym_surf = small_font.render(symbol, True, PLAYER_AURA_COLOR[:3])
                sym_surf.set_alpha(symbol_alpha)
                sym_rect = sym_surf.get_rect(center=(sx, sy))
                self.screen.blit(sym_surf, sym_rect)

    def _draw_spawn_zones(self, visible):
        player_city_pos = [self.player_spawn[0] + 1, self.player_spawn[1] + 1]
        player_zone_rect = pygame.Rect(
            self.player_spawn[0] * TILE_SIZE,
            self.player_spawn[1] * TILE_SIZE,
            TILE_SIZE * 3,
            TILE_SIZE * 3,
        )
        pygame.draw.rect(self.screen, PLAYER_HIGHLIGHT, player_zone_rect, 3)
        self._draw_city(player_city_pos, is_player=True)
        self._draw_player_aura(player_city_pos)
        for team in self.enemy_teams:
            city_pos = [team['spawn'][0] + 1, team['spawn'][1] + 1]
            city_visible = _is_city_visible(city_pos, visible)
            if city_visible:
                zone_rect = pygame.Rect(
                    team['spawn'][0] * TILE_SIZE,
                    team['spawn'][1] * TILE_SIZE,
                    TILE_SIZE * 3,
                    TILE_SIZE * 3,
                )
                pygame.draw.rect(self.screen, team['color'], zone_rect, 3)
                self._draw_city(city_pos, is_player=False, team_color=team['color'])

    def _draw_top_game_interface(self):
        stars = self.player_gold
        stars_change = 5
        draw_top_interface(self.screen, stars, stars_change)

    def _draw_shop_menu(self):
        from settings import font, small_font
        if not self.shop_open or not font:
            return
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.shop_open_time
        progress = min(1.0, elapsed / SHOP_ANIM_DURATION)
        eased = 1 - (1 - progress) ** 3
        panel_w = 520
        panel_h = 450
        panel_x = WIDTH // 2 - panel_w // 2
        target_y = FIELD_HEIGHT // 2 - panel_h // 2
        start_y = target_y - 80
        panel_y = int(start_y + (target_y - start_y) * eased)
        overlay_alpha = int(200 * eased)
        overlay = pygame.Surface((WIDTH, FIELD_HEIGHT))
        overlay.set_alpha(overlay_alpha)
        overlay.fill((10, 12, 20))
        self.screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((45, 52, 70, int(255 * eased)))
        self.screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(self.screen, (100, 149, 237), panel_rect, 3, border_radius=12)
        title = font.render("RECRUIT UNITS", True, (240, 248, 255))
        title.set_alpha(int(255 * eased))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, panel_y + 35)))
        gold_text = font.render(f"GOLD: {self.player_gold}", True, (255, 215, 0))
        gold_text.set_alpha(int(255 * eased))
        self.screen.blit(gold_text, gold_text.get_rect(center=(WIDTH // 2, panel_y + 70)))
        if small_font:
            hint_text = small_font.render("Press [B] to close", True, (150, 150, 150))
            hint_text.set_alpha(int(255 * eased))
            self.screen.blit(hint_text, hint_text.get_rect(center=(WIDTH // 2, panel_y + 95)))
        unit_types = list(UNIT_TYPES.keys())
        start_y = panel_y + 125
        self.shop_buttons = []
        for i, utype in enumerate(unit_types):
            data = UNIT_TYPES[utype]
            btn_y = start_y + i * 70
            btn_rect = pygame.Rect(panel_x + 20, btn_y, panel_w - 140, 60)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color = (100, 180, 255) if btn_rect.collidepoint(mouse_x, mouse_y) else (70, 130, 180)
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=8)
            key_number = str(i + 1)
            key_text = small_font.render(f"[{key_number}]", True, (255, 215, 0))
            self.screen.blit(key_text, (panel_x + 30, btn_y + 20))
            unit_name = small_font.render(
                f"{data['name']} (HP:{data['hp']} DMG:{data['damage'][0]}-{data['damage'][1]})",
                True,
                (240, 248, 255),
            )
            cost_text = small_font.render(f"Cost: {data['hp']} gold", True, (255, 215, 0))
            self.screen.blit(unit_name, (panel_x + 70, btn_y + 12))
            self.screen.blit(cost_text, (panel_x + 70, btn_y + 34))
            self.shop_buttons.append((btn_rect, utype, data["hp"]))
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.shop_close_btn = pygame.Rect(panel_x + panel_w - 95, panel_y + panel_h - 65, 80, 40)
        close_color = (
            MENU_BTN_RED_HOVER
            if self.shop_close_btn.collidepoint(mouse_x, mouse_y)
            else MENU_BTN_RED
        )
        pygame.draw.rect(self.screen, close_color, self.shop_close_btn, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.shop_close_btn, 2, border_radius=8)
        close_text = small_font.render("CLOSE", True, (240, 248, 255))
        self.screen.blit(close_text, close_text.get_rect(center=self.shop_close_btn.center))

    def _handle_shop_click(self, mouse_x, mouse_y):
        from utils import get_unit_at
        if not self.shop_open:
            if self.selected_unit is not None:
                return
            city_pos = [self.player_spawn[0] + 1, self.player_spawn[1] + 1]
            city_x = city_pos[0] * TILE_SIZE
            city_y = city_pos[1] * TILE_SIZE
            city_rect = pygame.Rect(city_x, city_y, TILE_SIZE, TILE_SIZE)
            if city_rect.collidepoint(mouse_x, mouse_y):
                self.shop_open_time = pygame.time.get_ticks()
                self.shop_open = True
                self.shop_city_pos = city_pos
            return
        if self.shop_close_btn and self.shop_close_btn.collidepoint(mouse_x, mouse_y):
            self.shop_open = False
            self.shop_city_pos = None
            return
        for btn_rect, utype, cost in self.shop_buttons:
            if btn_rect.collidepoint(mouse_x, mouse_y):
                if self.player_gold >= cost:
                    spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
                    spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
                    attempts = 0
                    all_units = self.player_units.copy()
                    for team in self.enemy_teams:
                        all_units.extend(team['units'])
                    while (
                            get_unit_at([spawn_x, spawn_y], all_units)
                            and attempts < 10
                    ):
                        spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
                        spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
                        attempts += 1
                    if attempts < 10:
                        new_unit = Unit([spawn_x, spawn_y], unit_type=utype, is_player=True)
                        self.player_units.append(new_unit)
                        self.player_gold -= cost
                return

    def _buy_unit_by_index(self, index):
        from utils import get_unit_at
        unit_types = list(UNIT_TYPES.keys())
        if index < 0 or index >= len(unit_types):
            return
        utype = unit_types[index]
        cost = UNIT_TYPES[utype]["hp"]
        if self.player_gold >= cost:
            spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
            spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
            attempts = 0
            all_units = self.player_units.copy()
            for team in self.enemy_teams:
                all_units.extend(team['units'])
            while (
                    get_unit_at([spawn_x, spawn_y], all_units)
                    and attempts < 10
            ):
                spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
                spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
                attempts += 1
            if attempts < 10:
                new_unit = Unit([spawn_x, spawn_y], unit_type=utype, is_player=True)
                self.player_units.append(new_unit)
                self.player_gold -= cost

    def _draw_attack_indicators(self, visible):
        if self.current_turn != "player" or not self.selected_unit:
            return
        if tuple(self.selected_unit.pos) not in visible and not self.debug_fog_override:
            return
        all_enemies = []
        for team in self.enemy_teams:
            all_enemies.extend(team['units'])
        attackable_tiles = _get_attackable_tiles(self.selected_unit, all_enemies)
        for tx, ty in attackable_tiles:
            if (tx, ty) not in visible and not self.debug_fog_override:
                continue
            rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            highlight_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, ATTACK_RANGE_COLOR, (0, 0, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(highlight_surf, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            self.screen.blit(highlight_surf, rect.topleft)

    def _draw_fog_of_war(self, visible):
        if self.debug_fog_override:
            return
        for y in range(ROWS):
            for x in range(COLS):
                tile_pos = (x, y)
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile_pos not in self.explored_tiles:
                    self.screen.blit(self.fog_unexplored_surf, tile_rect.topleft)
                elif tile_pos not in visible:
                    self.screen.blit(self.fog_explored_surf, tile_rect.topleft)

    def _draw_hp_bar(self, unit, draw_x, draw_y):
        bar_width = TILE_SIZE - 10
        bar_height = 6
        bar_x = draw_x - bar_width // 2
        bar_y = draw_y - TILE_SIZE // 2 - 8
        hp_ratio = unit.hp / unit.max_hp if unit.max_hp > 0 else 0
        if hp_ratio > 0.6:
            bar_color = (50, 205, 50)
        elif hp_ratio > 0.3:
            bar_color = (255, 165, 0)
        else:
            bar_color = (255, 69, 0)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (20, 20, 20), bg_rect, border_radius=3)
        if hp_ratio > 0:
            fill_width = int(bar_width * hp_ratio)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(self.screen, bar_color, fill_rect, border_radius=3)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 1, border_radius=3)

    def _draw_units(self, visible):
        from settings import player_unit_imgs, bot_unit_imgs
        all_units = self.player_units.copy()
        for team in self.enemy_teams:
            all_units.extend(team['units'])
        for unit in all_units:
            if tuple(unit.pos) not in visible and not unit.is_player and not self.debug_fog_override:
                continue
            if unit.is_player:
                unit_img_dict = player_unit_imgs
            else:
                unit_img_dict = bot_unit_imgs
            unit_img = unit_img_dict.get(unit.unit_type)
            draw_x = int(unit.px) + unit.shake_offset[0]
            draw_y = int(unit.py) + unit.shake_offset[1]
            if unit_img:
                img_rect = unit_img.get_rect(center=(draw_x, draw_y))
                self.screen.blit(unit_img, img_rect)
            else:
                if unit.is_player:
                    glow = PLAYER_HIGHLIGHT
                else:
                    glow = BOT_GLOW
                    for team in self.enemy_teams:
                        if unit in team['units']:
                            glow = team['color']
                            break
                pygame.draw.circle(self.screen, glow, (draw_x, draw_y), TILE_SIZE // 3 + 10)
                pygame.draw.circle(self.screen, unit.color, (draw_x, draw_y), TILE_SIZE // 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (draw_x, draw_y), TILE_SIZE // 3, 2)
            self._draw_hp_bar(unit, draw_x, draw_y)
            if unit == self.selected_unit:
                for i in range(3):
                    alpha = 200 - i * 50
                    highlight_surf = pygame.Surface(
                        (TILE_SIZE + 20, TILE_SIZE + 20), pygame.SRCALPHA
                    )
                    pygame.draw.circle(
                        highlight_surf,
                        (*PLAYER_HIGHLIGHT, alpha),
                        (TILE_SIZE // 2 + 10, TILE_SIZE // 2 + 10),
                        TILE_SIZE // 3 + 12 + i * 4,
                        3,
                    )
                    self.screen.blit(
                        highlight_surf,
                        (unit.px - TILE_SIZE // 2 - 10, unit.py - TILE_SIZE // 2 - 10),
                    )

    def _draw_context_tooltip(self, visible):
        from settings import small_font
        if not small_font or not self.context_tooltip_unit:
            return
        all_units = self.player_units.copy()
        for team in self.enemy_teams:
            all_units.extend(team['units'])
        if self.context_tooltip_unit not in all_units:
            self.context_tooltip_unit = None
            return
        unit = self.context_tooltip_unit
        if tuple(unit.pos) not in visible and not unit.is_player and not self.debug_fog_override:
            self.context_tooltip_unit = None
            return
        info_lines = []
        info_lines.append(f"Type: {unit.name}")
        info_lines.append(f"HP: {unit.hp}/{unit.max_hp}")
        info_lines.append(f"DMG: {unit.damage_range[0]}-{unit.damage_range[1]}")
        if (self.selected_unit and
                self.selected_unit.is_player and
                not unit.is_player and
                self.current_turn == "player"):
            dx = abs(self.selected_unit.pos[0] - unit.pos[0])
            dy = abs(self.selected_unit.pos[1] - unit.pos[1])
            if dx <= 1 and dy <= 1 and (dx + dy) != 0:
                player_dmg_min = self.selected_unit.damage_range[0]
                player_dmg_max = self.selected_unit.damage_range[1]
                info_lines.append(f"")
                info_lines.append(f"Your DMG: {player_dmg_min}-{player_dmg_max}")
                remaining_hp = unit.hp - player_dmg_max
                if remaining_hp <= 0:
                    info_lines.append(f"Will KILL!")
                else:
                    info_lines.append(f"HP after: {remaining_hp}")
        padding = 8
        line_height = small_font.get_height() + 4
        tooltip_width = 180
        tooltip_height = len(info_lines) * line_height + padding * 2
        unit_screen_x = unit.pos[0] * TILE_SIZE + TILE_SIZE // 2
        unit_screen_y = unit.pos[1] * TILE_SIZE + TILE_SIZE // 2
        tooltip_x = unit_screen_x + TILE_SIZE // 2 + 10
        tooltip_y = unit_screen_y - tooltip_height // 2
        if tooltip_x + tooltip_width > WIDTH:
            tooltip_x = unit_screen_x - TILE_SIZE // 2 - tooltip_width - 10
        if tooltip_y < 0:
            tooltip_y = 10
        if tooltip_y + tooltip_height > FIELD_HEIGHT:
            tooltip_y = FIELD_HEIGHT - tooltip_height - 10
        tooltip_surf = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        tooltip_surf.fill((20, 25, 40, 230))
        self.screen.blit(tooltip_surf, (tooltip_x, tooltip_y))
        border_color = unit.color if not unit.is_player else PLAYER_HIGHLIGHT
        pygame.draw.rect(self.screen, border_color, (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 2,
                         border_radius=6)
        for i, line in enumerate(info_lines):
            if line == "":
                continue
            text_color = (255, 215, 0) if "Your DMG" in line or "Will KILL" in line else (240, 248, 255)
            text_surf = small_font.render(line, True, text_color)
            self.screen.blit(text_surf, (tooltip_x + padding, tooltip_y + padding + i * line_height))

    def _handle_input(self, interface_btn, menu_btn_rect):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if event.key == pygame.K_F11 and keys[pygame.K_F12]:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_F12 and keys[pygame.K_F11]:
                    self.debug_mode = not self.debug_mode
                if event.key == pygame.K_ESCAPE:
                    if self.shop_open:
                        self.shop_open = False
                        self.shop_city_pos = None
                    else:
                        self._set_pause_state(not self.paused)
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self._reset_game()
                    elif self.current_turn == "player" and not self.paused and not self.shop_open:
                        self._end_player_turn()
                if event.key == pygame.K_b and self.current_turn == "player" and not self.game_over and not self.paused:
                    if not self.shop_open:
                        self.shop_open_time = pygame.time.get_ticks()
                    self.shop_open = not self.shop_open
                    if not self.shop_open:
                        self.shop_city_pos = None
                if event.key == DEBUG_FOG_KEY:
                    self.debug_fog_override = not self.debug_fog_override
                if event.key == DEBUG_HEAL_KEY and self.current_turn == "player":
                    for u in self.player_units:
                        u.hp = u.max_hp
                if event.key == DEBUG_INSTANT_WIN_KEY:
                    for team in self.enemy_teams:
                        team['units'] = []
                    self.game_over = True
                    self.winner = "DEBUG WIN"
                if event.key == DEBUG_SKIP_TURN_KEY and self.current_turn == "player":
                    self._end_player_turn()
                if self.shop_open and self.current_turn == "player" and not self.game_over and not self.paused:
                    unit_types = list(UNIT_TYPES.keys())
                    if event.key == pygame.K_1 and len(unit_types) >= 1:
                        self._buy_unit_by_index(0)
                    elif event.key == pygame.K_2 and len(unit_types) >= 2:
                        self._buy_unit_by_index(1)
                    elif event.key == pygame.K_3 and len(unit_types) >= 3:
                        self._buy_unit_by_index(2)
                    elif event.key == pygame.K_4 and len(unit_types) >= 4:
                        self._buy_unit_by_index(3)
                if self.current_turn == "player" and not self.game_over and not self.paused and not self.shop_open:
                    if event.key == pygame.K_1 and len(self.player_units) > 0:
                        self.selected_unit = self.player_units[0]
                    elif event.key == pygame.K_2 and len(self.player_units) > 1:
                        self.selected_unit = self.player_units[1]
                    elif event.key == pygame.K_3 and len(self.player_units) > 2:
                        self.selected_unit = self.player_units[2]
                    elif event.key == pygame.K_4 and len(self.player_units) > 3:
                        self.selected_unit = self.player_units[3]
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if event.button == 3:
                    from utils import get_unit_at
                    grid_pos = [mouse_x // TILE_SIZE, mouse_y // TILE_SIZE]
                    all_units = self.player_units.copy()
                    for team in self.enemy_teams:
                        all_units.extend(team['units'])
                    clicked_unit = get_unit_at(grid_pos, all_units)
                    if clicked_unit:
                        if self.context_tooltip_unit == clicked_unit:
                            self.context_tooltip_unit = None
                        else:
                            self.context_tooltip_unit = clicked_unit
                    else:
                        self.context_tooltip_unit = None
                    continue
                if menu_btn_rect.collidepoint(mouse_x, mouse_y):
                    self._set_pause_state(True)
                    continue
                if self.paused:
                    if self.pause_resume_btn and self.pause_resume_btn.collidepoint(mouse_x, mouse_y):
                        self._set_pause_state(False)
                    elif (
                            self.pause_settings_btn
                            and self.pause_settings_btn.collidepoint(mouse_x, mouse_y)
                    ):
                        self._set_pause_state(False)
                        settings_menu(self.screen, self.clock)
                        self._set_pause_state(True)
                    elif self.pause_menu_btn and self.pause_menu_btn.collidepoint(mouse_x, mouse_y):
                        self.return_to_menu = True
                        return False
                    continue
                if interface_btn.collidepoint(mouse_x,
                                              mouse_y) and self.current_turn == "player" and not self.shop_open:
                    self._end_player_turn()
                    continue
                if self.current_turn == "player":
                    if self.shop_open:
                        self._handle_shop_click(mouse_x, mouse_y)
                    else:
                        self._handle_shop_click(mouse_x, mouse_y)
                        self._handle_field_click(mouse_x, mouse_y)
        return True

    def _handle_field_click(self, mouse_x, mouse_y):
        from utils import get_unit_at
        grid_pos = [mouse_x // TILE_SIZE, mouse_y // TILE_SIZE]
        clicked_unit = get_unit_at(grid_pos, self.player_units)
        if clicked_unit:
            if self.selected_unit == clicked_unit:
                self.selected_unit = None
            else:
                self.selected_unit = clicked_unit
        elif self.selected_unit and not self.selected_unit.has_moved:
            dx_move = abs(grid_pos[0] - self.selected_unit.pos[0])
            dy_move = abs(grid_pos[1] - self.selected_unit.pos[1])
            if dx_move <= 1 and dy_move <= 1 and (dx_move + dy_move) != 0:
                all_enemies = []
                for team in self.enemy_teams:
                    all_enemies.extend(team['units'])
                enemy_unit = get_unit_at(grid_pos, all_enemies)
                if enemy_unit:
                    self._perform_attack(self.selected_unit, enemy_unit)
                elif not get_unit_at(grid_pos, self.player_units) and not get_unit_at(
                        grid_pos, all_enemies
                ):
                    self.selected_unit.move_path = [grid_pos]
                    self.selected_unit.has_moved = True
                    self.selected_unit = None

    def _perform_attack(self, attacker, defender):
        attack_damage = attacker.get_attack_damage()
        defender.hp -= attack_damage
        defender.start_shake()
        self.damage_numbers.append(DamageNumber(defender.pos, attack_damage))
        self.battle_effects.append(BattleEffect(defender.pos))
        if not defender.is_alive():
            self.death_effects.append(DeathEffect(defender.pos))
        attacker.has_moved = True
        self.selected_unit = None

    def _end_player_turn(self):
        if GAME_CONFIG['num_bots'] == 0:
            self.current_turn = "player"
            self.turn_timer_start = pygame.time.get_ticks()
            self.total_paused_time = 0
            for u in self.player_units:
                u.has_moved = False
            self.player_gold += 5
            return
        self.current_turn = "bot"
        self.current_bot_index = 0
        self.bot_wait_until = pygame.time.get_ticks() + random.randint(500, 1000)
        # ИСПРАВЛЕНИЕ: сбрасываем action_index и устанавливаем wait_until для каждой команды
        for i, team in enumerate(self.enemy_teams):
            team['action_index'] = 0  # ← СБРОС счётчика действий
            if i == 0:  # Для первой команды устанавливаем задержку
                team['wait_until'] = pygame.time.get_ticks() + random.randint(500, 1000)
            else:  # Для остальных команд задержка будет установлена после завершения предыдущей
                team['wait_until'] = 0
            for u in team['units']:
                u.has_moved = False
        for u in self.player_units:
            u.has_moved = False
        self.player_gold += 5

    def _update_game(self):
        if self.paused or self.shop_open:
            return
        for unit in self.player_units:
            unit.update_animation()
            unit.update_shake()
        for team in self.enemy_teams:
            for unit in team['units']:
                unit.update_animation()
                unit.update_shake()
        self.damage_numbers = [d for d in self.damage_numbers if d.update()]
        self.battle_effects = [e for e in self.battle_effects if e.update()]
        self.death_effects = [e for e in self.death_effects if e.update()]
        if not self.game_over:
            all_enemy_units = []
            for team in self.enemy_teams:
                all_enemy_units.extend(team['units'])
            if not all_enemy_units:
                self.game_over = True
                self.winner = "YOU WIN!"
            elif not self.player_units:
                self.game_over = True
                self.winner = "YOU LOSE"
        if self.current_turn == "player" and not self.game_over:
            elapsed = pygame.time.get_ticks() - self.turn_timer_start - self.total_paused_time
            if elapsed >= TURN_TIME:
                self._end_player_turn()
        if self.current_turn == "bot" and not self.game_over and GAME_CONFIG['num_bots'] > 0:
            if self.current_bot_index < len(self.enemy_teams):
                current_team = self.enemy_teams[self.current_bot_index]
                if (
                        pygame.time.get_ticks() >= current_team['wait_until']
                        and current_team['action_index'] < len(current_team['units'])
                ):
                    all_enemies = self.player_units.copy()
                    for i, other_team in enumerate(self.enemy_teams):
                        if i != self.current_bot_index:
                            all_enemies.extend(other_team['units'])
                    bot_unit = current_team['units'][current_team['action_index']]
                    bot_step(
                        bot_unit,
                        all_enemies,
                        current_team['units'],
                        personality=current_team['personality'],
                        damage_callback=lambda pos, dmg: self.damage_numbers.append(DamageNumber(pos, dmg)),
                        effect_callback=lambda pos: self.battle_effects.append(BattleEffect(pos)),
                        death_callback=lambda pos: self.death_effects.append(DeathEffect(pos)),
                    )
                    current_team['action_index'] += 1
                    if current_team['action_index'] < len(current_team['units']):
                        current_team['wait_until'] = pygame.time.get_ticks() + random.randint(400, 800)
                    else:
                        current_team['gold'] = smart_bot_buy(
                            current_team['units'],
                            current_team['gold'],
                            current_team['spawn'],
                            personality=current_team['personality'],
                            enemy_units=self.player_units
                        )
                        current_team['gold'] += 5
                        self.current_bot_index += 1
                        if self.current_bot_index < len(self.enemy_teams):
                            self.enemy_teams[self.current_bot_index][
                                'wait_until'] = pygame.time.get_ticks() + random.randint(500, 1000)
                        else:
                            self.current_turn = "player"
                            self.turn_timer_start = pygame.time.get_ticks()
                            self.total_paused_time = 0
                            for u in self.player_units:
                                u.has_moved = False
        self.player_units = [u for u in self.player_units if u.is_alive()]
        for team in self.enemy_teams:
            team['units'] = [u for u in team['units'] if u.is_alive()]

    def _draw_game_over(self):
        from settings import font, big_font, UI_TEXT, PLAYER_HIGHLIGHT
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((15, 20, 35))
        self.screen.blit(overlay, (0, 0))
        if big_font and font:
            winner_text = big_font.render(self.winner, True, PLAYER_HIGHLIGHT)
            winner_shadow = big_font.render(self.winner, True, (0, 0, 0))
            text_x = WIDTH // 2 - winner_text.get_width() // 2
            text_y = HEIGHT // 2 - winner_text.get_height() // 2 - 20
            self.screen.blit(winner_shadow, (text_x + 3, text_y + 3))
            self.screen.blit(winner_text, (text_x, text_y))
            restart_text = font.render("Press SPACE to restart", True, UI_TEXT)
            restart_x = WIDTH // 2 - restart_text.get_width() // 2
            restart_y = text_y + winner_text.get_height() + 20
            self.screen.blit(restart_text, (restart_x, restart_y))

    def _draw_pause_menu(self):
        resume_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2 - 60, 240, 50)
        settings_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2, 240, 50)
        menu_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2 + 60, 240, 50)
        self.pause_resume_btn = resume_btn
        self.pause_settings_btn = settings_btn
        self.pause_menu_btn = menu_btn
        # === ПЕРЕДАЁМ АНИМАЦИЮ В МЕНЮ ПАУЗЫ ===
        draw_pause_menu(self.screen, resume_btn, settings_btn, menu_btn, self.pause_anim)

    def run(self):
        running = True
        while running:
            visible = self._get_visible_tiles()
            self.explored_tiles.update(visible)
            self.screen.blit(self.bg_surface, (0, 0))
            self.screen.blit(self.grid_surface, (0, 0))
            self._draw_spawn_zones(visible)
            self._draw_units(visible)
            self._draw_attack_indicators(visible)
            for dmg in self.damage_numbers:
                dmg.draw(self.screen, visible)
            for effect in self.battle_effects:
                effect.draw(self.screen, visible)
            for effect in self.death_effects:
                effect.draw(self.screen, visible)
            self._draw_fog_of_war(visible)
            self._draw_top_game_interface()
            all_bot_units = []
            for team in self.enemy_teams:
                all_bot_units.extend(team['units'])
            interface_btn = draw_interface(
                self.screen,
                self.current_turn,
                self.player_units,
                all_bot_units,
                [],
                self.turn_timer_start,
                TURN_TIME,
                self.selected_unit,
                self.paused,
                self.pause_start_time,
                self.total_paused_time,
            )
            menu_btn_rect = draw_menu_button(self.screen)
            if self.paused:
                self._draw_pause_menu()
            if self.game_over:
                self._draw_game_over()
            if self.debug_mode:
                all_enemy_units = []
                for team in self.enemy_teams:
                    all_enemy_units.extend(team['units'])
                draw_debug_overlay(
                    self.screen, visible, self.player_units, all_enemy_units
                )
            if self.shop_open:
                self._draw_shop_menu()
            self._draw_context_tooltip(visible)
            running = self._handle_input(interface_btn, menu_btn_rect)
            self._update_game()
            self._update_music_fade()
            pygame.display.update()
            self.clock.tick(60)
        return self.return_to_menu