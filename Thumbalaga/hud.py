import engine_draw
import engine_save
import framebuf
from engine_draw import Color
from engine_resources import TextureResource
from constants import *

MAX_SCORES = const(5)
INITIALS_LEN = const(3)
INITIAL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


class HUD:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.lives = START_LIVES
        self.stage = 1
        self._score_str = "0"
        self._hi_str = "0"
        # Stats
        self.shots_fired = 0
        self.hits = 0
        # Scoreboard: list of (score, initials) sorted descending
        self.scoreboard = []
        self._load_scoreboard()
        if self.scoreboard:
            self.high_score = self.scoreboard[0][0]
            self._hi_str = str(self.high_score)
        # Initials entry state
        self.initials = ['A', 'A', 'A']
        self.initial_pos = 0  # which character being edited (0-2)
        self.initial_flash = 0.0  # flash timer
        self.new_score_rank = -1  # rank in scoreboard (-1 = not on board)
        # Load sprites
        self.life_tex = self._load("assets/life_icon.bmp")
        self.narrow_tex = self._load("assets/badge_narrow.bmp")
        self.shield_tex = self._load("assets/badge_shields.bmp")
        self.narrow_fbs = self._split_frames(self.narrow_tex, 5, 10, 2)
        self.shield_fbs = self._split_frames(self.shield_tex, 8, 8, 4)

    def _load(self, path):
        try:
            return TextureResource(path)
        except:
            return None

    def _split_frames(self, tex, fw, fh, count):
        if tex is None:
            return []
        fbs = []
        for i in range(count):
            buf = bytearray(fw * fh * 2)
            src = tex.data
            src_w = tex.width
            for y in range(fh):
                for x in range(fw):
                    so = (y * src_w + i * fw + x) * 2
                    do = (y * fw + x) * 2
                    buf[do] = src[so]
                    buf[do + 1] = src[so + 1]
            fbs.append(framebuf.FrameBuffer(buf, fw, fh, framebuf.RGB565))
        return fbs

    def _load_scoreboard(self):
        try:
            engine_save.set_location("thumbalaga.sav")
            self.scoreboard = []
            for i in range(MAX_SCORES):
                s = engine_save.load("s" + str(i), 0)
                n = engine_save.load("n" + str(i), "---")
                if s and int(s) > 0:
                    self.scoreboard.append((int(s), str(n)))
            self.scoreboard.sort(key=lambda x: x[0], reverse=True)
        except:
            self.scoreboard = []

    def _save_scoreboard(self):
        try:
            engine_save.set_location("thumbalaga.sav")
            for i in range(MAX_SCORES):
                if i < len(self.scoreboard):
                    engine_save.save("s" + str(i), self.scoreboard[i][0])
                    engine_save.save("n" + str(i), self.scoreboard[i][1])
                else:
                    engine_save.save("s" + str(i), 0)
                    engine_save.save("n" + str(i), "---")
            # Also save hi for backwards compat
            if self.scoreboard:
                engine_save.save("hi", self.scoreboard[0][0])
        except:
            pass

    def is_high_score(self):
        """Check if current score qualifies for the scoreboard."""
        if self.score <= 0:
            return False
        if len(self.scoreboard) < MAX_SCORES:
            return True
        return self.score > self.scoreboard[-1][0]

    def insert_score(self, initials_str):
        """Insert current score into scoreboard with given initials."""
        self.scoreboard.append((self.score, initials_str))
        self.scoreboard.sort(key=lambda x: x[0], reverse=True)
        self.scoreboard = self.scoreboard[:MAX_SCORES]
        # Find rank
        self.new_score_rank = -1
        for i, (s, n) in enumerate(self.scoreboard):
            if s == self.score and n == initials_str:
                self.new_score_rank = i
                break
        if self.score >= self.high_score:
            self.high_score = self.score
            self._hi_str = str(self.high_score)
        self._save_scoreboard()

    def start_initials(self):
        """Reset initials entry state."""
        self.initials = ['A', 'A', 'A']
        self.initial_pos = 0
        self.initial_flash = 0.0

    def add_score(self, points):
        self.score += points
        self._score_str = str(self.score)
        if self.score > self.high_score:
            self.high_score = self.score
            self._hi_str = str(self.high_score)

    def set_stage(self, stage):
        self.stage = stage

    def reset(self):
        self.score = 0
        self._score_str = "0"
        self.lives = START_LIVES
        self.stage = 1
        self.shots_fired = 0
        self.hits = 0
        self.new_score_rank = -1

    def draw(self, fb):
        """Draw HUD — score top-left, high score top-right, badges bottom-right."""
        engine_draw.text(None, self._score_str, None, 2, 1, 1, 0, 1.0)
        # "HI" in red, score in white (dimmed)
        engine_draw.text(None, "HI", Color(COL_RED), 80, 1, 1, 0, 1.0)
        engine_draw.text(None, self._hi_str, None, 92, 1, 1, 0, 0.6)

        # Lives at bottom-left
        show_lives = max(0, self.lives - 1)
        if self.life_tex:
            for i in range(show_lives):
                engine_draw.blit(self.life_tex, 2 + i * 8, 122,
                                 Color(COL_MAGENTA), 1.0)
        else:
            for i in range(show_lives):
                fb.rect(2 + i * 8, 122, 6, 6, COL_WHITE, True)

        # Stage badges at bottom-right
        self._draw_stage_badges(fb)

    def _draw_stage_badges(self, fb):
        s = self.stage
        if s <= 0:
            return
        badges = []
        if s >= 50 and len(self.shield_fbs) > 3:
            count_50 = s // 50
            for _ in range(count_50):
                badges.append((self.shield_fbs[3], 8))
            s %= 50
        if s >= 30 and len(self.shield_fbs) > 2:
            badges.append((self.shield_fbs[2], 8))
            s -= 30
        if s >= 20 and len(self.shield_fbs) > 1:
            badges.append((self.shield_fbs[1], 8))
            s -= 20
        if s >= 10 and len(self.shield_fbs) > 0:
            badges.append((self.shield_fbs[0], 8))
            s -= 10
        if s >= 5 and len(self.narrow_fbs) > 1:
            badges.append((self.narrow_fbs[1], 5))
            s -= 5
        while s > 0 and len(self.narrow_fbs) > 0:
            badges.append((self.narrow_fbs[0], 5))
            s -= 1
        x = 126
        for badge_fb, bw in reversed(badges):
            x -= bw + 1
            if x < 50:
                break
            fb.blit(badge_fb, x, 117, COL_MAGENTA)

    def draw_centered_text(self, text, screen_y):
        x = max(0, 64 - len(text) * 3)
        engine_draw.text(None, text, None, x, screen_y, 1, 0, 1.0)

    def draw_title(self, fb):
        engine_draw.text(None, "PRESS A", None, 38, 8, 1, 0, 1.0)
        self.draw_scoreboard(fb, y_start=22, show_press_a=False)

    def draw_game_over(self, fb):
        engine_draw.text(None, "GAME OVER", Color(COL_RED), 30, 55, 1, 0, 1.0)

    def draw_results(self, fb):
        """Draw results screen: shots, hits, ratio, score."""
        engine_draw.text(None, "- RESULTS -", Color(COL_RED), 22, 8, 1, 0, 1.0)

        engine_draw.text(None, "SHOTS FIRED", Color(COL_TEAL), 16, 24, 1, 0, 1.0)
        engine_draw.text(None, str(self.shots_fired), None, 88, 24, 1, 0, 1.0)

        engine_draw.text(None, "HITS", Color(COL_TEAL), 16, 36, 1, 0, 1.0)
        engine_draw.text(None, str(self.hits), None, 88, 36, 1, 0, 1.0)

        if self.shots_fired > 0:
            ratio = (self.hits * 100) // self.shots_fired
        else:
            ratio = 0
        engine_draw.text(None, "HIT RATIO", Color(COL_TEAL), 16, 48, 1, 0, 1.0)
        engine_draw.text(None, str(ratio) + "%", None, 88, 48, 1, 0, 1.0)

        engine_draw.text(None, "SCORE", Color(COL_RED), 16, 66, 1, 0, 1.0)
        engine_draw.text(None, self._score_str, Color(COL_YELLOW), 88, 66, 1, 0, 1.0)

        if self.is_high_score():
            engine_draw.text(None, "NEW HIGH SCORE!", Color(COL_YELLOW), 10, 84, 1, 0, 1.0)
            engine_draw.text(None, "PRESS A", None, 38, 100, 1, 0, 1.0)
        else:
            engine_draw.text(None, "PRESS A", None, 38, 90, 1, 0, 1.0)

    def draw_initials(self, fb, dt):
        """Draw initials entry screen. Returns True when done."""
        import engine_io
        self.initial_flash += dt

        engine_draw.text(None, "ENTER INITIALS", Color(COL_RED), 10, 15, 1, 0, 1.0)
        engine_draw.text(None, "SCORE " + self._score_str, Color(COL_YELLOW), 22, 30, 1, 0, 1.0)

        # Draw the 3 characters
        for i in range(INITIALS_LEN):
            ch = self.initials[i]
            x = 46 + i * 14
            y = 55
            # Flash the active character
            if i == self.initial_pos:
                show = int(self.initial_flash * 4) % 2 == 0
                if show:
                    engine_draw.text(None, ch, Color(COL_YELLOW), x, y, 1, 0, 1.0)
                # Draw underline
                fb.hline(x, y + 8, 6, COL_YELLOW)
            else:
                engine_draw.text(None, ch, None, x, y, 1, 0, 1.0)
                fb.hline(x, y + 8, 6, COL_WHITE)

        engine_draw.text(None, "UP/DN SELECT", Color(COL_TEAL), 16, 80, 1, 0, 1.0)
        engine_draw.text(None, "A=NEXT B=BACK", Color(COL_TEAL), 12, 92, 1, 0, 1.0)

        # Input handling
        pos = self.initial_pos
        ci = INITIAL_CHARS.index(self.initials[pos])

        if engine_io.UP.is_just_pressed:
            ci = (ci - 1) % len(INITIAL_CHARS)
            self.initials[pos] = INITIAL_CHARS[ci]
            self.initial_flash = 0.0
        elif engine_io.DOWN.is_just_pressed:
            ci = (ci + 1) % len(INITIAL_CHARS)
            self.initials[pos] = INITIAL_CHARS[ci]
            self.initial_flash = 0.0
        elif engine_io.A.is_just_pressed:
            if pos < INITIALS_LEN - 1:
                self.initial_pos += 1
                self.initial_flash = 0.0
            else:
                # Done — insert score
                initials_str = ''.join(self.initials)
                self.insert_score(initials_str)
                return True
        elif engine_io.B.is_just_pressed:
            if pos > 0:
                self.initial_pos -= 1
                self.initial_flash = 0.0

        return False

    def draw_scoreboard(self, fb, y_start=10, show_press_a=True):
        """Draw the top 5 scores."""
        engine_draw.text(None, "- TOP SCORES -", Color(COL_RED), 10, y_start, 1, 0, 1.0)

        for i in range(MAX_SCORES):
            y = y_start + 18 + i * 14
            if i < len(self.scoreboard):
                sc, name = self.scoreboard[i]
                if i == self.new_score_rank:
                    col = Color(COL_YELLOW)
                else:
                    col = Color(COL_TEAL)
                rank_str = str(i + 1) + "."
                engine_draw.text(None, rank_str, col, 10, y, 1, 0, 1.0)
                engine_draw.text(None, name, col, 30, y, 1, 0, 1.0)
                engine_draw.text(None, str(sc), col, 60, y, 1, 0, 1.0)
            else:
                engine_draw.text(None, str(i + 1) + ".", Color(COL_TEAL), 10, y, 1, 0, 1.0)
                engine_draw.text(None, "---", Color(COL_TEAL), 30, y, 1, 0, 1.0)

        if show_press_a:
            engine_draw.text(None, "PRESS A", None, 38, y_start + 95, 1, 0, 1.0)
