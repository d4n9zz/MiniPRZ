import random
from collections import deque
import settings
import terrain
from utils import move_towards, get_unit_at, get_empty_pos


class Unit:
    __slots__ = [
        'pos', 'unit_type', 'name', 'hp', 'max_hp',
        'damage_range', 'color', 'speed', 'is_player',
        'move_path', 'has_moved', 'px', 'py',
        'shake_timer', 'shake_offset'
    ]

    def __init__(self, pos, unit_type='pawn', is_player=False):
        type_data = settings.UNIT_TYPES.get(unit_type, settings.UNIT_TYPES['pawn'])
        self.pos = list(pos)
        self.unit_type = unit_type
        self.name = type_data['name']
        self.hp = type_data['hp']
        self.max_hp = type_data['hp']
        self.damage_range = type_data['damage']
        self.color = type_data['color']
        self.speed = type_data['speed']
        self.is_player = is_player
        self.move_path = []
        self.has_moved = False
        self.px = self.pos[0] * settings.TILE_SIZE + settings.TILE_SIZE // 2
        self.py = self.pos[1] * settings.TILE_SIZE + settings.TILE_SIZE // 2
        self.shake_timer = 0
        self.shake_offset = [0, 0]

    def is_alive(self):
        return self.hp > 0

    def get_attack_damage(self):
        return random.randint(self.damage_range[0], self.damage_range[1])

    def get_max_attack_damage(self):
        return self.damage_range[1]

    def start_shake(self):
        self.shake_timer = settings.SHAKE_DURATION

    def update_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            if self.shake_timer > 0:
                self.shake_offset[0] = random.randint(
                    -settings.SHAKE_INTENSITY, settings.SHAKE_INTENSITY
                )
                self.shake_offset[1] = random.randint(
                    -settings.SHAKE_INTENSITY, settings.SHAKE_INTENSITY
                )
            else:
                self.shake_offset = [0, 0]

    def update_animation(self):
        if not self.move_path:
            return
        target = self.move_path[0]
        if not isinstance(target, (list, tuple)) or len(target) < 2:
            return
        target_px = target[0] * settings.TILE_SIZE + settings.TILE_SIZE // 2
        target_py = target[1] * settings.TILE_SIZE + settings.TILE_SIZE // 2
        dx, dy = target_px - self.px, target_py - self.py
        step = self.speed
        if abs(dx) <= step and abs(dy) <= step:
            self.pos = list(target)
            self.move_path.pop(0)
            self.px, self.py = target_px, target_py
        else:
            self.px += step if dx > 0 else -step if dx < 0 else 0
            self.py += step if dy > 0 else -step if dy < 0 else 0


# ========== СПАВН ==========

def _free_spawn_cell(spawn_zone, occupied):
    """Случайная свободная клетка зоны 3x3 или None, если зона заполнена."""
    cells = [
        [x, y]
        for x in range(spawn_zone[0], spawn_zone[0] + 3)
        for y in range(spawn_zone[1], spawn_zone[1] + 3)
        if 0 <= x < settings.COLS and 0 <= y < settings.ROWS
        and not terrain.is_blocked([x, y]) and not get_unit_at([x, y], occupied)
    ]
    return random.choice(cells) if cells else None


def create_units(count, existing_units, is_player, spawn_zone=None):
    units = []
    unit_types = list(settings.UNIT_TYPES.keys())
    for _ in range(count):
        occupied = existing_units + units
        if spawn_zone:
            pos = _free_spawn_cell(spawn_zone, occupied)
            if pos is None:
                break  # зона заполнена, больше юнитов не создаём
        else:
            pos = get_empty_pos(occupied)
        unit_type = random.choice(unit_types)
        units.append(Unit(pos, unit_type=unit_type, is_player=is_player))
    return units


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ИИ ==========

