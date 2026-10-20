import random
from collections import deque

import pygame
import settings
import iso

WATER = 'water'
MOUNTAIN = 'mountain'

# Непроходимые клетки текущей карты: (x, y) -> 'water' | 'mountain'
BLOCKED = {}

MAX_ATTEMPTS = 30   # сколько раз пробуем сгенерировать карту, пока все города не окажутся связаны


def is_blocked(pos):
    return (pos[0], pos[1]) in BLOCKED


def clear():
    BLOCKED.clear()


def _in_bounds(x, y):
    return 0 <= x < settings.COLS and 0 <= y < settings.ROWS


def _protected_tiles(spawns):
    """Зоны городов 3x3 плюс рамка в 1 клетку вокруг них — тут местность не появляется."""
    protected = set()
    for sx, sy in spawns:
        for x in range(sx - 1, sx + 4):
            for y in range(sy - 1, sy + 4):
                protected.add((x, y))
    return protected


def _add_lake(rng, tiles, protected):
    """Озеро: «пятно», растущее от случайной клетки в случайные стороны."""
    cx = rng.randint(0, settings.COLS - 1)
    cy = rng.randint(0, settings.ROWS - 1)
    cells = [(cx, cy)]
    for _ in range(rng.randint(6, 16)):
        x, y = rng.choice(cells)
        dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        cells.append((x + dx, y + dy))
    for x, y in cells:
        if _in_bounds(x, y) and (x, y) not in protected:
            tiles[(x, y)] = WATER


def _add_ridge(rng, tiles, protected):
    """Горная гряда: блуждание по карте с редкими поворотами."""
    x = rng.randint(0, settings.COLS - 1)
    y = rng.randint(0, settings.ROWS - 1)
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    dx, dy = rng.choice(dirs)
    for _ in range(rng.randint(4, 9)):
        if _in_bounds(x, y) and (x, y) not in protected and (x, y) not in tiles:
            tiles[(x, y)] = MOUNTAIN
        if rng.random() < 0.3:
            dx, dy = rng.choice(dirs)
        x, y = x + dx, y + dy


def _all_cities_connected(tiles, spawns):
    """Поиск в ширину от первого города: дойдём ли до всех остальных (ход — на 8 сторон)."""
    centers = [(sx + 1, sy + 1) for sx, sy in spawns]
    if len(centers) < 2:
        return True
    start = centers[0]
    seen = {start}
    queue = deque([start])
    while queue:
        cx, cy = queue.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (cx + dx, cy + dy)
                if n in seen or not _in_bounds(*n) or n in tiles:
                    continue
                seen.add(n)
                queue.append(n)
    return all(c in seen for c in centers)


def generate(spawns, seed):
    """
    Строит местность по seed. Один и тот же seed на одном размере карты
    с теми же городами всегда даёт одну и ту же карту.
    """
    protected = _protected_tiles(spawns)
    scale = (settings.COLS * settings.ROWS) / (34 * 18)   # за единицу взята средняя карта
    for attempt in range(MAX_ATTEMPTS):
        rng = random.Random(seed * 1000 + attempt)         # свой генератор — глобальный random не трогаем
        tiles = {}
        for _ in range(max(1, round(rng.randint(3, 5) * scale))):
            _add_lake(rng, tiles, protected)
        for _ in range(max(1, round(rng.randint(3, 5) * scale))):
            _add_ridge(rng, tiles, protected)
        if _all_cities_connected(tiles, spawns):
            BLOCKED.clear()
            BLOCKED.update(tiles)
            return
    BLOCKED.clear()   # совсем не вышло — играем на чистом поле


# ========== ОТРИСОВКА (изометрия) ==========

def mountain_tiles():
    """Клетки с горами — их рисуют отдельно, вместе с юнитами, по глубине."""
    return sorted(pos for pos, kind in BLOCKED.items() if kind == MOUNTAIN)


def build_surface(size):
    """Рисует воду (плоскую) один раз на прозрачную поверхность размера карты."""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    for (x, y), kind in BLOCKED.items():
        if kind != WATER:
            continue
        pts = iso.diamond(x, y)
        pygame.draw.polygon(surf, (45, 110, 190), pts)
        cx, cy = iso.tile_center(x, y)
        for dy in (-5, 4):
            wave = [(cx - 14, cy + dy), (cx - 7, cy + dy - 2), (cx, cy + dy),
                    (cx + 7, cy + dy - 2), (cx + 14, cy + dy)]
            pygame.draw.lines(surf, (130, 190, 240), False, wave, 2)
        pygame.draw.polygon(surf, (25, 70, 140), pts, 1)
    return surf


def build_mountain_sprite():
    """Один спрайт горы (пирамида со снежной шапкой). Низ спрайта — ромб клетки."""
    w, h, ph = settings.ISO_W, settings.ISO_H, settings.ISO_PEAK_H
    surf = pygame.Surface((w, h + ph), pygame.SRCALPHA)
    cx = w // 2
    base = ph + h // 2                      # центр ромба основания в спрайте
    left, right = (0, base), (w - 1, base)
    bottom, back = (cx, base + h // 2 - 1), (cx, base - h // 2)
    apex = (cx, 2)

    def lerp(a, b, t):
        return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t))

    pygame.draw.polygon(surf, (88, 92, 100), [left, back, right, bottom])   # каменное основание
    left_face, right_face = [left, bottom, apex], [bottom, right, apex]
    pygame.draw.polygon(surf, (105, 109, 119), left_face)
    pygame.draw.polygon(surf, (140, 144, 154), right_face)
    t = 0.38
    pygame.draw.polygon(surf, (225, 230, 240), [apex, lerp(apex, left, t), lerp(apex, bottom, t)])
    pygame.draw.polygon(surf, (250, 252, 255), [apex, lerp(apex, bottom, t), lerp(apex, right, t)])
    pygame.draw.polygon(surf, (55, 58, 66), left_face, 1)
    pygame.draw.polygon(surf, (55, 58, 66), right_face, 1)
    return surf
