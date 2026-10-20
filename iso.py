"""Изометрическая проекция для MiniPRZ.

Логика игры остаётся на плоской сетке (x, y) и «плоских» пикселях
(unit.px / unit.py считаются как раньше через TILE_SIZE). Проекция применяется
только при отрисовке и при переводе клика мыши в клетку.

Все координаты — внутри карты (для подповерхности map_rect).
"""
import math
import pygame
import settings


# Поворот вида: свободный угол в радианах (0..2π) вокруг центра карты.
# Логика игры от поворота не зависит: меняется только то, как клетки попадают на экран.
ANGLE = 0.0


def set_angle(a):
    global ANGLE
    ANGLE = a % math.tau


def set_rotation(r):
    """Совместимость со старым кодом: r — число поворотов по 90°."""
    set_angle(r * math.pi / 2)


def _map_center():
    return settings.COLS / 2, settings.ROWS / 2


def _screen_center():
    """Куда на экране (внутри окна карты) попадает центр карты.
    Окно карты — вся область поля, поэтому карта не обрезается при повороте."""
    return settings.WIDTH // 2, settings.FIELD_HEIGHT // 2 + settings.ISO_TOP_PAD // 2


def rotate_point(u, v):
    """Точка карты (в координатах углов клеток, дробные допустимы) -> повёрнутая вокруг центра."""
    cc, cr = _map_center()
    du, dv = u - cc, v - cr
    c, s = math.cos(ANGLE), math.sin(ANGLE)
    return cc + du * c - dv * s, cr + du * s + dv * c


def unrotate_point(u, v):
    """Обратное к rotate_point."""
    cc, cr = _map_center()
    du, dv = u - cc, v - cr
    c, s = math.cos(ANGLE), math.sin(ANGLE)
    return cc + du * c + dv * s, cr - du * s + dv * c


def _project(u, v):
    cc, cr = _map_center()
    sx, sy = _screen_center()
    du, dv = u - cc, v - cr
    return (sx + (du - dv) * settings.ISO_W / 2,
            sy + (du + dv) * settings.ISO_H / 2)


def _center_f(x, y):
    cu, cv = rotate_point(x + 0.5, y + 0.5)
    return _project(cu, cv)


def tile_top(x, y):
    """Верхняя точка клетки (x, y) на экране; дробные x, y допустимы."""
    cx, cy = _center_f(x, y)
    return cx, cy - settings.ISO_H / 2


def depth(x, y):
    """Глубина клетки: чем больше, тем она ближе к зрителю (порядок рисования)."""
    cu, cv = rotate_point(x + 0.5, y + 0.5)
    return cu + cv


def corner(x, y):
    """Угол сетки (целые x, y — именно точка-угол, не клетка), для контуров."""
    u, v = rotate_point(x, y)
    px, py = _project(u, v)
    return int(px), int(py)


def tile_center(x, y):
    """Центр клетки (x, y) на земле."""
    cx, cy = _center_f(x, y)
    return int(cx), int(cy)


def world_to_screen(px, py):
    """Плоские пиксели (unit.px, unit.py) -> экранный центр клетки на земле."""
    t = settings.TILE_SIZE
    return tile_center(px / t - 0.5, py / t - 0.5)


def screen_to_grid(sx, sy):
    """Точка внутри карты -> клетка [x, y] (для кликов мыши)."""
    scx, scy = _screen_center()
    a = (sy - scy) / (settings.ISO_H / 2)
    b = (sx - scx) / (settings.ISO_W / 2)
    cc, cr = _map_center()
    x, y = unrotate_point(cc + (a + b) / 2, cr + (a - b) / 2)
    return [math.floor(x), math.floor(y)]


def diamond(x, y):
    """Четыре вершины клетки (x, y). При свободном повороте это уже не ровный ромб."""
    return [corner(x, y), corner(x + 1, y), corner(x + 1, y + 1), corner(x, y + 1)]


def map_outline():
    """Контур всей карты — четыре угла по порядку обхода."""
    c, r = settings.COLS, settings.ROWS
    return [corner(0, 0), corner(c, 0), corner(c, r), corner(0, r)]


def _shade(color, k):
    return tuple(max(0, min(255, int(v * k))) for v in color[:3])


def draw_box(surf, cx, base_y, hw, height, color, outline=True):
    """Изометрический параллелепипед. (cx, base_y) — центр ромба основания."""
    hh = hw // 2
    left = (cx - hw, base_y)
    right = (cx + hw, base_y)
    bottom = (cx, base_y + hh)
    back = (cx, base_y - hh)
    up = (0, -height)

    def u(p):
        return (p[0], p[1] + up[1])

    left_face = [left, bottom, u(bottom), u(left)]
    right_face = [bottom, right, u(right), u(bottom)]
    top_face = [u(left), u(back), u(right), u(bottom)]
    pygame.draw.polygon(surf, _shade(color, 0.62), left_face)
    pygame.draw.polygon(surf, _shade(color, 0.80), right_face)
    pygame.draw.polygon(surf, _shade(color, 1.0), top_face)
    if outline:
        edge = _shade(color, 0.35)
        for face in (left_face, right_face, top_face):
            pygame.draw.polygon(surf, edge, face, 1)


def draw_pyramid(surf, cx, base_y, hw, height, color, outline=True):
    """Изометрическая пирамида-крыша. (cx, base_y) — центр ромба основания."""
    hh = hw // 2
    left = (cx - hw, base_y)
    right = (cx + hw, base_y)
    bottom = (cx, base_y + hh)
    apex = (cx, base_y - height)
    left_face = [left, bottom, apex]
    right_face = [bottom, right, apex]
    pygame.draw.polygon(surf, _shade(color, 0.7), left_face)
    pygame.draw.polygon(surf, _shade(color, 1.0), right_face)
    if outline:
        edge = _shade(color, 0.35)
        pygame.draw.polygon(surf, edge, left_face, 1)
        pygame.draw.polygon(surf, edge, right_face, 1)
