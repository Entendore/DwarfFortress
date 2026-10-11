"""
Emoji Fortress — Bestiary Edition
=================================
Expanded creature system with 8 enemy types, each with unique behaviors.

New creatures:
  🐺 Wolf       - Pack hunter, +2 dmg per nearby wolf
  💀 Skeleton   - Rises from tombstones at night
  🕷️ Spider     - Leaves web tiles that slow movement
  🧌 Troll      - Regenerates HP, very tough
  🦇 Bat        - Flying, ignores terrain
  🟢 Slime      - Splits into smaller slimes on death
  🐉 Dragon     - Rare boss, fire breath AoE, flying
  👿 Demon      - Late-game teleporter, high damage

New systems:
  • Dynamic threat level that escalates over time
  • Loot drops from creatures (food, gold, materials)
  • Web tiles that slow movement
  • Escalating raid waves based on day
  • Bestiary tracking (creatures encountered)
  • Creature info on hover

Controls (same as before, plus):
  B             : toggle bestiary view
  T             : show threat info
"""

from __future__ import annotations

import heapq
import logging
import os
import pickle
import random
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

import pygame

# --------------------------------------------------------------------------- #
# Logging                                                                     #
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("emoji_fortress")

# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #
WINDOW_W, WINDOW_H = 1400, 850
MAP_W, MAP_H = 80, 50
TILE_SIZE = 28
TICK_RATE = 10.0
DAY_LENGTH = 120.0
SAVE_FILE = "emoji_fortress_save.pkl"
EDGE_SCROLL_MARGIN = 24
EDGE_SCROLL_SPEED = 600

# Tile kinds -------------------------------------------------------------- #
class TileKind(Enum):
    GRASS = auto()
    DIRT = auto()
    TREE = auto()
    STONE = auto()
    WATER = auto()
    WALL = auto()
    FLOOR = auto()
    STOCKPILE = auto()
    BED = auto()
    WORKSHOP = auto()
    TOMBSTONE = auto()
    WEB = auto()        # Spider web - slows movement

TILE_EMOJI: dict[TileKind, str] = {
    TileKind.GRASS:      "🟩",
    TileKind.DIRT:       "🟫",
    TileKind.TREE:       "🌲",
    TileKind.STONE:      "🪨",
    TileKind.WATER:      "💧",
    TileKind.WALL:       "🧱",
    TileKind.FLOOR:      "🟨",
    TileKind.STOCKPILE:  "📦",
    TileKind.BED:        "🛏️",
    TileKind.WORKSHOP:   "🔨",
    TileKind.TOMBSTONE:  "🪦",
    TileKind.WEB:        "🕸️",
}

TILE_SOLID: set[TileKind] = {
    TileKind.TREE, TileKind.STONE, TileKind.WATER, TileKind.WALL,
}
TILE_SLOW: set[TileKind] = {TileKind.WEB}  # Tiles that slow movement
TILE_MINEABLE: set[TileKind] = {TileKind.TREE, TileKind.STONE}
TILE_BUILDABLE: set[TileKind] = {TileKind.GRASS, TileKind.DIRT, TileKind.FLOOR}

# Dwarf state machine ----------------------------------------------------- #
class DwarfState(Enum):
    IDLE = auto()
    MOVING = auto()
    CHOPPING = auto()
    MINING = auto()
    HAULING = auto()
    EATING = auto()
    SLEEPING = auto()
    FIGHTING = auto()
    CRAFTING = auto()
    BUILDING_BED = auto()
    BUILDING_WORKSHOP = auto()
    DEAD = auto()

DWARF_EMOJI = "🧔"

# Creature kinds ---------------------------------------------------------- #
class CreatureKind(Enum):
    GOBLIN = "Goblin"
    WOLF = "Wolf"
    SKELETON = "Skeleton"
    SPIDER = "Spider"
    TROLL = "Troll"
    BAT = "Bat"
    SLIME = "Slime"
    DRAGON = "Dragon"
    DEMON = "Demon"

CREATURE_EMOJI: dict[CreatureKind, str] = {
    CreatureKind.GOBLIN:   "👹",
    CreatureKind.WOLF:     "🐺",
    CreatureKind.SKELETON: "💀",
    CreatureKind.SPIDER:   "🕷️",
    CreatureKind.TROLL:    "🧌",
    CreatureKind.BAT:      "🦇",
    CreatureKind.SLIME:    "🟢",
    CreatureKind.DRAGON:   "🐉",
    CreatureKind.DEMON:    "👿",
}

# Creature stats: (hp, damage, speed, attack_range, flying, regen, special)
CREATURE_STATS: dict[CreatureKind, dict] = {
    CreatureKind.GOBLIN: {
        "hp": 40, "damage": 10, "speed": 1.8, "range": 1.0,
        "flying": False, "regen": 0.0, "xp_reward": 25,
        "loot": [("food", 0.3), ("stone", 0.2)],
    },
    CreatureKind.WOLF: {
        "hp": 30, "damage": 8, "speed": 3.5, "range": 1.0,
        "flying": False, "regen": 0.0, "xp_reward": 20,
        "loot": [("food", 0.5), ("food", 0.3)],
        "pack_bonus": 2,  # +2 dmg per nearby wolf
    },
    CreatureKind.SKELETON: {
        "hp": 25, "damage": 6, "speed": 1.5, "range": 1.0,
        "flying": False, "regen": 0.0, "xp_reward": 15,
        "loot": [("stone", 0.4)],
    },
    CreatureKind.SPIDER: {
        "hp": 35, "damage": 10, "speed": 2.0, "range": 1.0,
        "flying": False, "regen": 0.0, "xp_reward": 30,
        "loot": [("wood", 0.3)],
        "web_chance": 0.3,  # chance to leave web when moving
    },
    CreatureKind.TROLL: {
        "hp": 120, "damage": 18, "speed": 1.2, "range": 1.5,
        "flying": False, "regen": 2.0, "xp_reward": 80,
        "loot": [("stone", 0.6), ("stone", 0.4), ("food", 0.5)],
    },
    CreatureKind.BAT: {
        "hp": 15, "damage": 4, "speed": 4.0, "range": 1.0,
        "flying": True, "regen": 0.0, "xp_reward": 10,
        "loot": [],
    },
    CreatureKind.SLIME: {
        "hp": 20, "damage": 5, "speed": 1.0, "range": 1.0,
        "flying": False, "regen": 0.5, "xp_reward": 12,
        "loot": [("food", 0.2)],
        "split_chance": 0.7,  # chance to split on death
    },
    CreatureKind.DRAGON: {
        "hp": 300, "damage": 40, "speed": 2.5, "range": 5.0,
        "flying": True, "regen": 1.0, "xp_reward": 300,
        "loot": [("stone", 1.0), ("stone", 1.0), ("wood", 1.0), ("food", 1.0)],
        "fire_breath_cd": 3.0, "fire_breath_radius": 2.5,
    },
    CreatureKind.DEMON: {
        "hp": 80, "damage": 22, "speed": 2.2, "range": 1.5,
        "flying": False, "regen": 0.0, "xp_reward": 100,
        "loot": [("stone", 0.5), ("wood", 0.5)],
        "teleport_cd": 5.0,
    },
}

# Hero classes ------------------------------------------------------------ #
class HeroClass(Enum):
    WARRIOR = "Warrior"
    MAGE = "Mage"
    ARCHER = "Archer"
    HEALER = "Healer"
    ROGUE = "Rogue"

HERO_EMOJI: dict[HeroClass, str] = {
    HeroClass.WARRIOR: "⚔️",
    HeroClass.MAGE:    "🧙",
    HeroClass.ARCHER:  "🏹",
    HeroClass.HEALER:  "💚",
    HeroClass.ROGUE:   "🗡️",
}

class HeroState(Enum):
    IDLE = auto()
    MOVING = auto()
    ATTACKING = auto()
    CASTING = auto()
    DEAD = auto()

class AbilityKind(Enum):
    CLEAVE = "Cleave"
    SHIELD = "Shield Bash"
    FIREBALL = "Fireball"
    TELEPORT = "Teleport"
    MULTISHOT = "Multi-Shot"
    PIERCE = "Piercing Shot"
    HEAL = "Heal"
    BLESS = "Bless"
    BACKSTAB = "Backstab"
    VANISH = "Vanish"

ABILITY_EMOJI: dict[AbilityKind, str] = {
    AbilityKind.CLEAVE:     "💥",
    AbilityKind.SHIELD:     "🛡️",
    AbilityKind.FIREBALL:   "🔥",
    AbilityKind.TELEPORT:   "✨",
    AbilityKind.MULTISHOT:  "🎯",
    AbilityKind.PIERCE:     "➡️",
    AbilityKind.HEAL:       "💖",
    AbilityKind.BLESS:      "⭐",
    AbilityKind.BACKSTAB:   "🗡️",
    AbilityKind.VANISH:     "💨",
}

class Trait(Enum):
    STRONG = "Strong"
    FAST = "Fast"
    LAZY = "Lazy"
    BRAVE = "Brave"
    COWARDLY = "Cowardly"
    GREEDY = "Greedy"
    KIND = "Kind"

TRAIT_EMOJI: dict[Trait, str] = {
    Trait.STRONG:    "💪",
    Trait.FAST:      "⚡",
    Trait.LAZY:      "🦥",
    Trait.BRAVE:     "🦁",
    Trait.COWARDLY:  "🐔",
    Trait.GREEDY:    "💰",
    Trait.KIND:      "💖",
}

class JobKind(Enum):
    CHOP = auto()
    MINE = auto()
    BUILD_WALL = auto()
    BUILD_FLOOR = auto()
    BUILD_BED = auto()
    BUILD_WORKSHOP = auto()
    CRAFT_TOOL = auto()
    CRAFT_ARMOR = auto()

class ParticleKind(Enum):
    WOOD_CHIPS = auto()
    ROCK_DUST = auto()
    BLOOD = auto()
    SPARKS = auto()
    HEART = auto()
    FIRE = auto()
    MAGIC = auto()
    WEB = auto()
    GOLD = auto()

COL_BG        = (20, 22, 28)
COL_PANEL     = (35, 38, 48)
COL_TEXT      = (230, 230, 230)
COL_DIM       = (150, 155, 170)
COL_ACCENT    = (255, 200, 90)
COL_DESIGNATE = (255, 90, 90, 140)
COL_NIGHT     = (10, 14, 40)
COL_DANGER    = (255, 80, 80)
COL_GOOD      = (120, 220, 140)
COL_HERO      = (100, 180, 255)
COL_THREAT    = (255, 100, 50)

EMOJI_FONT_CANDIDATES = [
    "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji",
    "Twemoji Mozilla", "Symbola", "DejaVu Sans",
]

Pos = Tuple[int, int]


# --------------------------------------------------------------------------- #
# Abilities                                                                   #
# --------------------------------------------------------------------------- #
@dataclass
class Ability:
    kind: AbilityKind
    cooldown: float
    current_cd: float = 0.0
    mana_cost: int = 10
    range_tiles: float = 1.0
    aoe_radius: float = 0.0
    damage: float = 0.0
    heal_amount: float = 0.0

    @property
    def ready(self) -> bool:
        return self.current_cd <= 0.0

    def use(self) -> None:
        self.current_cd = self.cooldown

    def tick(self, dt: float) -> None:
        self.current_cd = max(0.0, self.current_cd - dt)


