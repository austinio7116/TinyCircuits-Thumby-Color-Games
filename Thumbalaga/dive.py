import random
from constants import *

# Dive paths: lists of (dx, dy) waypoints relative to start position.
# Enemy interpolates from waypoint to waypoint as t goes 0->1.
# Generated from Galaga Z80 disassembly (hackbar/galaga), scaled for 128x128.

# ── Bee dive: arc out, dive deep past screen, loop back up ──
# Scaled from original but extended vertically so bees exit bottom of screen

DIVE_BEE_L = [
    (0, 0), (-8, 5), (-14, 15), (-10, 30), (2, 45),
    (18, 60), (30, 75), (35, 90), (30, 105),
    (15, 115), (0, 120), (-10, 110), (-8, 90), (0, 140),
]

DIVE_BEE_R = [
    (0, 0), (8, 5), (14, 15), (10, 30), (-2, 45),
    (-18, 60), (-30, 75), (-35, 90), (-30, 105),
    (-15, 115), (0, 120), (10, 110), (8, 90), (0, 140),
]

# ── Butterfly dive: arc, S-curve, dive past screen bottom ──

DIVE_BUTTERFLY_L = [
    (0, 0), (-10, 5), (-5, 15), (8, 25), (20, 35),
    (28, 50), (22, 65), (10, 80), (-5, 90),
    (-15, 100), (-10, 110), (0, 120), (5, 130), (0, 140),
]

DIVE_BUTTERFLY_R = [
    (0, 0), (10, 5), (5, 15), (-8, 25), (-20, 35),
    (-28, 50), (-22, 65), (-10, 80), (5, 90),
    (15, 100), (10, 110), (0, 120), (-5, 130), (0, 140),
]

# ── Boss normal dive: wide sweeping spiral, exits bottom ──

DIVE_BOSS_L = [
    (0, 0), (-12, 0), (-12, 14), (-4, 27), (10, 26),
    (2, 16), (-5, 26), (5, 37), (17, 47),
    (26, 59), (31, 73), (32, 86), (28, 100), (10, 140),
]

DIVE_BOSS_R = [
    (0, 0), (12, 0), (12, 14), (4, 27), (-10, 26),
    (-2, 16), (5, 26), (-5, 37), (-17, 47),
    (-26, 59), (-31, 73), (-32, 86), (-28, 100), (-10, 140),
]

# ── Boss capture dive: approach to tractor beam zone ──

DIVE_BOSS_CAPTURE_L = [
    (0, 0), (-6, -4), (-12, 2), (-14, 10), (-16, 17),
    (-18, 25), (-20, 33), (-22, 40), (-24, 48),
    (-26, 55), (-28, 63), (-30, 71), (-32, 78), (-34, 86),
]

DIVE_BOSS_CAPTURE_R = [
    (0, 0), (6, -4), (12, 2), (14, 10), (16, 17),
    (18, 25), (20, 33), (22, 40), (24, 48),
    (26, 55), (28, 63), (30, 71), (32, 78), (34, 86),
]

# ── Rogue fighter dive: like boss but longer, exits bottom ──

DIVE_ROGUE_L = [
    (0, 0), (-12, 0), (-11, 15), (-3, 28), (11, 24),
    (0, 16), (-4, 28), (7, 39), (20, 50),
    (28, 62), (32, 76), (31, 90), (26, 104), (10, 140),
]

DIVE_ROGUE_R = [
    (0, 0), (12, 0), (11, 15), (3, 28), (-11, 24),
    (0, 16), (4, 28), (-7, 39), (-20, 50),
    (-28, 62), (-32, 76), (-31, 90), (-26, 104), (-10, 140),
]


def select_dive_path(enemy):
    """Select dive path based on enemy type and formation position."""
    left = enemy.slot_col < FORM_COLS // 2
    etype = enemy.type

    if etype == ENEMY_BOSS or etype == ENEMY_BOSS_HIT:
        if enemy.will_beam:
            return DIVE_BOSS_CAPTURE_L if left else DIVE_BOSS_CAPTURE_R
        return DIVE_BOSS_L if left else DIVE_BOSS_R
    elif etype == ENEMY_BUTTERFLY:
        return DIVE_BUTTERFLY_L if left else DIVE_BUTTERFLY_R
    else:
        # Bees and all other types
        return DIVE_BEE_L if left else DIVE_BEE_R


