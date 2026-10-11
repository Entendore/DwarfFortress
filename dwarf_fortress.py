#!/usr/bin/env python3
"""
Emoji Dwarf Fortress v3 — The Ultimate Emoji DF Experience
New in v3: Weather, Day/Night, Fog of War, Taming, Moods/Artifacts,
Fluid Flow, 12 new creatures, Corpse/Graveyard, Skill Leveling, Improved UI.
"""

import pygame, random, sys, math
from collections import deque
from enum import IntEnum

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SW, SH = 1440, 900
TS = 24
MW, MH = 160, 130
UPW = 310
FPS = 30
MAX_Z = 6

# ═══════════════════════════════════════════════════════════════════════════════
# TILES
# ═══════════════════════════════════════════════════════════════════════════════
class T(IntEnum):
    GRASS=0;DIRT=1;STONE=2;WALL=3;WATER=4;TREE=5;IRON_ORE=6;GOLD_ORE=7
    COAL=8;BEDROCK=9;FLOOR=10;STAIR_DN=11;STAIR_UP=12;FARM=13;STOCKPILE=14
    WORKSHOP=15;BED=16;TABLE=17;DOOR=18;PWALL=19;BARRACKS=20;HOSPITAL=21
    TAVERN=22;SMELTER=23;TRAP=24;BRIDGE=25;FORTIF=26;GEM_ORE=27;PLAT_ORE=28
    MUSHROOM=29;ASH=30;LAVA=31;ICE=32;COFFIN=33;JEWELER=34;LEATHERWORK=35
    ANIMAL_PEN=36;WELL=37;STATUE=38;MAGMA_FORGE=39;ADAMANTINE=40

TE = {
    T.GRASS:"🌿",T.DIRT:"🟫",T.STONE:"🪨",T.WALL:"🧱",T.WATER:"💧",T.TREE:"🌲",
    T.IRON_ORE:"⛏️",T.GOLD_ORE:"🪙",T.COAL:"🖤",T.BEDROCK:"⬛",T.FLOOR:"⬜",
    T.STAIR_DN:"🔽",T.STAIR_UP:"🔼",T.FARM:"🌾",T.STOCKPILE:"📦",T.WORKSHOP:"🔨",
    T.BED:"🛏️",T.TABLE:"🪑",T.DOOR:"🚪",T.PWALL:"🧱",T.BARRACKS:"⚔️",T.HOSPITAL:"🏥",
    T.TAVERN:"🍺",T.SMELTER:"🔥",T.TRAP:"🪤",T.BRIDGE:"🌉",T.FORTIF:"🏰",
    T.GEM_ORE:"💎",T.PLAT_ORE:"🩶",T.MUSHROOM:"🍄",T.ASH:"🌫️",T.LAVA:"🌋",
    T.ICE:"🧊",T.COFFIN:"⚰️",T.JEWELER:"💠",T.LEATHERWORK:"🧵",T.ANIMAL_PEN:"🐄",
    T.WELL:"🪣",T.STATUE:"🗿",T.MAGMA_FORGE:"♨️",T.ADAMANTINE:"✨",
}

TBG = {
    T.GRASS:(34,80,34),T.DIRT:(80,55,30),T.STONE:(70,70,80),T.WALL:(90,80,70),
    T.WATER:(20,50,120),T.TREE:(20,70,20),T.IRON_ORE:(70,60,55),T.GOLD_ORE:(80,70,30),
    T.COAL:(35,35,40),T.BEDROCK:(20,20,20),T.FLOOR:(60,58,55),T.STAIR_DN:(55,50,50),
    T.STAIR_UP:(55,50,50),T.FARM:(50,80,30),T.STOCKPILE:(70,65,45),T.WORKSHOP:(75,60,50),
    T.BED:(65,50,55),T.TABLE:(65,55,45),T.DOOR:(80,60,40),T.PWALL:(85,75,65),
    T.BARRACKS:(80,50,50),T.HOSPITAL:(50,70,80),T.TAVERN:(70,55,50),T.SMELTER:(90,50,30),
    T.TRAP:(70,60,40),T.BRIDGE:(75,70,60),T.FORTIF:(65,65,75),T.GEM_ORE:(60,50,70),
    T.PLAT_ORE:(75,75,80),T.MUSHROOM:(45,55,40),T.ASH:(55,50,48),T.LAVA:(120,40,10),
    T.ICE:(60,70,90),T.COFFIN:(50,45,55),T.JEWELER:(65,55,70),T.LEATHERWORK:(70,55,50),
    T.ANIMAL_PEN:(55,75,45),T.WELL:(40,60,90),T.STATUE:(80,78,75),T.MAGMA_FORGE:(100,45,15),
    T.ADAMANTINE:(80,60,120),
}

WALK = {T.GRASS,T.DIRT,T.FLOOR,T.FARM,T.STOCKPILE,T.WORKSHOP,T.BED,T.TABLE,
        T.STAIR_UP,T.STAIR_DN,T.DOOR,T.BARRACKS,T.HOSPITAL,T.TAVERN,T.SMELTER,
        T.BRIDGE,T.FORTIF,T.MUSHROOM,T.ASH,T.COFFIN,T.JEWELER,T.LEATHERWORK,
        T.ANIMAL_PEN,T.WELL,T.STATUE,T.MAGMA_FORGE}
MINEABLE = {T.STONE,T.WALL,T.IRON_ORE,T.GOLD_ORE,T.COAL,T.GEM_ORE,T.PLAT_ORE,T.ADAMANTINE}

# ═══════════════════════════════════════════════════════════════════════════════
# PROFESSIONS & NAMES
# ═══════════════════════════════════════════════════════════════════════════════
PROFS = ["Miner","Woodcutter","Farmer","Mason","Smith","Hunter","Soldier","Doctor",
         "Brewer","Jeweler","Engineer","Leatherworker"]
PE = {"Miner":"⛏️","Woodcutter":"🪓","Farmer":"🌱","Mason":"🧱","Smith":"🔥",
      "Hunter":"🏹","Soldier":"⚔️","Doctor":"💊","Brewer":"🍺","Jeweler":"💠",
      "Engineer":"⚙️","Leatherworker":"🧵"}
DNAMES = ["Urist","Tholtig","Dodok","Litast","Erith","Mistem","Tun","Zasit","Inod","Cerol",
          "Stodir","Astesh","Rith","Doren","Kadol","Vabok","Reg","Meng","Ber","Ducim",
          "Sodel","Aban","Rimtar","Nil","Atis","Bomrek","Kogan","Momuz","Edem","Dastot",
          "Fikod","Ingish","Logem","Rigos","Avuz","Olon","Udil","Ber","Catten","Doren",
          "Erush","Goden","Kib","Kol","Mafol","Nish","Rakust","Shorast","Thikut","Udib"]

# ═══════════════════════════════════════════════════════════════════════════════
# BUILDABLE
# ═══════════════════════════════════════════════════════════════════════════════
BLD = {
    "Bed":       {"e":"🛏️","t":T.BED,       "c":{"Wood":2},              "k":"1","d":"Sleep heals energy"},
    "Table":     {"e":"🪑","t":T.TABLE,     "c":{"Wood":1,"Stone":1},     "k":"2","d":"Dining room need"},
    "Door":      {"e":"🚪","t":T.DOOR,      "c":{"Wood":1,"Stone":1},     "k":"3","d":"Access control"},
    "Wall":      {"e":"🧱","t":T.PWALL,     "c":{"Stone":2},              "k":"4","d":"Fortification"},
    "Workshop":  {"e":"🔨","t":T.WORKSHOP,  "c":{"Stone":3},              "k":"5","d":"Craft weapons/armor"},
    "Farm":      {"e":"🌾","t":T.FARM,      "c":{"Wood":1},              "k":"6","d":"Food production"},
    "Stockpile": {"e":"📦","t":T.STOCKPILE, "c":{},                       "k":"7","d":"Store all goods"},
    "Barracks":  {"e":"⚔️","t":T.BARRACKS,  "c":{"Stone":4,"Wood":2},     "k":"8","d":"Train soldiers"},
    "Hospital":  {"e":"🏥","t":T.HOSPITAL,  "c":{"Stone":3,"Wood":2},     "k":"9","d":"Heal the wounded"},
    "Tavern":    {"e":"🍺","t":T.TAVERN,    "c":{"Wood":3,"Stone":1},     "k":"0","d":"Brew beer, happiness"},
    "Smelter":   {"e":"🔥","t":T.SMELTER,   "c":{"Stone":5},              "k":"-","d":"Smelt ore bars"},
    "Trap":      {"e":"🪤","t":T.TRAP,      "c":{"Stone":1,"Wood":1},     "k":"=","d":"Damage hostiles"},
    "Fortif.":   {"e":"🏰","t":T.FORTIF,    "c":{"Stone":4},              "k":"[","d":"Ranged defense"},
    "Bridge":    {"e":"🌉","t":T.BRIDGE,    "c":{"Wood":3,"Stone":2},     "k":"]","d":"Cross gaps"},
    "Coffin":    {"e":"⚰️","t":T.COFFIN,    "c":{"Stone":3,"Wood":1},     "k":"\\","d":"Bury dead dwarves"},
    "Jeweler":   {"e":"💠","t":T.JEWELER,   "c":{"Stone":3,"Gem":1},      "k":";","d":"Cut gems for wealth"},
    "LeathWk":   {"e":"🧵","t":T.LEATHERWORK,"c":{"Wood":2,"Stone":2},    "k":"'","d":"Craft leather armor"},
    "Animal Pen":{"e":"🐄","t":T.ANIMAL_PEN,"c":{"Wood":4,"Stone":2},     "k":"/","d":"House tamed animals"},
    "Well":      {"e":"🪣","t":T.WELL,      "c":{"Stone":3,"Wood":1},     "k":",","d":"Clean water source"},
    "Statue":    {"e":"🗿","t":T.STATUE,    "c":{"Stone":5,"Gold":1},     "k":"<","d":"Beauty, happiness"},
    "Mag.Forge": {"e":"♨️","t":T.MAGMA_FORGE,"c":{"Stone":8,"Iron":3},    "k":">","d":"Steel & adamantite"},
}
BL = list(BLD.keys())

