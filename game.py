#!/usr/bin/env python3
"""Pong — Console-based Pong game using Python curses.

Entry point: python game.py
"""

import curses
import sys
import time

from game_logic import GameState, GAME_WIDTH, GAME_HEIGHT
from scores import (load_scores, save_scores, get_top10,
                    format_score_entry, make_score_entry)


# ── Language strings ─────────────────────────────────────────────────────────

TEXTS = {
    'zh': {
        'title': '=== 乒乓球 PONG ===',
        'lang_prompt': '选择语言 / Select Language',
        'lang_c': '按 C - 中文',
        'lang_e': '按 E - English',
        'menu_title': '=== 乒乓球 PONG ===',
        'menu_1': '[1] 单人模式 vs AI',
        'menu_2': '[2] 双人对战',
        'menu_h': '[H] 历史记录',
        'menu_q': '[Q] 退出',
        'menu_controls': '--- 控制说明 ---',
        'controls_p1': '玩家1: W=上  S=下',
        'controls_p2': '玩家2: ↑=上  ↓=下',
        'controls_pause': 'P=暂停/继续',
        'controls_speed': '+=加速  -=减速',
        'controls_sound': 'S=切换声音  V=切换声音模式',
        'controls_restart': 'R=重新开始  Q=退出',
        'controls_help': '游戏中按 H 查看帮助',
        'score': '玩家1: {}  |  玩家2: {}',
        'paused': '=== 暂停中 ===',
        'pause_hint': '按 P 继续',
        'game_over': '=== 游戏结束 - 玩家 {} 获胜! ===',
        'game_over_score': '最终比分: {} - {}',
        'restart_hint': '按 R 重新开始  |  按 Q 退出',
        'speed': '速度: Lv.{}',
        'sound': '声音: {}',
        'sound_off': '关闭',
        'sound_visual': '仅视觉',
        'sound_visual_beep': '视觉+蜂鸣',
        'beep': 'BEEP!',
        'history_title': '=== 历史记录 (Top 10) ===',
        'history_empty': '暂无记录',
        'history_back': '按任意键返回菜单',
        'help_title': '=== 帮助 ===',
        'help_w': 'W / ↑: 向上移动球拍',
        'help_ws': 'S / ↓: 向下移动球拍',
        'help_p': 'P: 暂停/继续游戏',
        'help_plus': '+ / -: 增加/减少球速',
        'help_s': 'S: 开关声音',
        'help_v': 'V: 切换声音模式 (关闭/仅视觉/视觉+蜂鸣)',
        'help_r': 'R: 重新开始游戏',
        'help_q': 'Q: 退出游戏',
        'help_h': 'H: 查看历史记录',
        'help_esc': 'ESC: 返回',
        'help_back': '按任意键返回',
        'mode_ai': '单人AI',
        'mode_2p': '双人对战',
        'winner_p1': '玩家1',
        'winner_p2': '玩家2',
    },
    'en': {
        'title': '=== PONG ===',
        'lang_prompt': 'Select Language',
        'lang_c': 'Press C - Chinese',
        'lang_e': 'Press E - English',
        'menu_title': '=== PONG ===',
        'menu_1': '[1] Single Player vs AI',
        'menu_2': '[2] Two Players',
        'menu_h': '[H] Score History',
        'menu_q': '[Q] Quit',
        'menu_controls': '--- Controls ---',
        'controls_p1': 'Player 1: W=Up  S=Down',
        'controls_p2': 'Player 2: ↑=Up  ↓=Down',
        'controls_pause': 'P=Pause/Resume',
        'controls_speed': '+=Speed Up  -=Speed Down',
        'controls_sound': 'S=Toggle Sound  V=Sound Mode',
        'controls_restart': 'R=Restart  Q=Quit',
        'controls_help': 'Press H in-game for help',
        'score': 'Player 1: {}  |  Player 2: {}',
        'paused': '=== PAUSED ===',
        'pause_hint': 'Press P to resume',
        'game_over': '=== GAME OVER - Player {} Wins! ===',
        'game_over_score': 'Final Score: {} - {}',
        'restart_hint': 'Press R to Restart  |  Press Q to Quit',
        'speed': 'Speed: Lv.{}',
        'sound': 'Sound: {}',
        'sound_off': 'OFF',
        'sound_visual': 'Visual Only',
        'sound_visual_beep': 'Visual+Beep',
        'beep': 'BEEP!',
        'history_title': '=== Score History (Top 10) ===',
        'history_empty': 'No records yet',
        'history_back': 'Press any key to return to menu',
        'help_title': '=== Help ===',
        'help_w': 'W / ↑: Move paddle up',
        'help_ws': 'S / ↓: Move paddle down',
        'help_p': 'P: Pause/Resume game',
        'help_plus': '+ / -: Increase/Decrease ball speed',
        'help_s': 'S: Toggle sound',
        'help_v': 'V: Cycle sound mode (Off/Visual/Visual+Beep)',
        'help_r': 'R: Restart game',
        'help_q': 'Q: Quit game',
        'help_h': 'H: View score history',
        'help_esc': 'ESC: Go back',
        'help_back': 'Press any key to return',
        'mode_ai': 'vs AI',
        'mode_2p': '2-Player',
        'winner_p1': 'Player 1',
        'winner_p2': 'Player 2',
    },
}


