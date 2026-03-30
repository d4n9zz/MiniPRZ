import pygame
import random

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
)
from entities import create_units, bot_step, Unit
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


def _get_random_spawn_position(is_player):
    if is_player:
        min_y = ROWS - 8
        max_y = ROWS - 4
    else:
        min_y = 1
        max_y = 5
    spawn_x = random.randint(0, COLS - 3)
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
    slots = [
        "screen",
        "clock",
        "player_units",
        "bot_units",
        "bot2_units",
        "selected_unit",
        "current_turn",
        "game_over",
        "winner",
        "explored_tiles",
        "turn_timer_start",
        "damage_numbers",
        "battle_effects",
        "death_effects",
        "bot_action_index",
        "bot_wait_until",
        "bot2_action_index",
        "bot2_wait_until",
        "return_to_menu",
        "paused",
        "pause_resume_btn",
        "pause_settings_btn",
        "pause_menu_btn",
        "total_paused_time",
        "pause_start_time",
        "music_fade_target",
        "music_fade_current",
        "music_fade_speed",
        "fog_unexplored_surf",
        "fog_explored_surf",
        "debug_mode",
        "debug_fog_override",
        "bg_surface",
        "grid_surface",
        "player_spawn",
        "bot_spawn",
        "bot2_spawn",
        "player_city_img",
        "bot_city_img",
        "player_gold",
        "bot_gold",
        "bot2_gold",
        "shop_open",
        "shop_city_pos",
        "shop_buttons",
        "shop_close_btn",
    ]

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
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
        while True:
            self.player_spawn = _get_random_spawn_position(is_player=True)
            self.bot_spawn = _get_random_spawn_position(is_player=False)
            self.bot2_spawn = _get_random_spawn_position(is_player=False)
            if (
                _get_distance_between_spawns(self.player_spawn, self.bot_spawn) >= min_distance
                and _get_distance_between_spawns(self.player_spawn, self.bot2_spawn) >= min_distance
                and _get_distance_between_spawns(self.bot_spawn, self.bot2_spawn) >= min_distance
            ):
                break
        self.player_units = create_units(2, [], is_player=True, spawn_zone=self.player_spawn)
        self.bot_units = create_units(
            2, self.player_units, is_player=False, spawn_zone=self.bot_spawn
        )
        self.bot2_units = create_units(
            2, self.player_units + self.bot_units, is_player=False, spawn_zone=self.bot2_spawn
        )
        self.selected_unit = None
        self.current_turn = "player"
        self.game_over = False
        self.winner = None
        self.explored_tiles = set()
        self.turn_timer_start = pygame.time.get_ticks()
        self.damage_numbers = []
        self.battle_effects = []
        self.death_effects = []
        self.bot_action_index = 0
        self.bot_wait_until = 0
        self.bot2_action_index = 0
        self.bot2_wait_until = 0
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
        self.bot_gold = 15
        self.bot2_gold = 15
        self.shop_open = False
        self.shop_city_pos = None
        self.shop_buttons = []
        self.shop_close_btn = None

    def _set_pause_state(self, state):
        if state == self.paused:
            return
        if state:
            self.pause_start_time = pygame.time.get_ticks()
            self.music_fade_target = 0.0
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

    def _draw_city(self, pos, is_player, bot_number=1):
        city_x = pos[0] * TILE_SIZE
        city_y = pos[1] * TILE_SIZE
        city_img = self.player_city_img if is_player else self.bot_city_img
        if city_img:
            self.screen.blit(city_img, (city_x, city_y))
        else:
            if is_player:
                city_color = PLAYER_HIGHLIGHT
            elif bot_number == 1:
                city_color = BOT_GLOW
            else:
                city_color = BOT2_GLOW
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

    def _draw_spawn_zones(self, visible):
        player_city_pos = [self.player_spawn[0] + 1, self.player_spawn[1] + 1]
        bot_city_pos = [self.bot_spawn[0] + 1, self.bot_spawn[1] + 1]
        bot2_city_pos = [self.bot2_spawn[0] + 1, self.bot2_spawn[1] + 1]

        player_zone_rect = pygame.Rect(
            self.player_spawn[0] * TILE_SIZE,
            self.player_spawn[1] * TILE_SIZE,
            TILE_SIZE * 3,
            TILE_SIZE * 3,
        )
        pygame.draw.rect(self.screen, PLAYER_HIGHLIGHT, player_zone_rect, 3)
        self._draw_city(player_city_pos, is_player=True)

        bot_city_visible = _is_city_visible(bot_city_pos, visible)
        if bot_city_visible:
            bot_zone_rect = pygame.Rect(
                self.bot_spawn[0] * TILE_SIZE,
                self.bot_spawn[1] * TILE_SIZE,
                TILE_SIZE * 3,
                TILE_SIZE * 3,
            )
            pygame.draw.rect(self.screen, BOT_GLOW, bot_zone_rect, 3)
            self._draw_city(bot_city_pos, is_player=False, bot_number=1)

        bot2_city_visible = _is_city_visible(bot2_city_pos, visible)
        if bot2_city_visible:
            bot2_zone_rect = pygame.Rect(
                self.bot2_spawn[0] * TILE_SIZE,
                self.bot2_spawn[1] * TILE_SIZE,
                TILE_SIZE * 3,
                TILE_SIZE * 3,
            )
            pygame.draw.rect(self.screen, BOT2_GLOW, bot2_zone_rect, 3)
            self._draw_city(bot2_city_pos, is_player=False, bot_number=2)

    def _draw_top_game_interface(self):
        stars = self.player_gold
        stars_change = 5
        draw_top_interface(self.screen, stars, stars_change)

    def _draw_shop_menu(self):
        from settings import font, small_font

        if not self.shop_open or not font:
            return

        panel_w = 520
        panel_h = 400
        panel_x = WIDTH // 2 - panel_w // 2
        panel_y = FIELD_HEIGHT // 2 - panel_h // 2

        overlay = pygame.Surface((WIDTH, FIELD_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((10, 12, 20))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (45, 52, 70), panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, (100, 149, 237), panel_rect, 3, border_radius=12)

        title = font.render("RECRUIT UNITS", True, (240, 248, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, panel_y + 35)))

        gold_text = font.render(f"GOLD: {self.player_gold}", True, (255, 215, 0))
        self.screen.blit(gold_text, gold_text.get_rect(center=(WIDTH // 2, panel_y + 70)))

        unit_types = list(UNIT_TYPES.keys())
        start_y = panel_y + 115
        self.shop_buttons = []

        for i, utype in enumerate(unit_types):
            data = UNIT_TYPES[utype]
            btn_y = start_y + i * 65
            btn_rect = pygame.Rect(panel_x + 20, btn_y, panel_w - 140, 55)

            mouse_x, mouse_y = pygame.mouse.get_pos()
            color = (100, 180, 255) if btn_rect.collidepoint(mouse_x, mouse_y) else (70, 130, 180)

            pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=8)

            unit_name = small_font.render(
                f"{data['name']} (HP:{data['hp']} DMG:{data['damage'][0]}-{data['damage'][1]})",
                True,
                (240, 248, 255),
            )
            cost_text = small_font.render(f"Cost: {data['hp']} gold", True, (255, 215, 0))

            self.screen.blit(unit_name, (panel_x + 35, btn_y + 10))
            self.screen.blit(cost_text, (panel_x + 35, btn_y + 33))

            self.shop_buttons.append((btn_rect, utype, data["hp"]))

        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.shop_close_btn = pygame.Rect(panel_x + panel_w - 95, panel_y + panel_h - 55, 80, 40)
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
            city_pos = [self.player_spawn[0] + 1, self.player_spawn[1] + 1]
            city_x = city_pos[0] * TILE_SIZE
            city_y = city_pos[1] * TILE_SIZE
            city_rect = pygame.Rect(city_x, city_y, TILE_SIZE, TILE_SIZE)
            if city_rect.collidepoint(mouse_x, mouse_y):
                self.shop_open = True
                self.shop_city_pos = city_pos
            return

        for btn_rect, utype, cost in self.shop_buttons:
            if btn_rect.collidepoint(mouse_x, mouse_y):
                if self.player_gold >= cost:
                    spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
                    spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
                    attempts = 0
                    while (
                        get_unit_at(
                            [spawn_x, spawn_y],
                            self.player_units + self.bot_units + self.bot2_units,
                        )
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

        if self.shop_close_btn and self.shop_close_btn.collidepoint(mouse_x, mouse_y):
            self.shop_open = False
            self.shop_city_pos = None

    def _bot_buy_units(self, bot_units, bot_gold_var, spawn_zone):
        unit_types = list(UNIT_TYPES.keys())
        random.shuffle(unit_types)

        for utype in unit_types:
            cost = UNIT_TYPES[utype]["hp"]
            if bot_gold_var >= cost and len(bot_units) < 8:
                spawn_x = random.randint(spawn_zone[0], spawn_zone[0] + 2)
                spawn_y = random.randint(spawn_zone[1], spawn_zone[1] + 2)
                from utils import get_unit_at

                attempts = 0
                while (
                    get_unit_at(
                        [spawn_x, spawn_y], self.player_units + self.bot_units + self.bot2_units
                    )
                    and attempts < 10
                ):
                    spawn_x = random.randint(spawn_zone[0], spawn_zone[0] + 2)
                    spawn_y = random.randint(spawn_zone[1], spawn_zone[1] + 2)
                    attempts += 1
                if attempts < 10:
                    new_unit = Unit([spawn_x, spawn_y], unit_type=utype, is_player=False)
                    bot_units.append(new_unit)
                    return bot_gold_var - cost
        return bot_gold_var

    def _draw_attack_indicators(self, visible):
        if self.current_turn != "player" or not self.selected_unit:
            return
        if tuple(self.selected_unit.pos) not in visible and not self.debug_fog_override:
            return
        attackable_tiles = _get_attackable_tiles(self.selected_unit, self.bot_units + self.bot2_units)
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

    def _draw_units(self, visible):
        from settings import player_unit_imgs, bot_unit_imgs

        all_units = self.player_units + self.bot_units + self.bot2_units
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
                elif unit in self.bot_units:
                    glow = BOT_GLOW
                else:
                    glow = BOT2_GLOW
                pygame.draw.circle(self.screen, glow, (draw_x, draw_y), TILE_SIZE // 3 + 10)
                pygame.draw.circle(self.screen, unit.color, (draw_x, draw_y), TILE_SIZE // 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (draw_x, draw_y), TILE_SIZE // 3, 2)
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
                if event.key == DEBUG_FOG_KEY:
                    self.debug_fog_override = not self.debug_fog_override
                if event.key == DEBUG_HEAL_KEY and self.current_turn == "player":
                    for u in self.player_units:
                        u.hp = u.max_hp
                if event.key == DEBUG_INSTANT_WIN_KEY:
                    self.bot_units = []
                    self.bot2_units = []
                    self.game_over = True
                    self.winner = "DEBUG WIN"
                if event.key == DEBUG_SKIP_TURN_KEY and self.current_turn == "player":
                    self._end_player_turn()
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
                if interface_btn.collidepoint(mouse_x, mouse_y) and self.current_turn == "player" and not self.shop_open:
                    self._end_player_turn()
                    continue
                if self.current_turn == "player":
                    if self.shop_open:
                        self._handle_shop_click(mouse_x, mouse_y)
                    else:
                        self._handle_field_click(mouse_x, mouse_y)
                        self._handle_shop_click(mouse_x, mouse_y)
        return True

    def _handle_field_click(self, mouse_x, mouse_y):
        from utils import get_unit_at

        grid_pos = [mouse_x // TILE_SIZE, mouse_y // TILE_SIZE]
        clicked_unit = get_unit_at(grid_pos, self.player_units)
        if clicked_unit:
            self.selected_unit = clicked_unit
        elif self.selected_unit and not self.selected_unit.has_moved:
            dx_move = abs(grid_pos[0] - self.selected_unit.pos[0])
            dy_move = abs(grid_pos[1] - self.selected_unit.pos[1])
            if dx_move <= 1 and dy_move <= 1 and (dx_move + dy_move) != 0:
                enemy_unit = get_unit_at(grid_pos, self.bot_units + self.bot2_units)
                if enemy_unit:
                    self._perform_attack(self.selected_unit, enemy_unit)
                elif not get_unit_at(grid_pos, self.player_units) and not get_unit_at(
                    grid_pos, self.bot_units + self.bot2_units
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
        self.current_turn = "bot"
        self.bot_action_index = 0
        self.bot_wait_until = pygame.time.get_ticks() + random.randint(500, 1000)
        for u in self.bot_units:
            u.has_moved = False
        for u in self.bot2_units:
            u.has_moved = False
        for u in self.player_units:
            u.has_moved = False
        self.player_gold += 5

    def _update_game(self):
        if self.paused or self.shop_open:
            return
        for unit in self.player_units + self.bot_units + self.bot2_units:
            unit.update_animation()
            unit.update_shake()
        self.damage_numbers = [d for d in self.damage_numbers if d.update()]
        self.battle_effects = [e for e in self.battle_effects if e.update()]
        self.death_effects = [e for e in self.death_effects if e.update()]
        if not self.game_over:
            if not self.bot_units and not self.bot2_units:
                self.game_over = True
                self.winner = "YOU WIN!"
            elif not self.player_units:
                self.game_over = True
                self.winner = "YOU LOSE"
        if self.current_turn == "player" and not self.game_over:
            elapsed = pygame.time.get_ticks() - self.turn_timer_start - self.total_paused_time
            if elapsed >= TURN_TIME:
                self._end_player_turn()
        if self.current_turn == "bot" and not self.game_over:
            if (
                pygame.time.get_ticks() >= self.bot_wait_until
                and self.bot_action_index < len(self.bot_units)
            ):
                all_enemies = self.player_units + self.bot2_units
                bot_step(
                    self.bot_units[self.bot_action_index],
                    all_enemies,
                    self.bot_units,
                    lambda pos, dmg: self.damage_numbers.append(DamageNumber(pos, dmg)),
                    lambda pos: self.battle_effects.append(BattleEffect(pos)),
                    lambda pos: self.death_effects.append(DeathEffect(pos)),
                )
                self.bot_action_index += 1
                if self.bot_action_index < len(self.bot_units):
                    self.bot_wait_until = pygame.time.get_ticks() + random.randint(400, 800)
                else:
                    self.bot_gold = self._bot_buy_units(self.bot_units, self.bot_gold, self.bot_spawn)
                    self.bot_gold += 5
                    self.current_turn = "bot2"
                    self.bot2_action_index = 0
                    self.bot2_wait_until = pygame.time.get_ticks() + random.randint(500, 1000)
        elif self.current_turn == "bot2" and not self.game_over:
            if (
                pygame.time.get_ticks() >= self.bot2_wait_until
                and self.bot2_action_index < len(self.bot2_units)
            ):
                all_enemies = self.player_units + self.bot_units
                bot_step(
                    self.bot2_units[self.bot2_action_index],
                    all_enemies,
                    self.bot2_units,
                    lambda pos, dmg: self.damage_numbers.append(DamageNumber(pos, dmg)),
                    lambda pos: self.battle_effects.append(BattleEffect(pos)),
                    lambda pos: self.death_effects.append(DeathEffect(pos)),
                )
                self.bot2_action_index += 1
                if self.bot2_action_index < len(self.bot2_units):
                    self.bot2_wait_until = pygame.time.get_ticks() + random.randint(400, 800)
                else:
                    self.bot2_gold = self._bot_buy_units(
                        self.bot2_units, self.bot2_gold, self.bot2_spawn
                    )
                    self.bot2_gold += 5
                    self.current_turn = "player"
                    self.turn_timer_start = pygame.time.get_ticks()
                    self.total_paused_time = 0
                    for u in self.player_units:
                        u.has_moved = False
        self.player_units = [u for u in self.player_units if u.is_alive()]
        self.bot_units = [u for u in self.bot_units if u.is_alive()]
        self.bot2_units = [u for u in self.bot2_units if u.is_alive()]

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
        draw_pause_menu(self.screen, resume_btn, settings_btn, menu_btn)

    def run(self):
        running = True
        while running:
            visible = self._get_visible_tiles()
            self.explored_tiles.update(visible)
            self.screen.blit(self.bg_surface, (0, 0))
            self.screen.blit(self.grid_surface, (0, 0))
            self._draw_top_game_interface()
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
            interface_btn = draw_interface(
                self.screen,
                self.current_turn,
                self.player_units,
                self.bot_units,
                self.bot2_units,
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
                draw_debug_overlay(
                    self.screen, visible, self.player_units, self.bot_units + self.bot2_units
                )
            if self.shop_open:
                self._draw_shop_menu()
            running = self._handle_input(interface_btn, menu_btn_rect)
            self._update_game()
            self._update_music_fade()
            pygame.display.update()
            self.clock.tick(60)
        return self.return_to_menu