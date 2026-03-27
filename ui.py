import pygame
from settings import (
    UI_BG, UI_BORDER, UI_TEXT, UI_BUTTON_NORMAL,
    UI_BUTTON_HOVER, UI_BUTTON_SHADOW, TIMER_SAFE, TIMER_WARNING, TIMER_DANGER,
    FIELD_HEIGHT, WIDTH, INTERFACE_HEIGHT, MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER,
    DEBUG_BTN_OFF, DEBUG_BTN_ON, DEBUG_TEXT_COLOR, DEBUG_BG_COLOR
)


def draw_top_interface(screen, stars, stars_change):
    from settings import small_font, font, WIDTH

    stars_text = f"Stars (+{stars_change})"
    stars_label = small_font.render(stars_text, True, (240, 248, 255))
    stars_value = font.render(str(stars), True, (255, 215, 0))

    label_width = stars_label.get_width()
    value_width = stars_value.get_width()

    padding = 20
    panel_height = 70
    max_width = max(label_width, value_width)
    panel_width = max_width + padding * 2

    panel_x = WIDTH // 2 - panel_width // 2
    panel_y = 10

    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, (20, 25, 45), panel_rect, border_radius=12)
    pygame.draw.rect(screen, (100, 149, 237), panel_rect, 2, border_radius=12)

    label_x = WIDTH // 2 - label_width // 2
    value_x = WIDTH // 2 - value_width // 2

    screen.blit(stars_label, (label_x, panel_y + 10))
    screen.blit(stars_value, (value_x, panel_y + 32))


def draw_menu_button(screen):
    from settings import small_font
    text_surf = small_font.render("PAUSE", True, UI_TEXT) if small_font else None
    padding = 10
    if text_surf:
        btn_w = text_surf.get_width() + padding * 2
        btn_h = text_surf.get_height() + padding * 2
    else:
        btn_w = 50
        btn_h = 50
    btn_rect = pygame.Rect(10, 10, btn_w, btn_h)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    color = UI_BUTTON_HOVER if btn_rect.collidepoint(mouse_x, mouse_y) else UI_BUTTON_NORMAL
    pygame.draw.rect(screen, UI_BUTTON_SHADOW, btn_rect.move(2, 2), border_radius=8)
    pygame.draw.rect(screen, color, btn_rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), btn_rect, 1, border_radius=8)
    if text_surf:
        screen.blit(text_surf, text_surf.get_rect(center=btn_rect.center))
    return btn_rect


def draw_debug_button(screen, is_active, menu_btn_rect=None):
    from settings import small_font
    text_surf = small_font.render("DBG", True, UI_TEXT) if small_font else None
    padding = 8
    if text_surf:
        btn_w = text_surf.get_width() + padding * 2
        btn_h = text_surf.get_height() + padding * 2
    else:
        btn_w = 40
        btn_h = 40

    if menu_btn_rect:
        btn_x = menu_btn_rect.x
        btn_y = menu_btn_rect.bottom + 10
    else:
        btn_x = WIDTH - btn_w - 10
        btn_y = 10

    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    base_color = DEBUG_BTN_ON if is_active else DEBUG_BTN_OFF
    color = UI_BUTTON_HOVER if btn_rect.collidepoint(mouse_x, mouse_y) else base_color
    pygame.draw.rect(screen, UI_BUTTON_SHADOW, btn_rect.move(2, 2), border_radius=8)
    pygame.draw.rect(screen, color, btn_rect, border_radius=8)
    border_col = (255, 255, 255) if is_active else (150, 150, 150)
    pygame.draw.rect(screen, border_col, btn_rect, 2, border_radius=8)
    if text_surf:
        screen.blit(text_surf, text_surf.get_rect(center=btn_rect.center))
    return btn_rect


