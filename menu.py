import pygame
import random
import sys
import settings
from settings import (
    WIDTH, HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM,
    MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER, MENU_BTN_RED, MENU_BTN_RED_HOVER,
    UI_TEXT, UI_BG, UI_BORDER
)
from music import play_menu


def settings_menu(screen, clock):
    from settings import font
    running_settings = True
    vol = settings.MUSIC_VOLUME

    while running_settings:
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(MENU_BG_TOP[0] * (1 - ratio) + MENU_BG_BOTTOM[0] * ratio)
            g = int(MENU_BG_TOP[1] * (1 - ratio) + MENU_BG_BOTTOM[1] * ratio)
            b = int(MENU_BG_TOP[2] * (1 - ratio) + MENU_BG_BOTTOM[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((10, 12, 20))
        screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 150, 400, 300)
        pygame.draw.rect(screen, UI_BG, panel_rect, border_radius=12)
        pygame.draw.rect(screen, UI_BORDER, panel_rect, 2, border_radius=12)

        if font:
            title = font.render("SETTINGS", True, UI_TEXT)
            screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
            vol_text = font.render(f"Volume: {int(vol * 100)}%", True, UI_TEXT)
            screen.blit(vol_text, vol_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

        btn_w, btn_h = 60, 60
        btn_minus = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 20, btn_w, btn_h)
        btn_plus = pygame.Rect(WIDTH // 2 + 90, HEIGHT // 2 + 20, btn_w, btn_h)
        btn_back = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50)

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for btn, text in [(btn_minus, "-"), (btn_plus, "+"), (btn_back, "BACK")]:
            color = MENU_BTN_BLUE_HOVER if btn.collidepoint(mouse_x, mouse_y) else MENU_BTN_BLUE
            if btn == btn_back:
                color = MENU_BTN_RED_HOVER if btn.collidepoint(mouse_x, mouse_y) else MENU_BTN_RED
            pygame.draw.rect(screen, color, btn, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), btn, 2, border_radius=8)
            if font:
                t_surf = font.render(text, True, UI_TEXT)
                screen.blit(t_surf, t_surf.get_rect(center=btn.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_minus.collidepoint(mouse_x, mouse_y):
                    vol = max(0.0, vol - 0.1)
                    settings.MUSIC_VOLUME = vol
                    pygame.mixer.music.set_volume(vol)
                elif btn_plus.collidepoint(mouse_x, mouse_y):
                    vol = min(1.0, vol + 0.1)
                    settings.MUSIC_VOLUME = vol
                    pygame.mixer.music.set_volume(vol)
                elif btn_back.collidepoint(mouse_x, mouse_y):
                    running_settings = False

        pygame.display.update()
        clock.tick(60)


def main_menu(screen, clock):
    from settings import font
    play_menu()
    running_menu = True
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
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(MENU_BG_TOP[0] * (1 - ratio) + MENU_BG_BOTTOM[0] * ratio)
            g = int(MENU_BG_TOP[1] * (1 - ratio) + MENU_BG_BOTTOM[1] * ratio)
            b = int(MENU_BG_TOP[2] * (1 - ratio) + MENU_BG_BOTTOM[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn_rect, action in buttons_rects:
                    if btn_rect.collidepoint(mouse_x, mouse_y):
                        if action == "play":
                            return True
                        elif action == "settings":
                            settings_menu(screen, clock)
                        elif action == "exit":
                            pygame.quit()
                            sys.exit()
            if event.type == pygame.MOUSEMOTION:
                if any(btn_rect.collidepoint(mouse_x, mouse_y) for btn_rect, _ in buttons_rects):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        clock.tick(60)

    return False