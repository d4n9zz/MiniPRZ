import random
import settings
from utils import move_towards, get_unit_at, get_empty_pos, COLS, ROWS


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


def create_units(count, existing_units, is_player, spawn_zone=None):
    units = []
    unit_types = list(settings.UNIT_TYPES.keys())
    for _ in range(count):
        if spawn_zone:
            pos = [
                random.randint(spawn_zone[0], spawn_zone[0] + 2),
                random.randint(spawn_zone[1], spawn_zone[1] + 2)
            ]
            attempts = 0
            while get_unit_at(pos, existing_units + units) and attempts < 10:
                pos = [
                    random.randint(spawn_zone[0], spawn_zone[0] + 2),
                    random.randint(spawn_zone[1], spawn_zone[1] + 2)
                ]
                attempts += 1
        else:
            pos = get_empty_pos(existing_units + units)
        unit_type = random.choice(unit_types)
        units.append(Unit(pos, unit_type=unit_type, is_player=is_player))
    return units


# ========== НОВЫЕ ФУНКЦИИ ДЛЯ УЛУЧШЕННОГО ИИ ==========

def _get_distance(pos1, pos2):
    """Манхэттенское расстояние между двумя позициями"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


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

    # Находим ближайшего врага
    nearest_enemy = min(enemies, key=lambda e: _get_distance(bot_unit.pos, e.pos))

    # Направление от врага
    dx = bot_unit.pos[0] - nearest_enemy.pos[0]
    dy = bot_unit.pos[1] - nearest_enemy.pos[1]

    # Нормализуем направление
    if dx != 0:
        dx = 1 if dx > 0 else -1
    if dy != 0:
        dy = 1 if dy > 0 else -1

    retreat_pos = [bot_unit.pos[0] + dx, bot_unit.pos[1] + dy]

    # Проверяем валидность позиции
    if (0 <= retreat_pos[0] < COLS and 0 <= retreat_pos[1] < ROWS):
        return retreat_pos

    return None


def _get_group_center(bot_units):
    """Вычисляет центр группы ботов"""
    if not bot_units:
        return None

    sum_x = sum(u.pos[0] for u in bot_units)
    sum_y = sum(u.pos[1] for u in bot_units)
    center_x = sum_x // len(bot_units)
    center_y = sum_y // len(bot_units)

    return [center_x, center_y]


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


def _choose_target(bot_unit, enemies, personality):
    """
    Выбирает лучшую цель для атаки.
    Учитывает угрозу, возможность добить и личность бота.
    """
    if not enemies:
        return None

    # Оцениваем всех врагов
    scored_enemies = []
    for enemy in enemies:
        distance = _get_distance(bot_unit.pos, enemy.pos)

        # Только смежные враги могут быть атакованы
        if distance <= 2:  # 1 = смежный, 2 = диагональ
            threat = _evaluate_threat(bot_unit, enemy)
            scored_enemies.append((enemy, threat))

    if not scored_enemies:
        return None

    # Сортируем по угрозе (убывание)
    scored_enemies.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем самую опасную цель
    return scored_enemies[0][0]


def _choose_movement_target(bot_unit, enemies, allies, personality):
    """
    Выбирает цель для движения.
    Учитывает личность, группу и угрозы.
    """
    if not enemies:
        return None

    # Для агрессивного бота — идём к самому опасному врагу
    if personality == 'aggressive':
        # Находим самого опасного врага (не только смежного)
        most_dangerous = max(enemies, key=lambda e: _evaluate_threat(bot_unit, e))
        return most_dangerous.pos

    # Для оборонительного бота — держимся группы
    elif personality == 'defensive':
        group_center = _get_group_center(allies)
        if group_center:
            distance_to_center = _get_distance(bot_unit.pos, group_center)

            # Если далеко от группы — идём к группе
            if distance_to_center > 3:
                return group_center

            # Если рядом с группой — идём к ближайшему врагу
            nearest_enemy = min(enemies, key=lambda e: _get_distance(bot_unit.pos, e.pos))
            return nearest_enemy.pos

    # По умолчанию — к ближайшему врагу
    else:
        nearest_enemy = min(enemies, key=lambda e: _get_distance(bot_unit.pos, e.pos))
        return nearest_enemy.pos


def bot_step(bot_unit, player_units, bot_units, personality='balanced',
             damage_callback=None, effect_callback=None, death_callback=None):
    """
    Улучшенный ИИ бота с учётом личности и тактики.

    personality: 'aggressive', 'defensive', 'balanced'
    """
    # Определяем врагов (все, кто не в bot_units)
    enemies = [u for u in player_units if u not in bot_units]
    allies = [u for u in bot_units if u != bot_unit]

    # ========== ПРОВЕРКА: НУЖНО ЛИ ОТСТУПАТЬ ==========
    if _should_retreat(bot_unit, personality):
        retreat_pos = _find_retreat_direction(bot_unit, enemies)
        if retreat_pos:
            if (0 <= retreat_pos[0] < COLS and 0 <= retreat_pos[1] < ROWS and
                    not get_unit_at(retreat_pos, bot_units) and
                    not get_unit_at(retreat_pos, enemies)):
                bot_unit.move_path = [retreat_pos]
                return

    # ========== ПРОВЕРКА: МОЖЕМ ЛИ АТАКОВАТЬ ==========
    adjacent_enemies = []
    for enemy in enemies:
        dx = abs(bot_unit.pos[0] - enemy.pos[0])
        dy = abs(bot_unit.pos[1] - enemy.pos[1])
        if dx <= 1 and dy <= 1 and (dx + dy) != 0:
            adjacent_enemies.append(enemy)

    if adjacent_enemies:
        # Выбираем лучшую цель
        target = _choose_target(bot_unit, adjacent_enemies, personality)

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

            return

    # ========== ДВИЖЕНИЕ К ЦЕЛИ ==========
    target_pos = _choose_movement_target(bot_unit, enemies, allies, personality)

    if target_pos:
        new_pos = move_towards(bot_unit.pos, target_pos)

        if isinstance(new_pos, list) and len(new_pos) == 2:
            # Проверяем валидность новой позиции
            if (0 <= new_pos[0] < COLS and 0 <= new_pos[1] < ROWS and
                    not get_unit_at(new_pos, bot_units) and
                    not get_unit_at(new_pos, enemies)):
                bot_unit.move_path = [new_pos]


def smart_bot_buy(bot_units, bot_gold, spawn_zone, personality='balanced', enemy_units=None):
    """
    Умная покупка юнитов с учётом стратегии и ситуации.
    """
    unit_types = list(settings.UNIT_TYPES.keys())

    # Стратегия покупки в зависимости от личности
    if personality == 'aggressive':
        # Приоритет: сильные атакующие юниты
        priority = ['mage', 'knight', 'archer', 'pawn']
    elif personality == 'defensive':
        # Приоритет: танки и поддержка
        priority = ['knight', 'pawn', 'archer', 'mage']
    else:
        # Сбалансированная стратегия
        priority = unit_types.copy()
        random.shuffle(priority)

    # Адаптация под врагов (если есть информация)
    if enemy_units and len(enemy_units) > 0:
        # Подсчитываем типы врагов
        enemy_types = {}
        for enemy in enemy_units:
            enemy_types[enemy.unit_type] = enemy_types.get(enemy.unit_type, 0) + 1

        # Если у врагов много ближников — покупаем лучников
        if enemy_types.get('pawn', 0) + enemy_types.get('knight', 0) > 3:
            if 'archer' in priority:
                priority.remove('archer')
                priority.insert(0, 'archer')

        # Если у врагов много лучников — покупаем танков
        if enemy_types.get('archer', 0) > 2:
            if 'knight' in priority:
                priority.remove('knight')
                priority.insert(0, 'knight')

    # Покупаем юнит по приоритету
    for utype in priority:
        cost = settings.UNIT_TYPES[utype]["hp"]
        if bot_gold >= cost and len(bot_units) < 8:
            spawn_x = random.randint(spawn_zone[0], spawn_zone[0] + 2)
            spawn_y = random.randint(spawn_zone[1], spawn_zone[1] + 2)

            attempts = 0
            while (get_unit_at([spawn_x, spawn_y], bot_units) and attempts < 10):
                spawn_x = random.randint(spawn_zone[0], spawn_zone[0] + 2)
                spawn_y = random.randint(spawn_zone[1], spawn_zone[1] + 2)
                attempts += 1

            if attempts < 10:
                new_unit = Unit([spawn_x, spawn_y], unit_type=utype, is_player=False)
                bot_units.append(new_unit)
                return bot_gold - cost

    return bot_gold