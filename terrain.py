import random
from collections import deque

import pygame
import settings

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


# ========== ОТРИСОВКА ==========

def build_surface(size):
    """Рисует всю местность один раз на прозрачную поверхность размера карты."""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    t = settings.TILE_SIZE
    k = t / 50.0   # все размеры ниже подобраны под клетку 50 px

    def p(x, y):
        return int(x * k), int(y * k)

    for (x, y), kind in BLOCKED.items():
        ox, oy = x * t, y * t
        rect = pygame.Rect(ox, oy, t, t)
        if kind == WATER:
            pygame.draw.rect(surf, (45, 110, 190), rect)
            for wy in (16, 33):
                pts = [(ox + p(6, 0)[0], oy + p(0, wy)[1]),
                       (ox + p(16, 0)[0], oy + p(0, wy - 4)[1]),
                       (ox + p(26, 0)[0], oy + p(0, wy)[1]),
                       (ox + p(36, 0)[0], oy + p(0, wy - 4)[1]),
                       (ox + p(44, 0)[0], oy + p(0, wy)[1])]
                pygame.draw.lines(surf, (130, 190, 240), False, pts, 2)
            pygame.draw.rect(surf, (25, 70, 140), rect, 1)
        else:
            pygame.draw.rect(surf, (88, 92, 100), rect)
            peak = [(ox + p(5, 0)[0], oy + p(0, 44)[1]),
                    (ox + p(25, 0)[0], oy + p(0, 7)[1]),
                    (ox + p(45, 0)[0], oy + p(0, 44)[1])]
            shade = [peak[1], peak[2], (ox + p(25, 0)[0], oy + p(0, 44)[1])]
            cap = [(ox + p(18, 0)[0], oy + p(0, 20)[1]),
                   peak[1],
                   (ox + p(32, 0)[0], oy + p(0, 20)[1])]
            pygame.draw.polygon(surf, (140, 144, 154), peak)
            pygame.draw.polygon(surf, (105, 109, 119), shade)
            pygame.draw.polygon(surf, (245, 248, 255), cap)
            pygame.draw.rect(surf, (55, 58, 66), rect, 1)
    return surf
