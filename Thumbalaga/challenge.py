"""Challenging Stage: 5 waves of 8 enemies fly through in looping
patterns without shooting. 100 pts per kill, 10000 bonus for perfect (40/40).

Enemy types per challenge stage (from Z80 disassembly d_290E table):
  Stage  3: Bee          Stage 19: Enterprise
  Stage  7: Butterfly    Stage 23: Bosconian
  Stage 11: Galaxian     Stage 27: Dragonfly
  Stage 15: Scorpion     Stage 31: Satellite

All 40 enemies use the same type. Rotation animation matches flight direction.
"""

from constants import *
from constants import get_idle_frames
import math

# ── Challenge flight paths from Galaga Z80 disassembly (paths 6-21) ──
# Evenly distributed across full screen height (-70 to +35 camera coords).

_CP6 = [(-34,-70), (-34,-58), (-34,-45), (-33,-32), (-31,-20), (-29,-7), (-25,6), (-20,18), (-14,30), (-5,35), (6,33), (13,24), (11,15), (1,8)]
_CP6M = [(34,-70), (34,-58), (34,-45), (33,-32), (31,-20), (29,-7), (25,6), (20,18), (14,30), (5,35), (-6,33), (-13,24), (-11,15), (-1,8)]
_CP7 = [(-64,35), (-49,34), (-33,29), (-18,23), (-4,13), (8,1), (16,-16), (16,-36), (15,-56), (7,-70), (1,-54), (1,-34), (2,-13), (16,-12)]
_CP7M = [(64,35), (49,34), (33,29), (18,23), (4,13), (-8,1), (-16,-16), (-16,-36), (-15,-56), (-7,-70), (-1,-54), (-1,-34), (-2,-13), (-16,-12)]
_CP8 = [(-34,-70), (-34,-55), (-34,-40), (-34,-26), (-32,-10), (-30,6), (-28,20), (-24,35), (-24,34), (-28,18), (-31,3), (-32,-12), (-33,-27), (-34,-44)]
_CP8M = [(34,-70), (34,-55), (34,-40), (34,-26), (32,-10), (30,6), (28,20), (24,35), (24,34), (28,18), (31,3), (32,-12), (33,-27), (34,-44)]
_CP9 = [(-64,35), (-29,35), (9,35), (40,16), (50,-23), (33,-59), (-1,-70), (-32,-51), (-43,-13), (-26,23), (9,35), (45,35), (82,35), (119,35)]
_CP9M = [(64,35), (29,35), (-9,35), (-40,16), (-50,-23), (-33,-59), (1,-70), (32,-51), (43,-13), (26,23), (-9,35), (-45,35), (-82,35), (-119,35)]
_CP10 = [(-34,-32), (-34,-17), (-34,-1), (-31,14), (-16,26), (5,34), (-1,32), (-21,23), (-32,10), (-33,-6), (-33,-22), (-33,-38), (-33,-54), (-33,-70)]
_CP10M = [(34,-32), (34,-17), (34,-1), (31,14), (16,26), (-5,34), (1,32), (21,23), (32,10), (33,-6), (33,-22), (33,-38), (33,-54), (33,-70)]
_CP11 = [(-64,35), (-37,35), (-17,35), (-31,31), (-46,6), (-44,-24), (-38,-54), (-16,-70), (-4,-48), (-4,-17), (5,-8), (33,-8), (62,-8), (90,-8)]
_CP11M = [(64,35), (37,35), (17,35), (31,31), (46,6), (44,-24), (38,-54), (16,-70), (4,-48), (4,-17), (-5,-8), (-33,-8), (-62,-8), (-90,-8)]
_CP12 = [(-34,-31), (-29,-23), (-25,-7), (-49,2), (-33,15), (-23,30), (-47,31), (-37,15), (-21,3), (-44,-6), (-41,-23), (-34,-30), (-34,-50), (-34,-70)]
_CP12M = [(34,-31), (29,-23), (25,-7), (49,2), (33,15), (23,30), (47,31), (37,15), (21,3), (44,-6), (41,-23), (34,-30), (34,-50), (34,-70)]
_CP13 = [(-64,24), (-45,-16), (-32,-65), (-15,-39), (-37,-38), (-13,-68), (1,-26), (-19,-35), (4,-64), (18,-20), (-1,-40), (20,-48), (38,-2), (63,35)]
_CP13M = [(64,24), (45,-16), (32,-65), (15,-39), (37,-38), (13,-68), (-1,-26), (19,-35), (-4,-64), (-18,-20), (1,-40), (-20,-48), (-38,-2), (-63,35)]
_CP14 = [(-34,-70), (-58,-37), (-63,4), (-36,33), (2,21), (2,-18), (-34,-24), (-32,13), (-4,-1), (-32,2), (-25,-7), (-44,-17), (-85,-26), (-127,-19)]
_CP14M = [(34,-70), (58,-37), (63,4), (36,33), (-2,21), (-2,-18), (34,-24), (32,13), (4,-1), (32,2), (25,-7), (44,-17), (85,-26), (127,-19)]
_CP15 = [(-64,27), (-33,12), (-9,-25), (20,-36), (10,4), (-16,-28), (-44,-24), (-25,6), (0,-32), (-13,-70), (-23,-30), (2,9), (31,33), (65,35)]
_CP15M = [(64,27), (33,12), (9,-25), (-20,-36), (-10,4), (16,-28), (44,-24), (25,6), (0,-32), (13,-70), (23,-30), (-2,9), (-31,33), (-65,35)]
_CP16 = [(-34,-70), (-34,-50), (-33,-41), (-10,-41), (-10,-32), (-10,-11), (-1,-8), (17,-8), (17,6), (17,27), (18,35), (41,35), (63,35), (86,35)]
_CP16M = [(34,-70), (34,-50), (33,-41), (10,-41), (10,-32), (10,-11), (1,-8), (-17,-8), (-17,6), (-17,27), (-18,35), (-41,35), (-63,35), (-86,35)]
_CP17 = [(-64,35), (-41,33), (-18,30), (7,27), (30,23), (36,7), (14,1), (-8,-3), (-19,-15), (4,-19), (10,-31), (-12,-37), (0,-51), (1,-70)]
_CP17M = [(64,35), (41,33), (18,30), (-7,27), (-30,23), (-36,7), (-14,1), (8,-3), (19,-15), (-4,-19), (-10,-31), (12,-37), (0,-51), (-1,-70)]
_CP18 = [(-34,-70), (-37,-51), (-66,-51), (-79,-48), (-59,-27), (-38,-5), (-18,16), (0,35), (-22,35), (-50,35), (-79,35), (-108,35), (-136,35), (-165,35)]
_CP18M = [(34,-70), (37,-51), (66,-51), (79,-48), (59,-27), (38,-5), (18,16), (0,35), (22,35), (50,35), (79,35), (108,35), (136,35), (165,35)]
_CP19 = [(-64,31), (-48,23), (-37,1), (-36,-27), (-36,-54), (-27,-70), (-12,-52), (5,-51), (20,-68), (29,-51), (28,-24), (28,4), (38,26), (56,35)]
_CP19M = [(64,31), (48,23), (37,1), (36,-27), (36,-54), (27,-70), (12,-52), (-5,-51), (-20,-68), (-29,-51), (-28,-24), (-28,4), (-38,26), (-56,35)]
_CP20 = [(-34,-70), (-34,-48), (-41,-27), (-63,-35), (-48,-50), (-34,-33), (-30,-11), (-18,8), (5,14), (4,-6), (-18,0), (-8,20), (15,32), (42,35)]
_CP20M = [(34,-70), (34,-48), (41,-27), (63,-35), (48,-50), (34,-33), (30,-11), (18,8), (-5,14), (-4,-6), (18,0), (8,20), (-15,32), (-42,35)]
_CP21 = [(-64,35), (-51,34), (-37,29), (-24,22), (-11,11), (1,-2), (12,-19), (17,-42), (12,-64), (-2,-69), (-12,-52), (-9,-28), (4,-19), (15,-32)]
_CP21M = [(64,35), (51,34), (37,29), (24,22), (11,11), (-1,-2), (-12,-19), (-17,-42), (-12,-64), (2,-69), (12,-52), (9,-28), (-4,-19), (-15,-32)]

