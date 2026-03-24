import pygame
import os
import random
from settings import FONT_FALLBACKS, TILE_SIZE, COLS, ROWS


def load_font(size):
    for name in FONT_FALLBACKS:
        try:
            font_test = pygame.font.SysFont(name, size)
            test = font_test.render(">", True, (255, 255, 255))
            if test.get_width() > 0:
                return font_test
        except pygame.error:
            continue
    return pygame.font.SysFont(None, size)


def load_unit_image(filepath):
    try:
        if os.path.exists(filepath):
            img = pygame.image.load(filepath).convert_alpha()
            img = pygame.transform.smoothscale(img, (TILE_SIZE - 10, TILE_SIZE - 10))
            return img
    except pygame.error:
        return None


def get_empty_pos(existing_units):
    while True:
        pos = [random.randint(0, COLS - 1), random.randint(0, ROWS - 1)]
        occupied = False
        for u in existing_units:
            if hasattr(u, 'pos'):
                if u.pos == pos:
                    occupied = True
                    break
            elif isinstance(u, dict) and "pos" in u:
                if u["pos"] == pos:
                    occupied = True
                    break
        if not occupied:
            return pos


def get_unit_at(pos, units_list):
    for u in units_list:
        if hasattr(u, 'pos'):
            if u.pos == pos:
                return u
        elif isinstance(u, dict) and "pos" in u:
            if u["pos"] == pos:
                return u
    return None


def move_towards(start, target):
    dx, dy = target[0] - start[0], target[1] - start[1]
    step = [0, 0]
    if dx != 0:
        step[0] = 1 if dx > 0 else -1
    if dy != 0:
        step[1] = 1 if dy > 0 else -1
    return [start[0] + step[0], start[1] + step[1]]