# --------------------------------------------------------------------------- #
# Hero                                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Hero:
    id: int
    x: float
    y: float
    name: str
    hero_class: HeroClass
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    hp: float = 100.0
    max_hp: float = 100.0
    mana: float = 50.0
    max_mana: float = 50.0
    attack: float = 15.0
    defense: float = 5.0
    speed: float = 3.0
    attack_range: float = 1.5
    state: HeroState = HeroState.IDLE
    alive: bool = True
    target: Optional[Pos] = None
    target_enemy: Optional[int] = None
    _path: list[Pos] = field(default_factory=list)
    attack_cd: float = 0.0
    abilities: list[Ability] = field(default_factory=list)
    selected: bool = False
    invisible: bool = False
    invis_cd: float = 0.0
    buff_cd: float = 0.0
    attack_buff: float = 1.0

    def __post_init__(self) -> None:
        if self.hero_class == HeroClass.WARRIOR:
            self.abilities = [
                Ability(AbilityKind.CLEAVE, cooldown=5.0, mana_cost=15,
                        range_tiles=1.5, aoe_radius=1.5, damage=20.0),
                Ability(AbilityKind.SHIELD, cooldown=8.0, mana_cost=10,
                        range_tiles=1.5, damage=15.0),
            ]
            self.max_hp = 150.0; self.hp = 150.0
            self.attack = 20.0; self.defense = 10.0
            self.speed = 2.5; self.attack_range = 1.5
        elif self.hero_class == HeroClass.MAGE:
            self.abilities = [
                Ability(AbilityKind.FIREBALL, cooldown=6.0, mana_cost=25,
                        range_tiles=5.0, aoe_radius=1.5, damage=35.0),
                Ability(AbilityKind.TELEPORT, cooldown=10.0, mana_cost=20,
                        range_tiles=6.0),
            ]
            self.max_hp = 80.0; self.hp = 80.0
            self.max_mana = 100.0; self.mana = 100.0
            self.attack = 10.0; self.defense = 3.0
            self.speed = 2.8; self.attack_range = 5.0
        elif self.hero_class == HeroClass.ARCHER:
            self.abilities = [
                Ability(AbilityKind.MULTISHOT, cooldown=4.0, mana_cost=15,
                        range_tiles=6.0, damage=12.0),
                Ability(AbilityKind.PIERCE, cooldown=7.0, mana_cost=20,
                        range_tiles=7.0, damage=40.0),
            ]
            self.max_hp = 90.0; self.hp = 90.0
            self.max_mana = 70.0; self.mana = 70.0
            self.attack = 18.0; self.defense = 4.0
            self.speed = 3.2; self.attack_range = 6.0
        elif self.hero_class == HeroClass.HEALER:
            self.abilities = [
                Ability(AbilityKind.HEAL, cooldown=5.0, mana_cost=20,
                        range_tiles=4.0, heal_amount=40.0),
                Ability(AbilityKind.BLESS, cooldown=12.0, mana_cost=30,
                        range_tiles=4.0),
            ]
            self.max_hp = 70.0; self.hp = 70.0
            self.max_mana = 120.0; self.mana = 120.0
            self.attack = 8.0; self.defense = 2.0
            self.speed = 2.6; self.attack_range = 4.0
        elif self.hero_class == HeroClass.ROGUE:
            self.abilities = [
                Ability(AbilityKind.BACKSTAB, cooldown=6.0, mana_cost=15,
                        range_tiles=1.5, damage=50.0),
                Ability(AbilityKind.VANISH, cooldown=15.0, mana_cost=25),
            ]
            self.max_hp = 85.0; self.hp = 85.0
            self.max_mana = 80.0; self.mana = 80.0
            self.attack = 22.0; self.defense = 5.0
            self.speed = 3.8; self.attack_range = 1.5

    @property
    def tile_pos(self) -> Pos:
        return int(self.x), int(self.y)

    def gain_xp(self, amount: int) -> None:
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            self.max_hp += 10; self.hp = self.max_hp
            self.max_mana += 5; self.mana = self.max_mana
            self.attack += 2; self.defense += 1

    def tick(self, dt: float) -> None:
        self.mana = min(self.max_mana, self.mana + dt * 2)
        for ab in self.abilities:
            ab.tick(dt)
        if self.invisible:
            self.invis_cd -= dt
            if self.invis_cd <= 0:
                self.invisible = False
        if self.attack_buff > 1.0:
            self.buff_cd -= dt
            if self.buff_cd <= 0:
                self.attack_buff = 1.0


# --------------------------------------------------------------------------- #
# Creature (replaces Goblin)                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class Creature:
    id: int
    kind: CreatureKind
    x: float
    y: float
    hp: float
    max_hp: float
    damage: float
    speed: float
    attack_range: float
    flying: bool
    regen: float
    xp_reward: int
    attack_cd: float = 0.0
    _path: list[Pos] = field(default_factory=list)
    # Special ability cooldowns
    fire_cd: float = 0.0
    teleport_cd: float = 0.0
    # For slimes
    size: float = 1.0  # 1.0 = normal, 0.5 = small

    @property
    def tile_pos(self) -> Pos:
        return int(self.x), int(self.y)

    @classmethod
    def create(cls, kind: CreatureKind, x: float, y: float, id: int,
               size: float = 1.0) -> Creature:
        stats = CREATURE_STATS[kind]
        hp = stats["hp"] * size
        return cls(
            id=id, kind=kind, x=x, y=y,
            hp=hp, max_hp=hp,
            damage=stats["damage"] * size,
            speed=stats["speed"],
            attack_range=stats["range"],
            flying=stats["flying"],
            regen=stats["regen"] * size,
            xp_reward=int(stats["xp_reward"] * size),
            size=size,
        )


# --------------------------------------------------------------------------- #
# Loot                                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Loot:
    x: float
    y: float
    kind: str  # "food", "wood", "stone", "gold"
    amount: int
    age: float = 0.0
    ttl: float = 30.0  # despawn after 30 seconds

    @property
    def alive(self) -> bool:
        return self.age < self.ttl


# --------------------------------------------------------------------------- #
# D* Lite (unchanged)                                                         #
# --------------------------------------------------------------------------- #
class DStarLite:
    def __init__(self, get_successors: Callable[[Pos], List[Tuple[Pos, float]]],
                 heuristic: Callable[[Pos, Pos], float]):
        self.get_successors = get_successors
        self.heuristic = heuristic
        self.goal: Optional[Pos] = None
        self.start: Optional[Pos] = None
        self.km: float = 0.0
        self.g: Dict[Pos, float] = defaultdict(lambda: float('inf'))
        self.rhs: Dict[Pos, float] = defaultdict(lambda: float('inf'))
        self.U: List[Tuple[Tuple[float, float], int, Pos]] = []
        self._counter: int = 0

    def _calculate_key(self, s: Pos) -> Tuple[float, float]:
        if self.start is None:
            return (float('inf'), float('inf'))
        min_gr = min(self.g[s], self.rhs[s])
        return (min_gr + self.heuristic(s, self.start) + self.km, min_gr)

    def _insert(self, s: Pos) -> None:
        key = self._calculate_key(s)
        self._counter += 1
        heapq.heappush(self.U, (key, self._counter, s))

    def initialize(self, goal: Pos, start: Pos) -> None:
        self.goal = goal; self.start = start
        self.km = 0.0; self.g.clear(); self.rhs.clear()
        self.U.clear(); self._counter = 0
        self.rhs[goal] = 0.0; self._insert(goal)

    def update_vertex(self, u: Pos) -> None:
        if u != self.goal:
            best = float('inf')
            for s, cost in self.get_successors(u):
                val = self.g[s] + cost
                if val < best:
                    best = val
            self.rhs[u] = best
        if self.g[u] != self.rhs[u]:
            self._insert(u)

    def compute_shortest_path(self) -> None:
        while self.U:
            key_tuple, _, u = heapq.heappop(self.U)
            current_key = self._calculate_key(u)
            if key_tuple < current_key:
                continue
            k_old = key_tuple
            if self.start is not None:
                start_key = self._calculate_key(self.start)
                if k_old >= start_key and self.g[self.start] == self.rhs[self.start]:
                    self._insert(u); break
            if self.g[u] > self.rhs[u]:
                self.g[u] = self.rhs[u]
                for pred, _ in self.get_successors(u):
                    self.update_vertex(pred)
            else:
                self.g[u] = float('inf')
                self.update_vertex(u)
                for pred, _ in self.get_successors(u):
                    self.update_vertex(pred)

    def get_path(self, start: Pos, goal: Pos) -> List[Pos]:
        if self.goal != goal:
            self.initialize(goal, start)
            self.compute_shortest_path()
        elif self.start != start:
            old_start = self.start; self.start = start
            self.km += self.heuristic(old_start, start)
            self.compute_shortest_path()
        if self.g[start] == float('inf'):
            return []
        path = [start]; current = start; visited = {start}
        while current != goal:
            if self.rhs[current] == float('inf'):
                return []
            best_next = None; best_val = float('inf')
            for s, cost in self.get_successors(current):
                val = self.g[s] + cost
                if val < best_val:
                    best_val = val; best_next = s
            if best_next is None or best_next in visited:
                return []
            visited.add(best_next); path.append(best_next)
            current = best_next
            if len(path) > 1000:
                return []
        return path

    def notify_change(self, changed_pos: Pos) -> None:
        if self.goal is None:
            return
        self.update_vertex(changed_pos)
        for neighbor, _ in self.get_successors(changed_pos):
            self.update_vertex(neighbor)
        self.compute_shortest_path()


class Pathfinder:
    def __init__(self, world):
        self.world = world
        self.cache: Dict[Pos, DStarLite] = {}
        self.stats = {"queries": 0, "hits": 0, "misses": 0}

    def _get_successors(self, pos: Pos) -> List[Tuple[Pos, float]]:
        x, y = pos
        successors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if not self.world.in_bounds(nx, ny):
                continue
            tile = self.world.tiles[ny][nx]
            if not tile.walkable and (nx, ny) != self.world._current_goal:
                continue
            cost = 1.0 + self.world.rng.random() * 0.05
            # Web tiles slow movement
            if tile.kind == TileKind.WEB:
                cost *= 2.0
            successors.append(((nx, ny), cost))
        return successors

    def _heuristic(self, pos: Pos, goal: Pos) -> float:
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def get_path(self, start: Pos, goal: Pos) -> List[Pos]:
        self.stats["queries"] += 1
        self.world._current_goal = goal
        if goal not in self.cache:
            self.cache[goal] = DStarLite(self._get_successors, self._heuristic)
            self.stats["misses"] += 1
        else:
            self.stats["hits"] += 1
        dsl = self.cache[goal]
        path = dsl.get_path(start, goal)
        self.world._current_goal = None
        return path

    def notify_change(self, pos: Pos) -> None:
        for dsl in self.cache.values():
            dsl.notify_change(pos)


# --------------------------------------------------------------------------- #
# Data                                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Tile:
    kind: TileKind
    designation: Optional[JobKind] = None
    web_age: float = 0.0  # for web decay

    @property
    def walkable(self) -> bool:
        return self.kind not in TILE_SOLID


@dataclass
class Job:
    kind: JobKind
    pos: tuple[int, int]
    assigned: Optional[int] = None
    progress: float = 0.0
    required: float = 1.0

    @property
    def done(self) -> bool:
        return self.progress >= self.required