def draw_pause_menu(screen, resume_btn, menu_btn):
    from settings import font, big_font
    overlay = pygame.Surface((WIDTH, FIELD_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((15, 20, 35))
    screen.blit(overlay, (0, 0))
    panel_rect = pygame.Rect(WIDTH // 2 - 150, FIELD_HEIGHT // 2 - 100, 300, 200)
    pygame.draw.rect(screen, UI_BG, panel_rect, border_radius=12)
    pygame.draw.rect(screen, UI_BORDER, panel_rect, 3, border_radius=12)
    if big_font:
        title = big_font.render("PAUSED", True, UI_TEXT)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, FIELD_HEIGHT // 2 - 50)))
    mouse_x, mouse_y = pygame.mouse.get_pos()
    for btn, text, color, hover_color in [(resume_btn, "RESUME", MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER),
                                          (menu_btn, "MAIN MENU", MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER)]:
        current_color = hover_color if btn.collidepoint(mouse_x, mouse_y) else color
        pygame.draw.rect(screen, UI_BUTTON_SHADOW, btn.move(3, 3), border_radius=10)
        pygame.draw.rect(screen, current_color, btn, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), btn, 2, border_radius=10)
        if font:
            text_surf = font.render(text, True, UI_TEXT)
            screen.blit(text_surf, text_surf.get_rect(center=btn.center))
    return resume_btn, menu_btn


def draw_unit_card(screen, card_x, card_y, unit):
    from settings import card_font
    card_width, card_height = 70, 60
    card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
    pygame.draw.rect(screen, UI_BG, card_rect, border_radius=8)
    pygame.draw.rect(screen, unit.color, card_rect, 2, border_radius=8)
    pygame.draw.line(screen, unit.color,
                     (card_x + 10, card_y + 30),
                     (card_x + card_width - 10, card_y + 30), 2)
    if card_font:
        type_text = card_font.render(unit.name, True, unit.color)
        screen.blit(type_text, type_text.get_rect(
            center=(card_x + card_width // 2, card_y + 16)))
        hp_text = card_font.render(f"HP {unit.hp}", True, UI_TEXT)
        screen.blit(hp_text, hp_text.get_rect(
            center=(card_x + card_width // 2, card_y + 44)))


def draw_interface(screen, current_turn, player_units, bot_units, bot2_units,
                   turn_timer_start, turn_time, selected_unit,
                   paused, pause_start_time, total_paused_time):
    from settings import font, small_font
    panel_rect = pygame.Rect(0, FIELD_HEIGHT, WIDTH, INTERFACE_HEIGHT)
    pygame.draw.rect(screen, UI_BG, panel_rect)
    pygame.draw.rect(screen, UI_BORDER, panel_rect, 3)
    if font:
        turn_text = font.render(f"Turn: {current_turn.upper()}", True, UI_TEXT)
        screen.blit(turn_text, (25, FIELD_HEIGHT + 22))
    btn_rect = pygame.Rect(WIDTH - 170, FIELD_HEIGHT + 12, 150, 56)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    btn_color = UI_BUTTON_HOVER if btn_rect.collidepoint(mouse_x, mouse_y) else UI_BUTTON_NORMAL
    pygame.draw.rect(screen, UI_BUTTON_SHADOW, btn_rect.move(4, 4), border_radius=12)
    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=12)
    pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=12)
    if font:
        button_text = font.render("END TURN", True, UI_TEXT)
        screen.blit(button_text, button_text.get_rect(center=btn_rect.center))
    for i, unit in enumerate(player_units):
        draw_unit_card(screen, 280 + i * 80, FIELD_HEIGHT + 10, unit)
    for i, unit in enumerate(bot_units):
        draw_unit_card(screen, WIDTH - 420 + i * 80, FIELD_HEIGHT + 10, unit)
    for i, unit in enumerate(bot2_units):
        draw_unit_card(screen, WIDTH - 500 + i * 80, FIELD_HEIGHT + 10, unit)
    if selected_unit:
        info_x = WIDTH // 2
        info_y = FIELD_HEIGHT + 20
        if font:
            sel_text = font.render(f"SELECTED: {selected_unit.name}", True, selected_unit.color)
            screen.blit(sel_text, sel_text.get_rect(center=(info_x, info_y)))
            hp_text = font.render(f"HP: {selected_unit.hp}/{selected_unit.max_hp}", True, UI_TEXT)
            screen.blit(hp_text, hp_text.get_rect(center=(info_x, info_y + 30)))
    if current_turn == "player":
        _draw_timer(screen, turn_timer_start, turn_time, small_font,
                    paused, pause_start_time, total_paused_time)
    return btn_rect


def _draw_timer(screen, turn_timer_start, turn_time, small_font,
                paused, pause_start_time, total_paused_time):
    interface_time = pygame.time.get_ticks()
    if paused:
        paused_duration = interface_time - pause_start_time
        total_pause = total_paused_time + paused_duration
    else:
        total_pause = total_paused_time
    effective_time = interface_time - turn_timer_start - total_pause
    remaining = max(0, turn_time - effective_time)
    ratio = remaining / turn_time if turn_time > 0 else 0
    bar_w, bar_h, padding = 130, 16, 15
    bar_x, bar_y = WIDTH - padding - bar_w, padding
    pygame.draw.rect(screen, (10, 12, 20),
                     (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), border_radius=10)
    pygame.draw.rect(screen, (50, 55, 75),
                     (bar_x, bar_y, bar_w, bar_h), border_radius=8)
    fill_col = TIMER_DANGER if remaining <= 5000 else TIMER_WARNING if remaining <= 10000 else TIMER_SAFE
    pygame.draw.rect(screen, fill_col,
                     (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=8)
    if small_font:
        secs = int((remaining + 999) / 1000)
        time_text = small_font.render(f"{secs}s", True, UI_TEXT)
        bg_surf = pygame.Surface((time_text.get_width() + 12, time_text.get_height() + 6), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        time_y = bar_y + bar_h // 2 - time_text.get_height() // 2
        screen.blit(bg_surf, (bar_x - time_text.get_width() - 20, time_y))
        screen.blit(time_text, (bar_x - time_text.get_width() - 16, time_y))


def draw_debug_overlay(screen, clock, visible_tiles, player_units, bot_units):
    from settings import small_font, TILE_SIZE, COLS, ROWS
    if not small_font:
        return
    fps = int(clock.get_fps())
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x = mouse_x // TILE_SIZE
    grid_y = mouse_y // TILE_SIZE
    info_lines = [
        f"FPS: {fps}",
        f"Mouse: {mouse_x}, {mouse_y}",
        f"Grid: {grid_x}, {grid_y}",
        f"Visible Tiles: {len(visible_tiles)}",
        f"Player Units: {len(player_units)}",
        f"Bot Units: {len(bot_units)}"
    ]
    y_offset = 10
    for line in info_lines:
        text_surf = small_font.render(line, True, DEBUG_TEXT_COLOR)
        bg_surf = pygame.Surface((text_surf.get_width() + 4, text_surf.get_height() + 4), pygame.SRCALPHA)
        bg_surf.fill(DEBUG_BG_COLOR)
        screen.blit(bg_surf, (10, y_offset))
        screen.blit(text_surf, (12, y_offset + 2))
        y_offset += text_surf.get_height() + 4
    if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
        from utils import get_unit_at
        unit = get_unit_at([grid_x, grid_y], player_units + bot_units)
        if unit:
            unit_info = [
                f"Unit: {unit.name}",
                f"HP: {unit.hp}/{unit.max_hp}",
                f"Type: {unit.unit_type}",
                f"Owner: {'Player' if unit.is_player else 'Bot'}"
            ]
            box_h = len(unit_info) * (small_font.get_height() + 4) + 8
            box_w = 150
            box_x = mouse_x + 10
            box_y = mouse_y + 10
            if box_x + box_w > WIDTH:
                box_x = mouse_x - box_w - 10
            if box_y + box_h > FIELD_HEIGHT:
                box_y = mouse_y - box_h - 10
            panel_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            panel_surf.fill((0, 0, 0, 200))
            screen.blit(panel_surf, (box_x, box_y))
            pygame.draw.rect(screen, DEBUG_TEXT_COLOR, (box_x, box_y, box_w, box_h), 1)
            for i, line in enumerate(unit_info):
                text_surf = small_font.render(line, True, DEBUG_TEXT_COLOR)
                screen.blit(text_surf, (box_x + 4, box_y + 4 + i * (small_font.get_height() + 4)))