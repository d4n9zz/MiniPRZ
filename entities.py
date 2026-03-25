import random
import settings
from utils import move_towards, get_unit_at, get_empty_pos, COLS, ROWS


class Unit:
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

    def is_alive(self):
        return self.hp > 0

    def get_attack_damage(self):
        return random.randint(self.damage_range[0], self.damage_range[1])

    def get_max_attack_damage(self):
        return self.damage_range[1]

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


def create_units(count, existing_units, is_player):
    units = []
    unit_types = list(settings.UNIT_TYPES.keys())
    for _ in range(count):
        pos = get_empty_pos(existing_units + units)
        unit_type = random.choice(unit_types)
        units.append(Unit(pos, unit_type=unit_type, is_player=is_player))
    return units


def bot_step(bot_unit, player_units, bot_units, damage_callback, effect_callback, death_callback):
    adjacent_enemies = []
    for p_unit in player_units:
        dx = abs(bot_unit.pos[0] - p_unit.pos[0])
        dy = abs(bot_unit.pos[1] - p_unit.pos[1])
        if dx <= 1 and dy <= 1 and (dx + dy) != 0:
            adjacent_enemies.append(p_unit)

    if adjacent_enemies:
        max_dmg = bot_unit.get_max_attack_damage()
        kill_target = None
        for enemy in adjacent_enemies:
            if enemy.hp <= max_dmg:
                kill_target = enemy
                break
        if kill_target:
            target = kill_target
        else:
            target = min(adjacent_enemies, key=lambda u: u.hp)
        attack_damage = bot_unit.get_attack_damage()
        target.hp -= attack_damage
        damage_callback(target.pos, attack_damage)
        effect_callback(target.pos)
        if not target.is_alive():
            death_callback(target.pos)
        return

    if player_units:
        nearest_unit = min(player_units, key=lambda u: abs(u.pos[0] - bot_unit.pos[0]) + abs(u.pos[1] - bot_unit.pos[1]))
        target_pos = nearest_unit.pos
        new_pos = move_towards(bot_unit.pos, target_pos)
        if isinstance(new_pos, list) and len(new_pos) == 2:
            if (0 <= new_pos[0] < COLS and 0 <= new_pos[1] < ROWS and
                    not get_unit_at(new_pos, bot_units) and
                    not get_unit_at(new_pos, player_units)):
                bot_unit.move_path = [new_pos]