@dataclass
class Skills:
    mining: float = 0.0
    woodcutting: float = 0.0
    combat: float = 0.0
    building: float = 0.0
    crafting: float = 0.0

    def gain(self, skill: str, amount: float) -> None:
        cur = getattr(self, skill)
        setattr(self, skill, min(100.0, cur + amount))


@dataclass
class Dwarf:
    id: int
    x: float
    y: float
    name: str
    trait: Trait
    state: DwarfState = DwarfState.IDLE
    hunger: float = 0.0
    energy: float = 100.0
    mood: float = 70.0
    hp: float = 100.0
    max_hp: float = 100.0
    age_days: int = 0
    alive: bool = True
    carrying: Optional[str] = None
    target: Optional[tuple[int, int]] = None
    job: Optional[Job] = None
    think_cd: float = 0.0
    skills: Skills = field(default_factory=Skills)
    bed_pos: Optional[tuple[int, int]] = None
    _path: list[tuple[int, int]] = field(default_factory=list)
    attack_cd: float = 0.0

    @property
    def tile_pos(self) -> tuple[int, int]:
        return int(self.x), int(self.y)

    @property
    def speed_mult(self) -> float:
        m = 1.0
        if self.trait == Trait.FAST:    m *= 1.4
        if self.trait == Trait.LAZY:    m *= 0.7
        return m

    @property
    def strength_mult(self) -> float:
        return 1.5 if self.trait == Trait.STRONG else 1.0


@dataclass
class Inventory:
    wood: int = 0
    stone: int = 0
    food: int = 20
    tools: int = 0
    armor: int = 0
    gold: int = 0


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    kind: ParticleKind
    life: float
    max_life: float
    emoji: str

    @property
    def alive(self) -> bool:
        return self.life > 0


@dataclass
class Message:
    text: str
    age: float = 0.0
    ttl: float = 8.0


