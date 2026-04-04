"""Simulate Galaga Z80 flight path system and output scaled waypoints.

The original Galaga uses a rotation-based path system on a 224x288 screen.
This script simulates the per-frame movement math from the Z80 disassembly
(hackbar/galaga, rom0/gg1-5.s) and outputs (x, y) waypoint lists scaled
for a 128x128 screen, suitable for Thumbalaga's interpolation engine.

Original coordinate system:
  - 224 wide x 288 tall (portrait)
  - 9.7 fixed-point positions
  - 10-bit rotation angle (0-1023 = 360 degrees)
  - Primary/secondary axis decomposition
  - Axes alternate updates at 30Hz each (even/odd frames)

Output coordinate system:
  - Camera coords: -64 to +64 on both axes
  - Scale: x *= 128/224, y *= 128/288
"""

import math
import json


# ============================================================
# Z80 flight path simulator
# ============================================================

class PathSimulator:
    """Simulate the Galaga Z80 flight path movement system."""

    def __init__(self):
        self.x = 0.0  # 9.7 fixed-point, we use float
        self.y = 0.0
        self.angle = 0  # 10-bit (0-1023)
        self.frame = 0
        self.path_x = []
        self.path_y = []

    def reset(self, x, y, angle_quadrant):
        """Set starting position and angle.
        x, y: 8-bit screen coords from db_2A6C
        angle_quadrant: 0=right, 1=down, 2=left, 3=up
        """
        self.x = float(x)
        self.y = float(y)
        self.angle = angle_quadrant * 256  # quadrant to 10-bit angle
        self.frame = 0
        self.path_x = [self.x]
        self.path_y = [self.y]

    def step(self, speed_lo, speed_hi, rot_delta, mirror=False):
        """Execute one frame of movement.
        speed_lo: low nibble of speed byte (0x0A field)
        speed_hi: high nibble of speed byte (0x0B field)
        rot_delta: signed rotation step per frame
        mirror: if True, negate rotation (for opposite-side entry)
        """
        # Update rotation angle
        if mirror:
            rot_delta = -rot_delta
        self.angle = (self.angle + rot_delta) & 0x3FF  # 10-bit wrap

        # Convert angle to radians
        # 0 = right, 256 = down, 512 = left, 768 = up
        angle_rad = (self.angle / 1024.0) * 2.0 * math.pi

        # Determine speed for this frame (alternating axes)
        if self.frame % 2 == 0:
            speed = speed_hi
        else:
            speed = speed_lo

        # Primary axis: along the angle direction
        # Secondary axis: perpendicular contribution (cross-axis)
        # The Z80 code decomposes into primary (full speed) and secondary
        # (fractional, based on angle within quadrant)
        #
        # Simplified: treat as standard polar decomposition
        # dx = speed * cos(angle), dy = speed * sin(angle)
        # But the Z80 uses an alternating-axis scheme, so effective speed
        # is roughly speed/2 per axis per frame (since each axis only
        # updates every other frame)
        dx = speed * math.cos(angle_rad)
        dy = speed * math.sin(angle_rad)

        self.x += dx
        self.y += dy
        self.frame += 1
        self.path_x.append(self.x)
        self.path_y.append(self.y)

    def run_token(self, speed_byte, rot_delta, duration, mirror=False):
        """Run a 3-byte path token for `duration` frames."""
        speed_lo = speed_byte & 0x0F
        speed_hi = (speed_byte >> 4) & 0x0F
        # Treat rot_delta as signed byte
        if rot_delta > 127:
            rot_delta -= 256
        for _ in range(duration):
            self.step(speed_lo, speed_hi, rot_delta, mirror)

    def run_tokens(self, tokens, mirror=False):
        """Run a list of (speed_byte, rot_delta, duration) tokens."""
        for speed, rot, dur in tokens:
            self.run_token(speed, rot, dur, mirror)

    def get_path(self):
        """Return the raw (x, y) path as list of tuples."""
        return list(zip(self.path_x, self.path_y))

    def get_scaled_waypoints(self, num_points=16, scale_x=128/224, scale_y=128/288,
                              center_x=112, center_y=144, as_camera=True):
        """Sample evenly-spaced waypoints and scale for 128x128 screen.

        Original Galaga screen: 224x288, center at roughly (112, 144).
        Camera coords: -64 to +64 centered at (0, 0).

        Args:
            num_points: number of waypoints to output
            scale_x/y: scaling factors
            center_x/y: original screen center
            as_camera: if True, output as camera coords (-64..64)
        """
        path = self.get_path()
        n = len(path)
        if n < 2:
            return [(0, 0)]

        # Sample evenly
        indices = [int(i * (n - 1) / (num_points - 1)) for i in range(num_points)]
        waypoints = []
        for idx in indices:
            ox, oy = path[idx]
            # Scale relative to center
            sx = (ox - center_x) * scale_x
            sy = -(oy - center_y) * scale_y  # negate Y for screen coords
            if as_camera:
                # Camera coords are already centered
                waypoints.append((round(sx, 1), round(sy, 1)))
            else:
                waypoints.append((round(sx + 64, 1), round(sy + 64, 1)))
        return waypoints

    def get_relative_waypoints(self, num_points=16, scale_x=128/224, scale_y=128/288):
        """Get waypoints as (dx, dy) offsets from the start position, scaled.
        Y is negated because original Galaga has Y=0 at bottom (player),
        but our game has Y increasing downward (positive dy = dive down).
        """
        path = self.get_path()
        n = len(path)
        if n < 2:
            return [(0, 0)]

        start_x, start_y = path[0]
        indices = [int(i * (n - 1) / (num_points - 1)) for i in range(num_points)]
        waypoints = []
        for idx in indices:
            ox, oy = path[idx]
            dx = (ox - start_x) * scale_x
            dy = -(oy - start_y) * scale_y  # negate Y: original Y-down = our Y-up
            waypoints.append((round(dx, 1), round(dy, 1)))
        return waypoints


