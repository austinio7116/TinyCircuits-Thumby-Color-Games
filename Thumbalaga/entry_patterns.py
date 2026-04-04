from constants import *

# Entry paths: sequences of (x, y) camera coordinates enemies fly through
# before reaching their formation slot. Generated from Galaga Z80 disassembly
# (hackbar/galaga), scaled for 128x128 screen from original 224x288.

# ── Paths from top of screen ──
# Full Galaga entry loops: sweep in from top, curve through, loop back.
# Approach compressed aggressively, loop portion kept round (0.75x width, 0.55x height).
# 17 waypoints each for smooth curves.

# Path 0: enter top-left, sweep right, loop back left
PATH_TL = [
    (-34,-70), (-32,-55), (-27,-40), (-19,-28), (-9,-16),
    (-1,-5), (7,8), (7,23), (-3,34), (-14,32),
    (-21,19), (-28,8), (-40,12), (-54,22), (-66,2), (-51,-14),
]

# Path 0 mirrored: enter top-right, sweep left, loop back right
PATH_TR = [
    (34,-70), (32,-55), (27,-40), (19,-28), (9,-16),
    (1,-5), (-7,8), (-7,23), (3,34), (14,32),
    (21,19), (28,8), (40,12), (54,22), (66,2), (51,-14),
]

# Path 2: enter top-left wider, sweep right, loop back
PATH_TL_WIDE = [
    (-39,-70), (-37,-55), (-32,-41), (-25,-29), (-16,-19),
    (-8,-11), (0,-3), (7,6), (10,19), (5,30),
    (-4,35), (-13,31), (-24,27), (-33,31), (-43,26), (-40,11),
]

# Path 2 mirrored
PATH_TR_WIDE = [
    (39,-70), (37,-55), (32,-41), (25,-29), (16,-19),
    (8,-11), (0,-3), (-7,6), (-10,19), (-5,30),
    (4,35), (13,31), (24,27), (33,31), (43,26), (40,11),
]

# Path 4: enter top-left, deeper sweep, loop back
PATH_TL_DEEP = [
    (-34,-70), (-33,-59), (-29,-48), (-23,-40), (-15,-32),
    (-8,-25), (0,-17), (9,-9), (15,10), (9,26),
    (-5,35), (-21,31), (-30,25), (-41,27), (-53,18), (-46,1),
]

# Path 4 mirrored
PATH_TR_DEEP = [
    (34,-70), (33,-59), (29,-48), (23,-40), (15,-32),
    (8,-25), (0,-17), (-9,-9), (-15,10), (-9,26),
    (5,35), (21,31), (30,25), (41,27), (53,18), (46,1),
]

# ── Paths from sides (start off-screen at x=+/-80) ──

# Path 1: from left side, looping up to formation
PATH_SL = [
    (-80, 48), (-64, 47), (-50, 44), (-37, 39), (-25, 31),
    (-18, 22), (-18, 10), (-32, 6), (-26, 14), (-17, 13),
]

# Path 1 mirrored: from right side
PATH_SR = [
    (80, 48), (64, 47), (50, 44), (37, 39), (25, 31),
    (18, 22), (18, 10), (32, 6), (26, 14), (17, 13),
]

# Path 3: from left, tighter loop
PATH_SL_TIGHT = [
    (-80, 48), (-64, 47), (-50, 45), (-35, 42), (-19, 37),
    (-7, 27), (-3, 14), (-22, 4), (-20, 18), (-3, 19),
]

# Path 3 mirrored
PATH_SR_TIGHT = [
    (80, 48), (64, 47), (50, 45), (35, 42), (19, 37),
    (7, 27), (3, 14), (22, 4), (20, 18), (3, 19),
]

# Path 5: from left side, low entry
PATH_SL_LOW = [
    (-80, 45), (-64, 44), (-50, 42), (-36, 39), (-22, 35),
    (-13, 27), (-11, 15), (-23, 12), (-20, 21), (-9, 20),
]

# Path 5 mirrored
PATH_SR_LOW = [
    (80, 45), (64, 44), (50, 42), (36, 39), (22, 35),
    (13, 27), (11, 15), (23, 12), (20, 21), (9, 20),
]


# ============================================================
# Wave definitions: match original Galaga entry order
# ============================================================
#
# Original Galaga (5 waves of 8, total 40):
#   Wave 1: 4 center butterflies + 4 center bees (simultaneous, split)
#   Wave 2: 4 bosses + 4 outer butterflies
#   Wave 3: 8 remaining butterflies
#   Wave 4: 8 bees (inner)
#   Wave 5: 8 bees (outer)
#
# Our formation (8 cols x 5 rows, total 36):
#   Row 0: Bosses (cols 2-5 only, 4 total)
#   Row 1: Butterflies (8)
#   Row 2: Butterflies (8)
#   Row 3: Bees (8)
#   Row 4: Bees (8)
#
# Mapping to match original wave composition:
#   Wave 1 (8): 4 center butterflies (r1 c2-5) + 4 center bees (r3 c2-5)
#   Wave 2 (8): 4 bosses (r0 c2-5) + 4 center butterflies (r2 c2-5)
#   Wave 3 (8): outer butterflies (r1 c0,1,6,7 + r2 c0,1,6,7)
#   Wave 4 (8): bees (r3 c0,1,6,7 + r4 c2,3,4,5)
#   Wave 5 (4): remaining bees (r4 c0,1,6,7)