# --------------------------------------------------------------------------- #
# World                                                                       #
# --------------------------------------------------------------------------- #
class World:
    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.w = width
        self.h = height
        self.rng = random.Random(seed)
        self.seed = seed if seed is not None else self.rng.randint(0, 10**9)
        self.tiles: list[list[Tile]] = [
            [Tile(TileKind.GRASS) for _ in range(width)] for _ in range(height)
        ]
        self.jobs: list[Job] = []
        self.dwarves: list[Dwarf] = []
        self.heroes: list[Hero] = []
        self.creatures: list[Creature] = []
        self.loot: list[Loot] = []
        self.particles: list[Particle] = []
        self.inv = Inventory()
        self.messages: list[Message] = []
        self.day_time: float = DAY_LENGTH * 0.25
        self.day: int = 1
        self.next_creature_id = 0
        self.next_dwarf_id = 0
        self.next_hero_id = 0
        self.raid_cooldown: float = DAY_LENGTH * 1.2
        self.total_deaths: int = 0
        self.total_kills: int = 0
        self.threat_level: int = 1
        self.bestiary: dict[CreatureKind, int] = {}  # kind -> kill count
        self._current_goal: Optional[Pos] = None
        self.pathfinder = Pathfinder(self)
        self._generate()
        self._spawn_dwarves(6)
        self._spawn_heroes()

    def _generate(self) -> None:
        for _ in range(6):
            cx, cy = self.rng.randrange(self.w), self.rng.randrange(self.h)
            for _ in range(60):
                x = max(0, min(self.w - 1, cx + self.rng.randint(-4, 4)))
                y = max(0, min(self.h - 1, cy + self.rng.randint(-4, 4)))
                self.tiles[y][x].kind = TileKind.DIRT
                cx, cy = x, y
        for _ in range(14):
            cx, cy = self.rng.randrange(self.w), self.rng.randrange(self.h)
            for _ in range(25):
                x = max(0, min(self.w - 1, cx + self.rng.randint(-3, 3)))
                y = max(0, min(self.h - 1, cy + self.rng.randint(-3, 3)))
                if self.tiles[y][x].kind in (TileKind.GRASS, TileKind.DIRT):
                    self.tiles[y][x].kind = TileKind.TREE
        for _ in range(8):
            cx, cy = self.rng.randrange(self.w), self.rng.randrange(self.h)
            for _ in range(18):
                x = max(0, min(self.w - 1, cx + self.rng.randint(-2, 2)))
                y = max(0, min(self.h - 1, cy + self.rng.randint(-2, 2)))
                if self.tiles[y][x].kind in (TileKind.GRASS, TileKind.DIRT):
                    self.tiles[y][x].kind = TileKind.STONE
        cx, cy = self.rng.randrange(10, self.w - 10), self.rng.randrange(10, self.h - 10)
        for dy in range(-3, 4):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 12:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.w and 0 <= y < self.h:
                        self.tiles[y][x].kind = TileKind.WATER
        cx, cy = self.w // 2, self.h // 2
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                x, y = cx + dx, cy + dy
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.tiles[y][x].kind = TileKind.GRASS
        self.tiles[cy][cx].kind = TileKind.STOCKPILE
        self.log("Welcome to Emoji Fortress. Your heroes have arrived!")

    def _spawn_dwarves(self, n: int) -> None:
        cx, cy = self.w // 2, self.h // 2
        names = ["Urist", "Kel", "Morn", "Zasit", "Doren", "Vok",
                 "Thikut", "Linar", "Rem", "Kas", "Esh", "Bor"]
        for i in range(n):
            trait = self.rng.choice(list(Trait))
            self.dwarves.append(Dwarf(
                id=self.next_dwarf_id,
                x=float(cx + self.rng.randint(-2, 2)),
                y=float(cy + self.rng.randint(-2, 2)),
                name=self.rng.choice(names) + str(self.next_dwarf_id),
                trait=trait,
            ))
            self.next_dwarf_id += 1

    def _spawn_heroes(self) -> None:
        cx, cy = self.w // 2, self.h // 2
        hero_names = ["Arthas", "Gandalf", "Legolas", "Elara", "Shadow"]
        for i, hclass in enumerate(HeroClass):
            self.heroes.append(Hero(
                id=self.next_hero_id,
                x=float(cx + self.rng.randint(-3, 3)),
                y=float(cy + self.rng.randint(-3, 3)),
                name=hero_names[i],
                hero_class=hclass,
            ))
            self.next_hero_id += 1

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def tile_at(self, x: int, y: int) -> Optional[Tile]:
        if self.in_bounds(x, y):
            return self.tiles[y][x]
        return None

    def log(self, text: str) -> None:
        self.messages.append(Message(text))
        if len(self.messages) > 60:
            self.messages.pop(0)

    def add_job(self, kind: JobKind, x: int, y: int) -> None:
        for j in self.jobs:
            if j.pos == (x, y):
                return
        self.jobs.append(Job(kind=kind, pos=(x, y)))
        self.tiles[y][x].designation = kind

    def cancel_job(self, x: int, y: int) -> None:
        self.jobs = [j for j in self.jobs if j.pos != (x, y)]
        t = self.tile_at(x, y)
        if t is not None:
            t.designation = None

    def find_path(self, sx: int, sy: int, gx: int, gy: int) -> list[tuple[int, int]]:
        if not self.in_bounds(gx, gy) or not self.tiles[gy][gx].walkable:
            return []
        return self.pathfinder.get_path((sx, sy), (gx, gy))

    def _notify_tile_change(self, x: int, y: int) -> None:
        self.pathfinder.notify_change((x, y))

    def spawn_particles(self, x: float, y: float, kind: ParticleKind,
                        count: int = 5) -> None:
        import math
        emoji_map = {
            ParticleKind.WOOD_CHIPS: "🟫",
            ParticleKind.ROCK_DUST:  "⚪",
            ParticleKind.BLOOD:      "🩸",
            ParticleKind.SPARKS:     "✨",
            ParticleKind.HEART:      "💖",
            ParticleKind.FIRE:       "🔥",
            ParticleKind.MAGIC:      "✨",
            ParticleKind.WEB:        "🕸️",
            ParticleKind.GOLD:       "💰",
        }
        for _ in range(count):
            angle = self.rng.random() * 6.283
            speed = self.rng.uniform(20, 80)
            self.particles.append(Particle(
                x=x, y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - 30,
                kind=kind,
                life=self.rng.uniform(0.4, 0.9),
                max_life=0.9,
                emoji=emoji_map[kind],
            ))

    def tick(self, dt: float) -> None:
        self.day_time += dt
        if self.day_time >= DAY_LENGTH:
            self.day_time -= DAY_LENGTH
            self.day += 1
            self.threat_level = min(10, 1 + self.day // 2)
            for d in self.dwarves:
                if d.alive:
                    d.age_days += 1
            self.log(f"Day {self.day} begins. Threat level: {self.threat_level}")
            needed = len([d for d in self.dwarves if d.alive])
            if self.inv.food >= needed:
                self.inv.food -= needed
            else:
                self.log("⚠️ Not enough food! Dwarves grow hungry.")
            # Skeletons rise from tombstones at night
            if self.day >= 3:
                self._spawn_skeletons()

        for m in self.messages:
            m.age += dt
        self.messages = [m for m in self.messages if m.age < m.ttl]

        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 200 * dt
        self.particles = [p for p in self.particles if p.alive]

        # Web decay
        for y in range(self.h):
            for x in range(self.w):
                t = self.tiles[y][x]
                if t.kind == TileKind.WEB:
                    t.web_age += dt
                    if t.web_age > 20.0:  # webs last 20 seconds
                        t.kind = TileKind.GRASS
                        t.web_age = 0.0
                        self._notify_tile_change(x, y)

        # Loot decay
        for l in self.loot:
            l.age += dt
        self.loot = [l for l in self.loot if l.alive]

        for d in self.dwarves:
            if d.alive:
                self._update_dwarf(d, dt)

        for h in self.heroes:
            if h.alive:
                self._update_hero(h, dt)

        self.raid_cooldown -= dt
        if self.raid_cooldown <= 0:
            self._spawn_raid()
            self.raid_cooldown = DAY_LENGTH * self.rng.uniform(0.8, 1.5)
        for c in list(self.creatures):
            self._update_creature(c, dt)

    def _spawn_skeletons(self) -> None:
        """Spawn skeletons from tombstones at night."""
        is_night = self.day_time > DAY_LENGTH * 0.75 or self.day_time < DAY_LENGTH * 0.2
        if not is_night:
            return
        for y in range(self.h):
            for x in range(self.w):
                if self.tiles[y][x].kind == TileKind.TOMBSTONE:
                    if self.rng.random() < 0.1:  # 10% chance per tombstone
                        c = Creature.create(CreatureKind.SKELETON, float(x), float(y),
                                           self.next_creature_id)
                        self.creatures.append(c)
                        self.next_creature_id += 1
                        self.log("💀 A skeleton rises from a tombstone!")

    def _update_hero(self, h: Hero, dt: float) -> None:
        h.tick(dt)
        if h.hp <= 0:
            h.alive = False; h.state = HeroState.DEAD
            self.total_deaths += 1
            self.log(f"💀 Hero {h.name} has fallen!")
            return
        if h.state == HeroState.MOVING:
            self._move_hero(h, dt)
        elif h.state == HeroState.ATTACKING:
            self._hero_attack(h, dt)

    def _move_hero(self, h: Hero, dt: float) -> None:
        if h.target is None:
            h.state = HeroState.IDLE; return
        tx, ty = h.target
        if abs(h.x - tx) < 0.1 and abs(h.y - ty) < 0.1:
            h.x, h.y = float(tx), float(ty)
            h.state = HeroState.IDLE; h.target = None; return
        if not h._path:
            path = self.find_path(int(h.x), int(h.y), tx, ty)
            h._path = path[1:] if path else []
            if not h._path:
                h.state = HeroState.IDLE; return
        nx, ny = h._path[0]
        speed = h.speed
        # Check if on web
        t = self.tile_at(int(h.x), int(h.y))
        if t and t.kind == TileKind.WEB:
            speed *= 0.5
        dx = nx - h.x; dy = ny - h.y
        dist = (dx * dx + dy * dy) ** 0.5 or 1.0
        step = speed * dt
        if step >= dist:
            h.x, h.y = float(nx), float(ny); h._path.pop(0)
        else:
            h.x += dx / dist * step; h.y += dy / dist * step

    def _hero_attack(self, h: Hero, dt: float) -> None:
        if h.target_enemy is None:
            h.state = HeroState.IDLE; return
        c = next((c for c in self.creatures if c.id == h.target_enemy), None)
        if c is None:
            h.state = HeroState.IDLE; return
        dx = c.x - h.x; dy = c.y - h.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > h.attack_range:
            h.target = (int(c.x), int(c.y)); h.state = HeroState.MOVING; return
        h.attack_cd -= dt
        if h.attack_cd <= 0:
            dmg = h.attack * h.attack_buff
            c.hp -= dmg
            self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.BLOOD, 2)
            h.attack_cd = 1.0
            if c.hp <= 0:
                self._kill_creature(c, h)
                h.state = HeroState.IDLE

    def use_ability(self, h: Hero, ability_idx: int, target_pos: Optional[Pos] = None) -> bool:
        if ability_idx >= len(h.abilities):
            return False
        ab = h.abilities[ability_idx]
        if not ab.ready or h.mana < ab.mana_cost:
            return False
        h.mana -= ab.mana_cost; ab.use()
        self._execute_ability(h, ab, target_pos)
        return True

    def _execute_ability(self, h: Hero, ab: Ability, target_pos: Optional[Pos]) -> None:
        if ab.kind == AbilityKind.CLEAVE:
            for c in list(self.creatures):
                dx = c.x - h.x; dy = c.y - h.y
                if dx * dx + dy * dy <= ab.aoe_radius * ab.aoe_radius:
                    c.hp -= ab.damage
                    self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.SPARKS, 3)
                    if c.hp <= 0:
                        self._kill_creature(c, h)
            self.spawn_particles(h.x + 0.5, h.y + 0.5, ParticleKind.SPARKS, 8)
            self.log(f"💥 {h.name} uses Cleave!")
        elif ab.kind == AbilityKind.SHIELD:
            nearby = self._nearest_creature(h.x, h.y, ab.range_tiles)
            if nearby:
                nearby.hp -= ab.damage
                self.spawn_particles(nearby.x + 0.5, nearby.y + 0.5, ParticleKind.SPARKS, 4)
                if nearby.hp <= 0:
                    self._kill_creature(nearby, h)
            self.log(f"🛡️ {h.name} uses Shield Bash!")
        elif ab.kind == AbilityKind.FIREBALL:
            if target_pos:
                tx, ty = target_pos
                for c in list(self.creatures):
                    dx = c.x - tx; dy = c.y - ty
                    if dx * dx + dy * dy <= ab.aoe_radius * ab.aoe_radius:
                        c.hp -= ab.damage
                        self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.FIRE, 5)
                        if c.hp <= 0:
                            self._kill_creature(c, h)
                self.spawn_particles(tx + 0.5, ty + 0.5, ParticleKind.FIRE, 10)
                self.log(f"🔥 {h.name} casts Fireball!")
        elif ab.kind == AbilityKind.TELEPORT:
            if target_pos:
                tx, ty = target_pos
                if self.in_bounds(tx, ty) and self.tiles[ty][tx].walkable:
                    h.x, h.y = float(tx), float(ty)
                    self.spawn_particles(h.x + 0.5, h.y + 0.5, ParticleKind.MAGIC, 8)
                    self.log(f"✨ {h.name} teleports!")
        elif ab.kind == AbilityKind.MULTISHOT:
            targets = sorted(self.creatures, key=lambda c: (c.x - h.x)**2 + (c.y - h.y)**2)[:3]
            for c in targets:
                dx = c.x - h.x; dy = c.y - h.y
                if dx * dx + dy * dy <= ab.range_tiles * ab.range_tiles:
                    c.hp -= ab.damage
                    self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.BLOOD, 2)
                    if c.hp <= 0:
                        self._kill_creature(c, h)
            self.log(f"🎯 {h.name} uses Multi-Shot!")
        elif ab.kind == AbilityKind.PIERCE:
            target = self._nearest_creature(h.x, h.y, ab.range_tiles)
            if target:
                target.hp -= ab.damage
                self.spawn_particles(target.x + 0.5, target.y + 0.5, ParticleKind.BLOOD, 4)
                if target.hp <= 0:
                    self._kill_creature(target, h)
            self.log(f"➡️ {h.name} uses Piercing Shot!")
        elif ab.kind == AbilityKind.HEAL:
            allies = [a for a in self.heroes + self.dwarves if getattr(a, "alive", True) and a is not h]
            if allies:
                target = min(allies, key=lambda a: a.hp / a.max_hp)
                if (target.x - h.x)**2 + (target.y - h.y)**2 <= ab.range_tiles**2:
                    target.hp = min(target.max_hp, target.hp + ab.heal_amount)
                    self.spawn_particles(target.x + 0.5, target.y + 0.5, ParticleKind.HEART, 6)
                    self.log(f"💖 {h.name} heals {target.name}!")
        elif ab.kind == AbilityKind.BLESS:
            allies = [a for a in self.heroes + self.dwarves if getattr(a, "alive", True) and a is not h]
            if allies:
                target = min(allies, key=lambda a: (a.x - h.x)**2 + (a.y - h.y)**2)
                if (target.x - h.x)**2 + (target.y - h.y)**2 <= ab.range_tiles**2:
                    if hasattr(target, "attack_buff"):
                        target.attack_buff = 1.8
                        target.buff_cd = 10.0
                    self.spawn_particles(target.x + 0.5, target.y + 0.5, ParticleKind.MAGIC, 6)
                    self.log(f"⭐ {h.name} blesses {target.name}!")
        elif ab.kind == AbilityKind.BACKSTAB:
            target = self._nearest_creature(h.x, h.y, ab.range_tiles)
            if target:
                target.hp -= ab.damage
                self.spawn_particles(target.x + 0.5, target.y + 0.5, ParticleKind.BLOOD, 5)
                if target.hp <= 0:
                    self._kill_creature(target, h)
            self.log(f"🗡️ {h.name} backstabs!")
        elif ab.kind == AbilityKind.VANISH:
            h.invisible = True
            h.invis_cd = 5.0
            self.spawn_particles(h.x + 0.5, h.y + 0.5, ParticleKind.MAGIC, 6)
            self.log(f"💨 {h.name} vanishes!")

    def _nearest_creature(self, x: float, y: float, range_tiles: float) -> Optional[Creature]:
        best: Optional[Creature] = None
        best_d2 = range_tiles * range_tiles
        for c in self.creatures:
            dx = c.x - x; dy = c.y - y
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2; best = c
        return best

    def _update_dwarf(self, d: Dwarf, dt: float) -> None:
        d.hunger = min(100.0, d.hunger + dt * 0.6)
        d.energy = max(0.0, d.energy - dt * 0.4)
        d.think_cd -= dt

        if d.hunger >= 100.0:
            self._kill_dwarf(d, "starvation")
            return
        if d.hp <= 0:
            self._kill_dwarf(d, "wounds")
            return

        is_night = self.day_time > DAY_LENGTH * 0.75 or self.day_time < DAY_LENGTH * 0.2

        nearby_creature = self._nearest_creature(d.x, d.y, range_tiles=2)
        if nearby_creature is not None and d.state != DwarfState.FIGHTING:
            d.state = DwarfState.FIGHTING
            d.target = (int(nearby_creature.x), int(nearby_creature.y))
            return

        if is_night and d.energy < 60 and d.state not in (DwarfState.SLEEPING,):
            self._send_to_bed(d)
            return

        if d.hunger > 70 and self.inv.food > 0 and d.state not in (DwarfState.EATING,):
            d.state = DwarfState.EATING
            d.target = (int(d.x), int(d.y))
            return

        if d.state == DwarfState.IDLE:
            if d.think_cd > 0:
                return
            d.think_cd = 0.5
            self._assign_work(d)
        elif d.state == DwarfState.MOVING:
            self._move_toward(d, dt)
        elif d.state in (DwarfState.CHOPPING, DwarfState.MINING):
            if d.job is None:
                d.state = DwarfState.IDLE
                return
            speed = 1.0 + d.skills.woodcutting * 0.01
            d.job.progress += dt * speed * d.strength_mult
            if self.rng.random() < dt * 3:
                kind = (ParticleKind.WOOD_CHIPS if d.state == DwarfState.CHOPPING
                        else ParticleKind.ROCK_DUST)
                self.spawn_particles(d.x + 0.5, d.y + 0.5, kind, 2)
            if d.job.done:
                self._complete_job(d)
        elif d.state == DwarfState.HAULING:
            self._move_toward(d, dt)
            if d.target and (int(d.x), int(d.y)) == d.target:
                if d.carrying == "wood":
                    self.inv.wood += 1
                elif d.carrying == "stone":
                    self.inv.stone += 1
                d.carrying = None
                d.state = DwarfState.IDLE
        elif d.state == DwarfState.EATING:
            if self.inv.food > 0:
                self.inv.food -= 1
                d.hunger = 0.0
                d.energy = min(100.0, d.energy + 10)
                d.mood = min(100.0, d.mood + 5)
                self.spawn_particles(d.x + 0.5, d.y + 0.5, ParticleKind.HEART, 3)
            d.state = DwarfState.IDLE
        elif d.state == DwarfState.SLEEPING:
            d.energy = min(100.0, d.energy + dt * 10)
            if d.energy >= 95 or not is_night:
                d.state = DwarfState.IDLE
        elif d.state == DwarfState.FIGHTING:
            self._fight(d, dt)
        elif d.state == DwarfState.CRAFTING:
            if d.job is None:
                d.state = DwarfState.IDLE
                return
            d.job.progress += dt * (1.0 + d.skills.crafting * 0.01)
            if self.rng.random() < dt * 4:
                self.spawn_particles(d.x + 0.5, d.y + 0.5, ParticleKind.SPARKS, 2)
            if d.job.done:
                self._complete_craft(d)
        elif d.state in (DwarfState.BUILDING_BED, DwarfState.BUILDING_WORKSHOP):
            if d.job is None:
                d.state = DwarfState.IDLE
                return
            d.job.progress += dt * (1.0 + d.skills.building * 0.01)
            if d.job.done:
                self._complete_build(d)

    def _assign_work(self, d: Dwarf) -> None:
        for j in self.jobs:
            if j.assigned is not None:
                continue
            if j.kind in (JobKind.CRAFT_TOOL, JobKind.CRAFT_ARMOR):
                j.assigned = d.id
                d.job = j
                d.target = j.pos
                d.state = DwarfState.MOVING
                return
        for j in self.jobs:
            if j.assigned is not None:
                continue
            if j.kind in (JobKind.BUILD_BED, JobKind.BUILD_WORKSHOP,
                          JobKind.BUILD_WALL, JobKind.BUILD_FLOOR):
                j.assigned = d.id
                d.job = j
                d.target = j.pos
                d.state = DwarfState.MOVING
                return
        for j in self.jobs:
            if j.assigned is not None:
                continue
            j.assigned = d.id
            d.job = j
            d.target = j.pos
            d.state = DwarfState.MOVING
            return
        dx = self.rng.randint(-3, 3)
        dy = self.rng.randint(-3, 3)
        nx = max(0, min(self.w - 1, int(d.x) + dx))
        ny = max(0, min(self.h - 1, int(d.y) + dy))
        if self.tiles[ny][nx].walkable:
            d.target = (nx, ny)
            d.state = DwarfState.MOVING

    def _send_to_bed(self, d: Dwarf) -> None:
        if d.bed_pos is not None:
            t = self.tile_at(*d.bed_pos)
            if t is not None and t.kind == TileKind.BED:
                d.target = d.bed_pos
                d.state = DwarfState.SLEEPING
                return
        for y in range(self.h):
            for x in range(self.w):
                if self.tiles[y][x].kind == TileKind.BED:
                    owned = any(dw.bed_pos == (x, y) and dw is not d
                                for dw in self.dwarves)
                    if not owned:
                        d.bed_pos = (x, y)
                        d.target = (x, y)
                        d.state = DwarfState.SLEEPING
                        return
        cx, cy = self.w // 2, self.h // 2
        d.target = (cx, cy)
        d.state = DwarfState.SLEEPING
        d.mood = max(0.0, d.mood - 2)

    def _move_toward(self, d: Dwarf, dt: float) -> None:
        if d.target is None:
            d.state = DwarfState.IDLE
            return
        tx, ty = d.target
        if abs(d.x - tx) < 0.1 and abs(d.y - ty) < 0.1:
            d.x, d.y = float(tx), float(ty)
            self._on_arrived(d)
            return
        if not d._path:
            path = self.find_path(int(d.x), int(d.y), tx, ty)
            d._path = path[1:] if path else []
            if not d._path:
                d.state = DwarfState.IDLE
                return
        nx, ny = d._path[0]
        speed = 2.5 * d.speed_mult
        # Check if on web
        t = self.tile_at(int(d.x), int(d.y))
        if t and t.kind == TileKind.WEB:
            speed *= 0.5
        dx = nx - d.x
        dy = ny - d.y
        dist = (dx * dx + dy * dy) ** 0.5 or 1.0
        step = speed * dt
        if step >= dist:
            d.x, d.y = float(nx), float(ny)
            d._path.pop(0)
        else:
            d.x += dx / dist * step
            d.y += dy / dist * step

    def _on_arrived(self, d: Dwarf) -> None:
        if d.job is not None:
            if d.job.kind == JobKind.CHOP:
                d.state = DwarfState.CHOPPING
            elif d.job.kind == JobKind.MINE:
                d.state = DwarfState.MINING
            elif d.job.kind in (JobKind.BUILD_WALL, JobKind.BUILD_FLOOR):
                d.state = DwarfState.BUILDING_BED
            elif d.job.kind == JobKind.BUILD_BED:
                d.state = DwarfState.BUILDING_BED
            elif d.job.kind == JobKind.BUILD_WORKSHOP:
                d.state = DwarfState.BUILDING_WORKSHOP
            elif d.job.kind in (JobKind.CRAFT_TOOL, JobKind.CRAFT_ARMOR):
                d.state = DwarfState.CRAFTING
            return
        d.state = DwarfState.IDLE

    def _complete_job(self, d: Dwarf) -> None:
        j = d.job
        assert j is not None
        tx, ty = j.pos
        t = self.tiles[ty][tx]
        if j.kind == JobKind.CHOP and t.kind == TileKind.TREE:
            t.kind = TileKind.GRASS
            d.carrying = "wood"
            d.skills.gain("woodcutting", 2.0)
            self._notify_tile_change(tx, ty)
        elif j.kind == JobKind.MINE and t.kind == TileKind.STONE:
            t.kind = TileKind.DIRT
            d.carrying = "stone"
            d.skills.gain("mining", 2.0)
            self._notify_tile_change(tx, ty)
        self.jobs = [x for x in self.jobs if x is not j]
        d.job = None
        d.target = (self.w // 2, self.h // 2)
        d.state = DwarfState.HAULING

    def _complete_build(self, d: Dwarf) -> None:
        j = d.job
        assert j is not None
        tx, ty = j.pos
        t = self.tiles[ty][tx]
        built = False
        if j.kind == JobKind.BUILD_WALL and self.inv.stone >= 1:
            self.inv.stone -= 1; t.kind = TileKind.WALL; built = True
        elif j.kind == JobKind.BUILD_FLOOR and self.inv.wood >= 1:
            self.inv.wood -= 1; t.kind = TileKind.FLOOR; built = True
        elif j.kind == JobKind.BUILD_BED and self.inv.wood >= 2:
            self.inv.wood -= 2; t.kind = TileKind.BED; built = True
        elif j.kind == JobKind.BUILD_WORKSHOP and self.inv.wood >= 3 and self.inv.stone >= 2:
            self.inv.wood -= 3; self.inv.stone -= 2; t.kind = TileKind.WORKSHOP; built = True
        if built:
            d.skills.gain("building", 3.0)
            self.spawn_particles(tx + 0.5, ty + 0.5, ParticleKind.SPARKS, 4)
            self._notify_tile_change(tx, ty)
        self.jobs = [x for x in self.jobs if x is not j]
        d.job = None
        d.state = DwarfState.IDLE

    def _complete_craft(self, d: Dwarf) -> None:
        j = d.job
        assert j is not None
        if j.kind == JobKind.CRAFT_TOOL and self.inv.wood >= 1 and self.inv.stone >= 1:
            self.inv.wood -= 1; self.inv.stone -= 1; self.inv.tools += 1
        elif j.kind == JobKind.CRAFT_ARMOR and self.inv.stone >= 3:
            self.inv.stone -= 3; self.inv.armor += 1
        d.skills.gain("crafting", 3.0)
        self.jobs = [x for x in self.jobs if x is not j]
        d.job = None
        d.state = DwarfState.IDLE

    def _fight(self, d: Dwarf, dt: float) -> None:
        c = self._nearest_creature(d.x, d.y, range_tiles=1.5)
        if c is None:
            d.state = DwarfState.IDLE
            return
        dx = c.x - d.x; dy = c.y - d.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > 1.0:
            d.target = (int(c.x), int(c.y))
            self._move_toward(d, dt)
            return
        d.attack_cd -= dt
        if d.attack_cd <= 0:
            dmg = 15 * d.strength_mult * (1 + d.skills.combat * 0.02)
            c.hp -= dmg
            d.skills.gain("combat", 1.5)
            self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.BLOOD, 3)
            d.attack_cd = 0.8
            if c.hp <= 0:
                self._kill_creature(c, None)
                d.mood = min(100.0, d.mood + 10)
                d.state = DwarfState.IDLE

    def _kill_dwarf(self, d: Dwarf, cause: str) -> None:
        d.alive = False
        d.state = DwarfState.DEAD
        self.total_deaths += 1
        tx, ty = int(d.x), int(d.y)
        if self.in_bounds(tx, ty):
            self.tiles[ty][tx].kind = TileKind.TOMBSTONE
            self._notify_tile_change(tx, ty)
        self.spawn_particles(d.x + 0.5, d.y + 0.5, ParticleKind.BLOOD, 8)
        self.log(f"💀 {d.name} died of {cause}.")

    def _spawn_raid(self) -> None:
        """Spawn raid based on threat level and day."""
        threat = self.threat_level
        # Determine creature composition based on threat
        possible_creatures = []
        if threat >= 1:
            possible_creatures.extend([CreatureKind.GOBLIN] * 3)
        if threat >= 2:
            possible_creatures.extend([CreatureKind.WOLF] * 2)
        if threat >= 3:
            possible_creatures.extend([CreatureKind.SPIDER] * 2)
        if threat >= 4:
            possible_creatures.extend([CreatureKind.BAT] * 2)
        if threat >= 5:
            possible_creatures.extend([CreatureKind.SKELETON] * 2)
        if threat >= 6:
            possible_creatures.extend([CreatureKind.SLIME] * 2)
        if threat >= 7:
            possible_creatures.extend([CreatureKind.TROLL])
        if threat >= 8:
            possible_creatures.extend([CreatureKind.DEMON])
        if threat >= 9 and self.day % 5 == 0:
            possible_creatures.append(CreatureKind.DRAGON)

        if not possible_creatures:
            possible_creatures = [CreatureKind.GOBLIN]

        count = min(8, 2 + threat // 2 + self.rng.randint(0, 2))
        edge = self.rng.choice(["n", "s", "e", "w"])
        
        raid_msg = []
        for _ in range(count):
            kind = self.rng.choice(possible_creatures)
            if edge == "n":
                x = self.rng.randint(0, self.w - 1); y = 0
            elif edge == "s":
                x = self.rng.randint(0, self.w - 1); y = self.h - 1
            elif edge == "e":
                x = self.w - 1; y = self.rng.randint(0, self.h - 1)
            else:
                x = 0; y = self.rng.randint(0, self.h - 1)
            
            c = Creature.create(kind, float(x), float(y), self.next_creature_id)
            self.creatures.append(c)
            self.next_creature_id += 1
            raid_msg.append(CREATURE_EMOJI[kind])
        
        self.log(f"⚠️ Raid! {count} creatures: {' '.join(raid_msg[:5])}...")

    def _update_creature(self, c: Creature, dt: float) -> None:
        """Update creature with type-specific behaviors."""
        # Regen
        if c.regen > 0:
            c.hp = min(c.max_hp, c.hp + c.regen * dt)
        
        # Special abilities
        if c.kind == CreatureKind.DRAGON:
            c.fire_cd -= dt
            if c.fire_cd <= 0:
                self._dragon_fire_breath(c)
                c.fire_cd = CREATURE_STATS[CreatureKind.DRAGON]["fire_breath_cd"]
        
        if c.kind == CreatureKind.DEMON:
            c.teleport_cd -= dt
            if c.teleport_cd <= 0 and self.rng.random() < 0.01:
                self._demon_teleport(c)
                c.teleport_cd = CREATURE_STATS[CreatureKind.DEMON]["teleport_cd"]
        
        # Spider leaves webs
        if c.kind == CreatureKind.SPIDER:
            if self.rng.random() < CREATURE_STATS[CreatureKind.SPIDER]["web_chance"] * dt:
                tx, ty = int(c.x), int(c.y)
                if self.in_bounds(tx, ty) and self.tiles[ty][tx].kind in (TileKind.GRASS, TileKind.DIRT):
                    self.tiles[ty][tx].kind = TileKind.WEB
                    self.tiles[ty][tx].web_age = 0.0
                    self._notify_tile_change(tx, ty)
        
        # Find target (prefer heroes, then dwarves)
        target = None
        best_d2 = float("inf")
        for h in self.heroes:
            if not h.alive or h.invisible:
                continue
            dx = h.x - c.x; dy = h.y - c.y
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2; target = h
        for d in self.dwarves:
            if not d.alive:
                continue
            dx = d.x - c.x; dy = d.y - c.y
            d2 = dx * dx + dy * dy
            if d2 < best_d2 * 0.7:
                best_d2 = d2; target = d
        
        if target is None:
            return
        
        dx = target.x - c.x; dy = target.y - c.y
        dist = (dx * dx + dy * dy) ** 0.5
        
        # Wolf pack bonus
        damage_mult = 1.0
        if c.kind == CreatureKind.WOLF:
            nearby_wolves = sum(1 for w in self.creatures 
                               if w.kind == CreatureKind.WOLF and w is not c
                               and (w.x - c.x)**2 + (w.y - c.y)**2 <= 4)
            damage_mult = 1.0 + nearby_wolves * 0.2
        
        if dist > c.attack_range:
            # Move toward target
            if c.flying:
                # Flying creatures ignore terrain
                speed = c.speed
                if dist > 0.1:
                    c.x += dx / dist * speed * dt
                    c.y += dy / dist * speed * dt
            else:
                # Ground creatures use pathfinding
                if not c._path or self.rng.random() < 0.05:
                    c._path = self.find_path(int(c.x), int(c.y),
                                            int(target.x), int(target.y))
                    c._path = c._path[1:] if c._path else []
                if c._path:
                    nx, ny = c._path[0]
                    speed = c.speed
                    # Check if on web
                    t = self.tile_at(int(c.x), int(c.y))
                    if t and t.kind == TileKind.WEB:
                        speed *= 0.5
                    sdx = nx - c.x; sdy = ny - c.y
                    sd = (sdx * sdx + sdy * sdy) ** 0.5 or 1.0
                    step = speed * dt
                    if step >= sd:
                        c.x, c.y = float(nx), float(ny)
                        c._path.pop(0)
                    else:
                        c.x += sdx / sd * step
                        c.y += sdy / sd * step
                else:
                    speed = c.speed * 0.8
                    if dist > 0.1:
                        c.x += dx / dist * speed * dt
                        c.y += dy / dist * speed * dt
        else:
            # Attack
            c.attack_cd -= dt
            if c.attack_cd <= 0:
                dmg = c.damage * damage_mult
                if hasattr(target, "defense"):
                    dmg = max(1, dmg - target.defense * 0.3)
                target.hp -= dmg
                self.spawn_particles(target.x + 0.5, target.y + 0.5,
                                    ParticleKind.BLOOD, 3)
                c.attack_cd = 1.2

    def _dragon_fire_breath(self, c: Creature) -> None:
        """Dragon fires breath in AoE."""
        radius = CREATURE_STATS[CreatureKind.DRAGON]["fire_breath_radius"]
        hit_something = False
        for h in self.heroes:
            if not h.alive or h.invisible:
                continue
            dx = h.x - c.x; dy = h.y - c.y
            if dx * dx + dy * dy <= radius * radius:
                h.hp -= c.damage * 0.7
                self.spawn_particles(h.x + 0.5, h.y + 0.5, ParticleKind.FIRE, 5)
                hit_something = True
        for d in self.dwarves:
            if not d.alive:
                continue
            dx = d.x - c.x; dy = d.y - c.y
            if dx * dx + dy * dy <= radius * radius:
                d.hp -= c.damage * 0.7
                self.spawn_particles(d.x + 0.5, d.y + 0.5, ParticleKind.FIRE, 5)
                hit_something = True
        if hit_something:
            self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.FIRE, 10)
            self.log(f"🔥 Dragon breathes fire!")

    def _demon_teleport(self, c: Creature) -> None:
        """Demon teleports near a target."""
        target = None
        best_d2 = float("inf")
        for h in self.heroes:
            if not h.alive or h.invisible:
                continue
            dx = h.x - c.x; dy = h.y - c.y
            d2 = dx * dx + dy * dy
            if d2 < best_d2 and d2 > 9:  # only teleport if far
                best_d2 = d2; target = h
        if target:
            # Teleport near target
            angle = self.rng.random() * 6.283
            dist = 2.0
            nx = target.x + dist * math.cos(angle)
            ny = target.y + dist * math.sin(angle)
            tx, ty = int(nx), int(ny)
            if self.in_bounds(tx, ty) and self.tiles[ty][tx].walkable:
                self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.MAGIC, 6)
                c.x, c.y = float(tx), float(ty)
                self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.MAGIC, 6)

    def _kill_creature(self, c: Creature, killer: Optional[Hero]) -> None:
        """Handle creature death: loot, XP, bestiary."""
        if c not in self.creatures:
            return
        self.creatures.remove(c)
        self.total_kills += 1
        
        # Update bestiary
        self.bestiary[c.kind] = self.bestiary.get(c.kind, 0) + 1
        
        # Grant XP to killer
        if killer:
            killer.gain_xp(c.xp_reward)
            self.log(f"⚔️ {killer.name} slew a {c.kind.value}!")
        
        # Drop loot
        stats = CREATURE_STATS[c.kind]
        for loot_kind, chance in stats["loot"]:
            if self.rng.random() < chance:
                amount = 1
                self.loot.append(Loot(c.x, c.y, loot_kind, amount))
                self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.GOLD, 3)
        
        # Slime splitting
        if c.kind == CreatureKind.SLIME and c.size > 0.6:
            if self.rng.random() < CREATURE_STATS[CreatureKind.SLIME]["split_chance"]:
                for _ in range(2):
                    offset_x = self.rng.uniform(-0.5, 0.5)
                    offset_y = self.rng.uniform(-0.5, 0.5)
                    small_slime = Creature.create(
                        CreatureKind.SLIME, c.x + offset_x, c.y + offset_y,
                        self.next_creature_id, size=0.5
                    )
                    self.creatures.append(small_slime)
                    self.next_creature_id += 1
                self.log("🟢 Slime splits!")
        
        self.spawn_particles(c.x + 0.5, c.y + 0.5, ParticleKind.BLOOD, 6)

    def _collect_loot(self, x: float, y: float) -> None:
        """Collect loot near position."""
        for l in list(self.loot):
            if (l.x - x)**2 + (l.y - y)**2 <= 1.0:
                if l.kind == "food":
                    self.inv.food += l.amount
                elif l.kind == "wood":
                    self.inv.wood += l.amount
                elif l.kind == "stone":
                    self.inv.stone += l.amount
                elif l.kind == "gold":
                    self.inv.gold += l.amount
                self.loot.remove(l)