# ============================================================
# Starting coordinates from db_2A6C
# ============================================================
# Each entry: (Y, X, rotation_quadrant)
# Y: 8-bit screen position, X: 8-bit screen position
# Rotation: 0=right, 1=down, 2=left, 3=up

START_COORDS = {
    0:  (0x9B, 0x34, 3),   # top entry, left of center
    1:  (0x9B, 0x44, 3),   # top entry, right of center
    2:  (0x23, 0x00, 0),   # left side entry
    3:  (0x23, 0x78, 2),   # right side entry
    4:  (0x9B, 0x2C, 3),   # top entry, further left
    5:  (0x9B, 0x4C, 3),   # top entry, further right
    6:  (0x2B, 0x00, 0),   # left side, lower
    7:  (0x2B, 0x78, 2),   # right side, lower
    8:  (0x9B, 0x34, 3),   # same as 0
    9:  (0x9B, 0x34, 3),   # same as 0
    10: (0x9B, 0x44, 3),   # same as 1
    11: (0x9B, 0x44, 3),   # same as 1
}

# Path index to starting coord index (from db_2A3C upper bits)
PATH_START_IDX = {
    0: 0, 1: 2, 2: 4, 3: 2,
    4: 0, 5: 6, 6: 0, 7: 2,
    8: 0, 9: 2, 10: 8, 11: 2,
    12: 8, 13: 2, 14: 0, 15: 2,
    16: 0, 17: 2, 18: 0, 19: 2,
    20: 0, 21: 2, 22: 10, 23: 10,
}


# ============================================================
# Raw path token data from Z80 disassembly
# Each entry is a list of (speed_byte, rot_delta, duration) tuples
# Special commands are handled by terminating the token list
# ============================================================

# --- DIVE ATTACK PATHS ---

# Yellow bee dive (db_flv_atk_yllw) - main path only
DIVE_BEE_TOKENS = [
    (0x12, 0x18, 0x1E),   # curve out: speed 1/2, rot=+24, 30 frames
    (0x12, 0x00, 0x34),   # straight dive: rot=0, 52 frames
    (0x12, 0xFB, 0x26),   # curve at bottom: rot=-5, 38 frames
    (0x12, 0x00, 0x02),   # brief straight
    (0x12, 0xFA, 0x3C),   # wide loop: rot=-6, 60 frames
    # 0xFA command = wrap around bottom, head home
    (0x12, 0xF8, 0x10),   # curve back: rot=-8, 16 frames
    (0x12, 0x00, 0x40),   # straight home: 64 frames
]

