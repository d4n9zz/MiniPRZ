import pygame
import random
import math
import settings
import terrain
import iso
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
UI_BORDER,
MAP_OUTSIDE_COLOR,
BOT_GLOW,
BOT2_GLOW,
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
from effects import DamageNumber, BattleEffect, DeathEffect, BattleLog
from ui import (
cards_arrow_rects,
cards_max_scroll,
CARD_STEP,
CARD_W,
CARDS_VIEW_W,
draw_interface,
draw_menu_button,
draw_pause_menu,
)
from music import play_game, fade_music_volume, pause_music, resume_music
from menu import settings_menu
from animation import UIAnimation
from config import get_field_size

GAME_CONFIG = {
'num_bots': 3,
'bot_colors': [BOT_GLOW, BOT2_GLOW, (100, 255, 100), (255, 100, 255), (255, 165, 0)],
'bot_personalities': ['aggressive', 'defensive', 'balanced', 'aggressive', 'defensive'],
'map_seed': None,   # число — каждая партия на одной и той же карте; None — случайная карта
}

def _get_random_spawn_position(is_player, bot_index=None, total_bots=None):
    if is_player:
        min_y = settings.ROWS - 8
        max_y = settings.ROWS - 4
        min_x = 0
        max_x = settings.COLS - 3
    else:
        min_y = 1
        max_y = settings.ROWS // 2
        min_x = 0
        max_x = settings.COLS - 3
        # Распределяем ботов по ширине карты
        if bot_index is not None and total_bots is not None and total_bots > 0:
            zone_width = max(4, settings.COLS // total_bots)
            min_x = bot_index * zone_width
            max_x = min(min_x + zone_width - 3, settings.COLS - 3)
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
            if 0 <= nx < settings.COLS and 0 <= ny < settings.ROWS:
                for enemy in enemy_units:
                    if enemy.pos == [nx, ny]:
                        attackable.append((nx, ny))
    return attackable

ROTATE_SENSITIVITY = 0.008   # радиан на пиксель движения мыши (0.008 ≈ 1 оборот за ~780 px)


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
        "bg_surface", "grid_surface",
        "player_spawn", "player_city_img",
        "bot_city_img", "player_gold",
        "shop_open", "shop_city_pos", "shop_buttons", "shop_close_btn",
        "shop_open_time", "context_tooltip_unit",
        "pause_anim", "map_rect", "rotating", "view_dirty",
        "cards_scroll", "cards_scroll_cur", "cards_last_selected",
        "battle_log", "terrain_surface", "map_seed", "visible_now",
        "fog_cache_key", "fog_cache_surf", "mountain_sprite", "mountain_tiles",
    ]

    def __init__(self, screen, clock, num_bots=None):
        self.screen = screen
        self.clock = clock
        if num_bots is not None:
            GAME_CONFIG['num_bots'] = num_bots
        play_game()
        self.rotating = False    # зажата ли СКМ (идёт вращение камеры)
        self.view_dirty = False  # угол поменялся — надо перерисовать статичные слои
        iso.set_angle(0)         # каждая новая игра начинается с обычного вида
        self._apply_selected_map()
        self._load_city_images()
        self._reset_game()

    def _team_label(self, unit):
        """Подпись стороны юнита для журнала и её цвет."""
        if unit.is_player:
            return "You", PLAYER_HIGHLIGHT
        for i, team in enumerate(self.enemy_teams):
            if unit in team['units']:
                return f"Bot {i + 1}", team['color']
        return "Bot", BOT_GLOW

    def _log_attack(self, attacker, defender, damage, killed):
        # Бой в тумане игрок не видит — в журнал он тоже не попадает
        if not (attacker.is_player or defender.is_player
                or tuple(attacker.pos) in self.visible_now
                or tuple(defender.pos) in self.visible_now):
            return
        a_label, a_color = self._team_label(attacker)
        d_label, d_color = self._team_label(defender)
        self.battle_log.add(
            f"{a_label} {attacker.name} hits {d_label} {defender.name} for {damage}", a_color)
        if killed:
            self.battle_log.add(f"{d_label} {defender.name} destroyed!", (255, 110, 110))

    def _get_all_enemy_units(self):
        all_enemies = []
        for team in self.enemy_teams:
            all_enemies.extend(team['units'])
        return all_enemies

    def _get_all_units(self):
        all_units = self.player_units.copy()
        all_units.extend(self._get_all_enemy_units())
        return all_units

    def _spawn_player_unit(self, utype):
        spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
        spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
        attempts = 0
        from utils import get_unit_at
        all_units = self._get_all_units()
        while get_unit_at([spawn_x, spawn_y], all_units) and attempts < 10:
            spawn_x = random.randint(self.player_spawn[0], self.player_spawn[0] + 2)
            spawn_y = random.randint(self.player_spawn[1], self.player_spawn[1] + 2)
            attempts += 1
        if attempts < 10:
            new_unit = Unit([spawn_x, spawn_y], unit_type=utype, is_player=True)
            self.player_units.append(new_unit)
            return True
        return False

    def _apply_selected_map(self):
        # Берём размер карты из настроек и пересоздаём всё, что от него зависит
        settings.apply_field_preset(get_field_size())
        self._create_static_surfaces()

    def _create_static_surfaces(self):
        # Окно всегда одного размера, карта стоит по центру области поля
        # (при свободном повороте карта «выглядывает» за свой ромб, поэтому окно карты —
        # вся область поля, а центр карты ставит iso._screen_center())
        self.map_rect = pygame.Rect(0, 0, WIDTH, FIELD_HEIGHT)
        self.grid_surface = pygame.Surface(self.map_rect.size, pygame.SRCALPHA)
        self._draw_grid_static()
        self.bg_surface = pygame.Surface((WIDTH, FIELD_HEIGHT))
        self._draw_background_static()

    def _mouse_to_grid(self, mouse_x, mouse_y):
        # Позиция мыши в окне -> клетка карты (изометрия, с учётом смещения карты).
        # Юнит нарисован выше своей клетки, поэтому клик по его спрайту (даже по «голове»)
        # засчитываем как клик по клетке юнита, а не по клетке позади него.
        mx = mouse_x - self.map_rect.x
        my = mouse_y - self.map_rect.y
        best = None
        for unit in self._get_all_units():
            if not unit.is_player and tuple(unit.pos) not in self.visible_now:
                continue
            gx, gy = iso.world_to_screen(unit.px, unit.py)
            if gx - 20 <= mx < gx + 20 and gy - settings.ISO_UNIT_LIFT - 20 <= my < gy + 6:
                depth = iso.depth(unit.px / TILE_SIZE - 0.5, unit.py / TILE_SIZE - 0.5)
                if best is None or depth > best[0]:
                    best = (depth, unit)
        if best is not None:
            return list(best[1].pos)
        return iso.screen_to_grid(mx, my)

    def _rotate_view(self, delta_angle):
        # Свободный поворот камеры (радианы): логика не меняется,
        # перерисовываем только то, что нарисовано заранее
        iso.set_angle(iso.ANGLE + delta_angle)
        self.view_dirty = True

    def _refresh_view(self):
        # Лёгкая перерисовка статичных слоёв (без пересоздания поверхностей) —
        # вызывается раз в кадр, пока крутим камеру
        self.grid_surface.fill((0, 0, 0, 0))
        self._draw_grid_static()
        self._draw_background_static()
        self.terrain_surface = terrain.build_surface(self.map_rect.size)

    def _load_city_images(self):
        self.player_city_img = None
        self.bot_city_img = None
        try:
            player_city = pygame.image.load("resources/ui/player_city.png").convert_alpha()
            self.player_city_img = pygame.transform.smoothscale(
                player_city, (settings.ISO_W - 6, settings.ISO_W - 6)
            )
        except pygame.error:
            pass
        try:
            bot_city = pygame.image.load("resources/ui/bot_city.png").convert_alpha()
            self.bot_city_img = pygame.transform.smoothscale(bot_city, (settings.ISO_W - 6, settings.ISO_W - 6))
        except pygame.error:
            pass

    def _draw_grid_static(self):
        # Каждая клетка — ромб; цвет чуть чередуется, чтобы сетка читалась как «шахматка»
        for y in range(settings.ROWS):
            for x in range(settings.COLS):
                pts = iso.diamond(x, y)
                color = GRID_COLOR if (x + y) % 2 == 0 else (
                    GRID_COLOR[0], GRID_COLOR[1] + 12, GRID_COLOR[2], GRID_COLOR[3] - 25)
                pygame.draw.polygon(self.grid_surface, color, pts)
                pygame.draw.polygon(self.grid_surface, GRID_BORDER, pts, 1)

    def _draw_background_static(self):
        # Вокруг карты тёмная рамка, внутри повёрнутого прямоугольника карты — градиент травы.
        # Заливаем построчно (по 2 px): так дёшево перерисовывать каждый кадр при вращении.
        self.bg_surface.fill(MAP_OUTSIDE_COLOR)
        outline = iso.map_outline()
        n = len(outline)
        top = max(0, min(p[1] for p in outline))
        bottom = min(FIELD_HEIGHT - 1, max(p[1] for p in outline))
        span = max(1, bottom - top)
        for y in range(top, bottom + 1, 2):
            xs = []
            for i in range(n):
                (x1, y1), (x2, y2) = outline[i], outline[(i + 1) % n]
                if y1 != y2 and min(y1, y2) <= y <= max(y1, y2):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            if len(xs) < 2:
                continue
            ratio = (y - top) / span
            color = (
                int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio),
                int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio),
                int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio),
            )
            x_min, x_max = int(min(xs)), int(max(xs))
            pygame.draw.rect(self.bg_surface, color, (x_min, y, x_max - x_min + 1, 2))
        pygame.draw.polygon(self.bg_surface, UI_BORDER, outline, 4)

    def _reset_game(self):
        # Ряд карточек юнитов возвращаем в начало
        self.cards_scroll = 0
        self.cards_scroll_cur = 0.0
        self.cards_last_selected = None
        # Если в настройках выбрали другую карту, она применяется с новой партии
        selected_map = get_field_size()
        if selected_map in settings.FIELD_PRESETS and selected_map != settings.FIELD_PRESET:
            self._apply_selected_map()
        # Сид определяет всю стартовую расстановку: города, местность и первых юнитов
        seed = GAME_CONFIG.get('map_seed')
        if seed is None:
            seed = random.randint(0, 999999)
        self.map_seed = seed
        random.seed(seed)
        min_distance = 5
        num_bots = GAME_CONFIG['num_bots']
        self.player_spawn = _get_random_spawn_position(is_player=True)
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
        # Местность строим, когда все города уже стоят: она не должна их запирать
        terrain.generate([self.player_spawn] + bot_spawns, seed)
        self.terrain_surface = terrain.build_surface(self.map_rect.size)
        self.mountain_sprite = terrain.build_mountain_sprite()
        self.mountain_tiles = terrain.mountain_tiles()
        for i, spawn in enumerate(bot_spawns):
            color = GAME_CONFIG['bot_colors'][i % len(GAME_CONFIG['bot_colors'])]
            personality = GAME_CONFIG['bot_personalities'][i % len(GAME_CONFIG['bot_personalities'])]
            self.enemy_teams.append({
                'units': create_units(2, self._get_all_enemy_units(), is_player=False, spawn_zone=spawn),
                'color': color,
                'personality': personality,
                'spawn': spawn,
                'gold': 15,
                'action_index': 0,
                'wait_until': 0,
            })
        self.player_units = create_units(2, [], is_player=True, spawn_zone=self.player_spawn)
        random.seed()   # дальше партия идёт случайно, как обычно
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
        self.fog_cache_key = None      # туман перерисовывается только когда он изменился
        self.fog_cache_surf = None
        self.player_gold = 15
        self.shop_open = False
        self.shop_city_pos = None
        self.shop_buttons = []
        self.shop_close_btn = None
        self.shop_open_time = 0
        self.context_tooltip_unit = None
        self.visible_now = set()
        self.battle_log = BattleLog()
        self.battle_log.add(f"Map seed: {self.map_seed}", (150, 160, 185))
        # === АНИМАЦИЯ МЕНЮ ПАУЗЫ ===
        self.pause_anim = UIAnimation(duration=UI_ANIM_DURATION)

    def _set_pause_state(self, state):
        if state == self.paused:
            return
        if state:
            self.pause_start_time = pygame.time.get_ticks()
            self.music_fade_target = 0.0
            self.music_fade_speed = 0.04
            self.pause_anim.restart()  # ← перезапуск анимации при открытии
        else:
            self.total_paused_time += pygame.time.get_ticks() - self.pause_start_time
            self.music_fade_target = 1.0
            self.music_fade_speed = 0.04
            try:
                resume_music()
            except Exception:
                pass
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

        if self.paused and self.music_fade_current <= 0.03:
            try:
                pause_music()
            except Exception:
                pass
            self.music_fade_current = 0.0
            fade_music_volume(0.0)

    def _get_visible_tiles(self):
        visible = set()
        for unit in self.player_units:
            x, y = unit.pos
            for dx in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
                for dy in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
                    if dx * dx + dy * dy <= VISIBILITY_RADIUS * VISIBILITY_RADIUS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < settings.COLS and 0 <= ny < settings.ROWS:
                            visible.add((nx, ny))
        player_city_x = self.player_spawn[0]
        player_city_y = self.player_spawn[1]
        for dx in range(3):
            for dy in range(3):
                city_tile = (player_city_x + dx, player_city_y + dy)
                if 0 <= city_tile[0] < settings.COLS and 0 <= city_tile[1] < settings.ROWS:
                    visible.add(city_tile)
                    self.explored_tiles.add(city_tile)
        return visible

    def _draw_city(self, pos, is_player, team_color=None):
        # pos — центральная клетка города; рисуем «здание», стоящее на ромбе
        cx, cy = iso.tile_center(pos[0], pos[1])
        city_img = self.player_city_img if is_player else self.bot_city_img
        if city_img:
            rect = city_img.get_rect(midbottom=(cx, cy + settings.ISO_H // 2 - 2))
            self.screen.blit(city_img, rect)
            return
        if is_player:
            city_color = PLAYER_HIGHLIGHT
        else:
            city_color = team_color if team_color else BOT_GLOW
        base_y = cy + 6
        iso.draw_box(self.screen, cx, base_y, 24, 18, city_color)
        iso.draw_pyramid(self.screen, cx, base_y - 18, 27, 16, (139, 69, 19))
        # Флажок на крыше
        pole_top = (cx, base_y - 18 - 16 - 12)
        pygame.draw.line(self.screen, (60, 40, 20), (cx, base_y - 18 - 16), pole_top, 2)
        pygame.draw.polygon(
            self.screen, (255, 255, 255),
            [pole_top, (pole_top[0] + 9, pole_top[1] + 3), (pole_top[0], pole_top[1] + 6)],
        )

    def _draw_player_aura(self, city_center_pos):
        cx, cy = iso.tile_center(city_center_pos[0], city_center_pos[1])
        t = pygame.time.get_ticks()
        base_angle = t * PLAYER_AURA_ROTATION_SPEED
        pulse = int(40 * abs(math.sin(t * 0.002)))
        aura_alpha = min(255, PLAYER_AURA_COLOR[3] + pulse)
        # Аура лежит на земле, поэтому в изометрии круг превращается в эллипс 2:1
        rx = PLAYER_AURA_RADIUS
        ry = PLAYER_AURA_RADIUS // 2
        ring_surf = pygame.Surface((rx * 2 + 20, ry * 2 + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(
            ring_surf,
            (*PLAYER_AURA_COLOR[:3], aura_alpha // 3),
            (10, 10, rx * 2, ry * 2),
            1,
        )
        self.screen.blit(ring_surf, (cx - rx - 10, cy - ry - 10))
        num_symbols = len(PLAYER_AURA_SYMBOLS)
        for i, symbol in enumerate(PLAYER_AURA_SYMBOLS):
            angle = base_angle + (i * 2 * math.pi / num_symbols)
            sx = cx + int(rx * math.cos(angle))
            sy = cy + int(ry * math.sin(angle))
            symbol_alpha = int(aura_alpha * (0.6 + 0.4 * abs(math.sin(t * 0.003 + i))))
            self._draw_aura_star(sx, sy, symbol.strip(), PLAYER_AURA_COLOR[:3], symbol_alpha)

    def _draw_aura_star(self, x, y, symbol, color, alpha, radius=9):
        # Звёздочка аура рисуется полигоном (шрифт Nunito не содержит символов ✦ ✧ ⚝).
        # ✦ — закрашенная 4-лучевая, ✧ — контурная 4-лучевая, ⚝ — контурная 5-лучевая
        rays = 5 if symbol == '⚝' else 4
        filled = symbol == '✦'
        inner = radius * (0.45 if rays == 5 else 0.35)
        size = radius * 2 + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size / 2
        points = []
        for k in range(rays * 2):
            r = radius if k % 2 == 0 else inner
            a = -math.pi / 2 + k * math.pi / rays
            points.append((c + r * math.cos(a), c + r * math.sin(a)))
        pygame.draw.polygon(surf, (*color, 255), points, 0 if filled else 1)
        surf.set_alpha(alpha)
        self.screen.blit(surf, (x - c, y - c))

    @staticmethod
    def _zone_polygon(spawn):
        x, y = spawn
        return [iso.corner(x, y), iso.corner(x + 3, y), iso.corner(x + 3, y + 3), iso.corner(x, y + 3)]

    def _draw_spawn_zones(self, visible):
        # Здесь только то, что лежит на земле: рамки зон и аура.
        # Сами города рисует _draw_units — они должны сортироваться по глубине с юнитами.
        player_city_pos = [self.player_spawn[0] + 1, self.player_spawn[1] + 1]
        pygame.draw.polygon(self.screen, PLAYER_HIGHLIGHT, self._zone_polygon(self.player_spawn), 3)
        self._draw_player_aura(player_city_pos)
        for team in self.enemy_teams:
            city_pos = [team['spawn'][0] + 1, team['spawn'][1] + 1]
            if _is_city_visible(city_pos, visible):
                pygame.draw.polygon(self.screen, team['color'], self._zone_polygon(team['spawn']), 3)

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
            btn_rect = pygame.Rect(panel_x + 20, btn_y, panel_w - 80, 60)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color = (100, 180, 255) if btn_rect.collidepoint(mouse_x, mouse_y) else (70, 130, 180)
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=8)
            key_number = str(i + 1)
            key_text = small_font.render(f"[{key_number}]", True, (255, 215, 0))
            key_x = panel_x + 30
            text_x = panel_x + 90
            self.screen.blit(key_text, (key_x, btn_y + 20))
            unit_name = small_font.render(
                f"{data['name']} (HP:{data['hp']} DMG:{data['damage'][0]}-{data['damage'][1]})",
                True,
                (240, 248, 255),
            )
            cost_text = small_font.render(f"Cost: {data['hp']} gold", True, (255, 215, 0))
            self.screen.blit(unit_name, (text_x, btn_y + 12))
            self.screen.blit(cost_text, (text_x, btn_y + 34))
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
            cx, cy = iso.tile_center(city_pos[0], city_pos[1])
            # Область клика — всё здание: от флажка до земли
            city_rect = pygame.Rect(cx + self.map_rect.x - 30, cy + self.map_rect.y - 56, 60, 72)
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
                    if self._spawn_player_unit(utype):
                        self.player_gold -= cost
                        self.battle_log.add(f"You recruited {UNIT_TYPES[utype]['name']} (-{cost})", (255, 215, 0))
                return

    def _buy_unit_by_index(self, index):
        from utils import get_unit_at
        unit_types = list(UNIT_TYPES.keys())
        if index < 0 or index >= len(unit_types):
            return
        utype = unit_types[index]
        cost = UNIT_TYPES[utype]["hp"]
        if self.player_gold >= cost:
            if self._spawn_player_unit(utype):
                self.player_gold -= cost
                self.battle_log.add(f"You recruited {UNIT_TYPES[utype]['name']} (-{cost})", (255, 215, 0))

    def _draw_attack_indicators(self, visible):
        if self.current_turn != "player" or not self.selected_unit:
            return
        if tuple(self.selected_unit.pos) not in visible:
            return
        all_enemies = []
        for team in self.enemy_teams:
            all_enemies.extend(team['units'])
        attackable_tiles = _get_attackable_tiles(self.selected_unit, all_enemies)
        for tx, ty in attackable_tiles:
            if (tx, ty) not in visible:
                continue
            pts = iso.diamond(tx, ty)
            min_x = min(p[0] for p in pts)
            min_y = min(p[1] for p in pts)
            w = max(p[0] for p in pts) - min_x + 1
            h = max(p[1] for p in pts) - min_y + 1
            local = [(px - min_x, py - min_y) for px, py in pts]
            highlight_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(highlight_surf, ATTACK_RANGE_COLOR, local)
            pygame.draw.polygon(highlight_surf, (255, 255, 255), local, 2)
            self.screen.blit(highlight_surf, (min_x, min_y))

    def _draw_fog_of_war(self, visible):
        # Туман рисуем в одну поверхность и перестраиваем только при изменении:
        # ромбы не прямоугольные, и 700+ blit-ов за кадр были бы лишними.
        key = (round(iso.ANGLE, 4), len(self.explored_tiles), frozenset(visible))
        if self.fog_cache_surf is None or key != self.fog_cache_key:
            surf = pygame.Surface(self.map_rect.size, pygame.SRCALPHA)
            for y in range(settings.ROWS):
                for x in range(settings.COLS):
                    tile_pos = (x, y)
                    if tile_pos not in self.explored_tiles:
                        color = FOG_UNEXPLORED
                    elif tile_pos not in visible:
                        color = FOG_EXPLORED_NO_VIS
                    else:
                        continue
                    pts = iso.diamond(x, y)
                    pygame.draw.polygon(surf, color, pts)
                    pygame.draw.polygon(surf, color, pts, 1)   # закрывает швы между ромбами
            self.fog_cache_surf = surf
            self.fog_cache_key = key
        self.screen.blit(self.fog_cache_surf, (0, 0))

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

    def _unit_image(self, unit):
        from settings import player_unit_imgs, bot_unit_imgs
        if unit.is_player:
            return player_unit_imgs.get(unit.unit_type)
        unit_img = None
        for team_index, team in enumerate(self.enemy_teams):
            if unit in team['units']:
                team_img_dict = bot_unit_imgs.get(team_index, {}) if isinstance(bot_unit_imgs, dict) else {}
                if isinstance(team_img_dict, dict):
                    unit_img = team_img_dict.get(unit.unit_type)
                if unit_img is None and isinstance(bot_unit_imgs, dict):
                    unit_img = bot_unit_imgs.get(unit.unit_type)
                break
        return unit_img

    def _draw_one_unit(self, unit):
        unit_img = self._unit_image(unit)
        # Центр клетки на земле (плавно едет вместе с анимацией хода) + тряска от удара
        ground_x, ground_y = iso.world_to_screen(unit.px, unit.py)
        ground_x += unit.shake_offset[0]
        ground_y += unit.shake_offset[1]
        draw_x = ground_x
        draw_y = ground_y - settings.ISO_UNIT_LIFT      # спрайт «стоит» над клеткой
        # Тень на земле
        shadow = pygame.Surface((36, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 36, 18))
        self.screen.blit(shadow, (ground_x - 18, ground_y - 9))
        # Кольцо выбора лежит на земле — эллипс 2:1
        if unit == self.selected_unit:
            for i in range(3):
                alpha = 200 - i * 50
                rw = settings.ISO_W - 14 + i * 8
                rh = rw // 2
                ring = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
                pygame.draw.ellipse(ring, (*PLAYER_HIGHLIGHT, alpha), (2, 2, rw, rh), 3)
                self.screen.blit(ring, (ground_x - rw // 2 - 2, ground_y - rh // 2 - 2))
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
            pygame.draw.circle(self.screen, glow, (draw_x, draw_y), TILE_SIZE // 3 + 4)
            pygame.draw.circle(self.screen, unit.color, (draw_x, draw_y), TILE_SIZE // 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (draw_x, draw_y), TILE_SIZE // 3, 2)
        self._draw_hp_bar(unit, draw_x, draw_y)

    def _draw_units(self, visible):
        # Всё, что стоит «в мире» (горы, города, юниты), рисуем от дальних клеток к ближним:
        # так передние объекты правильно перекрывают задние (порядок задаёт iso.depth).
        items = []
        for (x, y) in self.mountain_tiles:
            if (x, y) in self.explored_tiles:
                items.append((iso.depth(x, y), 0, 'mountain', (x, y)))
        items.append((iso.depth(self.player_spawn[0] + 1, self.player_spawn[1] + 1), 0, 'city',
                      (True, [self.player_spawn[0] + 1, self.player_spawn[1] + 1], None)))
        for team in self.enemy_teams:
            city_pos = [team['spawn'][0] + 1, team['spawn'][1] + 1]
            if _is_city_visible(city_pos, visible):
                items.append((iso.depth(city_pos[0], city_pos[1]), 0, 'city', (False, city_pos, team['color'])))
        for unit in self._get_all_units():
            if tuple(unit.pos) not in visible and not unit.is_player:
                continue
            depth = iso.depth(unit.px / TILE_SIZE - 0.5, unit.py / TILE_SIZE - 0.5)
            items.append((depth, 1, 'unit', unit))
        items.sort(key=lambda it: (it[0], it[1]))
        sprite_h = settings.ISO_PEAK_H
        for _, _, kind, data in items:
            if kind == 'mountain':
                top_x, top_y = iso.tile_top(data[0], data[1])
                self.screen.blit(self.mountain_sprite,
                                 (int(top_x) - settings.ISO_W // 2, int(top_y) - sprite_h))
            elif kind == 'city':
                self._draw_city(data[1], is_player=data[0], team_color=data[2])
            else:
                self._draw_one_unit(data)

    def _draw_context_tooltip(self, visible):
        from settings import small_font
        if not small_font or not self.context_tooltip_unit:
            return
        all_units = self._get_all_units()
        if self.context_tooltip_unit not in all_units:
            self.context_tooltip_unit = None
            return
        unit = self.context_tooltip_unit
        if tuple(unit.pos) not in visible and not unit.is_player:
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
        ground_x, ground_y = iso.tile_center(unit.pos[0], unit.pos[1])
        unit_screen_x = ground_x + self.map_rect.x
        unit_screen_y = ground_y - settings.ISO_UNIT_LIFT + self.map_rect.y
        half_w = settings.ISO_W // 2
        tooltip_x = unit_screen_x + half_w + 10
        tooltip_y = unit_screen_y - tooltip_height // 2
        if tooltip_x + tooltip_width > WIDTH:
            tooltip_x = unit_screen_x - half_w - tooltip_width - 10
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

    def _scroll_cards(self, direction):
        # direction: -1 — влево, +1 — вправо (на одну карточку)
        max_scroll = cards_max_scroll(len(self.player_units))
        self.cards_scroll = max(0, min(max_scroll, self.cards_scroll + direction * CARD_STEP))

    def _update_cards_scroll(self):
        max_scroll = cards_max_scroll(len(self.player_units))
        # Если выбрали юнита (клавишей или кликом) — показываем его карточку
        if self.selected_unit is not self.cards_last_selected:
            self.cards_last_selected = self.selected_unit
            if self.selected_unit in self.player_units:
                left = self.player_units.index(self.selected_unit) * CARD_STEP
                right = left + CARD_W
                if left < self.cards_scroll:
                    self.cards_scroll = left
                elif right > self.cards_scroll + CARDS_VIEW_W:
                    self.cards_scroll = right - CARDS_VIEW_W
        self.cards_scroll = max(0, min(max_scroll, self.cards_scroll))
        # Плавное движение к целевому смещению
        diff = self.cards_scroll - self.cards_scroll_cur
        if abs(diff) < 0.5:
            self.cards_scroll_cur = float(self.cards_scroll)
        else:
            self.cards_scroll_cur += diff * 0.25

    def _handle_input(self, interface_btn, menu_btn_rect):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.shop_open:
                        self.shop_open = False
                        self.shop_city_pos = None
                    else:
                        self._set_pause_state(not self.paused)
                if event.key == pygame.K_l and not self.paused:
                    self.battle_log.toggle()
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
                if self.shop_open and self.current_turn == "player" and not self.game_over and not self.paused:
                    unit_types = list(UNIT_TYPES.keys())
                    keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
                    for i, k in enumerate(keys):
                        if event.key == k and len(unit_types) > i:
                            self._buy_unit_by_index(i)
                            break
            if event.type == pygame.MOUSEWHEEL and not self.paused and not self.shop_open:
                # Колесо над нижней панелью прокручивает ряд карточек
                if pygame.mouse.get_pos()[1] >= FIELD_HEIGHT:
                    delta = -event.y if event.y else event.x
                    if delta:
                        self._scroll_cards(1 if delta > 0 else -1)
            if event.type == pygame.MOUSEMOTION and self.rotating:
                if self.paused or self.shop_open or not event.buttons[1]:
                    self.rotating = False
                else:
                    self._rotate_view(-event.rel[0] * ROTATE_SENSITIVITY)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                self.rotating = False
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                if event.button in (4, 5):
                    continue  # старые события колеса — не считаем кликами
                if event.button == 2:
                    # Зажатая средняя кнопка: тянем мышь влево/вправо — камера крутится свободно
                    if not self.paused and not self.shop_open:
                        self.rotating = True
                    continue
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if event.button == 3:
                    from utils import get_unit_at
                    grid_pos = self._mouse_to_grid(mouse_x, mouse_y)
                    all_units = self._get_all_units()
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
                        settings_menu(self.screen, self.clock, in_game=True)
                        self._set_pause_state(True)
                    elif self.pause_menu_btn and self.pause_menu_btn.collidepoint(mouse_x, mouse_y):
                        self.return_to_menu = True
                        return False
                    continue
                if event.button == 1 and not self.shop_open:
                    left_arrow, right_arrow = cards_arrow_rects()
                    if cards_max_scroll(len(self.player_units)) > 0:
                        if left_arrow.collidepoint(mouse_x, mouse_y):
                            self._scroll_cards(-1)
                            continue
                        if right_arrow.collidepoint(mouse_x, mouse_y):
                            self._scroll_cards(1)
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
                elif not self.paused and not self.shop_open:
                    self._handle_field_click(mouse_x, mouse_y)
        return True

    def _handle_field_click(self, mouse_x, mouse_y):
        from utils import get_unit_at
        grid_pos = self._mouse_to_grid(mouse_x, mouse_y)
        if not (0 <= grid_pos[0] < settings.COLS and 0 <= grid_pos[1] < settings.ROWS):
            return  # клик мимо карты (рамка или нижняя панель)
        clicked_unit = get_unit_at(grid_pos, self.player_units)
        if clicked_unit:
            if self.selected_unit == clicked_unit:
                self.selected_unit = None
            else:
                self.selected_unit = clicked_unit
            return
        if self.current_turn != "player":
            return
        if self.selected_unit and not self.selected_unit.has_moved:
            dx_move = abs(grid_pos[0] - self.selected_unit.pos[0])
            dy_move = abs(grid_pos[1] - self.selected_unit.pos[1])
            if dx_move <= 1 and dy_move <= 1 and (dx_move + dy_move) != 0:
                all_enemies = []
                for team in self.enemy_teams:
                    all_enemies.extend(team['units'])
                enemy_unit = get_unit_at(grid_pos, all_enemies)
                if enemy_unit:
                    self._perform_attack(self.selected_unit, enemy_unit)
                elif terrain.is_blocked(grid_pos):
                    return  # вода и горы непроходимы
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
        self._log_attack(attacker, defender, attack_damage, not defender.is_alive())
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
        self.battle_log.add("- Bots' turn -", (150, 160, 185))
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
            all_enemy_units = self._get_all_enemy_units()
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
                    all_enemies.extend(u for i, t in enumerate(self.enemy_teams) if i != self.current_bot_index for u in t['units'])
                    bot_unit = current_team['units'][current_team['action_index']]
                    bot_step(
                        bot_unit,
                        all_enemies,
                        current_team['units'],
                        personality=current_team['personality'],
                        damage_callback=lambda pos, dmg: self.damage_numbers.append(DamageNumber(pos, dmg)),
                        effect_callback=lambda pos: self.battle_effects.append(BattleEffect(pos)),
                        death_callback=lambda pos: self.death_effects.append(DeathEffect(pos)),
                        attack_callback=self._log_attack,
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
                            self.battle_log.add("- Your turn -", (150, 160, 185))
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
        resume_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2 - 40, 240, 50)
        settings_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2 + 20, 240, 50)
        menu_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2 + 80, 240, 50)
        self.pause_resume_btn = resume_btn
        self.pause_settings_btn = settings_btn
        self.pause_menu_btn = menu_btn
        # === ПЕРЕДАЁМ АНИМАЦИЮ В МЕНЮ ПАУЗЫ ===
        draw_pause_menu(self.screen, resume_btn, settings_btn, menu_btn, self.pause_anim)

    def run(self):
        running = True
        while running:
            if self.view_dirty:
                self._refresh_view()
                self.view_dirty = False
            visible = self._get_visible_tiles()
            self.explored_tiles.update(visible)
            self.visible_now = visible
            real_screen = self.screen
            real_screen.blit(self.bg_surface, (0, 0))
            real_screen.blit(self.grid_surface, self.map_rect.topleft)
            real_screen.blit(self.terrain_surface, self.map_rect.topleft)
            # Карта рисуется на подповерхности окна: внутри неё координаты
            # начинаются с (0, 0), поэтому код отрисовки юнитов, тумана и
            # эффектов работает без смещений. После карты экран возвращаем.
            self.screen = real_screen.subsurface(self.map_rect)
            try:
                self._draw_spawn_zones(visible)
                self._draw_attack_indicators(visible)
                self._draw_units(visible)
                for dmg in self.damage_numbers:
                    dmg.draw(self.screen, visible)
                for effect in self.battle_effects:
                    effect.draw(self.screen, visible)
                for effect in self.death_effects:
                    effect.draw(self.screen, visible)
                self._draw_fog_of_war(visible)
            finally:
                self.screen = real_screen
            all_bot_units = self._get_all_enemy_units()
            self._update_cards_scroll()
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
                self.cards_scroll_cur,
                stars=self.player_gold,
                stars_change=5,
            )
            menu_btn_rect = draw_menu_button(self.screen)
            self.battle_log.draw(self.screen, 10, 70, settings.card_font or settings.small_font)
            if self.paused:
                self._draw_pause_menu()
            if self.game_over:
                self._draw_game_over()
            if self.shop_open:
                self._draw_shop_menu()
            self._draw_context_tooltip(visible)
            running = self._handle_input(interface_btn, menu_btn_rect)
            self._update_game()
            self._update_music_fade()
            pygame.display.update()
            self.clock.tick(60)
        return self.return_to_menu