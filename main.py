import pygame
import random
import math
import os
import sys

pygame.init()

# Настройки
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 50
INTERFACE_HEIGHT = 80
FIELD_HEIGHT = HEIGHT - INTERFACE_HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini What?")
cols, rows = WIDTH // TILE_SIZE, FIELD_HEIGHT // TILE_SIZE


# ===== ИСПРАВЛЕНИЕ ШРИФТА =====
def load_font(size):
    """Пытается загрузить шрифт с поддержкой Unicode символов"""
    font_names = ["segoeuisymbol", "segoe ui", "arial", "dejavusans", "freesansbold", None]
    for name in font_names:
        try:
            font_test = pygame.font.SysFont(name, size)
            test = font_test.render("▶", True, (255, 255, 255))
            if test.get_width() > 0:
                return font_test
        except pygame.error:
            continue
    return pygame.font.SysFont(None, size)


font = load_font(28)
big_font = load_font(60)
small_font = load_font(20)
card_font = load_font(16)
damage_font = load_font(32) 
# ============================

clock = pygame.time.Clock()
VISIBILITY_RADIUS = 2

# Цвета
BG_TOP, BG_BOTTOM = (34, 139, 34), (144, 238, 144)
GRID_COLOR, GRID_BORDER = (25, 100, 25, 120), (18, 72, 18)
PLAYER_COLOR, PLAYER_GLOW, PLAYER_HIGHLIGHT = (255, 107, 107), (255, 150, 150), (255, 214, 107)
BOT_COLOR, BOT_GLOW = (106, 184, 255), (135, 206, 255)
UI_BG, UI_BORDER, UI_TEXT = (45, 52, 70), (100, 149, 237), (240, 248, 255)
UI_BUTTON_NORMAL, UI_BUTTON_HOVER, UI_BUTTON_SHADOW = (70, 130, 180), (100, 180, 255), (20, 25, 40)
HIT_EFFECT_COLORS = [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 105, 180), (138, 43, 226)]
FOG_UNEXPLORED, FOG_EXPLORED_NO_VIS = (15, 20, 35, 230), (30, 40, 60, 90)
TIMER_SAFE, TIMER_WARNING, TIMER_DANGER = (50, 205, 50), (255, 165, 0), (255, 69, 0)
MENU_BG_TOP, MENU_BG_BOTTOM = (25, 32, 50), (45, 52, 70)
MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER = (100, 149, 237), (135, 206, 250)
MENU_BTN_RED, MENU_BTN_RED_HOVER = (255, 99, 71), (255, 130, 102)


# ===== ЗАГРУЗКА ИЗОБРАЖЕНИЙ ЮНИТОВ =====
def load_unit_image(filepath):
    """Загружает изображение юнита с прозрачностью"""
    try:
        if os.path.exists(filepath):
            img = pygame.image.load(filepath).convert_alpha()
            img = pygame.transform.smoothscale(img, (TILE_SIZE - 10, TILE_SIZE - 10))
            return img
    except pygame.error as e:
        print(f"Не удалось загрузить {filepath}: {e}")
    return None


player_unit_img = load_unit_image("player_pawn.png")
bot_unit_img = load_unit_image("bot_pawn.png")


# =========================================


def get_empty_pos(existing_units):
    while True:
        pos = [random.randint(0, cols - 1), random.randint(0, rows - 1)]
        if not any(u["pos"] == pos for u in existing_units):
            return pos


def get_unit_at(pos, units_list):
    for u in units_list:
        if u["pos"] == pos:
            return u
    return None


def move_towards(start, target):
    dx, dy = target[0] - start[0], target[1] - start[1]
    step = [0, 0]
    if dx != 0:
        step[0] = 1 if dx > 0 else -1
    if dy != 0:
        step[1] = 1 if dy > 0 else -1
    return [start[0] + step[0], start[1] + step[1]]