# ═══════════════════════════════════════════════════════════════════════════════
# CREATURES (26 species)
# ═══════════════════════════════════════════════════════════════════════════════
CD = {
    # ── Passive Surface ──
    "Rabbit":     {"e":"🐰","hp":8,  "a":0, "d":0, "s":.6,"h":False,"xp":1,
                   "ai":"flee","loot":None,"zr":(0,0),"pk":3,"noct":False},
    "Fox":        {"e":"🦊","hp":15, "a":3, "d":1, "s":.5,"h":False,"xp":2,
                   "ai":"wander","loot":None,"zr":(0,0),"pk":2,"noct":True},
    "Deer":       {"e":"🦌","hp":20, "a":0, "d":2, "s":.55,"h":False,"xp":3,
                   "ai":"flee","loot":{"Food":2},"zr":(0,0),"pk":4,"noct":False},
    "Fish":       {"e":"🐟","hp":5,  "a":0, "d":0, "s":.3,"h":False,"xp":1,
                   "ai":"swim","loot":{"Food":1},"zr":(0,0),"pk":5,"noct":False},
    "Elk":        {"e":"🫎","hp":35, "a":2, "d":3, "s":.5,"h":False,"xp":5,
                   "ai":"wander","loot":{"Food":4},"zr":(0,0),"pk":3,"noct":False},
    "Owl":        {"e":"🦉","hp":10, "a":2, "d":1, "s":.55,"h":False,"xp":2,
                   "ai":"wander","loot":None,"zr":(0,0),"pk":2,"noct":True},
    "Butterfly":  {"e":"🦋","hp":3,  "a":0, "d":0, "s":.4,"h":False,"xp":0,
                   "ai":"wander","loot":None,"zr":(0,0),"pk":6,"noct":False},
    # ── Hostile Surface ──
    "Wolf":       {"e":"🐺","hp":25, "a":8, "d":3, "s":.45,"h":True,"xp":5,
                   "ai":"hunt","loot":None,"zr":(0,1),"pk":3,"noct":True},
    "Bear":       {"e":"🐻","hp":50, "a":15,"d":6, "s":.35,"h":True,"xp":10,
                   "ai":"hunt","loot":{"Food":5},"zr":(0,1),"pk":1,"noct":False},
    "Dire Wolf":  {"e":"🐺","hp":45, "a":14,"d":5, "s":.5,"h":True,"xp":12,
                   "ai":"hunt_dwarves","loot":{"Food":3},"zr":(0,2),"pk":4,"noct":True},
    "Eagle":      {"e":"🦅","hp":20, "a":10,"d":2, "s":.6,"h":True,"xp":6,
                   "ai":"hunt","loot":None,"zr":(0,1),"pk":2,"noct":False},
    "Crocodile":  {"e":"🐊","hp":55, "a":18,"d":8, "s":.3,"h":True,"xp":15,
                   "ai":"ambush","loot":{"Food":6,"Leather":2},"zr":(0,0),"pk":1,"noct":True},
    # ── Siege ──
    "Goblin":     {"e":"👹","hp":30, "a":10,"d":4, "s":.4,"h":True,"xp":8,
                   "ai":"hunt_dwarves","loot":{"Iron":1},"zr":(0,3),"pk":4,"noct":False},
    "Gob. Chief": {"e":"👿","hp":60, "a":16,"d":7, "s":.38,"h":True,"xp":20,
                   "ai":"hunt_dwarves","loot":{"Iron":3,"Gold":1},"zr":(0,2),"pk":1,"noct":False},
    "Gob. Shaman":{"e":"🧙","hp":35, "a":5, "d":3, "s":.35,"h":True,"xp":15,
                   "ai":"hunt_dwarves","loot":{"Gem":2},"zr":(0,2),"pk":1,"noct":False,
                   "special":"heal_ally"},
    # ── Underground ──
    "Cave Bat":   {"e":"🦇","hp":10, "a":5, "d":1, "s":.6,"h":True,"xp":3,
                   "ai":"wander","loot":None,"zr":(1,5),"pk":5,"noct":True},
    "Spider":     {"e":"🕷️","hp":18, "a":7, "d":2, "s":.5,"h":True,"xp":4,
                   "ai":"hunt","loot":None,"zr":(1,5),"pk":4,"noct":True},
    "Giant Rat":  {"e":"🐀","hp":12, "a":4, "d":1, "s":.55,"h":True,"xp":2,
                   "ai":"wander","loot":{"Food":1},"zr":(1,4),"pk":5,"noct":True},
    "Cave Crab":  {"e":"🦀","hp":22, "a":9, "d":6, "s":.3,"h":True,"xp":5,
                   "ai":"wander","loot":{"Food":2},"zr":(1,5),"pk":3,"noct":True},
    "Skeleton":   {"e":"💀","hp":40, "a":12,"d":5, "s":.35,"h":True,"xp":12,
                   "ai":"hunt_dwarves","loot":{"Iron":2},"zr":(1,5),"pk":3,"noct":True},
    "Troll":      {"e":"🧌","hp":80, "a":20,"d":8, "s":.3,"h":True,"xp":25,
                   "ai":"hunt_dwarves","loot":{"Stone":5,"Gold":2},"zr":(2,5),"pk":1,"noct":False},
    "Fire Imp":   {"e":"😈","hp":30, "a":15,"d":4, "s":.5,"h":True,"xp":10,
                   "ai":"wander","loot":{"Coal":3},"zr":(3,5),"pk":2,"noct":True,
                   "special":"fire"},
    "Water Elem.":{"e":"💧","hp":50, "a":12,"d":8, "s":.35,"h":True,"xp":15,
                   "ai":"swim","loot":None,"zr":(1,5),"pk":1,"noct":False},
    "Wraith":     {"e":"👻","hp":35, "a":14,"d":3, "s":.4,"h":True,"xp":18,
                   "ai":"hunt_dwarves","loot":{"Gem":1},"zr":(2,5),"pk":2,"noct":True,
                   "special":"phase"},
    "Ooze":       {"e":"🟢","hp":45, "a":10,"d":10,"s":.2,"h":True,"xp":8,
                   "ai":"wander","loot":None,"zr":(1,5),"pk":3,"noct":False},
    "Golem":      {"e":"🗿","hp":120,"a":18,"d":15,"s":.2,"h":True,"xp":40,
                   "ai":"hunt_dwarves","loot":{"Gold":5,"Gem":3},"zr":(3,5),"pk":1,"noct":False},
    # ── Megabeasts ──
    "Dragon":     {"e":"🐉","hp":300,"a":40,"d":20,"s":.25,"h":True,"xp":200,
                   "ai":"hunt_dwarves","loot":{"Gold":20,"Gem":10},"zr":(0,5),"pk":1,"noct":False,
                   "special":"fire_breath"},
    "Titan":      {"e":"👾","hp":500,"a":50,"d":25,"s":.2,"h":True,"xp":500,
                   "ai":"hunt_dwarves","loot":{"Platinum":10,"Gold":15},"zr":(0,5),"pk":1,"noct":False},
    "Hydra":      {"e":"🐍","hp":400,"a":35,"d":18,"s":.28,"h":True,"xp":300,
                   "ai":"hunt_dwarves","loot":{"Gem":15,"Gold":10},"zr":(0,5),"pk":1,"noct":True},
}