# Red butterfly/moth dive (db_flv_atk_red) - adapted for 128x128
# Original has a wide S-curve that spans ~270px horizontally.
# Tightened: shorter S-curve segments, more vertical emphasis.
DIVE_BUTTERFLY_TOKENS = [
    (0x12, 0x18, 0x1D),   # curve out: rot=+24, 29 frames
    (0x12, 0x00, 0x28),   # straight dive: 40 frames
    (0x12, 0xFA, 0x02),   # slight curve: rot=-6, 2 frames
    # Tightened S-curve (original was 48+48 frames, now 20+20)
    (0x11, 0x06, 0x14),   # S-curve right: slower speed, rot=+6, 20 frames
    (0x11, 0xFA, 0x14),   # S-curve left: rot=-6, 20 frames
    (0x12, 0x00, 0x10),   # straight: 16 frames
    # Loop back
    (0x12, 0xF0, 0x18),   # curve back: rot=-16, 24 frames
    (0x12, 0x00, 0x30),   # straight home: 48 frames
]

# Boss normal dive (db_flv_0411)
DIVE_BOSS_TOKENS = [
    (0x12, 0x18, 0x14),   # quick curve: rot=+24, 20 frames
    (0x12, 0x03, 0x2A),   # gradual curve: rot=+3, 42 frames
    (0x12, 0x10, 0x40),   # tighter turn: rot=+16, 64 frames
    (0x12, 0x01, 0x20),   # gentle coast: rot=+1, 32 frames
    (0x12, 0xFE, 0x71),   # long approach: rot=-2, 113 frames
]

# Boss capture dive (db_0454) - approach to beam zone
# Original: quick curve then F4 command (beam setup). The boss needs to
# dive from formation (~y=-46) to beam zone (y=10-30 in camera coords).
# We extend the path to cover the full dive to beam position.
DIVE_BOSS_CAPTURE_TOKENS = [
    (0x12, 0x18, 0x14),   # quick curve: rot=+24, 20 frames
    (0x12, 0x00, 0x04),   # brief straight
    (0x12, 0x00, 0x30),   # continue diving straight to beam zone, 48 frames
    (0x12, 0x00, 0x30),   # keep going, 48 frames
    (0x12, 0x00, 0x20),   # keep going, 32 frames
]

# Rogue fighter (db_fltv_rogefgter) - same as boss but longer final segment
DIVE_ROGUE_TOKENS = [
    (0x12, 0x18, 0x14),
    (0x12, 0x03, 0x2A),
    (0x12, 0x10, 0x40),
    (0x12, 0x01, 0x20),
    (0x12, 0xFE, 0x78),   # longer approach: 120 frames
]


# --- ENTRY FLIGHT PATHS ---

# Path 0: db_flv_001d - top entry, curve left
ENTRY_PATH_0_TOKENS = [
    (0x23, 0x06, 0x16),   # speed 2/3, rot=+6, 22 frames
    (0x23, 0x00, 0x19),   # straight, 25 frames
    # F7 = branch point (skipped)
    (0x23, 0xF0, 0x26),   # rot=-16, 38 frames (sharp curve to formation)
]

# Path 1: db_flv_0067 - top entry, different curve
ENTRY_PATH_1_TOKENS = [
    (0x23, 0x08, 0x08),   # rot=+8, 8 frames
    (0x23, 0x03, 0x1B),   # rot=+3, 27 frames
    (0x23, 0x08, 0x0F),   # rot=+8, 15 frames
    (0x23, 0x16, 0x15),   # rot=+22, 21 frames
    # F7 = branch point
    (0x23, 0x16, 0x19),   # rot=+22, 25 frames
]

# Path 2: db_flv_009f - from left side
ENTRY_PATH_2_TOKENS = [
    (0x33, 0x06, 0x18),   # speed 3/3, rot=+6, 24 frames
    (0x23, 0x00, 0x18),   # straight, 24 frames
    # F7 = branch
    (0x23, 0xF0, 0x20),   # rot=-16, 32 frames
]

# Path 3: db_flv_00d4 - from right side
ENTRY_PATH_3_TOKENS = [
    (0x23, 0x03, 0x18),   # rot=+3, 24 frames
    (0x33, 0x04, 0x10),   # speed 3/3, rot=+4, 16 frames
    (0x23, 0x08, 0x0A),   # rot=+8, 10 frames
    (0x44, 0x16, 0x12),   # speed 4/4, rot=+22, 18 frames
    # F7 = branch
    (0x44, 0x16, 0x1D),   # rot=+22, 29 frames
]

