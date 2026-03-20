import pygame
import random
import sys
from settings import (
    WIDTH, HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM,
    MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER, MENU_BTN_RED, MENU_BTN_RED_HOVER,
    UI_TEXT
)


def main_menu(screen, clock):
    """Главное меню игры"""
    from settings import font

    running_menu = True

    # Снежинки для анимации
    snowflakes = []
    for _ in range(100):
        snowflakes.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'size': random.randint(2, 5),
            'speed': random.uniform(0.5, 2.0),
            'wind': random.uniform(-0.3, 0.3)
        })

    while running_menu:
        # Градиентный фон
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(MENU_BG_TOP[0] * (1 - ratio) + MENU_BG_BOTTOM[0] * ratio)
            g = int(MENU_BG_TOP[1] * (1 - ratio) + MENU_BG_BOTTOM[1] * ratio)
            b = int(MENU_BG_TOP[2] * (1 - ratio) + MENU_BG_BOTTOM[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # Анимация снежинок
        for flake in snowflakes:
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(flake['x']), int(flake['y'])), flake['size'])
            flake['y'] += flake['speed']
            flake['x'] += flake['wind']
            if flake['y'] > HEIGHT:
                flake['y'] = -5
                flake['x'] = random.randint(0, WIDTH)
            if flake['x'] > WIDTH:
                flake['x'] = 0
            elif flake['x'] < 0:
                flake['x'] = WIDTH

        # Кнопки
        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_width, button_height = 260, 60

        buttons_config = [
            (WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height, "▶ PLAY",
             MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER, "play"),
            (WIDTH // 2 - button_width // 2, HEIGHT // 2, "⚙ SETTINGS",
             MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER, "settings"),
            (WIDTH // 2 - button_width // 2, HEIGHT // 2 + button_height, "✕ EXIT",
             MENU_BTN_RED, MENU_BTN_RED_HOVER, "exit"),
        ]

        buttons_rects = []
        for x, y, text, color, hover_color, action in buttons_config:
            btn_rect = pygame.Rect(x, y, button_width, button_height)
            buttons_rects.append((btn_rect, action))

            current_color = hover_color if btn_rect.collidepoint(mouse_x, mouse_y) else color
            pygame.draw.rect(screen, (10, 12, 20), btn_rect.move(4, 4), border_radius=12)
            pygame.draw.rect(screen, current_color, btn_rect, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=12)

            text_surface = font.render(text, True, UI_TEXT)
            screen.blit(text_surface, text_surface.get_rect(center=btn_rect.center))

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn_rect, action in buttons_rects:
                    if btn_rect.collidepoint(mouse_x, mouse_y):
                        if action == "play":
                            return True  # Запуск игры
                        elif action == "exit":
                            pygame.quit()
                            sys.exit()
            if event.type == pygame.MOUSEMOTION:
                if any(btn.collidepoint(mouse_x, mouse_y) for btn, _ in buttons_rects):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        clock.tick(60)

    return False