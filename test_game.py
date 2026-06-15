"""Comprehensive pytest tests for game_logic.py and scores.py.

No curses mocking needed — all game logic is pure Python.
"""

import json
import os
import tempfile
import math
from datetime import datetime

import pytest

from game_logic import (Ball, Paddle, GameState, GAME_WIDTH, GAME_HEIGHT,
                        PADDLE_HEIGHT, WINNING_SCORE, INITIAL_SPEED,
                        SPEED_INCREMENT, MAX_SPEED, MIN_SPEED)
from scores import (load_scores, save_scores, get_top10,
                    format_score_entry, make_score_entry)


# ═══════════════════════════════════════════════════════════════════════════════
# Ball Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBall:
    """Ball movement, bouncing, speed management."""

    def test_ball_initial_position(self):
        ball = Ball(40, 12)
        assert ball.x == 40
        assert ball.y == 12

    def test_ball_initial_speed(self):
        ball = Ball(40, 12)
        assert ball.speed == INITIAL_SPEED

    def test_ball_move_changes_position(self):
        ball = Ball(40, 12)
        old_x, old_y = ball.x, ball.y
        ball.move()
        # Ball should have moved
        assert (ball.x, ball.y) != (old_x, old_y)

    def test_ball_vertical_bounce_reverses_vy(self):
        ball = Ball(40, 1)
        ball.vy = -1.0  # Moving up
        ball.bounce_vertical()
        assert ball.vy == 1.0  # Now moving down

    def test_ball_horizontal_bounce_reverses_vx(self):
        ball = Ball(40, 12)
        vx_before = ball.vx
        ball.bounce_horizontal()
        assert ball.vx == -vx_before

    def test_ball_speed_increment_after_hit(self):
        ball = Ball(40, 12)
        speed_before = ball.speed
        ball.bounce_horizontal()
        assert ball.speed == speed_before + SPEED_INCREMENT

    def test_ball_speed_capped_at_max(self):
        ball = Ball(40, 12)
        ball.speed = MAX_SPEED
        ball.bounce_horizontal()
        assert ball.speed == MAX_SPEED

    def test_ball_reset_restores_initial_speed(self):
        ball = Ball(40, 12)
        ball.speed = 3.0
        ball.reset(50, 10)
        assert ball.x == 50
        assert ball.y == 10
        assert ball.speed == INITIAL_SPEED

    def test_ball_get_int_position(self):
        ball = Ball(40.3, 12.7)
        ix, iy = ball.get_int_position()
        assert ix == 40
        assert iy == 13

    def test_ball_random_direction_is_valid(self):
        """Ball direction should have vx magnitude >= cos(45°) ≈ 0.707."""
        for _ in range(20):
            ball = Ball(40, 12)
            assert abs(ball.vx) >= math.cos(math.pi / 4) - 0.01
            assert abs(ball.vy) <= math.sin(math.pi / 4) + 0.01

    def test_ball_move_multiple_frames(self):
        ball = Ball(40, 12)
        ball.vx = 1.0
        ball.vy = 0.0
        ball.speed = 1.0
        for _ in range(5):
            ball.move()
        assert ball.x == 45.0
        assert ball.y == 12.0


# ═══════════════════════════════════════════════════════════════════════════════
# Paddle Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaddle:
    """Paddle movement and boundary constraints."""

    def test_paddle_initial_position(self):
        p = Paddle(2, 12)
        assert p.x == 2
        assert p.y == 12

    def test_paddle_move_up(self):
        p = Paddle(2, 12)
        p.move_up()
        assert p.y == 11

    def test_paddle_move_down(self):
        p = Paddle(2, 12)
        p.move_down()
        assert p.y == 13

    def test_paddle_boundary_top(self):
        p = Paddle(2, 2)
        p.move_up(10)
        assert p.y == p.min_y

    def test_paddle_boundary_bottom(self):
        p = Paddle(2, GAME_HEIGHT - 2)
        p.move_down(10)
        assert p.y == p.max_y

    def test_paddle_get_top_bottom(self):
        p = Paddle(2, 12, height=5)
        assert p.get_top() == 10
        assert p.get_bottom() == 14

    def test_paddle_get_y_range(self):
        p = Paddle(2, 12, height=5)
        y_range = list(p.get_y_range())
        assert y_range == [10, 11, 12, 13, 14]

    def test_paddle_custom_game_height(self):
        p = Paddle(2, 5, height=3, game_height=20)
        assert p.min_y == 1
        assert p.max_y == 18