# ── Enemy type per challenge config (from Z80 d_290E table) ──
# Index = (stage - 3) // 4, cycling 0-7
_CHALLENGE_ENEMY_TYPE = [
    ENEMY_BEE,        # config 0 (stage 3)
    ENEMY_BUTTERFLY,  # config 1 (stage 7)
    ENEMY_GALAXIAN,   # config 2 (stage 11)
    ENEMY_SCORPION,   # config 3 (stage 15)
    ENEMY_ENTERPRISE, # config 4 (stage 19)
    ENEMY_BOSCONIAN,  # config 5 (stage 23)
    ENEMY_DRAGONFLY,  # config 6 (stage 27)
    ENEMY_SATELLITE,  # config 7 (stage 31)
]

# ── 8 challenge wave configurations (from Z80 d_challg_stg_dat) ──
# Each config: 5 waves, each wave = (pathA, pathB, split)
# split=True: both paths fly simultaneously; split=False: trailing single file
_CHALLENGE_CONFIGS = [
    # Config 0 (stage 3): straight paths
    [(_CP6, _CP6M, True), (_CP7, _CP7, False), (_CP7M, _CP7M, False),
     (_CP6M, _CP6M, False), (_CP6, _CP6, False)],
    # Config 1 (stage 7): loop paths
    [(_CP8, _CP8M, True), (_CP9, _CP9M, True), (_CP9, _CP9M, True),
     (_CP8M, _CP8M, False), (_CP8, _CP8, False)],
    # Config 2 (stage 11): zigzag paths
    [(_CP10, _CP10M, False), (_CP11, _CP11M, True), (_CP11, _CP11M, True),
     (_CP10, _CP10M, False), (_CP16, _CP16M, False)],
    # Config 3 (stage 15): figure-8 paths
    [(_CP12, _CP12M, True), (_CP13, _CP13, False), (_CP13M, _CP13M, False),
     (_CP12, _CP12M, True), (_CP17, _CP17M, True)],
    # Config 4 (stage 19): swoop paths
    [(_CP14, _CP14, False), (_CP15, _CP15, False), (_CP15M, _CP15M, False),
     (_CP14, _CP14, False), (_CP14M, _CP14M, False)],
    # Config 5 (stage 23): multi-bounce
    [(_CP16, _CP16, False), (_CP17, _CP17M, True), (_CP17, _CP17M, True),
     (_CP16M, _CP16M, False), (_CP16, _CP16, False)],
    # Config 6 (stage 27): step-wise
    [(_CP18, _CP18, False), (_CP19, _CP19, False), (_CP19M, _CP19M, False),
     (_CP18M, _CP18M, False), (_CP18, _CP18, False)],
    # Config 7 (stage 31): challenge-specific
    [(_CP20, _CP20M, True), (_CP21, _CP21, False), (_CP21M, _CP21M, False),
     (_CP20, _CP20M, True), (_CP20, _CP20M, True)],
]