# --------------------------------------------------------------------------- #
# Math helpers                                                                #
# --------------------------------------------------------------------------- #
def math_cos(x: float) -> float:
    import math
    return math.cos(x)

def math_sin(x: float) -> float:
    import math
    return math.sin(x)


# --------------------------------------------------------------------------- #
# Renderer                                                                    #
# --------------------------------------------------------------------------- #
class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.tile_font = self._load_emoji_font(TILE_SIZE)
        self.small_emoji_font = self._load_emoji_font(14)
        self.ui_font = pygame.font.SysFont("consolas,menlo,dejavu sans mono", 16)
        self.small_font = pygame.font.SysFont("consolas,menlo,dejavu sans mono", 13)
        self.tiny_font = pygame.font.SysFont("consolas,menlo,dejavu sans mono", 11)
        self._emoji_cache: dict[str, pygame.Surface] = {}
        self._small_emoji_cache: dict[str, pygame.Surface] = {}

    def _load_emoji_font(self, size: int) -> pygame.font.Font:
        for name in EMOJI_FONT_CANDIDATES:
            try:
                f = pygame.font.SysFont(name, size)
                surf = f.render("🌲", True, COL_TEXT)
                if surf.get_width() > 2:
                    return f
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def _emoji_surface(self, ch: str, small: bool = False) -> pygame.Surface:
        cache = self._small_emoji_cache if small else self._emoji_cache
        surf = cache.get(ch)
        if surf is None:
            font = self.small_emoji_font if small else self.tile_font
            surf = font.render(ch, True, COL_TEXT)
            cache[ch] = surf
        return surf

    def draw_tile(self, kind: TileKind, screen_x: int, screen_y: int,
                  designation: Optional[JobKind] = None,
                  zoom: float = 1.0) -> None:
        emoji = TILE_EMOJI[kind]
        surf = self._emoji_surface(emoji)
        size = int(TILE_SIZE * zoom)
        surf = pygame.transform.smoothscale(surf, (size, size))
        rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
        self.screen.blit(surf, rect)
        if designation is not None:
            overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            overlay.fill(COL_DESIGNATE)
            self.screen.blit(overlay, (screen_x, screen_y))

    def draw_hero(self, h: Hero, screen_x: int, screen_y: int,
                  zoom: float = 1.0) -> None:
        size = int(TILE_SIZE * zoom)
        if not h.alive:
            surf = self._emoji_surface("💀")
            surf = pygame.transform.smoothscale(surf, (size, size))
            rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
            self.screen.blit(surf, rect)
            return
        if h.invisible:
            surf = self._emoji_surface(HERO_EMOJI[h.hero_class])
            surf = pygame.transform.smoothscale(surf, (size, size))
            surf.set_alpha(80)
            rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
            self.screen.blit(surf, rect)
        else:
            surf = self._emoji_surface(HERO_EMOJI[h.hero_class])
            surf = pygame.transform.smoothscale(surf, (size, size))
            rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
            self.screen.blit(surf, rect)
        if h.hp < h.max_hp:
            bar_w = size - 4; bar_h = 3
            bx = screen_x + 2; by = screen_y - 6
            pygame.draw.rect(self.screen, (60, 0, 0), (bx, by, bar_w, bar_h))
            pygame.draw.rect(self.screen, COL_GOOD,
                            (bx, by, int(bar_w * h.hp / h.max_hp), bar_h))
        if h.mana < h.max_mana:
            bar_w = size - 4; bar_h = 2
            bx = screen_x + 2; by = screen_y - 3
            pygame.draw.rect(self.screen, (0, 0, 60), (bx, by, bar_w, bar_h))
            pygame.draw.rect(self.screen, COL_HERO,
                            (bx, by, int(bar_w * h.mana / h.max_mana), bar_h))
        if h.selected:
            pygame.draw.rect(self.screen, COL_ACCENT,
                            (screen_x - 1, screen_y - 1, size + 2, size + 2), 2)
        if h.level > 1:
            lvl_surf = self.tiny_font.render(str(h.level), True, COL_ACCENT)
            self.screen.blit(lvl_surf, (screen_x + size - 10, screen_y))

    def draw_dwarf(self, d: Dwarf, screen_x: int, screen_y: int,
                   zoom: float = 1.0) -> None:
        size = int(TILE_SIZE * zoom)
        if d.alive:
            emoji = DWARF_EMOJI
            if d.state == DwarfState.FIGHTING:
                emoji = "⚔️"
            elif d.state in (DwarfState.CHOPPING, DwarfState.MINING):
                emoji = "⛏️"
            elif d.state == DwarfState.SLEEPING:
                emoji = "😴"
            elif d.state == DwarfState.EATING:
                emoji = "🍖"
            elif d.state == DwarfState.CRAFTING:
                emoji = "🔨"
            surf = self._emoji_surface(emoji)
            surf = pygame.transform.smoothscale(surf, (size, size))
            rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
            self.screen.blit(surf, rect)
            if d.hp < d.max_hp:
                bar_w = size - 4; bar_h = 3
                bx = screen_x + 2; by = screen_y - 4
                pygame.draw.rect(self.screen, (60, 0, 0), (bx, by, bar_w, bar_h))
                pygame.draw.rect(self.screen, COL_DANGER,
                                (bx, by, int(bar_w * d.hp / d.max_hp), bar_h))
        else:
            surf = self._emoji_surface("💀")
            surf = pygame.transform.smoothscale(surf, (size, size))
            rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
            self.screen.blit(surf, rect)

    def draw_creature(self, c: Creature, screen_x: int, screen_y: int,
                      zoom: float = 1.0) -> None:
        size = int(TILE_SIZE * zoom)
        emoji = CREATURE_EMOJI[c.kind]
        surf = self._emoji_surface(emoji)
        # Scale slimes by size
        if c.kind == CreatureKind.SLIME:
            size = int(size * c.size)
        surf = pygame.transform.smoothscale(surf, (size, size))
        rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2))
        self.screen.blit(surf, rect)
        if c.hp < c.max_hp:
            bar_w = size - 4; bar_h = 3
            bx = screen_x + 2; by = screen_y - 4
            pygame.draw.rect(self.screen, (60, 0, 0), (bx, by, bar_w, bar_h))
            pygame.draw.rect(self.screen, COL_DANGER,
                            (bx, by, int(bar_w * c.hp / c.max_hp), bar_h))

    def draw_loot(self, l: Loot, screen_x: int, screen_y: int,
                  zoom: float = 1.0) -> None:
        size = int(16 * zoom)
        emoji_map = {"food": "🍖", "wood": "🪵", "stone": "🪨", "gold": "💰"}
        emoji = emoji_map.get(l.kind, "💎")
        surf = self._emoji_surface(emoji, small=True)
        surf = pygame.transform.smoothscale(surf, (size, size))
        # Bobbing animation
        bob = int(3 * zoom * math.sin(l.age * 3))
        rect = surf.get_rect(center=(screen_x + size // 2, screen_y + size // 2 + bob))
        self.screen.blit(surf, rect)

    def draw_particle(self, p: Particle, screen_x: int, screen_y: int,
                      zoom: float = 1.0) -> None:
        size = max(6, int(14 * zoom))
        surf = self._emoji_surface(p.emoji, small=True)
        surf = pygame.transform.smoothscale(surf, (size, size))
        alpha = max(0, min(255, int(255 * p.life / p.max_life)))
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(int(screen_x), int(screen_y)))
        self.screen.blit(surf, rect)

    def draw_ui(self, world: World, paused: bool, zoom: float,
                selected_heroes: list[Hero],
                hover_tile: Optional[tuple[int, int]]) -> None:
        panel_w = 320
        panel = pygame.Surface((panel_w, WINDOW_H))
        panel.fill(COL_PANEL)
        self.screen.blit(panel, (WINDOW_W - panel_w, 0))

        x = WINDOW_W - panel_w + 14
        y = 12
        title = self.ui_font.render("EMOJI FORTRESS", True, COL_ACCENT)
        self.screen.blit(title, (x, y)); y += 22

        lines = [
            f"Day {world.day}   {self._time_str(world.day_time)}",
            f"Threat: {'🔴' * world.threat_level}{'⚫' * (10 - world.threat_level)}",
            f"Dwarves: {sum(1 for d in world.dwarves if d.alive)}/{len(world.dwarves)}",
            f"Heroes : {sum(1 for h in world.heroes if h.alive)}/{len(world.heroes)}",
            f"Kills: {world.total_kills}   Deaths: {world.total_deaths}",
            "",
            f"🪵 {world.inv.wood}  🪨 {world.inv.stone}  🍖 {world.inv.food}",
            f"🛠️ {world.inv.tools}  🛡️ {world.inv.armor}  💰 {world.inv.gold}",
            f"Jobs: {len(world.jobs)}  Creatures: {len(world.creatures)}",
        ]
        if paused:
            lines.insert(0, "⏸  PAUSED")
        for line in lines:
            surf = self.ui_font.render(line, True, COL_TEXT)
            self.screen.blit(surf, (x, y)); y += 16

        # Heroes panel
        y += 4
        header = self.ui_font.render("— HEROES —", True, COL_ACCENT)
        self.screen.blit(header, (x, y)); y += 18
        for h in world.heroes:
            if not h.alive:
                surf = self.tiny_font.render(f"💀 {h.name}", True, COL_DIM)
                self.screen.blit(surf, (x, y)); y += 14
                continue
            emoji = HERO_EMOJI[h.hero_class]
            sel = "►" if h.selected else " "
            line = f"{sel}{emoji} {h.name} Lv{h.level}"
            color = COL_ACCENT if h.selected else COL_TEXT
            surf = self.tiny_font.render(line, True, color)
            self.screen.blit(surf, (x, y)); y += 13
            # Mini HP/Mana bars
            bar_w = 80
            bx = x + 4
            pygame.draw.rect(self.screen, (60, 0, 0), (bx, y, bar_w, 3))
            pygame.draw.rect(self.screen, COL_GOOD,
                            (bx, y, int(bar_w * h.hp / h.max_hp), 3))
            pygame.draw.rect(self.screen, (0, 0, 60), (bx, y + 4, bar_w, 2))
            pygame.draw.rect(self.screen, COL_HERO,
                            (bx, y + 4, int(bar_w * h.mana / h.max_mana), 2))
            y += 10

        # Bestiary
        y += 4
        header = self.ui_font.render("— BESTIARY —", True, COL_ACCENT)
        self.screen.blit(header, (x, y)); y += 18
        if world.bestiary:
            for kind, count in sorted(world.bestiary.items(), key=lambda x: -x[1]):
                emoji = CREATURE_EMOJI[kind]
                line = f"{emoji} {kind.value:<10} x{count}"
                surf = self.tiny_font.render(line, True, COL_DIM)
                self.screen.blit(surf, (x, y)); y += 13
                if y > WINDOW_H - 200:
                    break
        else:
            surf = self.tiny_font.render("No creatures slain yet", True, COL_DIM)
            self.screen.blit(surf, (x, y)); y += 13

        # Hover info
        y += 4
        header = self.ui_font.render("— Hover —", True, COL_ACCENT)
        self.screen.blit(header, (x, y)); y += 16
        if hover_tile is not None:
            tx, ty = hover_tile
            t = world.tile_at(tx, ty)
            if t is not None:
                surf = self.tiny_font.render(f"({tx},{ty}) {t.kind.name}", True, COL_TEXT)
                self.screen.blit(surf, (x, y)); y += 13
                # Show creatures on tile
                creatures_here = [c for c in world.creatures if c.tile_pos == (tx, ty)]
                if creatures_here:
                    for c in creatures_here[:3]:
                        emoji = CREATURE_EMOJI[c.kind]
                        surf = self.tiny_font.render(f"{emoji} {c.kind.value} HP:{int(c.hp)}",
                                                    True, COL_DANGER)
                        self.screen.blit(surf, (x, y)); y += 13

        # Message log
        log_h = 100
        log_panel = pygame.Surface((WINDOW_W - panel_w, log_h))
        log_panel.fill(COL_PANEL)
        self.screen.blit(log_panel, (0, WINDOW_H - log_h))
        ly = WINDOW_H - log_h + 6
        visible = [m for m in world.messages if m.age < m.ttl][-5:]
        for m in visible:
            alpha = max(80, int(255 * (1 - m.age / m.ttl)))
            surf = self.small_font.render(m.text, True, COL_TEXT)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (12, ly)); ly += 17

    def draw_minimap(self, world: World, camera_x: float, camera_y: float,
                     zoom: float) -> None:
        mm_w, mm_h = 180, 115
        mm_x = 10
        mm_y = WINDOW_H - 100 - mm_h
        bg = pygame.Surface((mm_w, mm_h))
        bg.fill((15, 17, 22))
        pygame.draw.rect(bg, COL_ACCENT, (0, 0, mm_w, mm_h), 1)
        cell_w = mm_w / world.w
        cell_h = mm_h / world.h
        color_map = {
            TileKind.GRASS:      (80, 160, 80),
            TileKind.DIRT:       (120, 80, 50),
            TileKind.TREE:       (30, 110, 40),
            TileKind.STONE:      (130, 130, 140),
            TileKind.WATER:      (60, 100, 200),
            TileKind.WALL:       (180, 100, 80),
            TileKind.FLOOR:      (200, 190, 120),
            TileKind.STOCKPILE:  (220, 180, 80),
            TileKind.BED:        (180, 120, 180),
            TileKind.WORKSHOP:   (200, 140, 80),
            TileKind.TOMBSTONE:  (100, 100, 110),
            TileKind.WEB:        (200, 200, 200),
        }
        for y in range(world.h):
            for x in range(world.w):
                c = color_map.get(world.tiles[y][x].kind, (40, 40, 40))
                pygame.draw.rect(bg, c,
                                (int(x * cell_w), int(y * cell_h),
                                 max(1, int(cell_w)), max(1, int(cell_h))))
        for d in world.dwarves:
            if d.alive:
                pygame.draw.rect(bg, COL_GOOD,
                                (int(d.x * cell_w), int(d.y * cell_h), 2, 2))
        for h in world.heroes:
            if h.alive and not h.invisible:
                pygame.draw.rect(bg, COL_HERO,
                                (int(h.x * cell_w) - 1, int(h.y * cell_h) - 1, 3, 3))
        for c in world.creatures:
            pygame.draw.rect(bg, COL_DANGER,
                            (int(c.x * cell_w), int(c.y * cell_h), 2, 2))
        s = TILE_SIZE * zoom
        vx = camera_x / (world.w * s) * mm_w
        vy = camera_y / (world.h * s) * mm_h
        vw = (WINDOW_W - 320) / (world.w * s) * mm_w
        vh = WINDOW_H / (world.h * s) * mm_h
        pygame.draw.rect(bg, COL_ACCENT, (int(vx), int(vy), int(vw), int(vh)), 1)
        self.screen.blit(bg, (mm_x, mm_y))

    def draw_night_overlay(self, world: World, view_rect: pygame.Rect) -> None:
        t = world.day_time / DAY_LENGTH
        darkness = max(0.0, 0.55 - abs(t - 0.5) * 1.6)
        if darkness > 0.02:
            overlay = pygame.Surface((view_rect.width, view_rect.height), pygame.SRCALPHA)
            overlay.fill((10, 14, 40, int(darkness * 200)))
            self.screen.blit(overlay, view_rect.topleft)

    @staticmethod
    def _time_str(t: float) -> str:
        hours = int((t / DAY_LENGTH) * 24)
        mins = int(((t / DAY_LENGTH) * 24 - hours) * 60)
        return f"{hours:02d}:{mins:02d}"