# Path 4: db_flv_017b - top entry variant
ENTRY_PATH_4_TOKENS = [
    (0x23, 0x06, 0x18),   # rot=+6, 24 frames
    (0x23, 0x00, 0x18),   # straight, 24 frames
    # F7 = branch
    (0x44, 0xF0, 0x20),   # speed 4/4, rot=-16, 32 frames
]

# Path 5: db_flv_01b0 - from side, complex entry
ENTRY_PATH_5_TOKENS = [
    (0x23, 0x03, 0x20),   # rot=+3, 32 frames
    (0x23, 0x08, 0x0F),   # rot=+8, 15 frames
    (0x23, 0x16, 0x12),   # rot=+22, 18 frames
    # F7 = branch
    (0x23, 0x16, 0x1D),   # rot=+22, 29 frames
]

# Path 6: db_flv_01e8 - straight approach
ENTRY_PATH_6_TOKENS = [
    (0x23, 0x00, 0x10),   # straight, 16 frames
    (0x23, 0x01, 0x40),   # very gentle curve, 64 frames
    (0x22, 0x0C, 0x37),   # speed 2/2, rot=+12, 55 frames
]

# Path 7: db_flv_01f5 - curved approach
ENTRY_PATH_7_TOKENS = [
    (0x23, 0x02, 0x3A),   # rot=+2, 58 frames
    (0x23, 0x10, 0x09),   # rot=+16, 9 frames
    (0x23, 0x00, 0x18),   # straight, 24 frames
    (0x23, 0x20, 0x10),   # rot=+32, 16 frames
    (0x23, 0x00, 0x18),   # straight, 24 frames
    (0x23, 0x20, 0x0D),   # rot=+32, 13 frames
]

# Path 8: db_flv_020b - loop entry
ENTRY_PATH_8_TOKENS = [
    (0x23, 0x00, 0x10),   # straight, 16 frames
    (0x23, 0x01, 0x30),   # gentle curve, 48 frames
    (0x00, 0x40, 0x08),   # speed 0, rot=+64, 8 frames (sharp spin)
    (0x23, 0xFF, 0x30),   # rot=-1, 48 frames
]

# Path 9: db_flv_021b - wide curve
ENTRY_PATH_9_TOKENS = [
    (0x23, 0x00, 0x30),   # straight, 48 frames
    (0x23, 0x05, 0x80),   # rot=+5, 128 frames
    (0x23, 0x05, 0x4C),   # rot=+5, 76 frames
    (0x23, 0x04, 0x01),   # rot=+4, 1 frame
    (0x23, 0x00, 0x50),   # straight, 80 frames
]

# Path 10: db_flv_022b - zigzag
ENTRY_PATH_10_TOKENS = [
    (0x23, 0x00, 0x28),   # straight, 40 frames
    (0x23, 0x06, 0x1D),   # rot=+6, 29 frames
    (0x23, 0x00, 0x11),   # straight, 17 frames
    (0x00, 0x40, 0x08),   # spin, 8 frames
    (0x23, 0x00, 0x11),   # straight, 17 frames
    (0x23, 0xFA, 0x1D),   # rot=-6, 29 frames
    (0x23, 0x00, 0x50),   # straight, 80 frames
]

# Path 11: db_flv_0241 - complex curve
ENTRY_PATH_11_TOKENS = [
    (0x23, 0x00, 0x21),   # straight, 33 frames
    (0x00, 0x20, 0x10),   # spin, 16 frames
    (0x23, 0xF8, 0x20),   # rot=-8, 32 frames
    (0x23, 0xFF, 0x20),   # rot=-1, 32 frames
    (0x23, 0xF8, 0x1B),   # rot=-8, 27 frames
    (0x23, 0xE8, 0x0B),   # rot=-24, 11 frames
    (0x23, 0x00, 0x21),   # straight, 33 frames
    (0x00, 0x20, 0x08),   # spin, 8 frames
    (0x23, 0x00, 0x42),   # straight, 66 frames
]

# Path 12: db_flv_025d - figure-8
ENTRY_PATH_12_TOKENS = [
    (0x23, 0x00, 0x08),   # straight, 8 frames
    (0x00, 0x20, 0x08),   # spin, 8 frames
    (0x23, 0xF0, 0x20),   # rot=-16, 32 frames
    (0x23, 0x10, 0x20),   # rot=+16, 32 frames
    (0x23, 0xF0, 0x40),   # rot=-16, 64 frames
    (0x23, 0x10, 0x20),   # rot=+16, 32 frames
    (0x23, 0xF0, 0x20),   # rot=-16, 32 frames
    (0x00, 0x20, 0x08),   # spin, 8 frames
    (0x23, 0x00, 0x30),   # straight, 48 frames
]

