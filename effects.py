import pygame
import math
import random
from settings import TILE_SIZE, HIT_EFFECT_COLORS, DEATH_EFFECT_COLORS


class DamageNumber:
    def __init__(self, pos, value):
        self.pos = pos
        self.value = value
        self.y_offset = pos[1] * TILE_SIZE + TILE_SIZE // 2
        self.timer = 20

    def update(self):
        self.y_offset -= 1.5
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, visible_tiles):
        from settings import damage_font
        if tuple(self.pos) not in visible_tiles or not damage_font:
            return
        px = self.pos[0] * TILE_SIZE + TILE_SIZE // 2
        py = self.y_offset
        if self.value >= 4:
            color = (255, 69, 0)
        elif self.value >= 3:
            color = (255, 140, 0)
        else:
            color = (255, 255, 255)
        alpha = min(255, self.timer * 15)
        damage_surf = pygame.Surface((60, 40), pygame.SRCALPHA)
        damage_text = damage_font.render(f"-{self.value}", True, color)
        damage_shadow = damage_font.render(f"-{self.value}", True, (0, 0, 0))
        damage_surf.blit(damage_shadow, (2, 2))
        damage_surf.blit(damage_text, (0, 0))
        damage_surf.set_alpha(alpha)
        screen.blit(damage_surf, (px - 30, py - 20))


class BattleEffect:
    def __init__(self, pos):
        self.pos = pos
        self.timer = 10
        self.color_index = 0

    def update(self):
        self.timer -= 1
        self.color_index = (self.color_index + 1) % len(HIT_EFFECT_COLORS)
        return self.timer > 0

    def draw(self, screen, visible_tiles):
        if tuple(self.pos) not in visible_tiles:
            return
        px = self.pos[0] * TILE_SIZE + TILE_SIZE // 2
        py = self.pos[1] * TILE_SIZE + TILE_SIZE // 2
        pulse = abs(math.sin(pygame.time.get_ticks() / 80)) * 6
        color = HIT_EFFECT_COLORS[self.color_index]
        pygame.draw.circle(screen, color, (int(px), int(py)),
                           int(TILE_SIZE // 3 + 8 + pulse), 4)


class DeathEffect:
    def __init__(self, pos):
        self.pos = pos
        self.timer = 30
        self.particles = []
        self.expansion = 0
        for _ in range(20):
            self.particles.append({
                'x': pos[0] * TILE_SIZE + TILE_SIZE // 2,
                'y': pos[1] * TILE_SIZE + TILE_SIZE // 2,
                'vx': (random.random() - 0.5) * 10,
                'vy': (random.random() - 0.5) * 10,
                'color': DEATH_EFFECT_COLORS[random.randint(0, len(DEATH_EFFECT_COLORS) - 1)],
                'size': random.randint(4, 8)
            })

    def update(self):
        self.timer -= 1
        self.expansion += 1.5
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.3
            p['size'] = max(0, p['size'] - 0.2)
        return self.timer > 0

    def draw(self, screen, visible_tiles):
        if tuple(self.pos) not in visible_tiles:
            return
        px = self.pos[0] * TILE_SIZE + TILE_SIZE // 2
        py = self.pos[1] * TILE_SIZE + TILE_SIZE // 2
        alpha = max(0, min(255, self.timer * 10))
        expansion_surf = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
        pygame.draw.circle(expansion_surf, (255, 100, 100, alpha),
                           (TILE_SIZE, TILE_SIZE), int(self.expansion), 3)
        screen.blit(expansion_surf, (px - TILE_SIZE, py - TILE_SIZE))
        for p in self.particles:
            if p['size'] > 0:
                pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), int(p['size']))