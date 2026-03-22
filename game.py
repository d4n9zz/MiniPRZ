import pygame
import random
from settings import (
    WIDTH, HEIGHT, TILE_SIZE, FIELD_HEIGHT, VISIBILITY_RADIUS,
    TURN_TIME, BG_TOP, BG_BOTTOM, GRID_COLOR, GRID_BORDER,
    FOG_UNEXPLORED, FOG_EXPLORED_NO_VIS, PLAYER_HIGHLIGHT,
    COLS, ROWS, BOT_GLOW
)
from entities import create_units, bot_step
from effects import DamageNumber, BattleEffect, DeathEffect
from ui import draw_interface
from music import play_game
class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        play_game()
        self._reset_game()
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
    def _draw_background(self):
        for y in range(FIELD_HEIGHT):
            ratio = y / FIELD_HEIGHT
            r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
            g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
            b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
    def _draw_grid(self):
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, GRID_COLOR, rect)
                pygame.draw.rect(self.screen, GRID_BORDER, rect, 1)
    def _draw_fog_of_war(self, visible):
        for y in range(ROWS):
            for x in range(COLS):
                tile_pos = (x, y)
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile_pos not in self.explored_tiles:
                    fog_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    fog_overlay.fill(FOG_UNEXPLORED)
                    self.screen.blit(fog_overlay, tile_rect.topleft)
                elif tile_pos not in visible:
                    fog_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    fog_overlay.fill(FOG_EXPLORED_NO_VIS)
                    self.screen.blit(fog_overlay, tile_rect.topleft)
    def _draw_units(self, visible):
        from settings import player_unit_imgs, bot_unit_imgs
        for unit in self.player_units + self.bot_units:
            if tuple(unit.pos) not in visible and not unit.is_player:
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
    def _handle_input(self, interface_btn):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self._reset_game()
                    elif self.current_turn == "player":
                        self._end_player_turn()
                if self.current_turn == "player" and not self.game_over:
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
            if pygame.time.get_ticks() - self.turn_timer_start >= TURN_TIME:
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
    def run(self):
        running = True
        while running:
            visible = self._get_visible_tiles()
            self.explored_tiles.update(visible)
            self._draw_background()
            self._draw_grid()
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
                self.bot_units, self.turn_timer_start, TURN_TIME, self.selected_unit
            )
            if self.game_over:
                self._draw_game_over()
            running = self._handle_input(interface_btn)
            self._update_game()
            pygame.display.update()
            self.clock.tick(60)