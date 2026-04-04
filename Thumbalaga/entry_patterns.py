from constants import *

# Entry paths: sequences of (x, y) camera coordinates enemies fly through
# before reaching their formation slot. Generated from Galaga Z80 disassembly
# (hackbar/galaga), scaled for 128x128 screen from original 224x288.

# ── Paths from top of screen ──
# Full Galaga entry loops: sweep in from top, curve through, loop back.
# Y compressed 0.55x for square aspect ratio (original is portrait 224x288).

# Path 0: enter top-left, sweep right, loop back left
PATH_TL = [
    (-34, -80), (-34, -30), (-34, -3), (-31, 4), (-21, 9),
    (-9, 14), (3, 19), (7, 26), (-4, 30),
    (-19, 28), (-28, 22), (-42, 24), (-65, 23), (-51, 15),
]

# Path 0 mirrored: enter top-right, sweep left, loop back right
PATH_TR = [
    (34, -80), (34, -30), (34, -3), (31, 4), (21, 9),
    (9, 14), (-3, 19), (-7, 26), (4, 30),
    (19, 28), (28, 22), (42, 24), (65, 23), (51, 15),
]

# Path 2: enter top-left wider, sweep right, loop back
PATH_TL_WIDE = [
    (-39, -80), (-39, -30), (-39, -3), (-36, 4), (-27, 10),
    (-16, 14), (-5, 18), (6, 22), (10, 28),
    (0, 32), (-13, 31), (-26, 30), (-41, 31), (-40, 24),
]

# Path 2 mirrored
PATH_TR_WIDE = [
    (39, -80), (39, -30), (39, -3), (36, 4), (27, 10),
    (16, 14), (5, 18), (-6, 22), (-10, 28),
    (0, 32), (13, 31), (26, 30), (41, 31), (40, 24),
]

# Path 4: enter top-left, deeper sweep, loop back
PATH_TL_DEEP = [
    (-34, -80), (-34, -30), (-34, -3), (-32, 3), (-25, 8),
    (-14, 12), (-4, 15), (7, 19), (14, 28),
    (1, 36), (-19, 36), (-33, 33), (-51, 32), (-46, 24),
]

# Path 4 mirrored
PATH_TR_DEEP = [
    (34, -80), (34, -30), (34, -3), (32, 3), (25, 8),
    (14, 12), (4, 15), (-7, 19), (-14, 28),
    (-1, 36), (19, 36), (33, 33), (51, 32), (46, 24),
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
    Later stages add transient enemies (not implemented yet).
    """
    if stage % 2 == 1:
        return _pattern_trailing()
    else:
        return _pattern_split()


def _pattern_trailing():
    """Odd stages (1, 3, 5, ...) — matches original Galaga stage 1/3.
    Wave 1: SPLIT from top — butterflies left, bees right (simultaneous)
    Wave 2: TRAILING from left side — 8 in single file (bosses + butterflies)
    Wave 3: TRAILING from right side — 8 in single file (outer butterflies)
    Wave 4: TRAILING from top-right — 8 in single file (bees)
    Wave 5: TRAILING from top-left — 4 in single file (remaining bees)
    """
    return [
        # Wave 1 (split): center butterflies from top-left + center bees from top-right
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
        # Wave 1 (split): center butterflies + center bees from top (wide offset)
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
        # Wave 2 (split): bosses + butterflies alternating from each side
        {
            'delay': 1.2,
            'path': PATH_SL,
            'slots': [(2, 0), (2, 2), (3, 0), (3, 2)],
            'spacing': 0.18,
        },
        {
            'delay': 1.2,
            'path': PATH_SR_LOW,
            'slots': [(4, 0), (4, 2), (5, 0), (5, 2)],
            'spacing': 0.18,
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
def update_entry(entry_state, formation, dt, entry_speed=1.0):
    """Update entry animation. Returns True when all enemies are in formation."""
    entry_state.time += dt * entry_speed
    all_done = True

    for group in entry_state.pattern:
        group_delay = group['delay']
        if entry_state.time < group_delay:
            all_done = False
            continue

        path = group['path']
        spacing = group['spacing']

        for i, (col, row) in enumerate(group['slots']):
            idx = row * FORM_COLS + col
            e = formation.enemies[idx]
            if e is None or not e.alive:
                continue

            if e.entry_done and e.in_formation:
                continue  # already settled

            all_done = False

            enemy_time = entry_state.time - group_delay - i * spacing
            if enemy_time < 0:
                continue  # not started yet

            if e.node.opacity < 0.5:
                e.node.opacity = 1.0

            t = enemy_time / ENTRY_DURATION
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
                    e.node.position.x = end_x + (slot_x - end_x) * lerp_t
                    e.node.position.y = end_y + (slot_y - end_y) * lerp_t
            else:
                # Still on entry path
                px, py = interpolate_path(path, t)
                e.node.position.x = px
                e.node.position.y = py

    return all_done