def _get_distance(pos1, pos2):
    """Манхэттенское расстояние между двумя позициями"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def _cell_is_free(pos, units):
    """
    Клетка в пределах поля, на ней нет юнита,
    и никто из юнитов не идёт на неё (учитываем move_path).
    """
    if not (0 <= pos[0] < settings.COLS and 0 <= pos[1] < settings.ROWS):
        return False
    if terrain.is_blocked(pos):
        return False
    for u in units:
        if u.pos == pos:
            return False
        if any(list(p) == pos for p in u.move_path):
            return False
    return True


def _evaluate_threat(bot_unit, enemy):
    """
    Оценивает угрозу от врага.
    Чем выше значение, тем опаснее враг.
    Формула: max_damage / distance (ближе и сильнее = опаснее)
    """
    distance = _get_distance(bot_unit.pos, enemy.pos)
    if distance == 0:
        distance = 1  # Избегаем деления на ноль

    max_damage = enemy.get_max_attack_damage()
    threat = max_damage / distance

    # Бонус за возможность добить
    if enemy.hp <= bot_unit.get_max_attack_damage():
        threat *= 3  # Приоритет добивания

    # Бонус за низкий HP врага (легче убить)
    if enemy.hp <= 5:
        threat *= 1.5

    return threat


def _find_retreat_direction(bot_unit, enemies):
    """
    Находит направление для отступления от ближайшего врага.
    Возвращает позицию для отступления или None.
    """
    if not enemies:
        return None

    nearest_enemy = min(enemies, key=lambda e: _get_distance(bot_unit.pos, e.pos))

    dx = bot_unit.pos[0] - nearest_enemy.pos[0]
    dy = bot_unit.pos[1] - nearest_enemy.pos[1]

    if dx != 0:
        dx = 1 if dx > 0 else -1
    if dy != 0:
        dy = 1 if dy > 0 else -1

    retreat_pos = [bot_unit.pos[0] + dx, bot_unit.pos[1] + dy]

    if 0 <= retreat_pos[0] < settings.COLS and 0 <= retreat_pos[1] < settings.ROWS:
        return retreat_pos

    return None


def _get_group_center(bot_units):
    """Вычисляет центр группы ботов"""
    if not bot_units:
        return None

    sum_x = sum(u.pos[0] for u in bot_units)
    sum_y = sum(u.pos[1] for u in bot_units)
    return [sum_x // len(bot_units), sum_y // len(bot_units)]


def _next_step(bot_unit, target, units):
    """
    Первый шаг кратчайшего пути к цели (поиск в ширину, ход на 8 сторон).
    Обходит воду, горы и клетки, занятые другими юнитами.
    Путь считается до клетки рядом с целью. Возвращает [x, y] или None.
    """
    start = tuple(bot_unit.pos)
    goal = tuple(target)

    def near_goal(c):
        return max(abs(c[0] - goal[0]), abs(c[1] - goal[1])) <= 1

    if near_goal(start):
        return None

    occupied = set()
    for u in units:
        if u is bot_unit:
            continue
        occupied.add(tuple(u.pos))
        for p in u.move_path:
            occupied.add(tuple(p))

    prev = {start: None}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if near_goal(cur):
            while prev[cur] != start:
                cur = prev[cur]
            return list(cur)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                n = (cur[0] + dx, cur[1] + dy)
                if n in prev:
                    continue
                if not (0 <= n[0] < settings.COLS and 0 <= n[1] < settings.ROWS):
                    continue
                if terrain.is_blocked(n) or n in occupied:
                    continue
                prev[n] = cur
                queue.append(n)
    return None


def _should_retreat(bot_unit, personality):
    """
    Определяет, должен ли бот отступать.
    Зависит от HP и личности.
    """
    hp_ratio = bot_unit.hp / bot_unit.max_hp

    if personality == 'aggressive':
        return hp_ratio < 0.2  # Отступает только при очень низком HP
    elif personality == 'defensive':
        return hp_ratio < 0.4  # Отступает раньше
    else:
        return hp_ratio < 0.3


def _choose_target(bot_unit, adjacent_enemies):
    """
    Выбирает лучшую цель среди смежных врагов (они уже отфильтрованы
    в bot_step) по оценке угрозы.
    """
    if not adjacent_enemies:
        return None
    return max(adjacent_enemies, key=lambda e: _evaluate_threat(bot_unit, e))


def _choose_movement_target(bot_unit, enemies, allies, personality):
    """
    Выбирает цель для движения.
    Учитывает личность, группу и угрозы.
    Всегда возвращает позицию, если есть хотя бы один враг.
    """
    if not enemies:
        return None

    nearest_enemy = min(enemies, key=lambda e: _get_distance(bot_unit.pos, e.pos))

    # Агрессивный бот идёт к самому опасному врагу
    if personality == 'aggressive':
        most_dangerous = max(enemies, key=lambda e: _evaluate_threat(bot_unit, e))
        return most_dangerous.pos

    # Оборонительный бот держится группы
    if personality == 'defensive':
        group_center = _get_group_center(allies)
        if group_center and _get_distance(bot_unit.pos, group_center) > 3:
            return group_center
        # Союзников нет или группа рядом — идём к ближайшему врагу
        return nearest_enemy.pos

    # По умолчанию — к ближайшему врагу
    return nearest_enemy.pos


# ========== ХОД БОТА ==========

def bot_step(bot_unit, player_units, bot_units, personality='balanced',
             damage_callback=None, effect_callback=None, death_callback=None,
             attack_callback=None):
    """
    Улучшенный ИИ бота с учётом личности и тактики.

    personality: 'aggressive', 'defensive', 'balanced'
    """
    enemies = [u for u in player_units if u not in bot_units]
    allies = [u for u in bot_units if u != bot_unit]
    all_units = bot_units + enemies

    # ========== ОТСТУПЛЕНИЕ ==========
    if _should_retreat(bot_unit, personality):
        retreat_pos = _find_retreat_direction(bot_unit, enemies)
        if retreat_pos and _cell_is_free(retreat_pos, all_units):
            bot_unit.move_path = [retreat_pos]
            return

    # ========== АТАКА ==========
    adjacent_enemies = []
    for enemy in enemies:
        dx = abs(bot_unit.pos[0] - enemy.pos[0])
        dy = abs(bot_unit.pos[1] - enemy.pos[1])
        if dx <= 1 and dy <= 1 and (dx + dy) != 0:
            adjacent_enemies.append(enemy)

    if adjacent_enemies:
        target = _choose_target(bot_unit, adjacent_enemies)

        if target:
            attack_damage = bot_unit.get_attack_damage()
            target.hp -= attack_damage
            target.start_shake()

            if damage_callback:
                damage_callback(target.pos, attack_damage)
            if effect_callback:
                effect_callback(target.pos)
            if not target.is_alive() and death_callback:
                death_callback(target.pos)
            if attack_callback:
                attack_callback(bot_unit, target, attack_damage, not target.is_alive())

            return

    # ========== ДВИЖЕНИЕ ==========
    target_pos = _choose_movement_target(bot_unit, enemies, allies, personality)

    if target_pos:
        new_pos = _next_step(bot_unit, target_pos, all_units)
        if new_pos and _cell_is_free(new_pos, all_units):
            bot_unit.move_path = [new_pos]


# ========== ПОКУПКА ==========

def smart_bot_buy(bot_units, bot_gold, spawn_zone, personality='balanced', enemy_units=None):
    """
    Умная покупка юнитов с учётом стратегии и ситуации.
    Возвращает остаток золота.
    """
    unit_types = list(settings.UNIT_TYPES.keys())

    if personality == 'aggressive':
        priority = ['mage', 'knight', 'archer', 'pawn']
    elif personality == 'defensive':
        priority = ['knight', 'pawn', 'archer', 'mage']
    else:
        priority = unit_types.copy()
        random.shuffle(priority)

    # Адаптация под состав врагов
    if enemy_units:
        enemy_types = {}
        for enemy in enemy_units:
            enemy_types[enemy.unit_type] = enemy_types.get(enemy.unit_type, 0) + 1

        # Много ближников у врага — лучники вперёд
        if enemy_types.get('pawn', 0) + enemy_types.get('knight', 0) > 3:
            if 'archer' in priority:
                priority.remove('archer')
                priority.insert(0, 'archer')

        # Много лучников у врага — рыцари вперёд
        if enemy_types.get('archer', 0) > 2:
            if 'knight' in priority:
                priority.remove('knight')
                priority.insert(0, 'knight')

    if len(bot_units) >= 8:
        return bot_gold

    # Свободная клетка с учётом и своих юнитов, и вражеских
    pos = _free_spawn_cell(spawn_zone, bot_units + list(enemy_units or []))
    if pos is None:
        return bot_gold  # зона спавна заполнена

    for utype in priority:
        cost = settings.UNIT_TYPES[utype]["hp"]
        if bot_gold >= cost:
            bot_units.append(Unit(pos, unit_type=utype, is_player=False))
            return bot_gold - cost

    return bot_gold