# ═══════════════════════════════════════════════════════════════════════════════
# Collision Detection Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCollision:
    """Ball-paddle and ball-wall collision detection."""

    def test_wall_bounce_top(self):
        state = GameState()
        state.ball.x = 40.0
        state.ball.y = 0.0
        state.ball.vy = -1.0
        event = state.check_collision()
        assert event == 'wall_bounce'
        assert state.ball.vy > 0  # Bounced down

    def test_wall_bounce_bottom(self):
        state = GameState()
        state.ball.x = 40.0
        state.ball.y = float(GAME_HEIGHT - 1)
        state.ball.vy = 1.0
        event = state.check_collision()
        assert event == 'wall_bounce'
        assert state.ball.vy < 0  # Bounced up

    def test_paddle_hit_left(self):
        state = GameState()
        state.ball.x = 3.0
        state.ball.y = float(GAME_HEIGHT // 2)
        state.ball.vx = -1.0
        state.paddle1.y = GAME_HEIGHT // 2
        event = state.check_collision()
        assert event == 'paddle_hit'
        assert state.ball.vx > 0  # Bounced right

    def test_paddle_hit_right(self):
        state = GameState()
        state.ball.x = float(GAME_WIDTH - 4)
        state.ball.y = float(GAME_HEIGHT // 2)
        state.ball.vx = 1.0
        state.paddle2.y = GAME_HEIGHT // 2
        event = state.check_collision()
        assert event == 'paddle_hit'
        assert state.ball.vx < 0  # Bounced left

    def test_no_collision_in_middle(self):
        state = GameState()
        state.ball.x = 40.0
        state.ball.y = 12.0
        event = state.check_collision()
        assert event is None

    def test_paddle_hit_at_edge_of_paddle(self):
        """Ball hits the very top or bottom of paddle."""
        state = GameState()
        state.paddle1.y = GAME_HEIGHT // 2
        # Ball at top edge of paddle
        state.ball.x = 3.0
        state.ball.y = float(state.paddle1.get_top())
        state.ball.vx = -1.0
        event = state.check_collision()
        assert event == 'paddle_hit'

    def test_ball_misses_paddle_scores(self):
        """Ball passes left paddle -> player 2 scores."""
        state = GameState()
        state.ball.x = -1.0
        state.ball.y = 2.0  # Outside paddle's vertical range
        state.paddle1.y = GAME_HEIGHT // 2  # Paddle is in center
        event = state.check_collision()
        assert event == 'score_p2'
        assert state.score2 == 1

    def test_ball_passes_right_scores(self):
        """Ball passes right paddle -> player 1 scores."""
        state = GameState()
        state.ball.x = float(GAME_WIDTH + 1)
        state.ball.y = 2.0  # Outside paddle's vertical range
        state.paddle2.y = GAME_HEIGHT // 2
        event = state.check_collision()
        assert event == 'score_p1'
        assert state.score1 == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring & Win Condition Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScoring:
    """Scoring logic and win conditions."""

    def test_score_increments_correctly(self):
        state = GameState()
        state.ball.x = -1.0
        state.ball.y = 2.0  # Outside paddle range
        state.check_collision()
        assert state.score2 == 1
        assert state.score1 == 0

    def test_ball_resets_after_score(self):
        state = GameState()
        # Place ball past left paddle but outside paddle's y range
        state.ball.x = -1.0
        state.ball.y = 1.0  # Outside paddle's vertical range
        state.check_collision()
        # Ball should be reset to center
        assert state.ball.x == GAME_WIDTH // 2
        assert state.ball.y == GAME_HEIGHT // 2
        assert state.ball.speed == INITIAL_SPEED

    def test_win_at_11_points_p1(self):
        state = GameState()
        state.score1 = 10
        state.score2 = 3
        # Place ball past right paddle but outside paddle's y range
        state.ball.x = float(GAME_WIDTH + 1)
        state.ball.y = 1.0  # Outside paddle's vertical range
        state.check_collision()
        assert state.score1 == 11
        assert state.game_over is True
        assert state.winner == 1

    def test_win_at_11_points_p2(self):
        state = GameState()
        state.score1 = 3
        state.score2 = 10
        state.ball.x = -1.0
        state.ball.y = 1.0  # Outside paddle's vertical range
        state.check_collision()
        assert state.score2 == 11
        assert state.game_over is True
        assert state.winner == 2

    def test_no_ball_reset_after_win(self):
        """Ball should NOT reset after a winning score."""
        state = GameState()
        state.score1 = 10
        state.ball.x = float(GAME_WIDTH + 1)
        state.check_collision()
        # Ball position should NOT be reset (game is over)
        assert state.ball.x != GAME_WIDTH // 2

    def test_game_over_blocks_updates(self):
        state = GameState()
        state.game_over = True
        event = state.update()
        assert event is None

    def test_paused_blocks_updates(self):
        state = GameState()
        state.paused = True
        event = state.update()
        assert event is None


# ═══════════════════════════════════════════════════════════════════════════════
# GameState Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGameState:
    """GameState lifecycle, controls, and settings."""

    def test_reset_game(self):
        state = GameState()
        state.score1 = 10
        state.score2 = 8
        state.game_over = True
        state.winner = 1
        state.speed_level = 5
        state.reset_game()
        assert state.score1 == 0
        assert state.score2 == 0
        assert state.game_over is False
        assert state.winner is None
        assert state.speed_level == 1

    def test_toggle_pause(self):
        state = GameState()
        assert state.paused is False
        state.toggle_pause()
        assert state.paused is True
        state.toggle_pause()
        assert state.paused is False

    def test_no_pause_toggle_when_game_over(self):
        state = GameState()
        state.game_over = True
        state.toggle_pause()
        assert state.paused is False

    def test_increase_speed(self):
        state = GameState()
        state.increase_speed()
        assert state.speed_level == 2
        assert state.ball_speed == INITIAL_SPEED + SPEED_INCREMENT

    def test_decrease_speed(self):
        state = GameState()
        state.speed_level = 5
        state.ball_speed = INITIAL_SPEED + 4 * SPEED_INCREMENT
        state.decrease_speed()
        assert state.speed_level == 4

    def test_speed_minimum(self):
        state = GameState()
        state.decrease_speed()
        assert state.speed_level == 1  # Cannot go below 1

    def test_speed_maximum(self):
        state = GameState()
        state.speed_level = 10
        state.increase_speed()
        assert state.speed_level == 10  # Cannot go above 10

    def test_cycle_sound_mode(self):
        state = GameState()
        assert state.sound_mode == 'visual+beep'
        state.cycle_sound_mode()
        assert state.sound_mode == 'off'
        state.cycle_sound_mode()
        assert state.sound_mode == 'visual'
        state.cycle_sound_mode()
        assert state.sound_mode == 'visual+beep'

    def test_trigger_visual_feedback(self):
        state = GameState()
        state.sound_mode = 'visual'
        state.trigger_visual_feedback()
        assert state.beep_text_timer > 0
        assert state.flash_border is True
        assert state.flash_timer > 0

    def test_no_visual_feedback_when_off(self):
        state = GameState()
        state.sound_mode = 'off'
        state.trigger_visual_feedback()
        # When sound is off, no visual feedback should be triggered
        assert state.beep_text_timer == 0
        assert state.flash_border is False

    def test_should_beep(self):
        state = GameState()
        state.sound_mode = 'visual+beep'
        assert state.should_beep() is True
        state.sound_mode = 'visual'
        assert state.should_beep() is False
        state.sound_mode = 'off'
        assert state.should_beep() is False


# ═══════════════════════════════════════════════════════════════════════════════
# AI Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAI:
    """AI paddle tracking logic."""

    def test_ai_moves_toward_ball(self):
        state = GameState()
        state.mode = 'ai'
        state.ball.y = 5.0
        state.paddle2.y = 12
        # Run enough frames for AI to react
        for _ in range(10):
            state.update_ai()
        # Paddle should have moved toward ball
        assert state.paddle2.y < 12

    def test_ai_does_not_move_in_2p_mode(self):
        state = GameState()
        state.mode = '2p'
        state.paddle2.y = 12
        state.update_ai()
        assert state.paddle2.y == 12  # No movement

    def test_ai_delay_prevents_instant_tracking(self):
        state = GameState()
        state.mode = 'ai'
        state.ball.y = 5.0
        state.paddle2.y = 12
        # After 1 frame, AI should not have moved (delay)
        state.update_ai()
        assert state.paddle2.y == 12

    def test_ai_stays_in_bounds(self):
        state = GameState()
        state.mode = 'ai'
        state.ball.y = 0.0
        state.paddle2.y = 12
        for _ in range(50):
            state.update_ai()
        # Paddle should never go out of bounds
        assert state.paddle2.y >= state.paddle2.min_y
        assert state.paddle2.y <= state.paddle2.max_y

    def test_ai_has_random_error(self):
        """AI should not always track perfectly — verify target has error."""
        state = GameState()
        state.mode = 'ai'
        state.ball.y = 10.0
        # Force AI to update
        state.ai_delay_counter = 3
        state.update_ai()
        # Target should be close to ball but may have error
        assert abs(state.ai_target_y - state.ball.y) <= 2.0


# ═══════════════════════════════════════════════════════════════════════════════
# Score Persistence Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScores:
    """Score history save/load and top 10 ranking."""

    def test_make_score_entry(self):
        entry = make_score_entry(winner=1, score1=11, score2=5,
                                 mode='ai', speed_level=3)
        assert entry['winner'] == 1
        assert entry['score1'] == 11
        assert entry['score2'] == 5
        assert entry['mode'] == 'ai'
        assert entry['speed_level'] == 3
        assert 'date' in entry

    def test_save_and_load_scores(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as f:
            tmp_path = f.name

        try:
            entry = make_score_entry(1, 11, 5, 'ai', 3)
            save_scores(entry, path=tmp_path)
            loaded = load_scores(path=tmp_path)
            assert len(loaded) == 1
            assert loaded[0]['winner'] == 1
            assert loaded[0]['score1'] == 11
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_load_scores_nonexistent_file(self):
        scores = load_scores(path='/tmp/nonexistent_scores_12345.json')
        assert scores == []

    def test_load_scores_corrupted_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as f:
            f.write('{invalid json!!!')
            tmp_path = f.name

        try:
            scores = load_scores(path=tmp_path)
            assert scores == []
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_load_scores_empty_list(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as f:
            json.dump([], f)
            tmp_path = f.name

        try:
            scores = load_scores(path=tmp_path)
            assert scores == []
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_get_top10_returns_up_to_10(self):
        entries = []
        for i in range(15):
            entries.append(make_score_entry(1, 11, i, 'ai', 1))
        top10 = get_top10(entries)
        assert len(top10) == 10

    def test_get_top10_sorted_by_winner_score_desc(self):
        entries = [
            make_score_entry(1, 11, 3, 'ai', 1),
            make_score_entry(1, 5, 11, '2p', 2),
            make_score_entry(2, 3, 11, 'ai', 1),
        ]
        top10 = get_top10(entries)
        # Winner scores: entry0=11, entry1=5, entry2=11
        # Sorted desc: 11, 11, 5
        assert top10[0]['score1'] == 11 or top10[0]['score2'] == 11
        assert top10[2]['score1'] == 5

    def test_get_top10_empty_list(self):
        assert get_top10([]) == []

    def test_format_score_entry_zh(self):
        entry = make_score_entry(1, 11, 5, 'ai', 3)
        formatted = format_score_entry(entry, language='zh')
        assert '单人AI' in formatted
        assert '11:5' in formatted
        assert 'Lv.3' in formatted

    def test_format_score_entry_en(self):
        entry = make_score_entry(2, 5, 11, '2p', 2)
        formatted = format_score_entry(entry, language='en')
        assert '2-Player' in formatted
        assert '5:11' in formatted
        assert 'Lv.2' in formatted

    def test_save_multiple_scores(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as f:
            tmp_path = f.name

        try:
            for i in range(3):
                entry = make_score_entry(1, 11, i, 'ai', 1)
                save_scores(entry, path=tmp_path)
            loaded = load_scores(path=tmp_path)
            assert len(loaded) == 3
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases: corners, boundaries, rapid state changes."""

    def test_ball_at_top_left_corner(self):
        """Ball at top-left corner should bounce correctly."""
        state = GameState()
        state.ball.x = 0.0
        state.ball.y = 0.0
        state.ball.vx = -1.0
        state.ball.vy = -1.0
        event = state.check_collision()
        # Should be wall_bounce (top wall)
        assert event == 'wall_bounce'

    def test_ball_passes_right_edge_scores(self):
        """Ball past right edge (not at corner) should score."""
        state = GameState()
        state.ball.x = float(GAME_WIDTH + 1)
        state.ball.y = 2.0  # Outside paddle's vertical range
        state.ball.vx = 1.0
        state.ball.vy = 0.0
        event = state.check_collision()
        assert event == 'score_p1'

    def test_ball_at_top_right_corner(self):
        """Ball at top-right corner — wall bounce takes priority."""
        state = GameState()
        state.ball.x = float(GAME_WIDTH)
        state.ball.y = 0.0
        state.ball.vx = 1.0
        state.ball.vy = -1.0
        event = state.check_collision()
        # y <= 0 triggers wall_bounce before x >= width check
        assert event == 'wall_bounce'

    def test_paddle_at_screen_edge_top(self):
        """Paddle at very top of screen should not go out of bounds."""
        p = Paddle(2, 0, height=5, game_height=GAME_HEIGHT)
        p.move_up(10)
        assert p.y >= p.min_y

    def test_paddle_at_screen_edge_bottom(self):
        """Paddle at very bottom of screen should not go out of bounds."""
        p = Paddle(2, GAME_HEIGHT - 1, height=5, game_height=GAME_HEIGHT)
        p.move_down(10)
        assert p.y <= p.max_y

    def test_rapid_pause_unpause(self):
        """Multiple rapid pauses/unpauses should work correctly."""
        state = GameState()
        for _ in range(10):
            state.toggle_pause()
        # Even number of toggles = unpaused
        assert state.paused is False

    def test_rapid_speed_changes(self):
        """Rapid speed changes should stay within bounds."""
        state = GameState()
        for _ in range(20):
            state.increase_speed()
        assert state.speed_level == 10
        for _ in range(20):
            state.decrease_speed()
        assert state.speed_level == 1

    def test_language_toggle(self):
        """Language should toggle between zh and en."""
        state = GameState()
        assert state.language == 'zh'
        state.language = 'en'
        assert state.language == 'en'
        state.language = 'zh'
        assert state.language == 'zh'

    def test_reset_after_game_over(self):
        """Reset should clear game over state."""
        state = GameState()
        state.game_over = True
        state.winner = 1
        state.score1 = 11
        state.score2 = 5
        state.reset_game()
        assert state.game_over is False
        assert state.winner is None
        assert state.score1 == 0
        assert state.score2 == 0

    def test_mode_preserved_after_reset(self):
        """Game mode should be preserved after reset."""
        state = GameState()
        state.mode = '2p'
        state.reset_game()
        assert state.mode == '2p'

    def test_language_preserved_after_reset(self):
        """Language should be preserved after reset."""
        state = GameState()
        state.language = 'en'
        state.reset_game()
        assert state.language == 'en'

    def test_sound_mode_preserved_after_reset(self):
        """Sound mode should be preserved after reset."""
        state = GameState()
        state.sound_mode = 'visual'
        state.reset_game()
        assert state.sound_mode == 'visual'

    def test_update_decays_timers(self):
        """Visual feedback timers should decay each frame."""
        state = GameState()
        state.trigger_visual_feedback()
        assert state.beep_text_timer == 5
        state.update()  # Should decay
        assert state.beep_text_timer == 4

    def test_ball_speed_applied_to_ball(self):
        """Changing speed level should update ball speed."""
        state = GameState()
        state.increase_speed()
        assert state.ball.speed == state.ball_speed