# Path 13: db_flv_0279 - oscillating
ENTRY_PATH_13_TOKENS = [
    (0x23, 0x10, 0x0C),   # rot=+16, 12 frames
    (0x23, 0x00, 0x20),   # straight, 32 frames
    (0x23, 0xE8, 0x10),   # rot=-24, 16 frames
    (0x23, 0xF4, 0x10),   # rot=-12, 16 frames
    (0x23, 0xE8, 0x10),   # rot=-24, 16 frames
    (0x23, 0xF4, 0x32),   # rot=-12, 50 frames
    (0x23, 0xE8, 0x10),   # rot=-24, 16 frames
    (0x23, 0xF4, 0x32),   # rot=-12, 50 frames
    (0x23, 0xE8, 0x10),   # rot=-24, 16 frames
    (0x23, 0xF4, 0x10),   # rot=-12, 16 frames
    (0x23, 0xE8, 0x0E),   # rot=-24, 14 frames
    (0x23, 0x02, 0x30),   # rot=+2, 48 frames
]

# Path 14: db_flv_029e - swooping
ENTRY_PATH_14_TOKENS = [
    (0x23, 0xF1, 0x08),   # rot=-15, 8 frames
    (0x23, 0x00, 0x10),   # straight, 16 frames
    (0x23, 0x05, 0x3C),   # rot=+5, 60 frames
    (0x23, 0x07, 0x42),   # rot=+7, 66 frames
    (0x23, 0x0A, 0x40),   # rot=+10, 64 frames
    (0x23, 0x10, 0x2D),   # rot=+16, 45 frames
    (0x23, 0x20, 0x19),   # rot=+32, 25 frames
    (0x00, 0xFC, 0x14),   # spin rot=-4, 20 frames
    (0x23, 0x02, 0x4A),   # rot=+2, 74 frames
]

# Path 15: db_flv_02ba - symmetric curve
ENTRY_PATH_15_TOKENS = [
    (0x23, 0x04, 0x20),   # rot=+4, 32 frames
    (0x23, 0x00, 0x16),   # straight, 22 frames
    (0x23, 0xF0, 0x30),   # rot=-16, 48 frames
    (0x23, 0x00, 0x12),   # straight, 18 frames
    (0x23, 0x10, 0x30),   # rot=+16, 48 frames
    (0x23, 0x00, 0x12),   # straight, 18 frames
    (0x23, 0x10, 0x30),   # rot=+16, 48 frames
    (0x23, 0x00, 0x16),   # straight, 22 frames
    (0x23, 0x04, 0x20),   # rot=+4, 32 frames
    (0x23, 0x00, 0x10),   # straight, 16 frames
]

# Path 16: db_flv_02d9 - multi-bounce
ENTRY_PATH_16_TOKENS = [
    (0x23, 0x00, 0x15),   # straight, 21 frames
    (0x00, 0x20, 0x08),   # spin, 8 frames
    (0x23, 0x00, 0x11),   # straight, 17 frames
    (0x00, 0xE0, 0x08),   # spin reverse, 8 frames
    (0x23, 0x00, 0x18),   # straight, 24 frames
    (0x00, 0x20, 0x08),   # spin, 8 frames
    (0x23, 0x00, 0x13),   # straight, 19 frames
    (0x00, 0xE0, 0x08),   # spin reverse, 8 frames
    (0x23, 0x00, 0x1F),   # straight, 31 frames
    (0x00, 0x20, 0x08),   # spin, 8 frames
    (0x23, 0x00, 0x30),   # straight, 48 frames
]

# Path 17: db_flv_02fb - complex approach
ENTRY_PATH_17_TOKENS = [
    (0x23, 0x02, 0x0E),   # rot=+2, 14 frames
    (0x23, 0x00, 0x34),   # straight, 52 frames
    (0x23, 0x12, 0x19),   # rot=+18, 25 frames
    (0x23, 0x00, 0x20),   # straight, 32 frames
    (0x23, 0xE0, 0x0E),   # rot=-32, 14 frames
    (0x23, 0x00, 0x12),   # straight, 18 frames
    (0x23, 0x20, 0x0E),   # rot=+32, 14 frames
    (0x23, 0x00, 0x0C),   # straight, 12 frames
    (0x23, 0xE0, 0x0E),   # rot=-32, 14 frames
    (0x23, 0x1B, 0x08),   # rot=+27, 8 frames
    (0x23, 0x00, 0x10),   # straight, 16 frames
]

