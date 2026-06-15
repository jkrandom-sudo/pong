"""Pure game logic for Pong - no curses imports.

This module contains Ball, Paddle, and GameState classes with zero curses
dependencies, making them fully testable with plain pytest.
"""

import random
import math
from typing import Optional, Tuple

# ── Constants ────────────────────────────────────────────────────────────────

GAME_WIDTH = 80
GAME_HEIGHT = 24
PADDLE_HEIGHT = 5
WINNING_SCORE = 11
INITIAL_SPEED = 1.0
SPEED_INCREMENT = 0.2
MAX_SPEED = 5.0
MIN_SPEED = 0.5
AI_DELAY_FRAMES = 3
AI_ERROR_RANGE = 2.0


# ── Ball ─────────────────────────────────────────────────────────────────────

class Ball:
    """Ball with position, velocity, and speed management."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 1.0
        self.vy = 0.0
        self.speed = INITIAL_SPEED
        self._randomize_direction()

    def _randomize_direction(self) -> None:
        """Set a random angle between -45 and +45 degrees, left or right."""
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        direction = random.choice([-1, 1])
        self.vx = direction * math.cos(angle)
        self.vy = math.sin(angle)

    def move(self) -> None:
        """Advance ball position by one frame."""
        self.x += self.vx * self.speed
        self.y += self.vy * self.speed

    def bounce_vertical(self) -> None:
        """Reverse vertical direction (top/bottom wall bounce)."""
        self.vy = -self.vy

    def bounce_horizontal(self) -> None:
        """Reverse horizontal direction (paddle hit) and increase speed."""
        self.vx = -self.vx
        self.speed = min(self.speed + SPEED_INCREMENT, MAX_SPEED)

    def reset(self, x: float, y: float) -> None:
        """Reset ball to given position with initial speed and random direction."""
        self.x = x
        self.y = y
        self.speed = INITIAL_SPEED
        self._randomize_direction()

    def get_position(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def get_int_position(self) -> Tuple[int, int]:
        return (round(self.x), round(self.y))


# ── Paddle ───────────────────────────────────────────────────────────────────

class Paddle:
    """Paddle with position, height, and boundary-constrained movement."""

    def __init__(self, x: int, y: int, height: int = PADDLE_HEIGHT,
                 game_height: int = GAME_HEIGHT):
        self.x = x
        self.y = y
        self.height = height
        self.game_height = game_height
        self.min_y = height // 2
        self.max_y = game_height - 1 - height // 2

    def move_up(self, amount: int = 1) -> None:
        """Move paddle up, clamped to top boundary."""
        self.y = max(self.min_y, self.y - amount)

    def move_down(self, amount: int = 1) -> None:
        """Move paddle down, clamped to bottom boundary."""
        self.y = min(self.max_y, self.y + amount)

    def get_top(self) -> int:
        return self.y - self.height // 2

    def get_bottom(self) -> int:
        return self.y + self.height // 2

    def get_y_range(self) -> range:
        return range(self.get_top(), self.get_bottom() + 1)


# ── GameState ────────────────────────────────────────────────────────────────

class GameState:
    """Complete game state — scores, paddles, ball, mode, settings."""

    def __init__(self):
        self.width = GAME_WIDTH
        self.height = GAME_HEIGHT
        self.paddle_height = PADDLE_HEIGHT
        self.winning_score = WINNING_SCORE

        # Paddles
        self.paddle1 = Paddle(2, GAME_HEIGHT // 2, game_height=GAME_HEIGHT)
        self.paddle2 = Paddle(GAME_WIDTH - 3, GAME_HEIGHT // 2,
                              game_height=GAME_HEIGHT)

        # Ball
        self.ball = Ball(GAME_WIDTH // 2, GAME_HEIGHT // 2)

        # Scores
        self.score1 = 0
        self.score2 = 0

        # Game mode / settings
        self.mode = 'ai'          # 'ai' | '2p'
        self.language = 'zh'      # 'zh' | 'en'
        self.sound_mode = 'visual+beep'  # 'off' | 'visual' | 'visual+beep'
        self.paused = False
        self.game_over = False
        self.winner: Optional[int] = None

        # AI state
        self.ai_delay_counter = 0
        self.ai_target_y = float(GAME_HEIGHT // 2)

        # Speed
        self.speed_level = 1
        self.ball_speed = INITIAL_SPEED

        # Screen navigation
        self.current_screen = 'language'  # language | menu | game | history

        # Visual feedback timers
        self.beep_text_timer = 0
        self.flash_border = False
        self.flash_timer = 0

    # ── Game lifecycle ────────────────────────────────────────────────────

    def reset_game(self) -> None:
        """Reset everything for a new match (keeps mode/language/sound)."""
        self.score1 = 0
        self.score2 = 0
        self.ball.reset(self.width // 2, self.height // 2)
        self.paddle1 = Paddle(2, self.height // 2, game_height=self.height)
        self.paddle2 = Paddle(self.width - 3, self.height // 2,
                              game_height=self.height)
        self.game_over = False
        self.winner = None
        self.paused = False
        self.speed_level = 1
        self.ball_speed = INITIAL_SPEED
        self.ai_delay_counter = 0
        self.ai_target_y = float(self.height // 2)

    # ── Controls ──────────────────────────────────────────────────────────

    def toggle_pause(self) -> None:
        if not self.game_over:
            self.paused = not self.paused

    def increase_speed(self) -> None:
        if self.speed_level < 10:
            self.speed_level += 1
            self.ball_speed = INITIAL_SPEED + (self.speed_level - 1) * SPEED_INCREMENT
            self.ball.speed = self.ball_speed

    def decrease_speed(self) -> None:
        if self.speed_level > 1:
            self.speed_level -= 1
            self.ball_speed = INITIAL_SPEED + (self.speed_level - 1) * SPEED_INCREMENT
            self.ball.speed = self.ball_speed

    def toggle_sound(self) -> None:
        """Toggle sound between off and visual+beep (simple on/off)."""
        if self.sound_mode == 'off':
            self.sound_mode = 'visual+beep'
        else:
            self.sound_mode = 'off'

    def cycle_sound_mode(self) -> None:
        modes = ['off', 'visual', 'visual+beep']
        idx = modes.index(self.sound_mode)
        self.sound_mode = modes[(idx + 1) % len(modes)]

    # ── AI ────────────────────────────────────────────────────────────────

    def update_ai(self) -> None:
        """Move AI paddle toward ball with delay and random error."""
        if self.mode != 'ai':
            return

        self.ai_delay_counter += 1
        if self.ai_delay_counter >= AI_DELAY_FRAMES:
            self.ai_delay_counter = 0
            error = random.uniform(-AI_ERROR_RANGE, AI_ERROR_RANGE)
            self.ai_target_y = self.ball.y + error
            self.ai_target_y = max(float(self.paddle2.min_y),
                                   min(float(self.paddle2.max_y),
                                       self.ai_target_y))

        diff = self.paddle2.y - self.ai_target_y
        if diff < -0.5:
            self.paddle2.move_down()
        elif diff > 0.5:
            self.paddle2.move_up()

    # ── Collision & scoring ───────────────────────────────────────────────

    def check_collision(self) -> Optional[str]:
        """Detect and handle collisions.

        Returns one of:
          'paddle_hit'  — ball hit a paddle
          'wall_bounce' — ball bounced off top/bottom wall
          'score_p1'    — player 1 scored
          'score_p2'    — player 2 scored
          None          — nothing happened
        """
        ball = self.ball
        bx, by = ball.get_position()

        # Wall bounce (top / bottom)
        if by <= 0 or by >= self.height - 1:
            ball.bounce_vertical()
            if by <= 0:
                ball.y = 0.0
            else:
                ball.y = float(self.height - 1)
            return 'wall_bounce'

        # Left paddle hit
        if (bx <= self.paddle1.x + 1 and ball.vx < 0 and
                self.paddle1.get_top() <= by <= self.paddle1.get_bottom()):
            ball.bounce_horizontal()
            ball.x = float(self.paddle1.x + 1)
            return 'paddle_hit'

        # Right paddle hit
        if (bx >= self.paddle2.x - 1 and ball.vx > 0 and
                self.paddle2.get_top() <= by <= self.paddle2.get_bottom()):
            ball.bounce_horizontal()
            ball.x = float(self.paddle2.x - 1)
            return 'paddle_hit'

        # Scoring — ball passed a paddle
        if bx < 0:
            self.score2 += 1
            if self.score2 >= WINNING_SCORE:
                self.game_over = True
                self.winner = 2
            else:
                ball.reset(self.width // 2, self.height // 2)
            return 'score_p2'

        if bx >= self.width:
            self.score1 += 1
            if self.score1 >= WINNING_SCORE:
                self.game_over = True
                self.winner = 1
            else:
                ball.reset(self.width // 2, self.height // 2)
            return 'score_p1'

        return None

    # ── Frame update ──────────────────────────────────────────────────────

    def update(self) -> Optional[str]:
        """Advance one frame. Returns collision event or None."""
        if self.paused or self.game_over:
            return None

        self.update_ai()
        self.ball.move()
        event = self.check_collision()

        # Decay visual feedback timers
        if self.beep_text_timer > 0:
            self.beep_text_timer -= 1
        if self.flash_timer > 0:
            self.flash_timer -= 1
        else:
            self.flash_border = False

        return event

    # ── Visual feedback helpers ───────────────────────────────────────────

    def trigger_visual_feedback(self) -> None:
        """Show visual feedback (border flash + BEEP! text)."""
        if self.sound_mode == 'off':
            return
        if self.sound_mode in ('visual', 'visual+beep'):
            self.beep_text_timer = 5
            self.flash_border = True
            self.flash_timer = 3

    def should_beep(self) -> bool:
        return self.sound_mode == 'visual+beep'
