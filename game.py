import pygame
import random
from settings import (
    WIDTH, HEIGHT, TILE_SIZE, FIELD_HEIGHT, VISIBILITY_RADIUS,
    TURN_TIME, BG_TOP, BG_BOTTOM, GRID_COLOR, GRID_BORDER,
    FOG_UNEXPLORED, FOG_EXPLORED_NO_VIS, PLAYER_HIGHLIGHT,
    COLS, ROWS, BOT_GLOW, DEBUG_TOGGLE_KEY, DEBUG_FOG_KEY,
    DEBUG_HEAL_KEY, DEBUG_INSTANT_WIN_KEY, DEBUG_SKIP_TURN_KEY
)
from entities import create_units, bot_step
from effects import DamageNumber, BattleEffect, DeathEffect
from ui import draw_interface, draw_menu_button, draw_pause_menu, draw_debug_button, draw_debug_overlay
from music import play_game, fade_music_volume


class Game:
    __slots__ = [
        'screen', 'clock', 'player_units', 'bot_units', 'selected_unit',
        'current_turn', 'game_over', 'winner', 'explored_tiles',
        'turn_timer_start', 'damage_numbers', 'battle_effects',
        'death_effects', 'bot_action_index', 'bot_wait_until',
        'return_to_menu', 'paused', 'pause_resume_btn', 'pause_menu_btn',
        'total_paused_time', 'pause_start_time', 'music_fade_target',
        'music_fade_current', 'music_fade_speed', 'fog_unexplored_surf',
        'fog_explored_surf', 'debug_mode', 'debug_fog_override',
        'debug_btn_rect', 'bg_surface', 'grid_surface'
    ]

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        play_game()
        self._create_static_surfaces()
        self._reset_game()

    def _create_static_surfaces(self):
        self.grid_surface = pygame.Surface((WIDTH, FIELD_HEIGHT), pygame.SRCALPHA)
        self._draw_grid_static()
        self.bg_surface = pygame.Surface((WIDTH, FIELD_HEIGHT))
        self._draw_background_static()

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
        self.player_units = create_units(2, [], is_player=True)
        self.bot_units = create_units(2, self.player_units, is_player=False)
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
        self.return_to_menu = False
        self.paused = False
        self.pause_resume_btn = None
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
        self.debug_btn_rect = None

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
            self.music_fade_current = min(self.music_fade_target, self.music_fade_current + self.music_fade_speed)
        elif self.music_fade_current > self.music_fade_target:
            self.music_fade_current = max(self.music_fade_target, self.music_fade_current - self.music_fade_speed)
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
        return visible

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
        for unit in self.player_units + self.bot_units:
            if tuple(unit.pos) not in visible and not unit.is_player and not self.debug_fog_override:
                continue
            unit_img_dict = player_unit_imgs if unit.is_player else bot_unit_imgs
            unit_img = unit_img_dict.get(unit.unit_type)
            if unit_img:
                img_rect = unit_img.get_rect(center=(int(unit.px), int(unit.py)))
                self.screen.blit(unit_img, img_rect)
            else:
                glow = PLAYER_HIGHLIGHT if unit.is_player else BOT_GLOW
                pygame.draw.circle(self.screen, glow, (int(unit.px), int(unit.py)), TILE_SIZE // 3 + 10)
                pygame.draw.circle(self.screen, unit.color, (int(unit.px), int(unit.py)), TILE_SIZE // 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(unit.px), int(unit.py)), TILE_SIZE // 3, 2)
            if unit == self.selected_unit:
                for i in range(3):
                    alpha = 200 - i * 50
                    highlight_surf = pygame.Surface((TILE_SIZE + 20, TILE_SIZE + 20), pygame.SRCALPHA)
                    pygame.draw.circle(highlight_surf, (*PLAYER_HIGHLIGHT, alpha),
                                       (TILE_SIZE // 2 + 10, TILE_SIZE // 2 + 10),
                                       TILE_SIZE // 3 + 12 + i * 4, 3)
                    self.screen.blit(highlight_surf,
                                     (unit.px - TILE_SIZE // 2 - 10, unit.py - TILE_SIZE // 2 - 10))

    def _handle_input(self, interface_btn, menu_btn_rect, debug_btn_rect):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._set_pause_state(not self.paused)
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self._reset_game()
                    elif self.current_turn == "player" and not self.paused:
                        self._end_player_turn()
                if event.key == DEBUG_TOGGLE_KEY:
                    self.debug_mode = not self.debug_mode
                if event.key == DEBUG_FOG_KEY:
                    self.debug_fog_override = not self.debug_fog_override
                if event.key == DEBUG_HEAL_KEY and self.current_turn == "player":
                    for u in self.player_units:
                        u.hp = u.max_hp
                if event.key == DEBUG_INSTANT_WIN_KEY:
                    self.bot_units = []
                    self.game_over = True
                    self.winner = "🏆 DEBUG WIN"
                if event.key == DEBUG_SKIP_TURN_KEY and self.current_turn == "player":
                    self._end_player_turn()
                if self.current_turn == "player" and not self.game_over and not self.paused:
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
                if debug_btn_rect.collidepoint(mouse_x, mouse_y):
                    self.debug_mode = not self.debug_mode
                    continue
                if menu_btn_rect.collidepoint(mouse_x, mouse_y):
                    self._set_pause_state(True)
                    continue
                if self.paused:
                    if self.pause_resume_btn and self.pause_resume_btn.collidepoint(mouse_x, mouse_y):
                        self._set_pause_state(False)
                    elif self.pause_menu_btn and self.pause_menu_btn.collidepoint(mouse_x, mouse_y):
                        self.return_to_menu = True
                        return False
                    continue
                if interface_btn.collidepoint(mouse_x, mouse_y) and self.current_turn == "player":
                    self._end_player_turn()
                    continue
                if self.current_turn == "player":
                    self._handle_field_click(mouse_x, mouse_y)
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
                enemy_unit = get_unit_at(grid_pos, self.bot_units)
                if enemy_unit:
                    self._perform_attack(self.selected_unit, enemy_unit)
                elif not get_unit_at(grid_pos, self.player_units) and not get_unit_at(grid_pos, self.bot_units):
                    self.selected_unit.move_path = [grid_pos]
                    self.selected_unit.has_moved = True
                    self.selected_unit = None

    def _perform_attack(self, attacker, defender):
        attack_damage = attacker.get_attack_damage()
        defender.hp -= attack_damage
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
        for u in self.player_units:
            u.has_moved = False

    def _update_game(self):
        if self.paused:
            return
        for unit in self.player_units + self.bot_units:
            unit.update_animation()
        self.damage_numbers = [d for d in self.damage_numbers if d.update()]
        self.battle_effects = [e for e in self.battle_effects if e.update()]
        self.death_effects = [e for e in self.death_effects if e.update()]
        if not self.game_over:
            if not self.bot_units:
                self.game_over = True
                self.winner = "🏆 YOU WIN! 🏆"
            elif not self.player_units:
                self.game_over = True
                self.winner = "💀 YOU LOSE 💀"
        if self.current_turn == "player" and not self.game_over:
            elapsed = pygame.time.get_ticks() - self.turn_timer_start - self.total_paused_time
            if elapsed >= TURN_TIME:
                self._end_player_turn()
        if self.current_turn == "bot" and not self.game_over:
            if pygame.time.get_ticks() >= self.bot_wait_until and self.bot_action_index < len(self.bot_units):
                bot_step(
                    self.bot_units[self.bot_action_index],
                    self.player_units,
                    self.bot_units,
                    lambda pos, dmg: self.damage_numbers.append(DamageNumber(pos, dmg)),
                    lambda pos: self.battle_effects.append(BattleEffect(pos)),
                    lambda pos: self.death_effects.append(DeathEffect(pos))
                )
                self.bot_action_index += 1
                if self.bot_action_index < len(self.bot_units):
                    self.bot_wait_until = pygame.time.get_ticks() + random.randint(400, 800)
                else:
                    self.current_turn = "player"
                    self.turn_timer_start = pygame.time.get_ticks()
                    self.total_paused_time = 0
                    for u in self.player_units:
                        u.has_moved = False
        self.player_units = [u for u in self.player_units if u.is_alive()]
        self.bot_units = [u for u in self.bot_units if u.is_alive()]

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
        resume_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2, 240, 50)
        menu_btn = pygame.Rect(WIDTH // 2 - 120, FIELD_HEIGHT // 2 + 60, 240, 50)
        self.pause_resume_btn = resume_btn
        self.pause_menu_btn = menu_btn
        draw_pause_menu(self.screen, resume_btn, menu_btn)

    def run(self):
        running = True
        while running:
            visible = self._get_visible_tiles()
            self.explored_tiles.update(visible)
            self.screen.blit(self.bg_surface, (0, 0))
            self.screen.blit(self.grid_surface, (0, 0))
            self._draw_units(visible)
            for dmg in self.damage_numbers:
                dmg.draw(self.screen, visible)
            for effect in self.battle_effects:
                effect.draw(self.screen, visible)
            for effect in self.death_effects:
                effect.draw(self.screen, visible)
            self._draw_fog_of_war(visible)
            interface_btn = draw_interface(
                self.screen, self.current_turn, self.player_units,
                self.bot_units, self.turn_timer_start, TURN_TIME, self.selected_unit,
                self.paused, self.pause_start_time, self.total_paused_time
            )
            menu_btn_rect = draw_menu_button(self.screen)
            debug_btn_rect = draw_debug_button(self.screen, self.debug_mode, menu_btn_rect)
            if self.paused:
                self._draw_pause_menu()
            if self.game_over:
                self._draw_game_over()
            if self.debug_mode:
                draw_debug_overlay(self.screen, self.clock, visible, self.player_units, self.bot_units)
            running = self._handle_input(interface_btn, menu_btn_rect, debug_btn_rect)
            self._update_game()
            self._update_music_fade()
            pygame.display.update()
            self.clock.tick(60)
        return self.return_to_menu