def get_entry_pattern(stage):
    """Return entry groups for the given stage.
    Original Galaga has 2 base patterns: odd stages = trailing, even = all-split.
    Stages 3+ add transient enemies that dive during entry.
    """
    if stage % 2 == 1:
        pattern = _pattern_trailing()
    else:
        pattern = _pattern_split()

    # Stages 3+: last 2 enemies in waves 1, 4, 5 break into dives mid-entry
    if stage >= 3:
        dive_count = min(2, (stage - 1) // 2)  # 1 at stage 3-4, 2 at stage 5+
        for i, group in enumerate(pattern):
            # Apply to first wave (i=0,1) and last two waves
            wave_idx = group['delay']
            if wave_idx == 0.0 or wave_idx >= 4.0:
                group['dive_at'] = 0.35   # break early in entry (while still high)
                group['dive_count'] = dive_count

    return pattern


def _pattern_trailing():
    """Odd stages (1, 3, 5, ...) — matches original Galaga stage 1/3.
    Wave 1: SIDE-BY-SIDE from top — butterflies + bees in parallel columns
    Wave 2: TRAILING from left side — 8 in single file (bosses + butterflies)
    Wave 3: TRAILING from right side — 8 in single file (outer butterflies)
    Wave 4: TRAILING from top-right — 8 in single file (bees)
    Wave 5: TRAILING from top-left — 4 in single file (remaining bees)
    """
    return [
        # Wave 1 (split): butterflies from top-left, bees from top-right
        {
            'delay': 0.0,
            'path': PATH_TL,
            'slots': [(2, 1), (3, 1), (4, 1), (5, 1)],
            'spacing': 0.20,
        },
        {
            'delay': 0.0,
            'path': PATH_TR,
            'slots': [(2, 3), (3, 3), (4, 3), (5, 3)],
            'spacing': 0.20,
        },
        # Wave 2 (trailing): bosses + butterflies ALTERNATING, single file from left side
        {
            'delay': 1.2,
            'path': PATH_SL,
            'slots': [(2, 0), (2, 2), (3, 0), (3, 2),
                       (4, 0), (4, 2), (5, 0), (5, 2)],
            'spacing': 0.18,
        },
        # Wave 3 (trailing): outer butterflies, single file from right side
        {
            'delay': 2.8,
            'path': PATH_SR,
            'slots': [(0, 1), (1, 1), (6, 1), (7, 1),
                       (0, 2), (1, 2), (6, 2), (7, 2)],
            'spacing': 0.18,
        },
        # Wave 4 (trailing): bees, single file from top-right
        {
            'delay': 4.2,
            'path': PATH_TR_WIDE,
            'slots': [(0, 3), (1, 3), (6, 3), (7, 3),
                       (2, 4), (3, 4), (4, 4), (5, 4)],
            'spacing': 0.18,
        },
        # Wave 5 (trailing): remaining bees, single file from top-left
        {
            'delay': 5.6,
            'path': PATH_TL_WIDE,
            'slots': [(0, 4), (1, 4), (6, 4), (7, 4)],
            'spacing': 0.18,
        },
    ]


def _pattern_split():
    """Even stages (2, 4, 6, ...) — matches original Galaga stage 2/4.
    All 5 waves are SPLIT (simultaneous from two directions).
    Wave 1: SPLIT from top (wide) — butterflies + bees
    Wave 2: SPLIT from sides — bosses + butterflies
    Wave 3: SPLIT from sides — outer butterflies
    Wave 4: SPLIT from top — bees
    Wave 5: SPLIT from top — remaining bees
    """
    return [
        # Wave 1 (split): butterflies from top-left, bees from top-right (wider paths)
        {
            'delay': 0.0,
            'path': PATH_TL_DEEP,
            'slots': [(2, 1), (3, 1), (4, 1), (5, 1)],
            'spacing': 0.20,
        },
        {
            'delay': 0.0,
            'path': PATH_TR_DEEP,
            'slots': [(2, 3), (3, 3), (4, 3), (5, 3)],
            'spacing': 0.20,
        },
        # Wave 2 (side-by-side from left): bosses + butterflies in parallel
        # Original uses two paths from the same side (path 3 + path 5, both left)
        {
            'delay': 1.2,
            'path': PATH_SL,
            'slots': [(2, 0), (3, 0), (4, 0), (5, 0)],
            'spacing': 0.18,
            'offset_x': -6,
        },
        {
            'delay': 1.2,
            'path': PATH_SL_LOW,
            'slots': [(2, 2), (3, 2), (4, 2), (5, 2)],
            'spacing': 0.18,
            'offset_x': 6,
        },
        # Wave 3 (split): outer butterflies from sides
        {
            'delay': 2.6,
            'path': PATH_SL_TIGHT,
            'slots': [(0, 1), (1, 1), (0, 2), (1, 2)],
            'spacing': 0.18,
        },
        {
            'delay': 2.6,
            'path': PATH_SR_TIGHT,
            'slots': [(6, 1), (7, 1), (6, 2), (7, 2)],
            'spacing': 0.18,
        },
        # Wave 4 (split): bees from top
        {
            'delay': 4.0,
            'path': PATH_TL_WIDE,
            'slots': [(0, 3), (1, 3), (6, 3), (7, 3)],
            'spacing': 0.18,
        },
        {
            'delay': 4.0,
            'path': PATH_TR_WIDE,
            'slots': [(2, 4), (3, 4), (4, 4), (5, 4)],
            'spacing': 0.18,
        },
        # Wave 5 (split): remaining bees from top
        {
            'delay': 5.2,
            'path': PATH_TL,
            'slots': [(0, 4), (1, 4)],
            'spacing': 0.18,
        },
        {
            'delay': 5.2,
            'path': PATH_TR,
            'slots': [(6, 4), (7, 4)],
            'spacing': 0.18,
        },
    ]


class EntryState:
    """Tracks entry animation progress."""
    def __init__(self, pattern):
        self.pattern = pattern
        self.time = 0.0

    def reset(self, pattern):
        self.pattern = pattern
        self.time = 0.0


@micropython.native
def interpolate_path(path, t):
    """Interpolate position along a path at parameter t (0-1)."""
    seg_count = len(path) - 1
    if seg_count <= 0:
        return path[0][0], path[0][1]

    t_scaled = t * seg_count
    seg_idx = int(t_scaled)
    seg_t = t_scaled - seg_idx

    if seg_idx >= seg_count:
        return path[-1][0], path[-1][1]

    x0, y0 = path[seg_idx]
    x1, y1 = path[seg_idx + 1]

    return x0 + (x1 - x0) * seg_t, y0 + (y1 - y0) * seg_t


@micropython.native
def update_entry(entry_state, formation, dt, entry_speed=1.0, dive_fn=None):
    """Update entry animation. Returns True when all enemies are in formation.
    dive_fn: optional callback(enemy) to make an enemy break into a dive mid-entry.
    """
    entry_state.time += dt * entry_speed
    all_done = True

    for group in entry_state.pattern:
        group_delay = group['delay']
        if entry_state.time < group_delay:
            all_done = False
            continue

        path = group['path']
        spacing = group['spacing']
        # dive_at: if set, last N enemies in this group break into a dive
        # at this t value instead of going to formation (transient enemies)
        dive_at = group.get('dive_at', 0)
        dive_count = group.get('dive_count', 0)
        dive_start_idx = len(group['slots']) - dive_count

        for i, (col, row) in enumerate(group['slots']):
            idx = row * FORM_COLS + col
            e = formation.enemies[idx]
            if e is None or not e.alive:
                continue

            if e.entry_done and e.in_formation:
                continue  # already settled

            if e.entry_done and not e.in_formation:
                continue  # broke into a dive

            all_done = False

            enemy_time = entry_state.time - group_delay - i * spacing
            if enemy_time < 0:
                continue  # not started yet

            if e.node.opacity < 0.5:
                e.node.opacity = 1.0

            # Horizontal offset for side-by-side entry (0 if not specified)
            ox = group.get('offset_x', 0)

            t = enemy_time / ENTRY_DURATION

            # Check if this enemy should break into a dive mid-entry
            # Only dive if enemy is in upper portion of screen (y < 20)
            if dive_at > 0 and i >= dive_start_idx and t >= dive_at \
               and e.node.position.y < 20 and dive_fn:
                e.entry_done = True
                dive_fn(e)
                continue

            if t >= 1.0:
                # Path traversal done — lerp to formation slot
                lerp_t = (enemy_time - ENTRY_DURATION) / ENTRY_LERP_DURATION
                if lerp_t >= 1.0:
                    # Fully in formation
                    e.in_formation = True
                    e.entry_done = True
                    sx, sy = formation.get_slot_screen_pos(col, row)
                    e.node.position.x = sx
                    e.node.position.y = sy
                else:
                    # Lerp from path end to formation slot
                    end_x, end_y = path[-1]
                    slot_x, slot_y = formation.get_slot_screen_pos(col, row)
                    e.node.position.x = (end_x + ox) + (slot_x - end_x - ox) * lerp_t
                    e.node.position.y = end_y + (slot_y - end_y) * lerp_t
            else:
                # Still on entry path
                px, py = interpolate_path(path, t)
                e.node.position.x = px + ox
                e.node.position.y = py

    return all_done