def main_menu():
    running_menu = True

    # ===== СНЕГ =====
    snowflakes = []
    for _ in range(100):
        snowflakes.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'size': random.randint(2, 5),
            'speed': random.uniform(0.5, 2.0),
            'wind': random.uniform(-0.3, 0.3)
        })
    # ================

    while running_menu:
        # Градиентный фон
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(MENU_BG_TOP[0] * (1 - ratio) + MENU_BG_BOTTOM[0] * ratio)
            g = int(MENU_BG_TOP[1] * (1 - ratio) + MENU_BG_BOTTOM[1] * ratio)
            b = int(MENU_BG_TOP[2] * (1 - ratio) + MENU_BG_BOTTOM[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # ===== ОТРИСОВКА СНЕГА =====
        for flake in snowflakes:
            pygame.draw.circle(screen, (255, 255, 255), (int(flake['x']), int(flake['y'])), flake['size'])
            flake['y'] += flake['speed']
            flake['x'] += flake['wind']
            if flake['y'] > HEIGHT:
                flake['y'] = -5
                flake['x'] = random.randint(0, WIDTH)
            if flake['x'] > WIDTH:
                flake['x'] = 0
            elif flake['x'] < 0:
                flake['x'] = WIDTH
        # ==========================

        menu_mouse_x, menu_mouse_y = pygame.mouse.get_pos()

        # ===== ИЗМЕНЕНИЕ КНОПОК =====
        button_width, button_height, button_spacing = 260, 60, 0
        play_btn = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height,
                               button_width, button_height)
        settings_btn = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2, button_width,
                                   button_height)
        exit_btn = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + button_height,
                               button_width, button_height)
        # ============================

        buttons = [(play_btn, "▶ PLAY", MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER),
                   (settings_btn, "⚙ SETTINGS", MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER),
                   (exit_btn, "✕ EXIT", MENU_BTN_RED, MENU_BTN_RED_HOVER)]

        for btn_rect, btn_text, color, hover_color in buttons:
            current_color = hover_color if btn_rect.collidepoint(menu_mouse_x, menu_mouse_y) else color
            pygame.draw.rect(screen, (10, 12, 20), btn_rect.move(4, 4), border_radius=12)
            pygame.draw.rect(screen, current_color, btn_rect, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=12)
            text_surface = font.render(btn_text, True, UI_TEXT)
            screen.blit(text_surface, text_surface.get_rect(center=btn_rect.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()  # 🔧 Исправлено: exit() → sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_btn.collidepoint(menu_mouse_x, menu_mouse_y):
                    running_menu = False
                elif exit_btn.collidepoint(menu_mouse_x, menu_mouse_y):
                    pygame.quit()
                    sys.exit()  # 🔧 Исправлено: exit() → sys.exit()
            if event.type == pygame.MOUSEMOTION:
                if any(btn.collidepoint(menu_mouse_x, menu_mouse_y) for btn, _, _, _ in buttons):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        pygame.display.update()
        clock.tick(60)


def run_game():
    player_units = [{"pos": get_empty_pos([]), "hp": 10, "move_path": [], "has_moved": False} for _ in range(2)]
    bot_units = [{"pos": get_empty_pos(player_units), "hp": 10, "move_path": [], "has_moved": False} for _ in range(2)]
    selected_unit, battle_effects, current_turn = None, [], "player"
    game_over, winner, bot_action_index, bot_wait_until = False, None, 0, 0
    explored_tiles, TURN_TIME, turn_timer_start = set(), 30000, pygame.time.get_ticks()
    damage_numbers = []  # 🔧 Список для цифр урона

    def get_visible_tiles():
        visible = set()
        for unit in player_units:
            x, y = unit["pos"]
            for dx in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
                for dy in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS + 1):
                    if dx * dx + dy * dy <= VISIBILITY_RADIUS * VISIBILITY_RADIUS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            visible.add((nx, ny))
        return visible

    def draw_background():
        for y in range(FIELD_HEIGHT):
            ratio = y / FIELD_HEIGHT
            r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
            g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
            b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    def draw_grid():
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, GRID_COLOR, rect)
                pygame.draw.rect(screen, GRID_BORDER, rect, 1)

    def draw_fog_of_war():
        current_visible = get_visible_tiles()
        for y in range(rows):
            for x in range(cols):
                tile_pos = (x, y)
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile_pos not in explored_tiles:
                    fog_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    fog_overlay.fill(FOG_UNEXPLORED)
                    screen.blit(fog_overlay, tile_rect.topleft)
                elif tile_pos not in current_visible:
                    fog_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    fog_overlay.fill(FOG_EXPLORED_NO_VIS)
                    screen.blit(fog_overlay, tile_rect.topleft)

    def update_all_animations():
        """Обновляет визуальные координаты (px, py) для плавного движения всех юнитов"""
        for unit in player_units + bot_units:
            if unit["move_path"]:
                target = unit["move_path"][0]

                if not isinstance(target, (list, tuple)) or len(target) < 2:
                    continue

                px = unit.get("px", unit["pos"][0] * TILE_SIZE + TILE_SIZE // 2)
                py = unit.get("py", unit["pos"][1] * TILE_SIZE + TILE_SIZE // 2)
                target_px = target[0] * TILE_SIZE + TILE_SIZE // 2
                target_py = target[1] * TILE_SIZE + TILE_SIZE // 2
                dx, dy = target_px - px, target_py - py
                step = 6
                if abs(dx) <= step and abs(dy) <= step:
                    unit["pos"] = list(target)
                    unit["move_path"].pop(0)
                    px, py = target_px, target_py
                else:
                    px += step if dx > 0 else -step if dx < 0 else 0
                    py += step if dy > 0 else -step if dy < 0 else 0
                unit["px"], unit["py"] = px, py

    def draw_units(visible):
        nonlocal selected_unit
        for unit in player_units + bot_units:
            if tuple(unit["pos"]) not in visible and unit in bot_units:
                continue

            px = unit.get("px", unit["pos"][0] * TILE_SIZE + TILE_SIZE // 2)
            py = unit.get("py", unit["pos"][1] * TILE_SIZE + TILE_SIZE // 2)
            is_player = unit in player_units

            if is_player and player_unit_img:
                img_rect = player_unit_img.get_rect(center=(int(px), int(py)))
                screen.blit(player_unit_img, img_rect)
            elif not is_player and bot_unit_img:
                img_rect = bot_unit_img.get_rect(center=(int(px), int(py)))
                screen.blit(bot_unit_img, img_rect)
            else:
                color = PLAYER_COLOR if is_player else BOT_COLOR
                glow = PLAYER_GLOW if is_player else BOT_GLOW
                pygame.draw.circle(screen, glow, (int(px), int(py)), TILE_SIZE // 3 + 10)
                pygame.draw.circle(screen, color, (int(px), int(py)), TILE_SIZE // 3)
                pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), TILE_SIZE // 3, 2)

            if unit == selected_unit:
                for i in range(3):
                    alpha = 200 - i * 50
                    highlight_surf = pygame.Surface((TILE_SIZE + 20, TILE_SIZE + 20), pygame.SRCALPHA)
                    pygame.draw.circle(highlight_surf, (*PLAYER_HIGHLIGHT, alpha),
                                       (TILE_SIZE // 2 + 10, TILE_SIZE // 2 + 10), TILE_SIZE // 3 + 12 + i * 4, 3)
                    screen.blit(highlight_surf, (px - TILE_SIZE // 2 - 10, py - TILE_SIZE // 2 - 10))

    # 🔧 НОВАЯ ФУНКЦИЯ: отрисовка цифр урона
    def draw_damage_numbers(visible):
        nonlocal damage_numbers
        new_damage_numbers = []

        for dmg in damage_numbers:
            ex, ey = dmg["pos"]

            # Пропускаем отрисовку урона в тумане (для ботов)
            if (ex, ey) not in visible:
                new_damage_numbers.append(dmg)
                continue

            px = ex * TILE_SIZE + TILE_SIZE // 2
            py = dmg["y_offset"]  # Анимация всплытия

            # Цвет зависит от величины урона
            if dmg["value"] >= 4:
                color = (255, 69, 0)  # 🔴 Крит (красный)
            elif dmg["value"] >= 3:
                color = (255, 140, 0)  # 🟠 Сильный (оранжевый)
            else:
                color = (255, 255, 255)  # ⚪ Обычный (белый)

            # Альфа-канал для исчезновения
            alpha = min(255, dmg["timer"] * 15)
            damage_surf = pygame.Surface((60, 40), pygame.SRCALPHA)

            # Рендерим текст с обводкой
            text = damage_font.render(f"-{dmg['value']}", True, color)
            shadow = damage_font.render(f"-{dmg['value']}", True, (0, 0, 0))

            damage_surf.blit(shadow, (2, 2))
            damage_surf.blit(text, (0, 0))
            damage_surf.set_alpha(alpha)

            screen.blit(damage_surf, (px - 30, py - 20))

            # Анимация: всплывает вверх
            dmg["y_offset"] -= 1.5
            dmg["timer"] -= 1

            if dmg["timer"] > 0:
                new_damage_numbers.append(dmg)

        damage_numbers = new_damage_numbers

    def draw_battle_effects(visible):
        nonlocal battle_effects
        new_effects = []
        for effect in battle_effects:
            ex, ey = effect["pos"]
            if (ex, ey) not in visible:
                new_effects.append(effect)
                continue
            px = ex * TILE_SIZE + TILE_SIZE // 2
            py = ey * TILE_SIZE + TILE_SIZE // 2
            pulse = abs(math.sin(pygame.time.get_ticks() / 80)) * 6
            color = HIT_EFFECT_COLORS[effect["timer"] % len(HIT_EFFECT_COLORS)]
            pygame.draw.circle(screen, color, (int(px), int(py)), int(TILE_SIZE // 3 + 8 + pulse), 4)
            effect["timer"] -= 1
            if effect["timer"] > 0:
                new_effects.append(effect)
        battle_effects = new_effects

    def draw_unit_card(card_x, card_y, unit_color, hp_value):
        """Рисует карточку юнита: сверху PAWN, снизу HP"""
        card_width = 70
        card_height = 60

        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(screen, UI_BG, card_rect, border_radius=8)
        pygame.draw.rect(screen, unit_color, card_rect, 2, border_radius=8)

        pygame.draw.line(screen, unit_color,
                         (card_x + 10, card_y + 30),
                         (card_x + card_width - 10, card_y + 30), 2)

        pawn_text = card_font.render("PAWN", True, unit_color)
        pawn_rect = pawn_text.get_rect(center=(card_x + card_width // 2, card_y + 16))
        screen.blit(pawn_text, pawn_rect)

        hp_text = card_font.render(f"HP {hp_value}", True, UI_TEXT)
        hp_rect = hp_text.get_rect(center=(card_x + card_width // 2, card_y + 44))
        screen.blit(hp_text, hp_rect)

    def draw_interface():
        nonlocal turn_timer_start
        panel_rect = pygame.Rect(0, FIELD_HEIGHT, WIDTH, INTERFACE_HEIGHT)
        pygame.draw.rect(screen, UI_BG, panel_rect)
        pygame.draw.rect(screen, UI_BORDER, panel_rect, 3)
        turn_text = font.render(f"✦ Turn: {current_turn.upper()} ✦", True, UI_TEXT)
        screen.blit(turn_text, (25, FIELD_HEIGHT + 22))

        interface_btn_rect = pygame.Rect(WIDTH - 170, FIELD_HEIGHT + 12, 150, 56)
        interface_mouse_x, interface_mouse_y = pygame.mouse.get_pos()
        btn_color = UI_BUTTON_HOVER if interface_btn_rect.collidepoint(interface_mouse_x,
                                                                       interface_mouse_y) else UI_BUTTON_NORMAL
        pygame.draw.rect(screen, UI_BUTTON_SHADOW, interface_btn_rect.move(4, 4), border_radius=12)
        pygame.draw.rect(screen, btn_color, interface_btn_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), interface_btn_rect, 2, border_radius=12)
        button_text = font.render("END TURN", True, UI_TEXT)
        text_rect = button_text.get_rect(center=interface_btn_rect.center)
        screen.blit(button_text, text_rect)

        for i, unit in enumerate(player_units):
            card_x_pos = 280 + i * 80
            card_y_pos = FIELD_HEIGHT + 10
            draw_unit_card(card_x_pos, card_y_pos, PLAYER_COLOR, unit["hp"])

        for i, unit in enumerate(bot_units):
            card_x_pos = WIDTH - 340 + i * 80
            card_y_pos = FIELD_HEIGHT + 10
            draw_unit_card(card_x_pos, card_y_pos, BOT_COLOR, unit["hp"])

        if current_turn == "player":
            interface_time = pygame.time.get_ticks()
            remaining = max(0, TURN_TIME - (interface_time - turn_timer_start))
            ratio = remaining / TURN_TIME
            bar_w, bar_h, padding = 130, 16, 15
            bar_x, bar_y = WIDTH - padding - bar_w, padding
            pygame.draw.rect(screen, (10, 12, 20), (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), border_radius=10)
            pygame.draw.rect(screen, (50, 55, 75), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
            fill_col = TIMER_DANGER if remaining <= 5000 else TIMER_WARNING if remaining <= 10000 else TIMER_SAFE
            pygame.draw.rect(screen, fill_col, (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=8)

            secs = int((remaining + 999) / 1000)
            time_text = small_font.render(f"⏱ {secs}s", True, UI_TEXT)
            bg_surf = pygame.Surface((time_text.get_width() + 12, time_text.get_height() + 6), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 180))
            time_y = bar_y + bar_h // 2 - time_text.get_height() // 2
            screen.blit(bg_surf, (bar_x - time_text.get_width() - 20, time_y))
            screen.blit(time_text, (bar_x - time_text.get_width() - 16, time_y))

        return interface_btn_rect

    def bot_step(b_unit):
        for p_unit in player_units:
            dx = abs(b_unit["pos"][0] - p_unit["pos"][0])
            dy = abs(b_unit["pos"][1] - p_unit["pos"][1])
            if dx <= 1 and dy <= 1 and (dx + dy) != 0:
                damage = random.randint(1, 4)
                p_unit["hp"] -= damage
                # 🔧 Добавляем цифру урона
                damage_numbers.append({
                    "pos": p_unit["pos"],
                    "value": damage,
                    "y_offset": p_unit["pos"][1] * TILE_SIZE + TILE_SIZE // 2,
                    "timer": 20
                })
                battle_effects.append({"pos": p_unit["pos"], "color": random.choice(HIT_EFFECT_COLORS), "timer": 8})
                return
        if player_units:
            target = random.choice(player_units)["pos"]
            new_pos = move_towards(b_unit["pos"], target)
            if isinstance(new_pos, list) and len(new_pos) == 2:
                if 0 <= new_pos[0] < cols and 0 <= new_pos[1] < rows:
                    if not get_unit_at(new_pos, bot_units) and not get_unit_at(new_pos, player_units):
                        b_unit["move_path"] = [new_pos]

    running_game = True
    while running_game:
        visible_tiles = get_visible_tiles()
        explored_tiles.update(visible_tiles)

        update_all_animations()

        draw_background()
        draw_grid()
        draw_units(visible_tiles)
        draw_damage_numbers(visible_tiles)
        draw_battle_effects(visible_tiles)
        draw_fog_of_war()

        interface_btn = draw_interface()

        if not game_over:
            if not bot_units:
                game_over = True
                winner = "🏆 YOU WIN! 🏆"
            elif not player_units:
                game_over = True
                winner = "💀 YOU LOSE 💀"

        if game_over:
            overlay_surf = pygame.Surface((WIDTH, HEIGHT))
            overlay_surf.set_alpha(200)
            overlay_surf.fill((15, 20, 35))
            screen.blit(overlay_surf, (0, 0))
            text = big_font.render(winner, True, PLAYER_HIGHLIGHT)
            shadow = big_font.render(winner, True, (0, 0, 0))
            screen.blit(shadow, (WIDTH // 2 - 148, HEIGHT // 2 - 38))
            screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2 - 40))
            screen.blit(font.render("Press SPACE to restart", True, UI_TEXT), (WIDTH // 2 - 100, HEIGHT // 2 + 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()  # 🔧 Исправлено: exit() → sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game_over:
                    return
                elif current_turn == "player":
                    current_turn = "bot"
                    bot_action_index = 0
                    bot_wait_until = pygame.time.get_ticks() + random.randint(500, 1000)
                    for u in bot_units:
                        u["has_moved"] = False
                    for u in player_units:
                        u["has_moved"] = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                game_mouse_x, game_mouse_y = pygame.mouse.get_pos()
                if interface_btn.collidepoint(game_mouse_x, game_mouse_y) and current_turn == "player":
                    current_turn = "bot"
                    bot_action_index = 0
                    bot_wait_until = pygame.time.get_ticks() + random.randint(500, 1000)
                    for u in bot_units:
                        u["has_moved"] = False
                    for u in player_units:
                        u["has_moved"] = False
                if current_turn == "player":
                    grid_pos = [game_mouse_x // TILE_SIZE, game_mouse_y // TILE_SIZE]
                    clicked_unit = get_unit_at(grid_pos, player_units)
                    if clicked_unit:
                        selected_unit = clicked_unit
                    elif selected_unit and not selected_unit["has_moved"]:
                        dx_move = abs(grid_pos[0] - selected_unit["pos"][0])
                        dy_move = abs(grid_pos[1] - selected_unit["pos"][1])
                        if dx_move <= 1 and dy_move <= 1 and (dx_move + dy_move) != 0:
                            enemy_unit = get_unit_at(grid_pos, bot_units)
                            if enemy_unit:
                                damage = random.randint(1, 4)
                                enemy_unit["hp"] -= damage
                                # 🔧 Добавляем цифру урона
                                damage_numbers.append({
                                    "pos": enemy_unit["pos"],
                                    "value": damage,
                                    "y_offset": enemy_unit["pos"][1] * TILE_SIZE + TILE_SIZE // 2,
                                    "timer": 20
                                })
                                battle_effects.append(
                                    {"pos": enemy_unit["pos"], "color": random.choice(HIT_EFFECT_COLORS), "timer": 10})
                                selected_unit["has_moved"] = True
                                selected_unit = None
                            elif not get_unit_at(grid_pos, player_units) and not get_unit_at(grid_pos, bot_units):
                                selected_unit["move_path"] = [grid_pos]
                                selected_unit["has_moved"] = True
                                selected_unit = None

        player_units = [u for u in player_units if u["hp"] > 0]
        bot_units = [u for u in bot_units if u["hp"] > 0]

        if current_turn == "player":
            game_time = pygame.time.get_ticks()
            if game_time - turn_timer_start >= TURN_TIME:
                current_turn = "bot"
                bot_action_index = 0
                bot_wait_until = pygame.time.get_ticks() + random.randint(200, 500)
                for u in bot_units:
                    u["has_moved"] = False
                for u in player_units:
                    u["has_moved"] = False

        if current_turn == "bot" and not game_over and bot_action_index < len(bot_units):
            game_time = pygame.time.get_ticks()
            if game_time >= bot_wait_until:
                bot_step(bot_units[bot_action_index])
                bot_action_index += 1
                if bot_action_index < len(bot_units):
                    bot_wait_until = game_time + random.randint(400, 800)
                else:
                    current_turn = "player"
                    turn_timer_start = pygame.time.get_ticks()
                    for u in player_units:
                        u["has_moved"] = False

        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    while True:
        main_menu()
        run_game()
