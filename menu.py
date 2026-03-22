import random
import sys
import pygame
import settings
from background import BackgroundManager
from config import set_music_volume, set_background, get_background, set_snow_enabled, get_snow_enabled
from music import play_menu
from settings import (
    WIDTH, HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM,
    MENU_BTN_BLUE, MENU_BTN_BLUE_HOVER, MENU_BTN_RED, MENU_BTN_RED_HOVER,
    UI_TEXT, UI_BG, UI_BORDER, BG_OVERLAY_ALPHA,
    CURRENT_BACKGROUND, CUSTOM_BACKGROUNDS, BACKGROUND_KEYS, GAME_VERSION
)
bg_manager = BackgroundManager()
def settings_menu(screen, clock):
    from settings import font
    running_settings = True
    vol = settings.MUSIC_VOLUME
    saved_bg = get_background()
    bg_index = BACKGROUND_KEYS.index(saved_bg) if saved_bg in BACKGROUND_KEYS else 0
    snow_enabled = get_snow_enabled()
    while running_settings:
        needs_gradient = not bg_manager.draw(screen, WIDTH, HEIGHT)
        if needs_gradient:
            for y in range(HEIGHT):
                ratio = y / HEIGHT
                r = int(MENU_BG_TOP[0] * (1 - ratio) + MENU_BG_BOTTOM[0] * ratio)
                g = int(MENU_BG_TOP[1] * (1 - ratio) + MENU_BG_BOTTOM[1] * ratio)
                b = int(MENU_BG_TOP[2] * (1 - ratio) + MENU_BG_BOTTOM[2] * ratio)
                pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(BG_OVERLAY_ALPHA)
        overlay.fill((10, 12, 20))
        screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 150, 400, 380)
        pygame.draw.rect(screen, UI_BG, panel_rect, border_radius=12)
        pygame.draw.rect(screen, UI_BORDER, panel_rect, 2, border_radius=12)
        if font:
            title = font.render("SETTINGS", True, UI_TEXT)
            screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110)))
            vol_text = font.render(f"Volume: {int(vol * 100)}%", True, UI_TEXT)
            screen.blit(vol_text, vol_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
            bg_name = BACKGROUND_KEYS[bg_index]
            bg_text = font.render(f"BG: {bg_name}", True, UI_TEXT)
            screen.blit(bg_text, bg_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            snow_text = font.render(f"Snow: {'ON' if snow_enabled else 'OFF'}", True, UI_TEXT)
            screen.blit(snow_text, snow_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))
        btn_w, btn_h = 55, 55
        btn_minus = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 80, btn_w, btn_h)
        btn_plus = pygame.Rect(WIDTH // 2 + 90, HEIGHT // 2 - 80, btn_w, btn_h)
        btn_bg_left = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 25, btn_w, btn_h)
        btn_bg_right = pygame.Rect(WIDTH // 2 + 90, HEIGHT // 2 - 25, btn_w, btn_h)
        btn_snow = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 + 60, 160, 50)
        btn_back = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 130, 200, 50)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for btn, text, is_red in [(btn_minus, "-", False), (btn_plus, "+", False),
                                  (btn_bg_left, "◀", False), (btn_bg_right, "▶", False),
                                  (btn_back, "BACK", True)]:
            if is_red:
                color = MENU_BTN_RED_HOVER if btn.collidepoint(mouse_x, mouse_y) else MENU_BTN_RED
            else:
                color = MENU_BTN_BLUE_HOVER if btn.collidepoint(mouse_x, mouse_y) else MENU_BTN_BLUE
            pygame.draw.rect(screen, color, btn, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), btn, 2, border_radius=8)
            if font:
                t_surf = font.render(text, True, UI_TEXT)
                screen.blit(t_surf, t_surf.get_rect(center=btn.center))
        snow_color = MENU_BTN_BLUE_HOVER if btn_snow.collidepoint(mouse_x, mouse_y) else MENU_BTN_BLUE
        pygame.draw.rect(screen, snow_color, btn_snow, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), btn_snow, 2, border_radius=8)
        if font:
            snow_btn_text = font.render(f"{'❄ ON' if snow_enabled else '☀ OFF'}", True, UI_TEXT)
            screen.blit(snow_btn_text, snow_btn_text.get_rect(center=btn_snow.center))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_minus.collidepoint(mouse_x, mouse_y):
                    vol = max(0.0, vol - 0.1)
                    settings.MUSIC_VOLUME = vol
                    pygame.mixer.music.set_volume(vol)
                    set_music_volume(vol)
                elif btn_plus.collidepoint(mouse_x, mouse_y):
                    vol = min(1.0, vol + 0.1)
                    settings.MUSIC_VOLUME = vol
                    pygame.mixer.music.set_volume(vol)
                    set_music_volume(vol)
                elif btn_bg_left.collidepoint(mouse_x, mouse_y):
                    bg_index = (bg_index - 1) % len(BACKGROUND_KEYS)
                    new_bg_key = BACKGROUND_KEYS[bg_index]
                    set_background(new_bg_key)
                    settings.CURRENT_BACKGROUND = new_bg_key
                    bg_manager.load_background(new_bg_key, CUSTOM_BACKGROUNDS)
                elif btn_bg_right.collidepoint(mouse_x, mouse_y):
                    bg_index = (bg_index + 1) % len(BACKGROUND_KEYS)
                    new_bg_key = BACKGROUND_KEYS[bg_index]
                    set_background(new_bg_key)
                    settings.CURRENT_BACKGROUND = new_bg_key
                    bg_manager.load_background(new_bg_key, CUSTOM_BACKGROUNDS)
                elif btn_snow.collidepoint(mouse_x, mouse_y):
                    snow_enabled = not snow_enabled
                    set_snow_enabled(snow_enabled)
                    settings.SNOW_ENABLED = snow_enabled
                elif btn_back.collidepoint(mouse_x, mouse_y):
                    running_settings = False
        pygame.display.update()
        clock.tick(60)