# --------------------------------------------------------------------------- #
# Camera                                                                      #
# --------------------------------------------------------------------------- #
@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0

    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        s = TILE_SIZE * self.zoom
        return int(wx * s - self.x), int(wy * s - self.y)

    def screen_to_world(self, sx: int, sy: int) -> tuple[float, float]:
        s = TILE_SIZE * self.zoom
        return (sx + self.x) / s, (sy + self.y) / s

    def clamp(self, world_w: int, world_h: int, view_w: int, view_h: int) -> None:
        s = TILE_SIZE * self.zoom
        max_x = max(0, world_w * s - view_w)
        max_y = max(0, world_h * s - view_h)
        self.x = max(0.0, min(max_x, self.x))
        self.y = max(0.0, min(max_y, self.y))


# --------------------------------------------------------------------------- #
# Game                                                                        #
# --------------------------------------------------------------------------- #
class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Emoji Fortress — Bestiary Edition")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.world = World(MAP_W, MAP_H, seed=1337)
        self.camera = Camera()
        self._center_camera()
        self.paused = False
        self.running = True
        self._accumulator = 0.0
        self._tick_dt = 1.0 / TICK_RATE
        self.selected_heroes: list[Hero] = []
        self.hover_tile: Optional[tuple[int, int]] = None
        self.mouse_pos = (0, 0)
        self.move_indicator: Optional[tuple[float, float, float]] = None

    def _center_camera(self) -> None:
        s = TILE_SIZE * self.camera.zoom
        self.camera.x = (MAP_W * s - (WINDOW_W - 320)) / 2
        self.camera.y = (MAP_H * s - WINDOW_H) / 2

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)
            self._handle_events(dt)
            if not self.paused:
                self._accumulator += dt
                while self._accumulator >= self._tick_dt:
                    self.world.tick(self._tick_dt)
                    self._accumulator -= self._tick_dt
            if self.move_indicator:
                x, y, ttl = self.move_indicator
                ttl -= dt
                if ttl <= 0:
                    self.move_indicator = None
                else:
                    self.move_indicator = (x, y, ttl)
            self._render()
        pygame.quit()

    def _handle_events(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        pan_speed = EDGE_SCROLL_SPEED / self.camera.zoom
        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.camera.y -= pan_speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.camera.y += pan_speed * dt
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.camera.x -= pan_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.camera.x += pan_speed * dt
        mx, my = pygame.mouse.get_pos()
        self.mouse_pos = (mx, my)
        if mx < EDGE_SCROLL_MARGIN:
            self.camera.x -= pan_speed * dt
        elif mx > WINDOW_W - 320 - EDGE_SCROLL_MARGIN:
            self.camera.x += pan_speed * dt
        if my < EDGE_SCROLL_MARGIN:
            self.camera.y -= pan_speed * dt
        elif my > WINDOW_H - EDGE_SCROLL_MARGIN:
            self.camera.y += pan_speed * dt
        self.camera.clamp(MAP_W, MAP_H, WINDOW_W - 320, WINDOW_H)

        if mx < WINDOW_W - 320:
            wx, wy = self.camera.screen_to_world(mx, my)
            tx, ty = int(wx), int(wy)
            if self.world.in_bounds(tx, ty):
                self.hover_tile = (tx, ty)
            else:
                self.hover_tile = None
        else:
            self.hover_tile = None

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                self._on_key(e.key, keys)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse(e.button, e.pos, keys)
            elif e.type == pygame.MOUSEWHEEL:
                self._zoom(e.y * 0.1)

    def _on_key(self, key: int, keys_state) -> None:
        if key == pygame.K_q:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
            self.world.log("Paused." if self.paused else "Resumed.")
        elif key == pygame.K_r:
            self.world = World(MAP_W, MAP_H, seed=random.randint(0, 10**9))
            self.selected_heroes = []
            self._center_camera()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self._zoom(0.15)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._zoom(-0.15)
        elif key == pygame.K_F5:
            self._save()
        elif key == pygame.K_F9:
            self._load()
        elif key == pygame.K_ESCAPE:
            for h in self.selected_heroes:
                h.selected = False
            self.selected_heroes = []
        elif key == pygame.K_TAB:
            self._cycle_hero()
        elif key == pygame.K_a and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self._select_all_heroes()
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            ability_idx = key - pygame.K_1
            self._use_ability_on_primary(ability_idx)

    def _cycle_hero(self) -> None:
        alive = [h for h in self.world.heroes if h.alive]
        if not alive:
            return
        if not self.selected_heroes:
            alive[0].selected = True
            self.selected_heroes = [alive[0]]
            return
        current = self.selected_heroes[0]
        idx = next((i for i, h in enumerate(alive) if h.id == current.id), -1)
        next_idx = (idx + 1) % len(alive)
        current.selected = False
        self.selected_heroes = [alive[next_idx]]
        alive[next_idx].selected = True
        s = TILE_SIZE * self.camera.zoom
        self.camera.x = alive[next_idx].x * s - (WINDOW_W - 320) / 2
        self.camera.y = alive[next_idx].y * s - WINDOW_H / 2
        self.camera.clamp(MAP_W, MAP_H, WINDOW_W - 320, WINDOW_H)

    def _select_all_heroes(self) -> None:
        for h in self.selected_heroes:
            h.selected = False
        self.selected_heroes = [h for h in self.world.heroes if h.alive]
        for h in self.selected_heroes:
            h.selected = True

    def _use_ability_on_primary(self, ability_idx: int) -> None:
        if not self.selected_heroes:
            return
        h = self.selected_heroes[0]
        mx, my = self.mouse_pos
        wx, wy = self.camera.screen_to_world(mx, my)
        target_pos = (int(wx), int(wy))
        if self.world.use_ability(h, ability_idx, target_pos):
            self.world.spawn_particles(h.x + 0.5, h.y + 0.5, ParticleKind.MAGIC, 5)

    def _zoom(self, delta: float) -> None:
        old_zoom = self.camera.zoom
        self.camera.zoom = max(0.5, min(2.5, self.camera.zoom + delta))
        ratio = self.camera.zoom / old_zoom
        cx = (self.camera.x + (WINDOW_W - 320) / 2) * ratio
        cy = (self.camera.y + WINDOW_H / 2) * ratio
        self.camera.x = cx - (WINDOW_W - 320) / 2
        self.camera.y = cy - WINDOW_H / 2
        self.camera.clamp(MAP_W, MAP_H, WINDOW_W - 320, WINDOW_H)

    def _on_mouse(self, button: int, pos: tuple[int, int], keys_state) -> None:
        if pos[0] >= WINDOW_W - 320:
            return
        wx, wy = self.camera.screen_to_world(*pos)
        tx, ty = int(wx), int(wy)
        if not self.world.in_bounds(tx, ty):
            return

        if button == 1:
            clicked_hero = None
            for h in self.world.heroes:
                if h.alive and abs(h.x - wx) < 0.6 and abs(h.y - wy) < 0.6:
                    clicked_hero = h
                    break
            if clicked_hero:
                if keys_state[pygame.K_LSHIFT] or keys_state[pygame.K_RSHIFT]:
                    clicked_hero.selected = not clicked_hero.selected
                    if clicked_hero.selected and clicked_hero not in self.selected_heroes:
                        self.selected_heroes.append(clicked_hero)
                    elif not clicked_hero.selected and clicked_hero in self.selected_heroes:
                        self.selected_heroes.remove(clicked_hero)
                else:
                    for h in self.selected_heroes:
                        h.selected = False
                    self.selected_heroes = [clicked_hero]
                    clicked_hero.selected = True
                return
            if not (keys_state[pygame.K_LSHIFT] or keys_state[pygame.K_RSHIFT]):
                for h in self.selected_heroes:
                    h.selected = False
                self.selected_heroes = []
            tile = self.world.tiles[ty][tx]
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                if tile.kind in TILE_BUILDABLE:
                    self.world.add_job(JobKind.BUILD_WORKSHOP, tx, ty)
            elif tile.kind == TileKind.TREE:
                self.world.add_job(JobKind.CHOP, tx, ty)
            elif tile.kind == TileKind.STONE:
                self.world.add_job(JobKind.MINE, tx, ty)
            elif tile.kind in (TileKind.GRASS, TileKind.DIRT, TileKind.FLOOR):
                if tile.designation == JobKind.BUILD_FLOOR:
                    self.world.cancel_job(tx, ty)
                    self.world.add_job(JobKind.BUILD_WALL, tx, ty)
                elif tile.designation == JobKind.BUILD_WALL:
                    self.world.cancel_job(tx, ty)
                else:
                    self.world.add_job(JobKind.BUILD_FLOOR, tx, ty)
        elif button == 3:
            if self.selected_heroes:
                if self.world.tiles[ty][tx].walkable:
                    for h in self.selected_heroes:
                        if h.alive:
                            h.target = (tx, ty)
                            h.state = HeroState.MOVING
                            h._path = []
                    self.move_indicator = (float(tx), float(ty), 1.0)
                    self.world.log(f"🚩 Heroes moving to ({tx},{ty})")
            else:
                self.world.cancel_job(tx, ty)
        elif button == 2:
            tile = self.world.tiles[ty][tx]
            if tile.kind in TILE_BUILDABLE:
                self.world.add_job(JobKind.BUILD_BED, tx, ty)

    def _save(self) -> None:
        try:
            data = {"world": self.world, "camera": self.camera, "version": 3}
            with open(SAVE_FILE, "wb") as f:
                pickle.dump(data, f)
            self.world.log(f"💾 Game saved.")
        except Exception as e:
            log.exception("Save failed")
            self.world.log(f"❌ Save failed: {e}")

    def _load(self) -> None:
        if not os.path.exists(SAVE_FILE):
            self.world.log("❌ No save file found.")
            return
        try:
            with open(SAVE_FILE, "rb") as f:
                data = pickle.load(f)
            self.world = data["world"]
            self.camera = data["camera"]
            self.selected_heroes = [h for h in self.world.heroes if h.selected]
            self.world.log("📂 Game loaded.")
        except Exception as e:
            log.exception("Load failed")
            self.world.log(f"❌ Load failed: {e}")

    def _render(self) -> None:
        self.screen.fill(COL_BG)
        s = TILE_SIZE * self.camera.zoom
        x0 = max(0, int(self.camera.x / s) - 1)
        y0 = max(0, int(self.camera.y / s) - 1)
        x1 = min(MAP_W, int((self.camera.x + WINDOW_W - 320) / s) + 2)
        y1 = min(MAP_H, int((self.camera.y + WINDOW_H) / s) + 2)

        for ty in range(y0, y1):
            for tx in range(x0, x1):
                tile = self.world.tiles[ty][tx]
                sx, sy = self.camera.world_to_screen(tx, ty)
                self.renderer.draw_tile(tile.kind, sx, sy, tile.designation,
                                        self.camera.zoom)

        if self.move_indicator:
            mx, my, ttl = self.move_indicator
            sx, sy = self.camera.world_to_screen(mx + 0.5, my + 0.5)
            pygame.draw.circle(self.screen, COL_ACCENT, (sx, sy),
                              int(8 * self.camera.zoom), 2)

        for l in self.world.loot:
            sx, sy = self.camera.world_to_screen(l.x, l.y)
            self.renderer.draw_loot(l, sx, sy, self.camera.zoom)

        for d in self.world.dwarves:
            if not d.alive and d.state == DwarfState.DEAD:
                continue
            sx, sy = self.camera.world_to_screen(d.x, d.y)
            self.renderer.draw_dwarf(d, sx, sy, self.camera.zoom)

        for h in self.world.heroes:
            sx, sy = self.camera.world_to_screen(h.x, h.y)
            self.renderer.draw_hero(h, sx, sy, self.camera.zoom)

        for c in self.world.creatures:
            sx, sy = self.camera.world_to_screen(c.x, c.y)
            self.renderer.draw_creature(c, sx, sy, self.camera.zoom)

        for p in self.world.particles:
            sx, sy = self.camera.world_to_screen(p.x, p.y)
            self.renderer.draw_particle(p, sx, sy, self.camera.zoom)

        view_rect = pygame.Rect(0, 0, WINDOW_W - 320, WINDOW_H)
        self.renderer.draw_night_overlay(self.world, view_rect)
        self.renderer.draw_ui(self.world, self.paused, self.camera.zoom,
                              self.selected_heroes, self.hover_tile)
        self.renderer.draw_minimap(self.world, self.camera.x, self.camera.y,
                                   self.camera.zoom)
        pygame.display.flip()


def main() -> int:
    try:
        Game().run()
    except Exception:
        log.exception("Fatal error")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())