# Path 18: db_flv_031d - step-wise
ENTRY_PATH_18_TOKENS = [
    (0x23, 0x00, 0x0D),   # straight, 13 frames
    (0x00, 0xC0, 0x04),   # spin, 4 frames
    (0x23, 0x00, 0x21),   # straight, 33 frames
    (0x00, 0x40, 0x06),   # spin, 6 frames
    (0x23, 0x00, 0x51),   # straight, 81 frames
    (0x00, 0xC0, 0x06),   # spin, 6 frames
    (0x23, 0x00, 0x73),   # straight, 115 frames
]

# Path 19: db_flv_0333 - symmetric wave
ENTRY_PATH_19_TOKENS = [
    (0x23, 0x08, 0x20),   # rot=+8, 32 frames
    (0x23, 0x00, 0x16),   # straight, 22 frames
    (0x23, 0xE0, 0x0C),   # rot=-32, 12 frames
    (0x23, 0x02, 0x0B),   # rot=+2, 11 frames
    (0x23, 0x11, 0x0C),   # rot=+17, 12 frames
    (0x23, 0x02, 0x0B),   # rot=+2, 11 frames
    (0x23, 0xE0, 0x0C),   # rot=-32, 12 frames
    (0x23, 0x00, 0x16),   # straight, 22 frames
    (0x23, 0x08, 0x20),   # rot=+8, 32 frames
]

# Challenge paths
# Path 20: db_flv_0fda
ENTRY_PATH_20_TOKENS = [
    (0x23, 0x00, 0x1B),   # straight, 27 frames
    (0x23, 0xF0, 0x40),   # rot=-16, 64 frames
    (0x23, 0x00, 0x09),   # straight, 9 frames
    (0x23, 0x05, 0x11),   # rot=+5, 17 frames
    (0x23, 0x00, 0x10),   # straight, 16 frames
    (0x23, 0x10, 0x40),   # rot=+16, 64 frames
    (0x23, 0x04, 0x30),   # rot=+4, 48 frames
]

# Path 21: db_flv_0ff0
ENTRY_PATH_21_TOKENS = [
    (0x23, 0x02, 0x35),   # rot=+2, 53 frames
    (0x23, 0x08, 0x10),   # rot=+8, 16 frames
    (0x23, 0x10, 0x3C),   # rot=+16, 60 frames
]

ALL_ENTRY_PATHS = {
    0: ENTRY_PATH_0_TOKENS,
    1: ENTRY_PATH_1_TOKENS,
    2: ENTRY_PATH_2_TOKENS,
    3: ENTRY_PATH_3_TOKENS,
    4: ENTRY_PATH_4_TOKENS,
    5: ENTRY_PATH_5_TOKENS,
    6: ENTRY_PATH_6_TOKENS,
    7: ENTRY_PATH_7_TOKENS,
    8: ENTRY_PATH_8_TOKENS,
    9: ENTRY_PATH_9_TOKENS,
    10: ENTRY_PATH_10_TOKENS,
    11: ENTRY_PATH_11_TOKENS,
    12: ENTRY_PATH_12_TOKENS,
    13: ENTRY_PATH_13_TOKENS,
    14: ENTRY_PATH_14_TOKENS,
    15: ENTRY_PATH_15_TOKENS,
    16: ENTRY_PATH_16_TOKENS,
    17: ENTRY_PATH_17_TOKENS,
    18: ENTRY_PATH_18_TOKENS,
    19: ENTRY_PATH_19_TOKENS,
    20: ENTRY_PATH_20_TOKENS,
    21: ENTRY_PATH_21_TOKENS,
}

ALL_DIVE_PATHS = {
    'bee': DIVE_BEE_TOKENS,
    'butterfly': DIVE_BUTTERFLY_TOKENS,
    'boss': DIVE_BOSS_TOKENS,
    'boss_capture': DIVE_BOSS_CAPTURE_TOKENS,
    'rogue': DIVE_ROGUE_TOKENS,
}