# ═══════════════════════════════════════════════════════════════════════════════
# RECIPES
# ═══════════════════════════════════════════════════════════════════════════════
RECIPES = {
    "Iron Bar":     {"i":{"Iron":2,"Coal":1},        "b":T.SMELTER,      "oe":"🔩"},
    "Gold Bar":     {"i":{"Gold":2,"Coal":1},        "b":T.SMELTER,      "oe":"🥇"},
    "Plat. Bar":    {"i":{"Platinum":2,"Coal":1},    "b":T.SMELTER,      "oe":"🥈"},
    "Steel Bar":    {"i":{"Iron Bar":1,"Coal":2},    "b":T.MAGMA_FORGE,  "oe":"⬜"},
    "Adamantine":   {"i":{"Adamantite":3,"Coal":2},  "b":T.MAGMA_FORGE,  "oe":"✨"},
    "Iron Sword":   {"i":{"Iron Bar":1,"Wood":1},    "b":T.WORKSHOP,     "oe":"🗡️"},
    "Iron Armor":   {"i":{"Iron Bar":2},             "b":T.WORKSHOP,     "oe":"🛡️"},
    "Steel Sword":  {"i":{"Steel Bar":1,"Wood":1},   "b":T.MAGMA_FORGE,  "oe":"🗡️"},
    "Steel Armor":  {"i":{"Steel Bar":2},            "b":T.MAGMA_FORGE,  "oe":"🛡️"},
    "Crossbow":     {"i":{"Wood":2,"Iron Bar":1},    "b":T.WORKSHOP,     "oe":"🏹"},
    "Leather Armor":{"i":{"Leather":3},              "b":T.LEATHERWORK,  "oe":"🥋"},
    "Beer":         {"i":{"Food":2},                 "b":T.TAVERN,       "oe":"🍺"},
    "Bandage":      {"i":{"Wood":1},                 "b":T.HOSPITAL,     "oe":"🩹"},
    "Cut Gem":      {"i":{"Gem":1},                  "b":T.JEWELER,      "oe":"💎"},
    "Gold Statue":  {"i":{"Gold Bar":2,"Stone":1},   "b":T.WORKSHOP,     "oe":"🗿"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# WEATHER TYPES
# ═══════════════════════════════════════════════════════════════════════════════
WEATHER = {
    "Clear":   {"particle":"☀️","color":(255,255,200),"freq":0},
    "Rain":    {"particle":"💧","color":(100,150,255),"freq":3},
    "Snow":    {"particle":"❄️","color":(220,230,255),"freq":2},
    "Storm":   {"particle":"⚡","color":(255,255,100),"freq":5},
    "Fog":     {"particle":"🌫️","color":(180,180,190),"freq":1},
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════════
def gen_noise(w, h, sc=20, seed=None):
    rng = random.Random(seed)
    gw, gh = w//sc+3, h//sc+3
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    o = [[0.0]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x/sc, y/sc
            ix, iy = int(gx), int(gy)
            fx, fy = gx-ix, gy-iy
            fx = fx*fx*(3-2*fx); fy = fy*fy*(3-2*fy)
            o[y][x] = g[iy][ix]*(1-fx)*(1-fy)+g[iy][ix+1]*fx*(1-fy)+g[iy+1][ix]*(1-fx)*fy+g[iy+1][ix+1]*fx*fy
    return o


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD
# ═══════════════════════════════════════════════════════════════════════════════
class World:
    def __init__(self, seed=None):
        self.seed = seed or random.randint(0, 999999)
        self.rng = random.Random(self.seed)
        self.layers = []
        self.designations = {}
        self.revealed = None  # revealed[z][y][x] for fog of war
        self.generate()

    def generate(self):
        for z in range(MAX_Z):
            layer = [[T.GRASS]*MW for _ in range(MH)]
            if z == 0: self._gen_surface(layer)
            else: self._gen_underground(layer, z)
            self.layers.append(layer)
        # Fog of war: surface starts partially revealed
        self.revealed = [[[False]*MW for _ in range(MH)] for _ in range(MAX_Z)]
        sx, sy = self.find_start_pos()
        for dy in range(-15, 16):
            for dx in range(-15, 16):
                rx, ry = sx+dx, sy+dy
                if 0<=rx<MW and 0<=ry<MH:
                    self.revealed[0][ry][rx] = True

    def _gen_surface(self, L):
        el = gen_noise(MW,MH,18,self.seed)
        mo = gen_noise(MW,MH,14,self.seed+1)
        or_ = gen_noise(MW,MH,10,self.seed+2)
        for y in range(MH):
            for x in range(MW):
                e,m,o = el[y][x],mo[y][x],or_[y][x]
                if x<2 or x>=MW-2 or y<2 or y>=MH-2: L[y][x]=T.BEDROCK
                elif e<.28: L[y][x]=T.WATER
                elif e<.36: L[y][x]=T.DIRT
                elif e<.65: L[y][x]=T.TREE if (m>.55 and self.rng.random()<.30) else T.GRASS
                elif e<.74: L[y][x]=T.DIRT
                elif e<.84:
                    L[y][x]=T.STONE
                    if o>.86: L[y][x]=T.GEM_ORE
                    elif o>.82: L[y][x]=T.GOLD_ORE
                    elif o>.76: L[y][x]=T.IRON_ORE
                    elif o>.70: L[y][x]=T.COAL
                else: L[y][x]=T.WALL

    def _gen_underground(self, L, z):
        sn = gen_noise(MW,MH,12+2*z,self.seed+100*z)
        on = gen_noise(MW,MH,8+z,self.seed+200*z)
        cn = gen_noise(MW,MH,15,self.seed+300*z)
        for y in range(MH):
            for x in range(MW):
                if x<2 or x>=MW-2 or y<2 or y>=MH-2: L[y][x]=T.BEDROCK; continue
                c_ = cn[y][x]; o_ = on[y][x]
                if c_ < .25+.03*z:
                    L[y][x]=T.FLOOR
                    if self.rng.random()<.05: L[y][x]=T.MUSHROOM
                    elif c_<.18 and z>1: L[y][x]=T.WATER
                    elif c_<.15 and z>=5: L[y][x]=T.LAVA
                    continue
                L[y][x]=T.STONE
                if z>=1:
                    if o_>.90 and z>=4: L[y][x]=T.ADAMANTINE
                    elif o_>.88-.02*z and z>=3: L[y][x]=T.PLAT_ORE
                    elif o_>.85-.02*z and z>=3: L[y][x]=T.GEM_ORE
                    elif o_>.80-.03*z: L[y][x]=T.IRON_ORE
                    elif o_>.78 and z>=2: L[y][x]=T.GOLD_ORE
                    elif o_>.72: L[y][x]=T.COAL

    def get(self,x,y,z=0):
        if 0<=x<MW and 0<=y<MH and 0<=z<MAX_Z: return self.layers[z][y][x]
        return T.BEDROCK
    def set(self,x,y,z,t):
        if 0<=x<MW and 0<=y<MH and 0<=z<MAX_Z: self.layers[z][y][x]=t
    def walk(self,x,y,z=0): return self.get(x,y,z) in WALK
    def rev(self,x,y,z=0):
        if 0<=x<MW and 0<=y<MH and 0<=z<MAX_Z: return self.revealed[z][y][x]
        return False
    def reveal_around(self, cx, cy, z, r=10):
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if dx*dx+dy*dy <= r*r:
                    rx, ry = cx+dx, cy+dy
                    if 0<=rx<MW and 0<=ry<MH: self.revealed[z][ry][rx] = True

    def find_start_pos(self):
        best, bs = None, -999
        for _ in range(500):
            x,y = random.randint(12,MW-12), random.randint(12,MH-12)
            s = 0
            for dy in range(-3,4):
                for dx in range(-3,4):
                    t = self.get(x+dx,y+dy,0)
                    if t==T.GRASS: s+=2
                    elif t==T.TREE: s+=1
                    elif t in (T.WATER,T.BEDROCK): s-=5
            if s>bs: bs,s = s,(x,y)
        return best or (MW//2,MH//2)

    def count_bld(self, tt):
        c=0
        for z in range(MAX_Z):
            for y in range(MH):
                for x in range(MW):
                    if self.layers[z][y][x]==tt: c+=1
        return c


# ═══════════════════════════════════════════════════════════════════════════════
# A* PATHFINDING
# ═══════════════════════════════════════════════════════════════════════════════
def astar(w, s, g, ms=400, z=0):
    if s==g: return [s]
    if not w.walk(g[0],g[1],z): return None
    sx,sy=s; gx,gy=g
    op=deque([s]); cf={}; gs_={s:0}; vis=set(); fs={s:abs(gx-sx)+abs(gy-sy)}
    while op and len(vis)<ms:
        cur=min(op,key=lambda p:fs.get(p,9999))
        if cur==g:
            p=[]; n=cur
            while n in cf: p.append(n);n=cf[n]
            p.reverse(); return p
        op.remove(cur); vis.add(cur)
        cx,cy=cur
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
            nx,ny=cx+dx,cy+dy; nb=(nx,ny)
            if nb in vis or not w.walk(nx,ny,z): continue
            ng=gs_[cur]+1
            if ng<gs_.get(nb,9999):
                cf[nb]=cur; gs_[nb]=ng; fs_[nb]=ng+abs(gx-nx)+abs(gy-ny)
                if nb not in op: op.append(nb)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PARTICLES
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, z, text, color, life=40, vx=0, vy=-0.5):
        self.x=x; self.y=y; self.z=z; self.text=text; self.color=color
        self.life=life; self.ml=life; self.vx=vx; self.vy=vy
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.life-=1
        return self.life>0


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY
# ═══════════════════════════════════════════════════════════════════════════════
class Entity:
    def __init__(self, x, y, z, emoji, name):
        self.x=x; self.y=y; self.z=z; self.emoji=emoji; self.name=name
        self.path=[]; self.task=None; self.hp=100; self.max_hp=100
        self.atk=5; self.dfn=2; self.spd=.35; self.ma=0.0
        self.bob=0.0; self.bd=1; self.alive=True
    def move_tick(self, w):
        if self.path:
            self.ma+=self.spd
            while self.ma>=1. and self.path:
                self.ma-=1.; n=self.path[0]
                if w.walk(n[0],n[1],self.z): self.x,self.y=n; self.path.pop(0)
                else: self.path=[]; return False
            self.bob+=.08*self.bd
            if self.bob>1. or self.bob<0.: self.bd*=-1; self.bob=max(0,min(1,self.bob))
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# CORPSE
# ═══════════════════════════════════════════════════════════════════════════════
class Corpse:
    def __init__(self, x, y, z, name, emoji, is_dwarf=False):
        self.x=x; self.y=y; self.z=z; self.name=name
        self.emoji=emoji; self.is_dwarf=is_dwarf; self.timer=0


# ═══════════════════════════════════════════════════════════════════════════════
# TAMED ANIMAL
# ═══════════════════════════════════════════════════════════════════════════════
class TamedAnimal(Entity):
    def __init__(self, x, y, z, species):
        cd = CD[species]
        super().__init__(x, y, z, cd["e"], species)
        self.species = species; self.hp = cd["hp"]; self.max_hp = cd["hp"]
        self.atk = cd["a"]; self.dfn = cd["d"]; self.spd = cd["s"]
        self.owner = None; self.think_timer = random.randint(20,60)
        self.product_timer = 0; self.product_type = None
        # Production
        if species in ("Deer","Elk"): self.product_type = "Food"
        elif species == "Crocodile": self.product_type = "Leather"


# ═══════════════════════════════════════════════════════════════════════════════
# DWARF
# ═══════════════════════════════════════════════════════════════════════════════
class Dwarf(Entity):
    def __init__(self, x, y, z, name, prof):
        super().__init__(x, y, z, PE.get(prof,"🧑"), name)
        self.prof=prof; self.hunger=0; self.sleep=0; self.happy=75
        self.carrying=None; self.tt=random.randint(15,60); self.log=[]
        self.ct=None; self.weapon=None; self.armor=None; self.ranged=None
        self.skills={"mining":1,"woodcut":1,"fight":1,"craft":1,"heal":1,"tame":1}
        self.kills=0; self.xp=0; self.level=1
        self.mood=None; self.mood_timer=0; self.artifact_name=None
        # Profession bonuses
        pmap = {"Soldier":("fight",3,12,6,120),"Hunter":("fight",2,10,2,100),
                "Doctor":("heal",4,5,2,90),"Smith":("craft",3,6,2,95),
                "Miner":("mining",3,6,2,100),"Woodcutter":("woodcut",3,6,2,100),
                "Jeweler":("craft",3,5,2,90),"Engineer":("craft",2,6,3,100),
                "Leatherworker":("craft",2,5,2,90),"Brewer":("craft",2,5,2,90)}
        if prof in pmap:
            sk,sv,ba,bd,hp = pmap[prof]
            self.skills[sk]=sv; self.atk+=ba; self.dfn+=bd; self.max_hp=hp; self.hp=hp

    def eff_atk(self):
        b = 12 if self.weapon else 0
        if self.prof=="Soldier": b += self.skills["fight"]*2
        return self.atk + b + self.level
    def eff_def(self):
        b = 6 if self.armor else 0
        if self.prof=="Soldier": b += self.skills["fight"]
        return self.dfn + b + self.level//2
    def gain_xp(self, amt):
        self.xp += amt
        needed = self.level * 50
        while self.xp >= needed:
            self.xp -= needed; self.level += 1
            self.max_hp += 5; self.hp = min(self.hp+5, self.max_hp)
            needed = self.level * 50
            self.log_msg(f"Level up! Now Lv{self.level}")
    def log_msg(self, m):
        self.log.append(m)
        if len(self.log)>8: self.log.pop(0)


# ═══════════════════════════════════════════════════════════════════════════════
# CREATURE
# ═══════════════════════════════════════════════════════════════════════════════
class Creature(Entity):
    def __init__(self, x, y, z, species):
        cd=CD[species]
        super().__init__(x, y, z, cd["e"], species)
        self.species=species; self.hp=cd["hp"]; self.max_hp=cd["hp"]
        self.atk=cd["a"]; self.dfn=cd["d"]; self.spd=cd["s"]
        self.hostile=cd["h"]; self.ai=cd["ai"]; self.xp=cd["xp"]
        self.loot=cd["loot"]; self.pack=cd["pk"]; self.special=cd.get("special")
        self.nocturnal=cd.get("noct",False)
        self.tt=random.randint(10,40); self.flee_t=0


# ═══════════════════════════════════════════════════════════════════════════════
# GAME
# ═══════════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        pygame.init()
        self.scr = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("⛏️ Emoji Dwarf Fortress v3 ⛏️")
        self.clk = pygame.time.Clock()
        self.fe = pygame.font.Font("/usr/share/fonts/truetype/emoji/NotoColorEmoji.ttf", TS-5)
        self.fs = pygame.font.Font("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 11)
        self.fm = pygame.font.Font("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 13)
        self.ft = pygame.font.Font("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 15)
        self.fb = pygame.font.Font("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 20)

        # Cache emojis
        self.ec = {}
        all_e = set(TE.values())|set(PE.values())|set(c["e"] for c in CD.values())
        all_e.update(["🧑","📦","🗡️","🛡️","🍺","🩹","🥇","🥈","🔩","💥","✨","☠️","📢",
                      "🎵","💰","🥋","🧵","⚙️","🐊","🦉","🦋","🐀","🦀","😈","👻","🟢",
                      "🔥","❄️","⚡","🌧️","💀","⚰️","⛏️","🪓","🍄","🩶","⬜","➕"])
        for e in all_e: self.ec[e] = self.fe.render(e, True, (255,255,255))

        # State
        self.run_ = True; self.paused = False; self.tick = 0
        self.sel_d = None; self.sel_c = None
        self.mode = "normal"; self.bld_ch = None
        self.cx = 0; self.cy = 0; self.cz = 0
        self.help = True; self.mmap = True
        self.msgs = []; self.parts = []
        self.sn = ["Spring","Summer","Autumn","Winter"]
        self.season = 0; self.year = 1; self.day = 1
        self.gspd = 1; self.tkills = 0; self.wealth = 0
        self.res = {"Stone":10,"Wood":15,"Iron":0,"Gold":0,"Coal":0,"Food":30,
                    "Gem":0,"Platinum":0,"Adamantite":0,"Leather":0,
                    "Iron Bar":0,"Gold Bar":0,"Plat. Bar":0,"Steel Bar":0,"Adamantine":0,
                    "Iron Sword":0,"Iron Armor":0,"Steel Sword":0,"Steel Armor":0,
                    "Crossbow":0,"Leather Armor":0,"Beer":0,"Bandage":0,"Cut Gem":0}
        self.alert = 0; self.alert_t = 0
        self.nxt_migr = random.randint(400,800)
        self.nxt_siege = random.randint(700,1400)
        self.nxt_mega = random.randint(2500,5000)
        self.nxt_merch = random.randint(500,1000)
        self.nxt_mood = random.randint(300,700)
        self.cspawn_t = random.randint(60,180)
        self.craft_q = []
        self.creatures = []; self.corpses = []; self.tamed = []
        self.weather = "Clear"; self.weather_t = random.randint(200,600)
        self.weather_parts = []  # screen-space weather particles
        self.hour = 8; self.is_night = False
        self.night_alpha = 0  # dimming overlay
        self.fluid_timer = 0
        self.ui_scroll = 0  # scroll offset for dwarf list
        self.total_dead = 0
        self.artifacts = []
        self.festivals_held = 0

        # World
        self.world = World()
        sx, sy = self.world.find_start_pos()
        self.cx = sx - (SW-UPW)//(2*TS)
        self.cy = sy - SH//(2*TS)

        # Dwarves
        self.dwarves = []
        names = random.sample(DNAMES, 10)
        profs = ["Miner","Miner","Woodcutter","Farmer","Mason","Smith","Hunter",
                 "Soldier","Soldier","Doctor"]
        for i in range(10):
            dx,dy = sx+random.randint(-2,2), sy+random.randint(-2,2)
            self.dwarves.append(Dwarf(dx,dy,0,names[i],profs[i]))

        # Clear start
        for dy in range(-4,5):
            for dx in range(-4,5):
                t=self.world.get(sx+dx,sy+dy,0)
                if t in (T.TREE,T.STONE,T.IRON_ORE,T.GOLD_ORE,T.COAL,T.GEM_ORE):
                    self.world.set(sx+dx,sy+dy,0,T.GRASS)

        self.msg("Welcome to Emoji Dwarf Fortress v3! 10 dwarves have arrived!",(255,220,100))
        self.msg("New: Weather, Day/Night, Fog of War, Taming, Artifacts, Fluid Flow!",(150,255,200))
        self.msg("Press H for full help. Build Coffins to bury the dead!",(180,220,255))

    def msg(self, t, c=(220,220,220)):
        self.msgs.append((t,c))
        if len(self.msgs)>100: self.msgs.pop(0)

    def part(self, x, y, z, text, color, life=35, vx=0, vy=-0.5):
        self.parts.append(Particle(x, y, z, text, color, life, vx, vy))

    # ─── INPUT ───────────────────────────────────────────────────────────
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: self.run_ = False
            elif ev.type == pygame.KEYDOWN: self.handle_key(ev.key, ev.mod)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button in (1,3): self.handle_click(ev.button, ev.pos)
            elif ev.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                map_w = SW - UPW
                if mx >= map_w:
                    self.ui_scroll = max(0, self.ui_scroll - ev.y * 3)
                elif self.mode == "build":
                    idx = BL.index(self.bld_ch) if self.bld_ch in BL else 0
                    self.bld_ch = BL[(idx + ev.y) % len(BL)]

    def handle_key(self, k, m):
        if k == pygame.K_ESCAPE: self.mode="normal"; self.bld_ch=None
        elif k == pygame.K_SPACE: self.paused = not self.paused
        elif k == pygame.K_h: self.help = not self.help
        elif k == pygame.K_n: self.mmap = not self.mmap
        elif k == pygame.K_p: self.gspd = (self.gspd % 3) + 1
        elif k == pygame.K_q:
            self.cz = max(0, self.cz-1)
            self.msg(f"Z-Level: {self.cz} ({'Surface' if self.cz==0 else 'Underground '+str(self.cz)})", (180,180,220))
        elif k == pygame.K_e:
            self.cz = min(MAX_Z-1, self.cz+1)
            self.msg(f"Z-Level: {self.cz} ({'Surface' if self.cz==0 else 'Underground '+str(self.cz)})", (180,180,220))
        elif k == pygame.K_TAB:
            all_e = [(d,"d") for d in self.dwarves]+[(c,"c") for c in self.creatures if c.alive]
            if all_e:
                ci = -1
                if self.sel_d:
                    ci = next((i for i,(e,t) in enumerate(all_e) if t=="d" and e==self.sel_d), -1)
                elif self.sel_c:
                    ci = next((i for i,(e,t) in enumerate(all_e) if t=="c" and e==self.sel_c), -1)
                ni = (ci+1) % len(all_e); sel,typ = all_e[ni]
                if typ=="d": self.sel_d=sel; self.sel_c=None; self.cz=sel.z
                else: self.sel_c=sel; self.sel_d=None; self.cz=sel.z
        elif k == pygame.K_m:
            self.mode = "mine" if self.mode!="mine" else "normal"
            self.msg(f"Mode: {'Mine' if self.mode=='mine' else 'Normal'}", (255,180,100))
        elif k == pygame.K_c:
            self.mode = "chop" if self.mode!="chop" else "normal"
            self.msg(f"Mode: {'Chop' if self.mode=='chop' else 'Normal'}", (100,255,100))
        elif k == pygame.K_t:
            self.mode = "tame" if self.mode!="tame" else "normal"
            self.msg(f"Mode: {'Tame (click dead animal)' if self.mode=='tame' else 'Normal'}", (100,255,255))
        elif k == pygame.K_b:
            if self.mode=="build": self.mode="normal"; self.bld_ch=None
            else: self.mode="build"; self.bld_ch=BL[0]
            self.msg("Build: 1-0,-,=,[,],\\,;,',/, , <  click to place. Scroll to cycle.", (255,200,100))
        elif k == pygame.K_r: self.mode = "remove" if self.mode!="remove" else "normal"
        elif k == pygame.K_d:
            self.mode = "dig_stair" if self.mode!="dig_stair" else "normal"
            self.msg(f"Mode: {'Dig Stair' if self.mode=='dig_stair' else 'Normal'}", (200,200,100))
        elif k == pygame.K_k: self.equip_soldiers()
        elif k == pygame.K_g: self.auto_craft()
        elif k == pygame.K_f:
            if self.sel_d:
                self.cx=self.sel_d.x-(SW-UPW)//(2*TS); self.cy=self.sel_d.y-SH//(2*TS); self.cz=self.sel_d.z
        bk = {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2,pygame.K_4:3,pygame.K_5:4,
              pygame.K_6:5,pygame.K_7:6,pygame.K_8:7,pygame.K_9:8,pygame.K_0:9,
              pygame.K_MINUS:10,pygame.K_EQUALS:11,pygame.K_LEFTBRACKET:12,
              pygame.K_RIGHTBRACKET:13,pygame.K_BACKSLASH:14,pygame.K_SEMICOLON:15,
              pygame.K_QUOTE:16,pygame.K_SLASH:17,pygame.K_COMMA:18,pygame.K_PERIOD:19,
              pygame.K_LESS:20}
        if k in bk and self.mode=="build":
            idx=bk[k]
            if idx<len(BL): self.bld_ch=BL[idx]

    def handle_click(self, btn, pos):
        mx, my = pos; mw = SW-UPW
        if mx >= mw: return
        tx, ty = int(mx/TS+self.cx), int(my/TS+self.cy); z = self.cz
        if btn == 3:
            self.mode="normal"; self.bld_ch=None
            for d in self.dwarves:
                if d.x==tx and d.y==ty and d.z==z: self.sel_d=d; self.sel_c=None; return
            for c in self.creatures:
                if c.alive and c.x==tx and c.y==ty and c.z==z: self.sel_c=c; self.sel_d=None; return
            return

        if self.mode == "mine":
            tile = self.world.get(tx,ty,z)
            if tile in MINEABLE and tile != T.BEDROCK:
                k=(tx,ty,z)
                if k not in self.world.designations: self.world.designations[k]="mine"
                else: del self.world.designations[k]
        elif self.mode == "chop":
            if self.world.get(tx,ty,z)==T.TREE:
                k=(tx,ty,z)
                if k not in self.world.designations: self.world.designations[k]="chop"
                else: del self.world.designations[k]
        elif self.mode == "tame":
            # Check for nearby dead creature to tame from
            for co in self.corpses:
                if co.x==tx and co.y==ty and co.z==z and not co.is_dwarf:
                    self.tame_from_corpse(co); return
        elif self.mode == "dig_stair":
            tile = self.world.get(tx,ty,z)
            if tile in MINEABLE and z < MAX_Z-1:
                self.world.designations[(tx,ty,z)] = "dig_stair"
        elif self.mode == "build" and self.bld_ch:
            tile = self.world.get(tx,ty,z)
            if tile in (T.GRASS, T.DIRT, T.FLOOR):
                bd = BLD[self.bld_ch]
                can = all(self.res.get(r,0)>=a for r,a in bd["c"].items())
                if can:
                    for r,a in bd["c"].items(): self.res[r]-=a
                    self.world.set(tx,ty,z, bd["t"])
                    self.msg(f"Built {self.bld_ch} at ({tx},{ty})", (100,255,100))
                else: self.msg(f"Need resources for {self.bld_ch}!", (255,80,80))
        elif self.mode == "remove":
            tile = self.world.get(tx,ty,z)
            rem = {T.BED,T.TABLE,T.DOOR,T.WORKSHOP,T.FARM,T.STOCKPILE,T.BARRACKS,
                   T.HOSPITAL,T.TAVERN,T.SMELTER,T.TRAP,T.FORTIF,T.BRIDGE,T.PWALL,
                   T.COFFIN,T.JEWELER,T.LEATHERWORK,T.ANIMAL_PEN,T.WELL,T.STATUE,T.MAGMA_FORGE}
            if tile in rem: self.world.set(tx,ty,z, T.FLOOR)
        elif self.mode == "normal":
            for d in self.dwarves:
                if d.x==tx and d.y==ty and d.z==z: self.sel_d=d; self.sel_c=None; return
            for c in self.creatures:
                if c.alive and c.x==tx and c.y==ty and c.z==z: self.sel_c=c; self.sel_d=None; return
            self.sel_d=None; self.sel_c=None

    # ─── EQUIP & CRAFT ───────────────────────────────────────────────────
    def equip_soldiers(self):
        eq = 0
        for d in self.dwarves:
            if d.prof=="Soldier":
                if not d.weapon:
                    if self.res.get("Steel Sword",0)>0: self.res["Steel Sword"]-=1; d.weapon="steel"; eq+=1
                    elif self.res.get("Iron Sword",0)>0: self.res["Iron Sword"]-=1; d.weapon="iron"; eq+=1
                if not d.armor:
                    if self.res.get("Steel Armor",0)>0: self.res["Steel Armor"]-=1; d.armor="steel"; eq+=1
                    elif self.res.get("Iron Armor",0)>0: self.res["Iron Armor"]-=1; d.armor="iron"; eq+=1
                if not d.ranged and self.res.get("Crossbow",0)>0: self.res["Crossbow"]-=1; d.ranged=True; eq+=1
        if eq: self.msg(f"Equipped soldiers! ({eq} items)", (100,200,255))
        else: self.msg("Nothing to equip. Craft gear first! (G to auto-craft)", (255,180,100))

    def auto_craft(self):
        q=0
        for rn,rc in RECIPES.items():
            can = all(self.res.get(r,0)>=a for r,a in rc["i"].items())
            if can and rn not in [x[0] for x in self.craft_q]:
                self.craft_q.append((rn,rc)); q+=1
                for r,a in rc["i"].items(): self.res[r]-=a
        self.msg(f"Queued {q} craft(s)" if q else "Can't afford any recipes", (200,200,100) if q else (255,150,100))

    def process_craft(self):
        if not self.craft_q: return
        rn, rc = self.craft_q[0]
        if self.world.count_bld(rc["b"])>0:
            self.craft_q.pop(0)
            self.res[rn] = self.res.get(rn,0)+1
            self.msg(f"Crafted: {rn} {rc.get('oe','')}", (200,255,200))
        elif len(self.craft_q)>8:
            self.craft_q.pop(0)

    # ─── TAME ────────────────────────────────────────────────────────────
    def tame_from_corpse(self, corpse):
        # Create a tamed animal from a dead creature
        species = corpse.name
        if species in ("Rabbit","Fox","Deer","Elk","Crocodile","Owl","Giant Rat","Cave Crab"):
            ta = TamedAnimal(corpse.x, corpse.y, corpse.z, species)
            self.tamed.append(ta)
            self.corpses.remove(corpse)
            self.msg(f"🐕 Tamed a {species}! It will follow your dwarves.", (100,255,200))
            self.world.reveal_around(corpse.x, corpse.y, corpse.z, 5)
        else:
            self.msg(f"Cannot tame {species}.", (255,150,100))

    # ─── CORPSE BURIAL ───────────────────────────────────────────────────
    def check_burials(self):
        # Auto-bury dead dwarves if coffins exist
        unburied_dwarves = [c for c in self.corpses if c.is_dwarf]
        if not unburied_dwarves: return
        for z in range(MAX_Z):
            for y in range(MH):
                for x in range(MW):
                    if self.world.get(x,y,z) == T.COFFIN:
                        # Find nearest unburied corpse
                        for co in unburied_dwarves:
                            if abs(co.x-x)+abs(co.y-y) < 30 and co.z == z:
                                self.corpses.remove(co)
                                self.world.set(x, y, z, T.COFFIN)  # keep as coffin
                                unburied_dwarves.remove(co)
                                self.msg(f"⚰️ {co.name} was laid to rest in a coffin.", (180,180,200))
                                # Boost happiness of all dwarves
                                for d in self.dwarves: d.happy = min(100, d.happy+3)
                                return

    # ─── CREATURE SPAWNING ───────────────────────────────────────────────
    def spawn_creatures(self):
        self.cspawn_t -= 1
        if self.cspawn_t > 0: return
        self.cspawn_t = random.randint(80, 220)
        night_boost = 1 if self.is_night else 0
        for _ in range(10):
            sx = random.randint(5, MW-5); sy = random.randint(5, MH-5)
            cands = []
            for sp, cd in CD.items():
                zmin, zmax = cd["zr"]
                if self.cz < zmin or self.cz > zmax: continue
                if sp in ("Dragon","Titan","Hydra"): continue
                # Nocturnal boost
                if cd.get("noct") and not self.is_night and random.random() < 0.7: continue
                if cd.get("noct") and self.is_night: cands.append((sp, 2))
                else: cands.append((sp, 1))
            if not cands: return
            # Weighted choice
            pool = []
            for sp, w in cands:
                pool.extend([sp]*w)
            species = random.choice(pool)
            cd = CD[species]
            tile = self.world.get(sx, sy, self.cz)
            if cd["ai"]=="swim" and tile!=T.WATER: continue
            if cd["ai"]!="swim" and tile not in WALK: continue
            count = random.randint(1, cd["pk"])
            for _ in range(count):
                cx_, cy_ = sx+random.randint(-3,3), sy+random.randint(-3,3)
                if self.world.walk(cx_, cy_, self.cz):
                    self.creatures.append(Creature(cx_, cy_, self.cz, species))
            break

    # ─── CREATURE AI ─────────────────────────────────────────────────────
    def update_creatures(self):
        z = self.cz
        for c in self.creatures:
            if not c.alive or c.z != z: continue
            # Lava damage
            if self.world.get(c.x, c.y, c.z) == T.LAVA:
                c.hp -= 5; self.part(c.x, c.y, c.z, "🔥", (255,100,0))
                if c.hp <= 0: c.alive=False; self.creature_death(c); continue
            # Fire imp special: set fires near dwarves
            if c.special == "fire" and c.hostile and self.tick % 20 == 0:
                for d in self.dwarves:
                    if d.alive and d.z==c.z and abs(d.x-c.x)+abs(d.y-c.y)<=2:
                        d.hp -= 3; self.part(d.x, d.y, d.z, "🔥", (255,150,0))
                        d.log_msg("Burned by Fire Imp!")
            # Dragon fire breath
            if c.special == "fire_breath" and c.hostile and self.tick % 15 == 0:
                for d in self.dwarves:
                    if d.alive and d.z==c.z and abs(d.x-c.x)+abs(d.y-c.y)<=3:
                        dmg = random.randint(8, 15)
                        d.hp -= dmg; self.part(d.x, d.y, d.z, f"-{dmg}🔥", (255,50,0))
                        d.log_msg(f"Dragon breath! -{dmg}")
                self.part(c.x, c.y, c.z, "🔥🔥🔥", (255,100,0), 20)

            # Wraith phase through walls sometimes
            if c.special == "phase" and self.tick % 30 == 0:
                # Can briefly move through solid tiles
                pass

            c.tt -= 1
            if c.tt <= 0:
                c.tt = random.randint(15, 50)
                self.creature_think(c)
            # Attack nearby
            if c.hostile and c.ct is None:
                for d in self.dwarves:
                    if d.alive and d.z==c.z and abs(d.x-c.x)<=1 and abs(d.y-c.y)<=1:
                        c.ct = d; break
            if c.ct:
                t = c.ct
                if not t.alive or t.z != c.z: c.ct = None; continue
                if abs(t.x-c.x)+abs(t.y-c.y) <= 1:
                    self.combat(c, t)
                elif not c.path:
                    p = astar(self.world,(c.x,c.y),(t.x,t.y),200,c.z)
                    if p: c.path = p
                    else: c.ct = None
                c.move_tick(self.world)
            else:
                c.move_tick(self.world)

    def creature_think(self, c):
        ai = c.ai
        if ai == "flee":
            nr, nd = None, 999
            for d in self.dwarves:
                if d.alive and d.z==c.z:
                    dist = abs(d.x-c.x)+abs(d.y-c.y)
                    if dist<nd: nd=dist; nr=d
            if nr and nd<12:
                fx, fy = c.x-nr.x, c.y-nr.y
                fx, fy = max(-5,min(5,fx)), max(-5,min(5,fy))
                tx, ty = max(3,min(MW-3,c.x+fx)), max(3,min(MH-3,c.y+fy))
                if self.world.walk(tx,ty,c.z):
                    p = astar(self.world,(c.x,c.y),(tx,ty),150,c.z)
                    if p: c.path = p
                return
        elif ai == "ambush":
            # Crocodile: hide near water, attack when prey close
            nr, nd = None, 999
            for d in self.dwarves:
                if d.alive and d.z==c.z:
                    dist = abs(d.x-c.x)+abs(d.y-c.y)
                    if dist<nd: nd=dist; nr=d
            if nr and nd < 8:
                c.ct = nr
                p = astar(self.world,(c.x,c.y),(nr.x,nr.y),200,c.z)
                if p: c.path = p
                return
        elif ai == "hunt_dwarves":
            nr, nd = None, 999
            for d in self.dwarves:
                if d.alive and d.z==c.z:
                    dist = abs(d.x-c.x)+abs(d.y-c.y)
                    if dist<nd: nd=dist; nr=d
            if nr and nd<25:
                c.ct = nr
                if not c.path:
                    p = astar(self.world,(c.x,c.y),(nr.x,nr.y),200,c.z)
                    if p: c.path = p
                return
        elif ai == "hunt":
            if c.flee_t > 0: c.flee_t -= 1; return
            if c.hp < c.max_hp*0.3:
                fx, fy = random.randint(-5,5), random.randint(-5,5)
                tx = max(3,min(MW-3,c.x+fx)); ty = max(3,min(MH-3,c.y+fy))
                if self.world.walk(tx,ty,c.z):
                    p = astar(self.world,(c.x,c.y),(tx,ty),100,c.z)
                    if p: c.path = p
                c.flee_t = 20; return
        # Default wander
        if not c.path:
            wx, wy = c.x+random.randint(-6,6), c.y+random.randint(-6,6)
            wx, wy = max(3,min(MW-3,wx)), max(3,min(MH-3,wy))
            tile = self.world.get(wx,wy,c.z)
            if c.ai == "swim":
                if tile == T.WATER:
                    p = astar(self.world,(c.x,c.y),(wx,wy),80,c.z)
                    if p: c.path = p
            elif tile in WALK:
                p = astar(self.world,(c.x,c.y),(wx,wy),100,c.z)
                if p: c.path = p

    # ─── COMBAT ──────────────────────────────────────────────────────────
    def combat(self, atk, dfn):
        av = atk.eff_atk() if isinstance(atk, Dwarf) else atk.atk
        dv = dfn.eff_def() if isinstance(dfn, Dwarf) else dfn.dfn
        av = int(av * random.uniform(.7, 1.3))
        dv = int(dv * random.uniform(.7, 1.3))
        dmg = max(1, av - dv + random.randint(-2, 2))
        dfn.hp -= dmg
        col = (255,80,80) if isinstance(dfn, Dwarf) else (255,200,100)
        self.part(dfn.x, dfn.y, dfn.z, f"-{dmg}", col)

        if isinstance(atk, Dwarf):
            atk.gain_xp(dmg // 2)
            if isinstance(dfn, Creature): atk.log_msg(f"Hit {dfn.species} for {dmg}")
            elif isinstance(dfn, Dwarf): dfn.log_msg(f"Hit by {atk.name} for {dmg}!")
        elif isinstance(atk, Creature):
            if isinstance(dfn, Dwarf):
                dfn.log_msg(f"Hit by {atk.species} for {dmg}")
                dfn.happy = max(0, dfn.happy-5)

        if dfn.hp <= 0:
            dfn.alive = False
            if isinstance(dfn, Dwarf):
                self.msg(f"☠️ {dfn.name} the {dfn.prof} was slain!", (255,50,50))
                self.alert = max(self.alert, 1); self.alert_t = 200
                self.total_dead += 1
                self.corpses.append(Corpse(dfn.x, dfn.y, dfn.z, dfn.name, dfn.emoji, True))
                # Mood penalty
                for d in self.dwarves: d.happy = max(0, d.happy-10)
            elif isinstance(dfn, Creature) and isinstance(atk, Dwarf):
                self.msg(f"⚔️ {atk.name} slew {dfn.species}!", (100,255,100))
                atk.kills += 1; self.tkills += 1
                atk.gain_xp(dfn.xp)
                atk.happy = min(100, atk.happy+3)
                self.creature_death(dfn)

    def creature_death(self, c):
        if c.loot:
            for r, a in c.loot.items(): self.res[r] = self.res.get(r,0)+a
        self.corpses.append(Corpse(c.x, c.y, c.z, c.species, c.emoji, False))
        self.part(c.x, c.y, c.z, "💀", (200,50,50), 50)
        # Shaman heal special
        if c.special == "heal_ally":
            allies = [a for a in self.creatures if a.alive and a.z==c.z and a is not c
                      and a.species in ("Goblin","Gob. Chief","Gob. Shaman")
                      and abs(a.x-c.x)+abs(a.y-c.y)<8]
            for a in allies[:3]: a.hp = min(a.max_hp, a.hp+10)

    def soldiers_defend(self):
        for d in self.dwarves:
            if d.prof not in ("Soldier","Hunter") or not d.alive: continue
            if d.task and d.task.get("type")=="combat": continue
            nr, nd = None, 999
            for c in self.creatures:
                if c.alive and c.hostile and c.z==d.z:
                    dist = abs(c.x-d.x)+abs(c.y-d.y)
                    if dist<nd: nd=dist; nr=c
            if nr and nd < 18:
                d.ct = nr; d.task = {"type":"combat","target":(nr.x,nr.y)}
                d.path = astar(self.world,(d.x,d.y),(nr.x,nr.y),200,d.z)
                d.log_msg(f"Engaging {nr.species}!")
            # Ranged attack from fortifications
            if d.ranged and d.path and self.world.get(d.x,d.y,d.z) == T.FORTIF:
                for c in self.creatures:
                    if c.alive and c.hostile and c.z==d.z and abs(c.x-d.x)+abs(c.y-d.y) < 10:
                        dmg = random.randint(3, 8) + d.level
                        c.hp -= dmg; self.part(c.x, c.y, c.z, f"🏹-{dmg}", (255,220,100))
                        if c.hp <= 0:
                            c.alive = False; self.msg(f"🏹 {d.name} shot {c.species}!", (100,255,100))
                            d.kills += 1; self.tkills += 1; d.gain_xp(c.xp)
                            self.creature_death(c)
                        break
            if d.ct and d.ct.alive:
                if abs(d.ct.x-d.x)<=1 and abs(d.ct.y-d.y)<=1 and d.ct.z==d.z:
                    self.combat(d, d.ct)
                    if not d.ct.alive: d.ct=None; d.task=None

    # ─── WEATHER ─────────────────────────────────────────────────────────
    def update_weather(self):
        self.weather_t -= 1
        if self.weather_t <= 0:
            self.weather_t = random.randint(300, 800)
            if self.season == 3:  # Winter
                self.weather = random.choices(["Clear","Snow","Storm","Fog"], [2,4,2,2])[0]
            elif self.season == 2:  # Autumn
                self.weather = random.choices(["Clear","Rain","Storm","Fog"], [3,3,2,2])[0]
            else:  # Spring/Summer
                self.weather = random.choices(["Clear","Rain","Clear","Storm"], [4,2,3,1])[0]
            wd = WEATHER.get(self.weather, WEATHER["Clear"])
            self.msg(f"Weather: {self.weather} {wd['particle']}", (180,200,220))
            if self.weather == "Storm": self.alert = max(self.alert, 1); self.alert_t = 100

        # Spawn weather particles (screen space)
        wd = WEATHER.get(self.weather, WEATHER["Clear"])
        freq = wd["freq"]
        if freq > 0:
            for _ in range(freq):
                sx_ = random.randint(0, SW-UPW)
                sy_ = random.randint(-20, -5)
                vy = random.uniform(2, 5) if self.weather != "Snow" else random.uniform(0.5, 1.5)
                vx = random.uniform(-1, 1)
                col = wd["color"]
                self.weather_parts.append([sx_, sy_, vx, vy, col, random.randint(60, 120)])

        # Update weather particles
        new_wp = []
        for wp in self.weather_parts:
            wp[0] += wp[2]; wp[1] += wp[3]; wp[5] -= 1
            if wp[5] > 0 and wp[1] < SH: new_wp.append(wp)
        self.weather_parts = new_wp[-300:]  # cap particles

    # ─── DAY/NIGHT ───────────────────────────────────────────────────────
    def update_daynight(self):
        self.hour += 0.005 * self.gspd  # ~1 game hour per ~200 ticks
        if self.hour >= 24: self.hour -= 24
        # Night is 20:00 - 06:00
        was_night = self.is_night
        self.is_night = self.hour >= 20 or self.hour < 6
        if self.is_night != was_night and self.is_night:
            self.msg("🌙 Night falls. Nocturnal creatures are more active!", (100,100,180))
        elif self.is_night != was_night:
            self.msg("☀️ Dawn breaks!", (255,220,100))
        # Smooth alpha transition
        target_a = 80 if self.is_night else 0
        self.night_alpha += (target_a - self.night_alpha) * 0.02

    # ─── FLUID FLOW ──────────────────────────────────────────────────────
    def update_fluids(self):
        self.fluid_timer += 1
        if self.fluid_timer < 10: return
        self.fluid_timer = 0
        z = self.cz
        # Simple: water/lava spreads to adjacent floor tiles
        to_flood = []
        for y in range(1, MH-1):
            for x in range(1, MW-1):
                tile = self.world.get(x, y, z)
                if tile == T.WATER:
                    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                        nx, ny = x+dx, y+dy
                        if self.world.get(nx,ny,z) == T.FLOOR and random.random() < 0.01:
                            to_flood.append((nx, ny, z, T.WATER))
                elif tile == T.LAVA:
                    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                        nx, ny = x+dx, y+dy
                        nt = self.world.get(nx, ny, z)
                        if nt == T.FLOOR and random.random() < 0.005:
                            to_flood.append((nx, ny, z, T.LAVA))
                        elif nt == T.WATER and random.random() < 0.1:
                            to_flood.append((nx, ny, z, T.STONE))  # obsidian
        for fx, fy, fz, ft in to_flood:
            self.world.set(fx, fy, fz, ft)

    # ─── MOOD / ARTIFACT ─────────────────────────────────────────────────
    def check_moods(self):
        self.nxt_mood -= 1
        if self.nxt_mood > 0: return
        self.nxt_mood = random.randint(500, 1200)
        # Pick a random dwarf
        candidates = [d for d in self.dwarves if d.alive and d.mood is None and d.happy > 50]
        if not candidates: return
        d = random.choice(candidates)
        mood_types = ["inspired", "possessed", "fey"]
        mood = random.choice(mood_types)
        d.mood = mood; d.mood_timer = random.randint(200, 400)
        self.msg(f"✨ {d.name} is {mood}! They need a workshop...", (200,200,255))
        d.log_msg(f"Struck by a {mood} mood!")

        # Check for workshop access
        has_workshop = self.world.count_bld(T.WORKSHOP) > 0
        has_jeweler = self.world.count_bld(T.JEWELER) > 0
        has_smelter = self.world.count_bld(T.SMELTER) > 0

    def update_moods(self):
        for d in self.dwarves:
            if d.mood is None: continue
            d.mood_timer -= 1
            if d.mood_timer <= 0:
                # Check if near workshop
                near_ws = False
                for dy in range(-5, 6):
                    for dx in range(-5, 6):
                        t = self.world.get(d.x+dx, d.y+dy, d.z)
                        if t in (T.WORKSHOP, T.JEWELER, T.SMELTER, T.MAGMA_FORGE):
                            near_ws = True; break
                    if near_ws: break
                if near_ws:
                    # Create artifact!
                    art_names = ["Sparkleliminals", "Dungeonbanes", "Earthgilds",
                                 "Ironthunders", "Gembloods", "Flamekisses",
                                 "Moorwhispers", "Starbreakers", "Doomhammers",
                                 "Lavablesseds", "Crystalhearts", "Shadowwebs"]
                    art = f"'{random.choice(art_names)}'"
                    d.artifact_name = art
                    self.artifacts.append({"name": art, "creator": d.name, "type": d.prof})
                    self.wealth += 100
                    d.happy = 100; d.gain_xp(100)
                    self.msg(f"🌟 {d.name} created {art}, a legendary artifact!", (255,255,100))
                    d.log_msg(f"Created {art}!")
                    # Bonus resources
                    bonus = random.choice(["Gem","Gold","Platinum"])
                    self.res[bonus] = self.res.get(bonus, 0) + random.randint(2, 5)
                else:
                    # Failed mood - goes melancholy
                    d.happy = max(0, d.happy - 30)
                    self.msg(f"😢 {d.name} couldn't find a workshop... melancholy.", (150,150,200))
                    d.log_msg("Failed to create artifact...")
                d.mood = None

    # ─── EVENTS ──────────────────────────────────────────────────────────
    def check_events(self):
        self.nxt_migr -= 1
        if self.nxt_migr <= 0:
            self.nxt_migr = random.randint(500, 1000)
            if len(self.dwarves) < 25 and self.alert == 0:
                cnt = random.randint(1, 3)
                avail = [n for n in DNAMES if n not in [d.name for d in self.dwarves]]
                profs = random.choices(PROFS, k=min(cnt, len(avail)))
                names = random.sample(avail, min(cnt, len(avail)))
                sx, sy = self.world.find_start_pos()
                for i in range(min(cnt, len(names))):
                    self.dwarves.append(Dwarf(sx+random.randint(-2,2), sy+random.randint(-2,2), 0, names[i], profs[i]))
                self.msg(f"🎉 {min(cnt, len(names))} migrant(s) arrived! Pop: {len(self.dwarves)}", (100,255,100))

        self.nxt_siege -= 1
        if self.nxt_siege <= 0:
            self.nxt_siege = random.randint(800, 1800)
            if self.year >= 1 and len(self.dwarves) > 3: self.trigger_siege()

        self.nxt_mega -= 1
        if self.nxt_mega <= 0:
            self.nxt_mega = random.randint(3500, 7000)
            if self.wealth > 150: self.trigger_megabeast()

        self.nxt_merch -= 1
        if self.nxt_merch <= 0:
            self.nxt_merch = random.randint(600, 1200)
            self.trigger_merchant()

        self.check_moods()

        if self.alert_t > 0: self.alert_t -= 1
        else: self.alert = max(0, self.alert-1)

        # Festival event
        if self.tick % 2000 == 0 and self.world.count_bld(T.TAVERN) > 0:
            self.festivals_held += 1
            for d in self.dwarves: d.happy = min(100, d.happy + 15)
            self.msg(f"🎉 Festival #{self.festivals_held} at the tavern! +15 happiness all!", (255,220,100))

        # Cave-in event (rare)
        if random.random() < 0.0003:
            cx_, cy_ = random.randint(5, MW-5), random.randint(5, MH-5)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    t = self.world.get(cx_+dx, cy_+dy, self.cz)
                    if t in (T.FLOOR, T.FARM, T.MUSHROOM):
                        self.world.set(cx_+dx, cy_+dy, self.cz, T.STONE)
            self.msg(f"⚠️ Cave-in at ({cx_},{cy_})! Be careful underground!", (255,180,50))

    def trigger_siege(self):
        cnt = random.randint(4,8) + self.year
        sx = random.choice([random.randint(3,10), random.randint(MW-10,MW-3)])
        sy = random.randint(3, MH-3)
        has_shaman = self.year >= 2 and random.random() < 0.3
        species_pool = ["Goblin"] * 3 + ["Goblin", "Goblin", "Gob. Chief"]
        if has_shaman: species_pool.append("Gob. Shaman")
        for i in range(cnt):
            sp = random.choice(species_pool)
            cx_, cy_ = sx+random.randint(-3,3), sy+random.randint(-3,3)
            if self.world.walk(cx_, cy_, 0):
                self.creatures.append(Creature(cx_, cy_, 0, sp))
        title = "GOBLIN SIEGE!" + (" (Shaman!)" if has_shaman else "")
        self.msg(f"📢⚠️ {title} {cnt} attackers!", (255,50,50))
        self.alert = 2; self.alert_t = 300

    def trigger_megabeast(self):
        sp = random.choice(["Dragon", "Titan", "Hydra"])
        sx = random.choice([random.randint(3,10), random.randint(MW-10,MW-3)])
        sy = random.randint(3, MH-3)
        if self.world.walk(sx, sy, 0):
            self.creatures.append(Creature(sx, sy, 0, sp))
        self.msg(f"📢🔥 A {sp.upper()} has come! {CD[sp]['e']}", (255,0,0))
        self.alert = 3; self.alert_t = 600

    def trigger_merchant(self):
        gifts = {"Food": random.randint(5,20), "Wood": random.randint(3,10)}
        if self.year >= 2: gifts["Iron"] = random.randint(2, 5)
        for r, a in gifts.items(): self.res[r] += a
        self.msg(f"🚚 Merchants arrive! +{gifts}", (255,220,100))

    # ─── TAMED ANIMALS ───────────────────────────────────────────────────
    def update_tamed(self):
        for a in self.tamed:
            if not a.alive: continue
            # Follow nearest dwarf loosely
            a.tt -= 1
            if a.tt <= 0:
                a.tt = random.randint(30, 80)
                nr, nd = None, 999
                for d in self.dwarves:
                    if d.alive and d.z == a.z:
                        dist = abs(d.x-a.x)+abs(d.y-a.y)
                        if dist < nd: nd=dist; nr=d
                if nr and nd > 6:
                    tx = nr.x + random.randint(-3,3)
                    ty = nr.y + random.randint(-3,3)
                    tx, ty = max(3,min(MW-3,tx)), max(3,min(MH-3,ty))
                    if self.world.walk(tx,ty,a.z):
                        p = astar(self.world,(a.x,a.y),(tx,ty),100,a.z)
                        if p: a.path = p
            a.move_tick(self.world)
            # Production
            if a.product_type and self.tick % 200 == 0:
                self.res[a.product_type] = self.res.get(a.product_type, 0) + 1
        self.tamed = [a for a in self.tamed if a.alive]

    # ─── UPDATE ──────────────────────────────────────────────────────────
    def update(self):
        if self.paused: return
        for _ in range(self.gspd):
            self.tick += 1
            keys = pygame.key.get_pressed()
            spd = 3 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.cx -= spd
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.cx += spd
            if keys[pygame.K_UP] or keys[pygame.K_w]: self.cy -= spd
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.cy += spd
            mb = pygame.mouse.get_pressed()
            if mb[2]:
                mx_, my_ = pygame.mouse.get_rel()
                self.cx -= mx_//TS; self.cy -= my_//TS

            if self.tick % 90 == 0:
                self.day += 1
                if self.day > 30:
                    self.day = 1; self.season = (self.season+1)%4
                    if self.season == 0: self.year += 1
                    if self.season == 2:
                        farms = self.world.count_bld(T.FARM)
                        if farms: self.res["Food"] += farms*3
                        self.msg(f"🌾 Harvest! +{farms*3} food", (255,220,100))

            if self.tick % 30 == 0:
                farms = self.world.count_bld(T.FARM)
                if farms: self.res["Food"] += max(1, farms//3)
            if self.tick % 50 == 0:
                tav = self.world.count_bld(T.TAVERN)
                if tav and self.res.get("Food",0)>=4 and self.res.get("Beer",0)<15:
                    self.res["Food"] -= 2; self.res["Beer"] += 1
            if self.tick % 60 == 0: self.process_craft()

            # Reveal around dwarves
            if self.tick % 10 == 0:
                for d in self.dwarves:
                    if d.alive: self.world.reveal_around(d.x, d.y, d.z, 12)

            for d in self.dwarves:
                if d.alive: self.update_dwarf(d)
            self.dwarves = [d for d in self.dwarves if d.alive]

            self.spawn_creatures()
            self.update_creatures()
            self.soldiers_defend()
            self.creatures = [c for c in self.creatures if c.alive]
            self.parts = [p for p in self.parts if p.update()]

            self.update_weather()
            self.update_daynight()
            self.update_fluids()
            self.update_moods()
            self.update_tamed()

            if self.tick % 30 == 0:
                self.check_events()
                self.check_burials()

            self.wealth = sum(v*({"Gold":10,"Gem":20,"Platinum":15,"Gold Bar":25,"Plat. Bar":30,
                                   "Steel Bar":35,"Adamantine":50,"Iron Sword":8,"Iron Armor":12,
                                   "Steel Sword":20,"Steel Armor":25,"Cut Gem":25}.get(k,1))
                           for k,v in self.res.items())
            self.wealth += len(self.artifacts) * 100

    def update_dwarf(self, d):
        if self.tick % 40 == 0:
            d.hunger = min(100, d.hunger+1); d.sleep = min(100, d.sleep+1)
        if d.hunger > 55:
            if self.res.get("Food",0)>0:
                self.res["Food"] -= 1; d.hunger = max(0,d.hunger-40); d.log_msg("Ate food")
            elif self.res.get("Beer",0)>0:
                self.res["Beer"] -= 1; d.hunger = max(0,d.hunger-25); d.happy = min(100,d.happy+2)
        if d.hunger >= 100:
            d.hp -= 1
            if self.tick % 60 == 0: d.log_msg("Starving! ☠️")
        if d.sleep > 75 and not d.task:
            for dy in range(-12,13):
                for dx in range(-12,13):
                    if self.world.get(d.x+dx,d.y+dy,d.z)==T.BED:
                        d.task={"type":"sleep","target":(d.x+dx,d.y+dy,d.z)}; d.log_msg("Going to sleep"); break
                if d.task: break
            if not d.task: d.sleep = max(0,d.sleep-1)
        if d.task and d.task["type"]=="sleep":
            tz = d.task["target"]
            if (d.x,d.y,d.z)==tz:
                d.sleep = max(0,d.sleep-3)
                if d.sleep < 10: d.task = None; d.log_msg("Woke up!")
            else: self.move_to(d, tz[:2], tz[2])
            return
        if d.ct and d.ct.alive:
            ct = d.ct
            if ct.z==d.z and abs(ct.x-d.x)<=1 and abs(ct.y-d.y)<=1:
                self.combat(d, ct)
                if not ct.alive: d.ct=None; d.task=None
            else: self.move_to(d, (ct.x,ct.y), d.z)
            return
        else: d.ct = None

        d.tt -= 1
        if d.tt <= 0:
            d.tt = random.randint(20,60)
            self.assign_task(d)
        if d.path:
            d.move_tick(self.world)
            if not d.path: self.complete_task(d)
        d.bob += .08*d.bd
        if d.bob>1 or d.bob<0: d.bd*=-1; d.bob=max(0,min(1,d.bob))
        if d.hunger > 65: d.happy = max(0,d.happy-.3)
        elif d.hunger < 25: d.happy = min(100,d.happy+.1)
        if d.sleep > 65: d.happy = max(0,d.happy-.2)
        if self.world.get(d.x,d.y,d.z)==T.TAVERN and not d.path:
            d.happy = min(100,d.happy+.15)
        if self.world.get(d.x,d.y,d.z)==T.HOSPITAL and not d.path and d.hp<d.max_hp:
            d.hp = min(d.max_hp, d.hp+.3)
        if self.world.get(d.x,d.y,d.z)==T.BARRACKS and d.prof=="Soldier" and not d.path:
            d.skills["fight"] = min(10, d.skills["fight"]+.01)
        # Statue happiness
        if self.world.get(d.x,d.y,d.z)==T.STATUE and not d.path:
            d.happy = min(100, d.happy+.2)
        # Well water bonus
        if self.world.get(d.x,d.y,d.z)==T.WELL and not d.path:
            d.happy = min(100, d.happy+.1)
        if not d.task: d.happy = max(0,d.happy-.05)

    def move_to(self, d, target, z):
        if (d.x,d.y)==target: return True
        if not d.path:
            p = astar(self.world,(d.x,d.y),target,300,z)
            if p: d.path = p
            else: d.task=None; d.ct=None; return False
        return False

    def assign_task(self, d):
        if d.task: return
        # Mine
        if d.prof in ("Miner","Mason") or random.random()<.4:
            mines = [p for p,t in self.world.designations.items() if t=="mine" and p[2]==d.z]
            if mines:
                mines.sort(key=lambda p: abs(p[0]-d.x)+abs(p[1]-d.y))
                tgt = mines[0]
                d.task={"type":"mine","target":tgt}; d.log_msg(f"Mining at {tgt[:2]}")
                self.move_to(d, tgt[:2], tgt[2]); return
        # Stairs
        stairs = [p for p,t in self.world.designations.items() if t=="dig_stair" and p[2]==d.z]
        if stairs and d.prof=="Miner":
            stairs.sort(key=lambda p: abs(p[0]-d.x)+abs(p[1]-d.y))
            tgt = stairs[0]
            d.task={"type":"dig_stair","target":tgt}; d.log_msg("Digging stair")
            self.move_to(d, tgt[:2], tgt[2]); return
        # Chop
        if d.prof=="Woodcutter" or random.random()<.3:
            chops = [p for p,t in self.world.designations.items() if t=="chop" and p[2]==d.z]
            if chops:
                chops.sort(key=lambda p: abs(p[0]-d.x)+abs(p[1]-d.y))
                tgt = chops[0]
                d.task={"type":"chop","target":tgt}; d.log_msg("Chopping tree")
                self.move_to(d, tgt[:2], tgt[2]); return
        # Wander
        wx, wy = d.x+random.randint(-6,6), d.y+random.randint(-6,6)
        wx, wy = max(3,min(MW-3,wx)), max(3,min(MH-3,wy))
        if self.world.walk(wx,wy,d.z):
            d.task={"type":"wander","target":(wx,wy,d.z)}

    def complete_task(self, d):
        if not d.task: return
        t = d.task
        if t["type"] == "mine":
            tx,ty,tz = t["target"]
            tile = self.world.get(tx,ty,tz)
            self.world.set(tx,ty,tz, T.FLOOR)
            drops = {T.STONE:("Stone",1),T.IRON_ORE:("Iron",1),T.GOLD_ORE:("Gold",1),
                     T.COAL:("Coal",1),T.WALL:("Stone",1),T.GEM_ORE:("Gem",1),
                     T.PLAT_ORE:("Platinum",1),T.ADAMANTINE:("Adamantite",1)}
            if tile in drops:
                rn, amt = drops[tile]; self.res[rn] += amt; d.log_msg(f"Mined {rn}")
                d.gain_xp(2)
            if (tx,ty,tz) in self.world.designations: del self.world.designations[(tx,ty,tz)]
            d.happy = min(100, d.happy+2)
        elif t["type"] == "dig_stair":
            tx,ty,tz = t["target"]
            self.world.set(tx,ty,tz, T.STAIR_DN)
            if tz+1 < MAX_Z: self.world.set(tx,ty,tz+1, T.STAIR_UP)
            d.log_msg("Dug stairs!")
            if (tx,ty,tz) in self.world.designations: del self.world.designations[(tx,ty,tz)]
            self.msg(f"🔽 Stairs to Z{tz+1}!", (200,200,100))
            d.gain_xp(3)
        elif t["type"] == "chop":
            tx,ty,tz = t["target"]
            self.world.set(tx,ty,tz, T.GRASS)
            self.res["Wood"] += 2; d.log_msg("Chopped tree 🪓")
            d.gain_xp(1)
            if (tx,ty,tz) in self.world.designations: del self.world.designations[(tx,ty,tz)]
        d.task = None

    # ─── RENDER ──────────────────────────────────────────────────────────
    def render(self):
        self.scr.fill((16, 14, 20))
        mw = SW - UPW
        z = self.cz
        sx0 = max(0, int(self.cx)); sy0 = max(0, int(self.cy))
        sx1 = min(MW, sx0 + mw//TS + 2); sy1 = min(MH, sy0 + SH//TS + 2)

        # Tiles
        for ty in range(sy0, sy1):
            for tx in range(sx0, sx1):
                # Fog of war
                if not self.world.rev(tx, ty, z):
                    pygame.draw.rect(self.scr, (10,10,15), (int((tx-self.cx)*TS), int((ty-self.cy)*TS), TS, TS))
                    continue
                tile = self.world.get(tx, ty, z)
                px = int((tx-self.cx)*TS); py = int((ty-self.cy)*TS)
                if px+TS<0 or py+TS<0 or px>mw or py>SH: continue
                bg = TBG.get(tile, (40,40,40))
                v = ((tx*7+ty*13)%10)-5
                bg = tuple(max(0,min(255,c+v)) for c in bg)
                pygame.draw.rect(self.scr, bg, (px, py, TS, TS))
                gc = tuple(max(0,c-12) for c in bg)
                pygame.draw.rect(self.scr, gc, (px, py, TS, TS), 1)
                emoji = TE.get(tile)
                if emoji and emoji in self.ec: self.scr.blit(self.ec[emoji], (px, py))
                dk = (tx,ty,z)
                if dk in self.world.designations:
                    desg = self.world.designations[dk]
                    col = (255,200,50) if desg=="mine" else (100,255,100) if desg=="chop" else (200,200,100)
                    pulse = abs(math.sin(self.tick*.1))*.5+.5
                    ms = pygame.Surface((TS,TS), pygame.SRCALPHA)
                    pygame.draw.rect(ms, (*col, int(80*pulse)), (0,0,TS,TS), 3)
                    self.scr.blit(ms, (px, py))

        # Corpses
        for co in self.corpses:
            if co.z != z: continue
            px, py = int((co.x-self.cx)*TS), int((co.y-self.cy)*TS)
            if px+TS<0 or py+TS<0 or px>mw or py>SH: continue
            co_emoji = "☠️" if co.is_dwarf else co.emoji
            if co_emoji in self.ec:
                s = self.ec[co_emoji].copy(); s.set_alpha(140)
                self.scr.blit(s, (px, py))

        # Tamed animals
        for a in self.tamed:
            if a.z != z: continue
            px, py = int((a.x-self.cx)*TS), int((a.y-self.cy)*TS)
            if px+TS<0 or py+TS<0 or px>mw or py>SH: continue
            es = self.ec.get(a.emoji)
            if es:
                bob = int(a.bob*2) if a.path else 0
                self.scr.blit(es, (px, py-bob))
                # Heart indicator
                hs = self.ec.get("💕")
                if hs:
                    sm = pygame.transform.smoothscale(hs, (TS//3, TS//3))
                    self.scr.blit(sm, (px+TS-6, py-4))

        # Creatures
        for c in self.creatures:
            if not c.alive or c.z != z: continue
            px, py = int((c.x-self.cx)*TS), int((c.y-self.cy)*TS)
            if px+TS<0 or py+TS<0 or px>mw or py>SH: continue
            es = self.ec.get(c.emoji)
            if es:
                bob = int(c.bob*2) if c.path else 0
                self.scr.blit(es, (px, py-bob))
            if c.hp < c.max_hp:
                ratio = c.hp/c.max_hp
                pygame.draw.rect(self.scr, (60,0,0), (px,py-4,TS,3))
                bc = (0,200,0) if ratio>.5 else (200,200,0) if ratio>.25 else (200,0,0)
                pygame.draw.rect(self.scr, bc, (px,py-4,int(TS*ratio),3))
            if c == self.sel_c:
                ps = abs(math.sin(self.tick*.15))*100+155
                ss = pygame.Surface((TS,TS), pygame.SRCALPHA)
                pygame.draw.rect(ss, (255,100,100,int(ps)), (0,0,TS,TS), 2)
                self.scr.blit(ss, (px, py))

        # Dwarves
        for d in self.dwarves:
            if d.z != z: continue
            px, py = int((d.x-self.cx)*TS), int((d.y-self.cy)*TS)
            if px+TS<0 or py+TS<0 or px>mw or py>SH: continue
            es = self.ec.get(d.emoji)
            if es:
                bob = int(d.bob*2) if d.path else 0
                self.scr.blit(es, (px, py-bob))
                if d.weapon or d.armor:
                    ind = "🗡️" if d.weapon else "🛡️"
                    isf = self.ec.get(ind)
                    if isf:
                        sm = pygame.transform.smoothscale(isf, (TS//2, TS//2))
                        self.scr.blit(sm, (px+TS//2, py-TS//3))
                if d.mood:
                    me = "✨" if d.mood == "inspired" else "🌀" if d.mood == "possessed" else "😤"
                    msf = self.ec.get(me)
                    if msf:
                        sm = pygame.transform.smoothscale(msf, (TS//2, TS//2))
                        self.scr.blit(sm, (px, py-TS//2))
            if d == self.sel_d:
                ps = abs(math.sin(self.tick*.15))*100+155
                ss = pygame.Surface((TS,TS), pygame.SRCALPHA)
                pygame.draw.rect(ss, (255,255,100,int(ps)), (0,0,TS,TS), 2)
                self.scr.blit(ss, (px, py))
            if d.hp < d.max_hp:
                ratio = d.hp/d.max_hp
                pygame.draw.rect(self.scr, (60,0,0), (px,py-5,TS,3))
                bc = (0,200,0) if ratio>.5 else (200,200,0) if ratio>.25 else (200,0,0)
                pygame.draw.rect(self.scr, bc, (px,py-5,int(TS*ratio),3))
            if d.task and d.path:
                im = {"mine":"⛏️","chop":"🪓","dig_stair":"🔽","combat":"⚔️"}.get(d.task.get("type",""),"🚶")
                isf = self.ec.get(im)
                if isf:
                    sm = pygame.transform.smoothscale(isf, (TS//2, TS//2))
                    self.scr.blit(sm, (px+TS//2, py-TS//3))

        # Floating particles
        for p in self.parts:
            if p.z != z: continue
            ppx = int((p.x-self.cx)*TS + TS//2)
            ppy = int((p.y-self.cy)*TS + (p.ml-p.life)*.8)
            alpha = min(255, int(255*p.life/p.ml))
            ps = self.fm.render(p.text, True, p.color); ps.set_alpha(alpha)
            self.scr.blit(ps, (ppx-ps.get_width()//2, ppy))

        # Weather particles (screen space)
        for wp in self.weather_parts:
            if len(wp) >= 6:
                x_, y_, _, _, col, life = wp
                alpha = min(200, life * 3)
                s = pygame.Surface((2, 6), pygame.SRCALPHA)
                s.fill((*col, alpha))
                self.scr.blit(s, (int(x_), int(y_)))

        # Night overlay
        if self.night_alpha > 1:
            ns = pygame.Surface((mw, SH), pygame.SRCALPHA)
            ns.fill((10, 10, 40, int(self.night_alpha)))
            self.scr.blit(ns, (0, 0))

        # Mode cursor
        if self.mode != "normal" and not pygame.mouse.get_pressed()[2]:
            mx_, my_ = pygame.mouse.get_pos()
            if mx_ < mw:
                htx = int(mx_/TS+self.cx); hty = int(my_/TS+self.cy)
                hsx = int((htx-self.cx)*TS); hsy = int((hty-self.cy)*TS)
                cs = pygame.Surface((TS,TS), pygame.SRCALPHA)
                cc = {"mine":(255,200,50,100),"chop":(100,255,100,100),"build":(100,200,255,100),
                      "remove":(255,100,100,100),"dig_stair":(200,200,100,100),
                      "tame":(100,255,255,100)}.get(self.mode,(255,255,255,80))
                pygame.draw.rect(cs, cc, (0,0,TS,TS), 0)
                pygame.draw.rect(cs, (255,255,255,180), (0,0,TS,TS), 2)
                self.scr.blit(cs, (hsx, hsy))

        # ── UI PANEL ──────────────────────────────────────────────────────
        px = SW - UPW
        pygame.draw.rect(self.scr, (26,24,31), (px, 0, UPW, SH))
        pygame.draw.line(self.scr, (50,45,60), (px, 0), (px, SH), 2)
        py = 5

        # Title
        self.scr.blit(self.fb.render("⛏️ Emoji Dwarf Fortress v3", True, (255,220,150)), (px+8, py)); py+=24

        # Alert
        if self.alert > 0:
            am = {1:"⚠️ DANGER", 2:"⚠️ SIEGE!", 3:"🔥 MEGABEAST!"}
            ac = {1:(255,200,50), 2:(255,80,50), 3:(255,0,0)}
            pulse = abs(math.sin(self.tick*.15))
            c = tuple(int(v*pulse+100*(1-pulse)) for v in ac[self.alert])
            self.scr.blit(self.ft.render(am[self.alert], True, c), (px+8, py)); py+=16

        # Weather & Time
        wd = WEATHER.get(self.weather, WEATHER["Clear"])
        time_str = f"{int(self.hour):02d}:00 {'🌙' if self.is_night else '☀️'}"
        weather_str = f"{wd['particle']} {self.weather}"
        self.scr.blit(self.fs.render(f"{time_str}  {weather_str}", True, (180,190,210)), (px+8, py)); py+=14

        # Date & Z
        sc = [(150,255,150),(255,255,100),(255,180,100),(180,200,255)]
        self.scr.blit(self.fs.render(f"{self.sn[self.season]} Y{self.year} D{self.day}  Z:{self.cz}  Pop:{len(self.dwarves)}", True, sc[self.season]), (px+8, py)); py+=14
        sp = f"Spd:{'>'*self.gspd} {'⏸PAUSED' if self.paused else ''}"
        self.scr.blit(self.fs.render(sp, True, (140,140,140)), (px+8, py)); py+=13
        mt = f"Mode:{self.mode.upper()}" + (f" [{self.bld_ch}]" if self.bld_ch else "")
        self.scr.blit(self.fm.render(mt, True, (255,200,100) if self.mode!="normal" else (130,130,130)), (px+8, py)); py+=16

        # Stats line
        cret_z = len([c for c in self.creatures if c.alive and c.z==z])
        tamed_n = len(self.tamed)
        stats = f"Kills:{self.tkills} Wealth:{self.wealth} Creep:{cret_z} Tamed:{tamed_n} Dead:{self.total_dead} Arts:{len(self.artifacts)}"
        self.scr.blit(self.fs.render(stats, True, (160,160,175)), (px+8, py)); py+=14
        pygame.draw.line(self.scr, (50,45,60), (px+6,py), (SW-6,py)); py+=4

        # Resources (compact)
        self.scr.blit(self.fm.render("📦 Resources", True, (200,200,220)), (px+8, py)); py+=15
        re = {"Stone":"🪨","Wood":"🪵","Iron":"🔩","Gold":"🪙","Coal":"🖤","Food":"🍖",
              "Gem":"💎","Plat.":"🩶","Adam.":"✨","Leath.":"🧵",
              "Ir.Bar":"🥇","Au.Bar":"💰","St.Bar":"⬜","Ad.Bar":"✨",
              "Ir.Swd":"🗡️","Ir.Arm":"🛡️","St.Swd":"🗡️","St.Arm":"🛡️",
              "Xbow":"🏹","L.Arm":"🥋","Beer":"🍺","Band.":"🩹","C.Gem":"💎"}
        rx = px + 8
        for rn, ra in self.res.items():
            if ra <= 0: continue
            e = re.get(rn, "📦")
            c = (190,190,190) if ra > 5 else (255,100,100)
            txt = f"{e}{rn}:{ra}"
            surf = self.fs.render(txt, True, c)
            self.scr.blit(surf, (rx, py))
            rx += surf.get_width() + 6
            if rx > SW - 40:
                rx = px + 8; py += 13
        py += 14
        pygame.draw.line(self.scr, (50,45,60), (px+6,py), (SW-6,py)); py+=4

        # Build options
        if self.mode == "build":
            self.scr.blit(self.fm.render("🔨 Build (1-0,-,=,[,],\\,;,',/,<)", True, (255,200,100)), (px+8, py)); py+=15
            for i, bn in enumerate(BL):
                bd = BLD[bn]; sel = bn == self.bld_ch
                cost_s = " ".join(f"{a}{r[0]}" for r,a in bd["c"].items()) if bd["c"] else "Free"
                can = all(self.res.get(r,0)>=a for r,a in bd["c"].items())
                c = (255,255,150) if sel else (100,100,100) if not can else (160,160,160)
                pre = "▶" if sel else " "
                self.scr.blit(self.fs.render(f"{pre}{bd['k']}{bd['e']}{bn}({cost_s})", True, c), (px+6, py))
                py += 12
            py += 4
            pygame.draw.line(self.scr, (50,45,60), (px+6,py), (SW-6,py)); py+=4

        # Dwarves (scrollable)
        self.scr.blit(self.fm.render(f"👥 Dwarves ({len(self.dwarves)})", True, (200,200,220)), (px+8, py)); py+=15
        max_shown = min(len(self.dwarves), max(1, (SH - py - 120) // 32))
        vis_dwarves = self.dwarves[self.ui_scroll:self.ui_scroll + max_shown]
        for d in vis_dwarves:
            if d == self.sel_d:
                pygame.draw.rect(self.scr, (40,36,50), (px+5,py-1,UPW-10,30), 0, 3)
                pygame.draw.rect(self.scr, (80,70,100), (px+5,py-1,UPW-10,30), 1, 3)
            # Mood indicator
            mood_e = ""
            if d.mood: mood_e = {"inspired":"✨","possessed":"🌀","fey":"😤"}.get(d.mood, "")
            artifact_e = "🌟" if d.artifact_name else ""
            self.scr.blit(self.fs.render(f"{d.emoji}{d.name} {d.prof} Lv{d.level}{mood_e}{artifact_e}", True,
                                          (255,240,200) if d==self.sel_d else (185,185,185)), (px+10, py))
            py+=12
            tstr = d.task["type"] if d.task else "idle"
            tc = (140,190,140) if tstr!="idle" else (190,130,130)
            gear = ""
            if d.weapon: gear += "🗡️"
            if d.armor: gear += "🛡️"
            self.scr.blit(self.fs.render(f" {tstr}{gear} HP:{d.hp}/{d.max_hp}", True, tc), (px+10, py))
            # Mini happiness bar
            bx2 = px+160; bw2 = UPW-175
            pygame.draw.rect(self.scr, (40,40,40), (bx2, py+3, bw2, 5))
            hc = (100,200,100) if d.happy>50 else (200,200,50) if d.happy>25 else (200,80,80)
            pygame.draw.rect(self.scr, hc, (bx2, py+3, int(bw2*d.happy/100), 5))
            py+=12
            self.scr.blit(self.fs.render(f" XP:{d.xp}/{d.level*50} Kills:{d.kills}", True, (120,120,135)), (px+10, py))
            py+=14
        if len(self.dwarves) > max_shown:
            self.scr.blit(self.fs.render(f"  Scroll: {self.ui_scroll+1}-{min(self.ui_scroll+max_shown, len(self.dwarves))}/{len(self.dwarves)}", True, (110,110,120)), (px+8, py))
            py += 13

        # ── Minimap ──────────────────────────────────────────────────────
        if self.mmap:
            mmw, mmh = 180, 100
            mmx = px+(UPW-mmw)//2; mmy = SH-mmh-8
            mm = pygame.Surface((mmw, mmh)); mm.fill((16,14,20))
            tc2 = {T.GRASS:(50,120,50),T.DIRT:(120,85,50),T.STONE:(100,100,110),
                   T.WALL:(130,120,100),T.WATER:(40,80,180),T.TREE:(30,100,30),
                   T.BEDROCK:(30,30,30),T.FLOOR:(90,85,80),T.LAVA:(140,50,10)}
            s_x, s_y = mmw/MW, mmh/MH
            for y in range(0, MH, 2):
                for x in range(0, MW, 2):
                    if not self.world.rev(x, y, z): continue
                    t = self.world.get(x, y, z)
                    c = tc2.get(t, (60,60,60))
                    mm.set_at((min(int(x*s_x),mmw-1), min(int(y*s_y),mmh-1)), c)
            for c in self.creatures:
                if c.alive and c.z==z:
                    cx2, cy2 = int(c.x*s_x), int(c.y*s_y)
                    if 0<=cx2<mmw and 0<=cy2<mmh:
                        cc = (255,60,60) if c.hostile else (100,200,100)
                        mm.set_at((cx2,cy2), cc)
            for d in self.dwarves:
                if d.z==z:
                    dx2, dy2 = int(d.x*s_x), int(d.y*s_y)
                    if 0<=dx2<mmw and 0<=dy2<mmh:
                        mm.set_at((dx2,dy2), (255,255,100))
                        if dx2+1<mmw: mm.set_at((dx2+1,dy2), (255,255,100))
            vx, vy = int(self.cx*s_x), int(self.cy*s_y)
            vw2, vh2 = int((mw/TS)*s_x), int((SH/TS)*s_y)
            pygame.draw.rect(mm, (255,255,255), (vx,vy,vw2,vh2), 1)
            self.scr.blit(mm, (mmx, mmy))
            pygame.draw.rect(self.scr, (60,55,70), (mmx-1,mmy-1,mmw+2,mmh+2), 1)
            self.scr.blit(self.fs.render(f"Z:{z} {'🌙' if self.is_night else '☀️'}", True, (200,200,255)), (mmx+2, mmy+2))

        # ── Selected Detail ──────────────────────────────────────────────
        if self.sel_d: self.render_dwarf_detail(self.sel_d)
        elif self.sel_c and self.sel_c.alive: self.render_creature_detail(self.sel_c)

        # ── Message Log ──────────────────────────────────────────────────
        log_y = SH - 13*min(len(self.msgs), 7) - 6
        ls = pygame.Surface((mw, SH-log_y), pygame.SRCALPHA); ls.fill((0,0,0,140))
        self.scr.blit(ls, (0, log_y))
        for i, (m, c) in enumerate(self.msgs[-7:]):
            self.scr.blit(self.fs.render(m, True, c), (6, log_y+3+i*13))

        # ── Help ─────────────────────────────────────────────────────────
        if self.help:
            lines = [
                "══ CONTROLS ══",
                "WASD/Arrows  Scroll    Right-drag  Scroll",
                "M  Mine    C  Chop    D  Dig Stairs",
                "B  Build   R  Remove  T  Tame animal",
                "K  Equip soldiers    G  Auto-craft",
                "Q/E  Z-level    MouseWheel  Cycle build/scroll UI",
                "TAB  Cycle entities    F  Follow selected",
                "P  Speed    Space  Pause    H  Help",
                "",
                "══ NEW IN V3 ══",
                "Weather: Rain/Snow/Storms affect the world",
                "Day/Night: Nocturnal creatures spawn at night 🌙",
                "Fog of War: Explore to reveal the map",
                "Taming: Kill animals, press T, click corpse to tame",
                "Artifacts: Dwarves get moods, need workshops nearby",
                "Corpses: Build Coffins (\\) to bury dead dwarves",
                "Fluids: Water & Lava slowly spread over time",
                "26 creature species! New: Owl, Eagle, Croc, Imp...",
                "Crossbows shoot from Fortifications! Steel gear!",
                "Adamantite ore deep underground for best gear",
            ]
            hw2, hh2 = 310, len(lines)*14+16
            hs = pygame.Surface((hw2, hh2), pygame.SRCALPHA)
            hs.fill((12,10,20,225)); pygame.draw.rect(hs, (100,90,140,200), (0,0,hw2,hh2), 1, 6)
            for i, l in enumerate(lines):
                c = (255,220,140) if l.startswith("═") else (190,190,200)
                hs.blit(self.fs.render(l, True, c), (10, 8+i*14))
            self.scr.blit(hs, (mw//2-hw2//2, SH//2-hh2//2))

        # FPS
        self.scr.blit(self.fs.render(f"FPS:{int(self.clk.get_fps())}", True, (70,70,70)), (mw-50, 4))
        if self.paused:
            ps = self.fb.render("⏸ PAUSED", True, (255,255,100))
            self.scr.blit(ps, ps.get_rect(center=(mw//2, 18)))

        pygame.display.flip()

    def render_dwarf_detail(self, d):
        dw, dh = 250, 200
        ds = pygame.Surface((dw, dh), pygame.SRCALPHA)
        ds.fill((20,18,30,215)); pygame.draw.rect(ds, (100,90,130,200), (0,0,dw,dh), 1, 6)
        dy = 6
        ds.blit(self.ft.render(f"{d.emoji} {d.name} Lv{d.level}", True, (255,240,200)), (8, dy)); dy+=18
        gear = ""
        if d.weapon: gear += " 🗡️" + d.weapon
        if d.armor: gear += " 🛡️" + d.armor
        if d.ranged: gear += " 🏹"
        if d.artifact_name: gear += f" 🌟{d.artifact_name}"
        ds.blit(self.fs.render(f"{d.prof}{gear}", True, (180,180,200)), (8, dy)); dy+=14
        ds.blit(self.fs.render(f"({d.x},{d.y}) Z:{d.z}  Atk:{d.eff_atk()} Def:{d.eff_def()}  Kills:{d.kills}", True, (150,150,170)), (8, dy)); dy+=14
        bars = [("HP",d.hp,d.max_hp,(200,60,60)),("Happy",d.happy,100,(100,200,100)),
                ("Hunger",100-d.hunger,100,(220,150,50)),("Energy",100-d.sleep,100,(100,150,220)),
                ("XP",d.xp,d.level*50,(180,180,100))]
        for label, val, mx_, col in bars:
            ds.blit(self.fs.render(f"{label}:", True, (160,160,170)), (8, dy))
            bx2, by2, bw2, bh2 = 65, dy+2, 115, 8
            pygame.draw.rect(ds, (40,40,40), (bx2,by2,bw2,bh2))
            pygame.draw.rect(ds, col, (bx2,by2,int(bw2*val/mx_),bh2))
            pygame.draw.rect(ds, (60,60,60), (bx2,by2,bw2,bh2), 1)
            ds.blit(self.fs.render(f"{int(val)}/{mx_}", True, (180,180,180)), (bx2+bw2+3, dy))
            dy += 14
        sk = " ".join(f"{s[:3]}:{int(v)}" for s,v in d.skills.items())
        ds.blit(self.fs.render(f"Skills: {sk}", True, (140,140,155)), (8, dy)); dy+=13
        if d.mood:
            ds.blit(self.fs.render(f"Mood: {d.mood} (needs workshop nearby!)", True, (255,200,255)), (8, dy)); dy+=13
        for msg in d.log[-2:]:
            dy += 11
            ds.blit(self.fs.render(f"• {msg}", True, (120,120,135)), (8, dy))
        self.scr.blit(ds, (6, 6))

    def render_creature_detail(self, c):
        cd = CD[c.species]
        dw, dh = 230, 115
        ds = pygame.Surface((dw, dh), pygame.SRCALPHA)
        ds.fill((30,18,18,215)); pygame.draw.rect(ds, (150,80,80,200), (0,0,dw,dh), 1, 6)
        dy = 6
        ds.blit(self.ft.render(f"{c.emoji} {c.species}", True, (255,200,200)), (8, dy)); dy+=18
        ds.blit(self.fs.render(f"HP:{c.hp}/{c.max_hp}  Atk:{c.atk}  Def:{c.dfn}  Spd:{c.spd:.1f}", True, (200,180,180)), (8, dy)); dy+=13
        ds.blit(self.fs.render(f"{'HOSTILE' if c.hostile else 'Passive'}  {'🌙Nocturnal' if c.nocturnal else '☀Diurnal'}  XP:{c.xp}", True, (200,150,150) if c.hostile else (150,200,150)), (8, dy)); dy+=13
        loot_s = "None"
        if c.loot: loot_s = ", ".join(f"{a}{r}" for r,a in c.loot.items())
        ds.blit(self.fs.render(f"Loot: {loot_s}", True, (180,180,150)), (8, dy)); dy+=13
        if c.special:
            ds.blit(self.fs.render(f"Special: {c.special}", True, (255,180,100)), (8, dy)); dy+=13
        ds.blit(self.fs.render(f"Z-Range: {cd['zr']}  Pack: {cd['pk']}  AI: {c.ai}", True, (160,160,170)), (8, dy))
        self.scr.blit(ds, (6, 6))

    # ─── MAIN LOOP ───────────────────────────────────────────────────────
    def run(self):
        pygame.mouse.get_rel()
        while self.run_:
            self.handle_events()
            self.update()
            self.render()
            self.clk.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()