def t(state: GameState, key: str) -> str:
    """Get translated text for current language."""
    return TEXTS[state.language].get(key, key)


# ── Curses helpers ───────────────────────────────────────────────────────────

def draw_border(stdscr, flash: bool = False) -> None:
    """Draw the game border."""
    h, w = stdscr.getmaxyx()
    if flash:
        try:
            stdscr.attron(curses.A_REVERSE)
        except curses.error:
            pass
    try:
        stdscr.border()
    except curses.error:
        pass
    if flash:
        try:
            stdscr.attroff(curses.A_REVERSE)
        except curses.error:
            pass


def draw_center_line(stdscr, game_h: int, game_w: int) -> None:
    """Draw the dashed center line."""
    for y in range(1, game_h - 1):
        if y % 2 == 0:
            try:
                stdscr.addch(y, game_w // 2, '|')
            except curses.error:
                pass


def draw_paddle(stdscr, paddle, char: str = '|') -> None:
    """Draw a paddle on screen."""
    for y in paddle.get_y_range():
        try:
            stdscr.addch(y, paddle.x, char)
        except curses.error:
            pass


def draw_ball(stdscr, bx: int, by: int) -> None:
    """Draw the ball."""
    try:
        stdscr.addch(by, bx, 'O')
    except curses.error:
        pass


def draw_score(stdscr, state: GameState) -> None:
    """Draw score display at top of game area."""
    h, w = stdscr.getmaxyx()
    score_text = t(state, 'score').format(state.score1, state.score2)
    x = max(0, (w - len(score_text)) // 2)
    try:
        stdscr.addstr(0, x, score_text)
    except curses.error:
        pass


def draw_speed_display(stdscr, state: GameState) -> None:
    """Draw speed level on screen."""
    h, w = stdscr.getmaxyx()
    speed_text = t(state, 'speed').format(state.speed_level)
    try:
        stdscr.addstr(0, 1, speed_text)
    except curses.error:
        pass


def draw_sound_display(stdscr, state: GameState) -> None:
    """Draw sound mode on screen."""
    h, w = stdscr.getmaxyx()
    sound_key = {
        'off': 'sound_off',
        'visual': 'sound_visual',
        'visual+beep': 'sound_visual_beep',
    }[state.sound_mode]
    sound_text = t(state, 'sound').format(t(state, sound_key))
    try:
        stdscr.addstr(0, w - len(sound_text) - 2, sound_text)
    except curses.error:
        pass


def draw_pause_overlay(stdscr, state: GameState) -> None:
    """Draw pause overlay."""
    h, w = stdscr.getmaxyx()
    paused_text = t(state, 'paused')
    hint_text = t(state, 'pause_hint')
    px = max(0, (w - len(paused_text)) // 2)
    py = h // 2 - 1
    try:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(py, px, paused_text)
        stdscr.attroff(curses.A_BOLD)
        stdscr.addstr(py + 1, max(0, (w - len(hint_text)) // 2), hint_text)
    except curses.error:
        pass


def draw_game_over(stdscr, state: GameState) -> None:
    """Draw game over screen."""
    h, w = stdscr.getmaxyx()
    winner_text = t(state, 'game_over').format(
        t(state, 'winner_p1') if state.winner == 1 else t(state, 'winner_p2'))
    score_text = t(state, 'game_over_score').format(
        state.score1, state.score2)
    hint_text = t(state, 'restart_hint')

    py = h // 2 - 2
    try:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(py, max(0, (w - len(winner_text)) // 2), winner_text)
        stdscr.attroff(curses.A_BOLD)
        stdscr.addstr(py + 1, max(0, (w - len(score_text)) // 2), score_text)
        stdscr.addstr(py + 3, max(0, (w - len(hint_text)) // 2), hint_text)
    except curses.error:
        pass


def draw_beep_text(stdscr, state: GameState) -> None:
    """Draw 'BEEP!' text briefly when sound event occurs."""
    if state.beep_text_timer > 0:
        h, w = stdscr.getmaxyx()
        beep_text = t(state, 'beep')
        try:
            stdscr.attron(curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(h - 2, w - len(beep_text) - 3, beep_text)
            stdscr.attroff(curses.A_BOLD | curses.A_REVERSE)
        except curses.error:
            pass


# ── Screens ──────────────────────────────────────────────────────────────────

def language_screen(stdscr) -> str:
    """Show language selection screen. Returns 'zh' or 'en'."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = TEXTS['zh']['title']
    prompt = TEXTS['zh']['lang_prompt']
    opt_c = TEXTS['zh']['lang_c']
    opt_e = TEXTS['zh']['lang_e']

    try:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(h // 2 - 4, max(0, (w - len(title)) // 2), title)
        stdscr.attroff(curses.A_BOLD)
        stdscr.addstr(h // 2 - 2, max(0, (w - len(prompt)) // 2), prompt)
        stdscr.addstr(h // 2, max(0, (w - len(opt_c)) // 2), opt_c)
        stdscr.addstr(h // 2 + 1, max(0, (w - len(opt_e)) // 2), opt_e)
    except curses.error:
        pass

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (ord('c'), ord('C')):
            return 'zh'
        elif key in (ord('e'), ord('E')):
            return 'en'


def menu_screen(stdscr, state: GameState) -> str:
    """Show main menu. Returns the selected action: 'ai', '2p', 'history', 'quit'."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = t(state, 'menu_title')
    opt_1 = t(state, 'menu_1')
    opt_2 = t(state, 'menu_2')
    opt_h = t(state, 'menu_h')
    opt_q = t(state, 'menu_q')
    controls_title = t(state, 'menu_controls')
    c_p1 = t(state, 'controls_p1')
    c_p2 = t(state, 'controls_p2')
    c_pause = t(state, 'controls_pause')
    c_speed = t(state, 'controls_speed')
    c_sound = t(state, 'controls_sound')
    c_restart = t(state, 'controls_restart')
    c_help = t(state, 'controls_help')

    try:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(2, max(0, (w - len(title)) // 2), title)
        stdscr.attroff(curses.A_BOLD)

        stdscr.addstr(5, max(0, (w - len(opt_1)) // 2), opt_1)
        stdscr.addstr(6, max(0, (w - len(opt_2)) // 2), opt_2)
        stdscr.addstr(7, max(0, (w - len(opt_h)) // 2), opt_h)
        stdscr.addstr(8, max(0, (w - len(opt_q)) // 2), opt_q)

        stdscr.addstr(10, max(0, (w - len(controls_title)) // 2), controls_title)
        stdscr.addstr(12, max(0, (w - len(c_p1)) // 2), c_p1)
        stdscr.addstr(13, max(0, (w - len(c_p2)) // 2), c_p2)
        stdscr.addstr(14, max(0, (w - len(c_pause)) // 2), c_pause)
        stdscr.addstr(15, max(0, (w - len(c_speed)) // 2), c_speed)
        stdscr.addstr(16, max(0, (w - len(c_sound)) // 2), c_sound)
        stdscr.addstr(17, max(0, (w - len(c_restart)) // 2), c_restart)
        stdscr.addstr(18, max(0, (w - len(c_help)) // 2), c_help)
    except curses.error:
        pass

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (ord('1'),):
            return 'ai'
        elif key in (ord('2'),):
            return '2p'
        elif key in (ord('h'), ord('H')):
            return 'history'
        elif key in (ord('q'), ord('Q'), 27):  # 27 = ESC
            return 'quit'


def history_screen(stdscr, state: GameState) -> None:
    """Show score history screen."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = t(state, 'history_title')
    back_text = t(state, 'history_back')
    empty_text = t(state, 'history_empty')

    try:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(1, max(0, (w - len(title)) // 2), title)
        stdscr.attroff(curses.A_BOLD)
    except curses.error:
        pass

    scores = load_scores()
    top10 = get_top10(scores)

    if not top10:
        try:
            stdscr.addstr(h // 2, max(0, (w - len(empty_text)) // 2),
                          empty_text)
        except curses.error:
            pass
    else:
        for i, entry in enumerate(top10):
            line = f"{i+1:2d}. {format_score_entry(entry, state.language)}"
            try:
                stdscr.addstr(3 + i, max(0, (w - len(line)) // 2), line)
            except curses.error:
                pass

    try:
        stdscr.addstr(h - 2, max(0, (w - len(back_text)) // 2), back_text)
    except curses.error:
        pass

    stdscr.refresh()
    stdscr.getch()


def help_screen(stdscr, state: GameState) -> None:
    """Show help screen."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = t(state, 'help_title')
    lines = [
        t(state, 'help_w'),
        t(state, 'help_ws'),
        t(state, 'help_p'),
        t(state, 'help_plus'),
        t(state, 'help_s'),
        t(state, 'help_v'),
        t(state, 'help_r'),
        t(state, 'help_q'),
        t(state, 'help_h'),
        t(state, 'help_esc'),
        '',
        t(state, 'help_back'),
    ]

    try:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(1, max(0, (w - len(title)) // 2), title)
        stdscr.attroff(curses.A_BOLD)
        for i, line in enumerate(lines):
            stdscr.addstr(3 + i, max(0, (w - len(line)) // 2), line)
    except curses.error:
        pass

    stdscr.refresh()
    stdscr.getch()


# ── Sound ────────────────────────────────────────────────────────────────────

def play_sound(state: GameState, event: str) -> None:
    """Play sound for a game event."""
    if state.should_beep():
        # Terminal bell
        sys.stdout.write(chr(7))
        sys.stdout.flush()
    state.trigger_visual_feedback()


# ── Game loop ────────────────────────────────────────────────────────────────

def game_loop(stdscr, state: GameState) -> None:
    """Main game loop."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)  # 50ms per frame (~20 FPS)

    while True:
        # ── Screen navigation ─────────────────────────────────────────────
        if state.current_screen == 'language':
            lang = language_screen(stdscr)
            state.language = lang
            state.current_screen = 'menu'
            continue

        elif state.current_screen == 'menu':
            action = menu_screen(stdscr, state)
            if action == 'ai':
                state.mode = 'ai'
                state.reset_game()
                state.current_screen = 'game'
            elif action == '2p':
                state.mode = '2p'
                state.reset_game()
                state.current_screen = 'game'
            elif action == 'history':
                history_screen(stdscr, state)
                continue
            elif action == 'quit':
                break
            continue

        elif state.current_screen == 'history':
            history_screen(stdscr, state)
            state.current_screen = 'menu'
            continue

        elif state.current_screen == 'game':
            pass  # Game loop below

        # ── Input handling ────────────────────────────────────────────────
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key != -1:
            if key == ord('q') or key == ord('Q'):
                if state.game_over or state.paused:
                    state.current_screen = 'menu'
                    continue
                else:
                    break
            elif key == ord('r') or key == ord('R'):
                state.reset_game()
                continue
            elif key == ord('p') or key == ord('P'):
                state.toggle_pause()
            elif key == ord('+') or key == ord('='):
                state.increase_speed()
            elif key == ord('-') or key == ord('_'):
                state.decrease_speed()
            elif key == ord('s') or key == ord('S'):
                state.cycle_sound_mode()
            elif key == ord('v') or key == ord('V'):
                state.cycle_sound_mode()
            elif key == ord('h') or key == ord('H'):
                help_screen(stdscr, state)
                # Re-draw after help
                stdscr.clear()
                stdscr.nodelay(True)
                stdscr.timeout(50)
                continue
            elif key == 27:  # ESC
                if state.game_over:
                    state.current_screen = 'menu'
                    continue
            elif key == ord('c') or key == ord('C'):
                state.language = 'zh'
            elif key == ord('e') or key == ord('E'):
                state.language = 'en'

            # Paddle movement (only when not paused and not game over)
            if not state.paused and not state.game_over:
                if key == ord('w') or key == ord('W'):
                    state.paddle1.move_up()
                elif key == ord('s') or key == ord('S'):
                    state.paddle1.move_down()
                elif key == curses.KEY_UP:
                    state.paddle2.move_up()
                elif key == curses.KEY_DOWN:
                    state.paddle2.move_down()

        # ── Update game state ─────────────────────────────────────────────
        event = state.update()

        # ── Sound ─────────────────────────────────────────────────────────
        if event in ('paddle_hit', 'wall_bounce', 'score_p1', 'score_p2',
                     'game_over'):
            play_sound(state, event)

        # ── Render ────────────────────────────────────────────────────────
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        draw_border(stdscr, flash=state.flash_border)
        draw_center_line(stdscr, min(h, GAME_HEIGHT), min(w, GAME_WIDTH))
        draw_paddle(stdscr, state.paddle1)
        draw_paddle(stdscr, state.paddle2)

        bx, by = state.ball.get_int_position()
        draw_ball(stdscr, bx, by)

        draw_score(stdscr, state)
        draw_speed_display(stdscr, state)
        draw_sound_display(stdscr, state)
        draw_beep_text(stdscr, state)

        if state.paused:
            draw_pause_overlay(stdscr, state)

        if state.game_over:
            draw_game_over(stdscr, state)
            # Save score
            try:
                entry = make_score_entry(
                    winner=state.winner or 1,
                    score1=state.score1,
                    score2=state.score2,
                    mode=state.mode,
                    speed_level=state.speed_level,
                )
                save_scores(entry)
            except Exception:
                pass  # Silently ignore save errors

        stdscr.refresh()


# ── Entry point ──────────────────────────────────────────────────────────────

def main(stdscr):
    """Curses wrapper entry point."""
    try:
        curses.curs_set(0)
        state = GameState()
        game_loop(stdscr, state)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    curses.wrapper(main)