CHALLENGE_WAVE_COUNT = const(5)
CHALLENGE_ENEMIES_PER_WAVE = const(8)
CHALLENGE_TOTAL = const(40)  # 5 * 8
CHALLENGE_ENEMY_SPACING = 0.15  # seconds between enemies in a wave
CHALLENGE_WAVE_DELAY = 2.5  # seconds between waves
CHALLENGE_PATH_DURATION = 2.5  # seconds to traverse path
CHALLENGE_PERFECT_BONUS = const(10000)
CHALLENGE_HIT_POINTS = const(100)


class ChallengeWaveEnemy:
    """A single enemy in a challenge wave."""
    __slots__ = ('node', 'path', 'start_time', 'active', 'alive',
                 'finished', 'wave_idx', '_last_x', '_etype')

    def __init__(self):
        self.node = None
        self.path = None
        self.start_time = 0.0
        self.active = False
        self.alive = True
        self.finished = False
        self.wave_idx = 0
        self._last_x = -200.0
        self._etype = ENEMY_BEE


class ChallengeState:
    """Manages the challenging stage."""

    def __init__(self):
        self.enemies = []
        self.wave_kills = [0] * CHALLENGE_WAVE_COUNT
        self.wave_done = [False] * CHALLENGE_WAVE_COUNT
        self.time = 0.0
        self.kills = 0
        self.total_spawned = 0
        self.all_done = False

    def init(self, enemy_nodes, stage=3):
        """Set up 5 waves of 8 enemies using the node pool."""
        self.enemies = []
        self.time = 0.0
        self.kills = 0
        self.total_spawned = 0
        self.all_done = False
        self.wave_kills = [0] * CHALLENGE_WAVE_COUNT
        self.wave_done = [False] * CHALLENGE_WAVE_COUNT

        # Determine challenge config and enemy type
        config_idx = ((stage - 3) // 4) % 8
        etype = _CHALLENGE_ENEMY_TYPE[config_idx]
        config = _CHALLENGE_CONFIGS[config_idx]

        node_idx = 0
        for wave_idx in range(CHALLENGE_WAVE_COUNT):
            pathA, pathB, split = config[wave_idx]
            wave_start = wave_idx * CHALLENGE_WAVE_DELAY

            for i in range(CHALLENGE_ENEMIES_PER_WAVE):
                if node_idx >= len(enemy_nodes):
                    break

                ce = ChallengeWaveEnemy()
                ce.node = enemy_nodes[node_idx]
                ce._etype = etype
                ce._last_x = -200.0

                # Assign path: split = 4 on each path, trailing = all on pathA
                if split:
                    ce.path = pathA if i < 4 else pathB
                    ce.start_time = wave_start + (i % 4) * CHALLENGE_ENEMY_SPACING
                else:
                    ce.path = pathA
                    ce.start_time = wave_start + i * CHALLENGE_ENEMY_SPACING

                ce.active = False
                ce.alive = True
                ce.finished = False
                ce.wave_idx = wave_idx

                # Set sprite type
                ce.node.frame_current_y = etype
                ia, ib = get_idle_frames(etype)
                ce.node.frame_current_x = ia
                ce.node.playing = False
                ce.node.opacity = 0.0
                ce.node.position.x = -200
                ce.node.position.y = -200
                ce.node.scale.x = 1.0

                self.enemies.append(ce)
                node_idx += 1

        self.total_spawned = len(self.enemies)


@micropython.native
def interpolate_challenge_path(path, t):
    """Interpolate position along a challenge path at parameter t (0-1)."""
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
def update_challenge(challenge, dt):
    """Update challenge stage. Returns True when all waves complete."""
    challenge.time += dt
    all_finished = True

    for ce in challenge.enemies:
        if ce.finished:
            continue

        if not ce.alive:
            ce.finished = True
            continue

        all_finished = False

        if challenge.time < ce.start_time:
            continue  # not started yet

        enemy_t = challenge.time - ce.start_time
        t = enemy_t / CHALLENGE_PATH_DURATION

        if t >= 1.0:
            # Exited screen — done
            ce.finished = True
            ce.active = False
            ce.node.opacity = 0.0
            ce.node.position.x = -200
            ce.node.position.y = -200
            continue

        # Make visible and move along path
        if not ce.active:
            ce.active = True
            ce.node.opacity = 1.0
            ce._last_x = ce.path[0][0]

        px, py = interpolate_challenge_path(ce.path, t)
        ce.node.position.x = px
        ce.node.position.y = py

        # Rotation animation — face direction of travel
        dx = px - ce._last_x
        ce._last_x = px

        max_frame = ENEMY_FRAME_COUNT[ce._etype] if ce._etype < len(ENEMY_FRAME_COUNT) else 8
        ia, ib = get_idle_frames(ce._etype)

        adx = abs(dx)
        if adx > 2:
            frame = 0
        elif adx > 0.8:
            frame = min(2, max_frame - 1)
        elif adx > 0.3:
            frame = min(4, max_frame - 1)
        else:
            frame = ia  # facing down when moving mostly vertically

        if dx < -0.3:
            ce.node.scale.x = -1.0
        elif dx > 0.3:
            ce.node.scale.x = 1.0

        ce.node.frame_current_x = min(frame, max_frame - 1)

    challenge.all_done = all_finished
    return all_finished