def main_menu(screen, clock):
    from settings import font, big_font, small_font
    bg_manager.load_background(CURRENT_BACKGROUND, CUSTOM_BACKGROUNDS)
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
        bg_manager.draw(screen, WIDTH, HEIGHT)
        if settings.SNOW_ENABLED:
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
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(BG_OVERLAY_ALPHA)
        overlay.fill((10, 12, 20))
        screen.blit(overlay, (0, 0))
        if big_font:
            title_shadow = big_font.render("MiniPRZ", True, (0, 0, 0))
            shadow_x = WIDTH // 2 - title_shadow.get_width() // 2 + 3
            shadow_y = 103
            screen.blit(title_shadow, (shadow_x, shadow_y))
            title_text = big_font.render("MiniPRZ", True, (255, 214, 107))
            title_x = WIDTH // 2 - title_text.get_width() // 2
            title_y = 100
            screen.blit(title_text, (title_x, title_y))
        if small_font:
            version_text = small_font.render(f"v{GAME_VERSION}", True, UI_TEXT)
            screen.blit(version_text, (WIDTH - version_text.get_width() - 10, HEIGHT - 30))
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
            if font:
                text_surface = font.render(text, True, UI_TEXT)
                screen.blit(text_surface, text_surface.get_rect(center=btn_rect.center))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                bg_manager.cleanup()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn_rect, action in buttons_rects:
                    if btn_rect.collidepoint(mouse_x, mouse_y):
                        if action == "play":
                            bg_manager.cleanup()
                            return True
                        elif action == "settings":
                            settings_menu(screen, clock)
                        elif action == "exit":
                            bg_manager.cleanup()
                            pygame.quit()
                            sys.exit()
            if event.type == pygame.MOUSEMOTION:
                if any(btn_rect.collidepoint(mouse_x, mouse_y) for btn_rect, _ in buttons_rects):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        pygame.display.update()
        clock.tick(60)
    bg_manager.cleanup()
    return False