# ============================================================
# Generate all paths
# ============================================================

def simulate_path(tokens, start_y, start_x, start_rot_quad, mirror=False):
    """Simulate a path and return the simulator."""
    sim = PathSimulator()
    sim.reset(start_x, start_y, start_rot_quad)
    sim.run_tokens(tokens, mirror)
    return sim


def generate_dive_paths(num_points=14):
    """Generate scaled dive path waypoints."""
    print("# ============================================================")
    print("# DIVE PATHS (relative offsets from start position)")
    print("# Generated from Galaga Z80 disassembly (hackbar/galaga)")
    print("# Scaled for 128x128 screen (from 224x288)")
    print("# ============================================================")
    print()

    # Dive paths start from formation, which is near the top of screen
    # Use a generic starting position for relative paths
    for name, tokens in ALL_DIVE_PATHS.items():
        # Simulate from a neutral starting point
        sim = PathSimulator()
        sim.reset(0x3C, 0x3C, 1)  # start facing down (quadrant 1)
        sim.run_tokens(tokens, mirror=False)

        wp = sim.get_relative_waypoints(num_points=num_points)
        wp_int = [(int(round(x)), int(round(y))) for x, y in wp]

        print(f"DIVE_{name.upper()} = [")
        for x, y in wp_int:
            print(f"    ({x}, {y}),")
        print("]")
        print()

        # Mirror version
        wp_m = [(-x, y) for x, y in wp_int]
        print(f"DIVE_{name.upper()}_MIRROR = [")
        for x, y in wp_m:
            print(f"    ({x}, {y}),")
        print("]")
        print()


def generate_entry_paths(num_points=12):
    """Generate scaled entry path waypoints in camera coordinates."""
    print("# ============================================================")
    print("# ENTRY PATHS (camera coordinates, -64 to +64)")
    print("# Generated from Galaga Z80 disassembly (hackbar/galaga)")
    print("# Scaled for 128x128 screen (from 224x288)")
    print("# ============================================================")
    print()

    for path_idx, tokens in ALL_ENTRY_PATHS.items():
        start_idx = PATH_START_IDX.get(path_idx, 0)
        start_y, start_x, start_rot = START_COORDS[start_idx]

        sim = simulate_path(tokens, start_y, start_x, start_rot)
        wp = sim.get_scaled_waypoints(num_points=num_points)
        wp_int = [(int(round(x)), int(round(y))) for x, y in wp]

        print(f"ENTRY_PATH_{path_idx} = [  # db_flv index {path_idx}, start=({start_x:#x},{start_y:#x},rot={start_rot})")
        for x, y in wp_int:
            print(f"    ({x}, {y}),")
        print("]")
        print()

        # Mirror version (negate x, keep y)
        wp_m = [(-x, y) for x, y in wp_int]
        print(f"ENTRY_PATH_{path_idx}_MIRROR = [")
        for x, y in wp_m:
            print(f"    ({x}, {y}),")
        print("]")
        print()


def generate_visualization():
    """Generate a simple ASCII visualization of paths for debugging."""
    print("\n# ============================================================")
    print("# PATH VISUALIZATIONS")
    print("# ============================================================\n")

    for name, tokens in ALL_DIVE_PATHS.items():
        sim = PathSimulator()
        sim.reset(0x3C, 0x3C, 1)
        sim.run_tokens(tokens)
        path = sim.get_path()

        print(f"--- {name} ({len(path)} frames) ---")
        # Find bounds
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        print(f"  X range: {min_x:.0f} to {max_x:.0f} (span: {max_x-min_x:.0f})")
        print(f"  Y range: {min_y:.0f} to {max_y:.0f} (span: {max_y-min_y:.0f})")
        print(f"  Scaled X span: {(max_x-min_x)*128/224:.0f}px")
        print(f"  Scaled Y span: {(max_y-min_y)*128/288:.0f}px")
        print()


if __name__ == '__main__':
    import sys

    if '--viz' in sys.argv:
        generate_visualization()
    elif '--entry' in sys.argv:
        generate_entry_paths()
    elif '--dive' in sys.argv:
        generate_dive_paths()
    else:
        print("# Galaga Path Generator")
        print("# Usage: python3 generate_paths.py [--dive] [--entry] [--viz]")
        print()
        generate_visualization()
        print()
        generate_dive_paths()
        print()
        generate_entry_paths()