def start_dive(enemy, formation=None, beam_active=False):
    """Initiate a dive attack. Boss either plans to tractor beam (solo) or takes escorts."""
    enemy.in_formation = False
    enemy.dive_t = 0.0
    enemy.dive_start_x = enemy.node.position.x
    enemy.dive_start_y = enemy.node.position.y
    enemy.fire_timer = random.random() * 0.5 + 0.3
    enemy.escorts = []
    enemy.will_beam = False

    is_boss = enemy.type == ENEMY_BOSS or enemy.type == ENEMY_BOSS_HIT
    if is_boss and formation:
        # Boss decides before diving: tractor beam (solo) or escorts (no beam)
        if not beam_active and random.random() < 0.25:
            enemy.will_beam = True

    # Must set dive_path AFTER will_beam is decided
    enemy.dive_path = select_dive_path(enemy)

    if not is_boss or not formation or enemy.will_beam:
        return

    # Boss convoy: grab 1-2 butterflies from rows 1-2 as escorts
    for row in [1, 2]:  # butterfly rows
        for dc in [0, -1, 1, -2, 2]:
            col = enemy.slot_col + dc
            if col < 0 or col >= FORM_COLS:
                continue
            esc = formation.get_enemy(col, row)
            if esc and esc.alive and esc.in_formation and \
               esc.type == ENEMY_BUTTERFLY and len(enemy.escorts) < 2:
                esc.in_formation = False
                esc.is_escort = True
                esc.dive_path = enemy.dive_path
                esc.dive_t = 0.0
                esc.dive_start_x = esc.node.position.x
                esc.dive_start_y = esc.node.position.y
                enemy.escorts.append(esc)
        if len(enemy.escorts) >= 2:
            break


@micropython.native
def update_diving_enemy(enemy, dt, dive_speed, formation):
    """Advance enemy along dive path. Returns True when dive complete."""
    enemy.dive_t += dt * dive_speed

    path = enemy.dive_path
    seg_count = len(path) - 1

    if enemy.dive_t >= 1.0:
        # Dive complete — return to formation
        enemy.in_formation = True
        enemy.dive_t = 0.0
        enemy.dive_path = None
        enemy.node.scale.x = 1.0
        sx, sy = formation.get_slot_screen_pos(enemy.slot_col, enemy.slot_row)
        enemy.node.position.x = sx
        enemy.node.position.y = sy
        # Return escorts too
        for esc in enemy.escorts:
            if esc.alive:
                esc.in_formation = True
                esc.is_escort = False
                esc.dive_path = None
                esc.node.scale.x = 1.0
                esx, esy = formation.get_slot_screen_pos(esc.slot_col, esc.slot_row)
                esc.node.position.x = esx
                esc.node.position.y = esy
        enemy.escorts = []
        return True

    t_scaled = enemy.dive_t * seg_count
    seg_idx = int(t_scaled)
    seg_t = t_scaled - seg_idx

    if seg_idx >= seg_count:
        seg_idx = seg_count - 1
        seg_t = 1.0

    x0, y0 = path[seg_idx]
    x1, y1 = path[seg_idx + 1]

    nx = enemy.dive_start_x + x0 + (x1 - x0) * seg_t
    ny = enemy.dive_start_y + y0 + (y1 - y0) * seg_t

    # Clamp to screen bounds (camera coords)
    if nx < -60:
        nx = -60
    elif nx > 60:
        nx = 60

    enemy.node.position.x = nx
    enemy.node.position.y = ny
    return False


def maybe_trigger_dive(formation, level, dt, beam_active=False):
    """Periodically select an enemy to dive. Returns the enemy if one started, else None."""
    formation.dive_timer -= dt
    if formation.dive_timer > 0:
        return None

    formation.dive_timer = level.dive_interval

    diving_count = len(formation.get_diving_enemies())
    if diving_count >= level.max_divers:
        return None

    candidates = formation.get_alive_in_formation()
    if not candidates:
        return None

    enemy = random.choice(candidates)
    start_dive(enemy, formation, beam_active)
    return enemy
