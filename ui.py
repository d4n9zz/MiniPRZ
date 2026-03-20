import pygame
from settings import (
    UI_BG, UI_BORDER, UI_TEXT, UI_BUTTON_NORMAL,
    UI_BUTTON_HOVER, UI_BUTTON_SHADOW, PLAYER_COLOR,
    BOT_COLOR, TIMER_SAFE, TIMER_WARNING, TIMER_DANGER,
    FIELD_HEIGHT, WIDTH, INTERFACE_HEIGHT
)

def draw_unit_card(screen, card_x, card_y, unit_color, hp_value):
    from settings import card_font
    card_width, card_height = 70, 60
    card_rect = pygame.Rect(card_x, card_y, card_width, card_height)

    pygame.draw.rect(screen, UI_BG, card_rect, border_radius=8)
    pygame.draw.rect(screen, unit_color, card_rect, 2, border_radius=8)
    pygame.draw.line(screen, unit_color,
                     (card_x + 10, card_y + 30),
                     (card_x + card_width - 10, card_y + 30), 2)

    if card_font:
        pawn_text = card_font.render("PAWN", True, unit_color)
        screen.blit(pawn_text, pawn_text.get_rect(
            center=(card_x + card_width // 2, card_y + 16)))

        hp_text = card_font.render(f"HP {hp_value}", True, UI_TEXT)
        screen.blit(hp_text, hp_text.get_rect(
            center=(card_x + card_width // 2, card_y + 44)))

def draw_interface(screen, current_turn, player_units, bot_units,
                   turn_timer_start, turn_time):
    from settings import font, small_font
    panel_rect = pygame.Rect(0, FIELD_HEIGHT, WIDTH, INTERFACE_HEIGHT)
    pygame.draw.rect(screen, UI_BG, panel_rect)
    pygame.draw.rect(screen, UI_BORDER, panel_rect, 3)

    if font:
        turn_text = font.render(f"✦ Turn: {current_turn.upper()} ✦", True, UI_TEXT)
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
        draw_unit_card(screen, 280 + i * 80, FIELD_HEIGHT + 10,
                       PLAYER_COLOR, unit.hp)

    for i, unit in enumerate(bot_units):
        draw_unit_card(screen, WIDTH - 340 + i * 80, FIELD_HEIGHT + 10,
                       BOT_COLOR, unit.hp)

    if current_turn == "player":
        _draw_timer(screen, turn_timer_start, turn_time, small_font)

    return btn_rect

def _draw_timer(screen, turn_timer_start, turn_time, small_font):
    interface_time = pygame.time.get_ticks()
    remaining = max(0, turn_time - (interface_time - turn_timer_start))
    ratio = remaining / turn_time
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
        time_text = small_font.render(f"⏱ {secs}s", True, UI_TEXT)
        bg_surf = pygame.Surface((time_text.get_width() + 12, time_text.get_height() + 6), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        time_y = bar_y + bar_h // 2 - time_text.get_height() // 2
        screen.blit(bg_surf, (bar_x - time_text.get_width() - 20, time_y))
        screen.blit(time_text, (bar_x - time_text.get_width() - 16, time_y))