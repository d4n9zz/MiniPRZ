import pygame
import math
import random
import settings
import iso
from settings import TILE_SIZE, HIT_EFFECT_COLORS, DEATH_EFFECT_COLORS


class DamageNumber:
    __slots__ = ['pos', 'value', 'sx', 'y_offset', 'timer']

    def __init__(self, pos, value):
        self.pos = pos
        self.value = value
        self.sx, cy = iso.tile_center(pos[0], pos[1])
        self.y_offset = cy - settings.ISO_UNIT_LIFT - 10
        self.timer = 20

    def update(self):
        self.y_offset -= 1.5
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, visible_tiles):
        from settings import damage_font
        if tuple(self.pos) not in visible_tiles or not damage_font:
            return
        px = self.sx
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
    __slots__ = ['pos', 'timer', 'color_index']

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
        px, py = iso.tile_center(self.pos[0], self.pos[1])
        py -= settings.ISO_UNIT_LIFT
        pulse = abs(math.sin(pygame.time.get_ticks() / 80)) * 6
        color = HIT_EFFECT_COLORS[self.color_index]
        rx = int(TILE_SIZE // 3 + 8 + pulse)      # кольцо в изометрии — эллипс 2:1
        ry = max(5, rx // 2)
        pygame.draw.ellipse(screen, color, (px - rx, py - ry, rx * 2, ry * 2), 4)


class DeathEffect:
    __slots__ = ['pos', 'timer', 'particles', 'expansion']

    def __init__(self, pos):
        self.pos = pos
        self.timer = 30
        self.particles = []
        self.expansion = 0
        start_x, start_y = iso.tile_center(pos[0], pos[1])
        start_y -= settings.ISO_UNIT_LIFT
        for _ in range(20):
            self.particles.append({
                'x': start_x,
                'y': start_y,
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
        px, py = iso.tile_center(self.pos[0], self.pos[1])
        alpha = max(0, min(255, self.timer * 10))
        e = int(self.expansion)
        if e >= 6:
            half = settings.ISO_W
            expansion_surf = pygame.Surface((half * 2, half * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(expansion_surf, (255, 100, 100, alpha),
                                (half - e, half - e // 2, e * 2, e), 3)
            screen.blit(expansion_surf, (px - half, py - half))
        for p in self.particles:
            if p['size'] > 0:
                pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), int(p['size']))


class BattleLog:
    """Журнал боя: последние события; записи сами гаснут, клавиша [L] закрепляет журнал."""
    MAX_ENTRIES = 60      # сколько записей хранить
    SHOW_MS = 7000        # сколько записи видны полностью
    FADE_MS = 2000        # сколько они потом гаснут
    PINNED_LINES = 12     # сколько строк видно в закреплённом режиме
    FADING_LINES = 7      # сколько строк видно в обычном режиме

    def __init__(self):
        self.entries = []
        self.pinned = False

    def add(self, text, color=(240, 248, 255)):
        self.entries.append({'text': text, 'color': color, 'time': pygame.time.get_ticks()})
        if len(self.entries) > self.MAX_ENTRIES:
            del self.entries[:len(self.entries) - self.MAX_ENTRIES]

    def toggle(self):
        self.pinned = not self.pinned

    def draw(self, screen, x, y, font):
        if not font:
            return
        now = pygame.time.get_ticks()
        lines = []
        if self.pinned:
            lines = [(e, 255) for e in self.entries[-self.PINNED_LINES:]]
        else:
            for e in self.entries[-self.FADING_LINES:]:
                age = now - e['time']
                if age >= self.SHOW_MS + self.FADE_MS:
                    continue
                if age <= self.SHOW_MS:
                    alpha = 255
                else:
                    alpha = int(255 * (1 - (age - self.SHOW_MS) / self.FADE_MS))
                lines.append((e, alpha))
        if not lines:
            return
        rendered = [(font.render(e['text'], True, e['color']), a) for e, a in lines]
        line_h = font.get_height() + 3
        width = max(260, max(s.get_width() for s, _ in rendered) + 16)
        height = len(rendered) * line_h + 12
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((15, 20, 35, int(170 * max(a for _, a in rendered) / 255)))
        screen.blit(panel, (x, y))
        for i, (surf, alpha) in enumerate(rendered):
            surf.set_alpha(alpha)
            screen.blit(surf, (x + 8, y + 6 + i * line_h))
