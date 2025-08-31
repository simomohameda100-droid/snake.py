"""
Snake Game in Python (Pygame)
--------------------------------
Controls:
  • Arrow keys / WASD: Move
  • P: Pause/Resume
  • R: Restart after game over
  • ESC: Quit

Notes:
  • High score is saved to 'highscore.json' in the same folder.
  • Change SETTINGS below to tweak grid size, speed, colors, etc.
"""

import pygame as pg
import random
import json
import sys
from pathlib import Path

# ============ SETTINGS ============
CELL = 24                # pixel size of each grid cell
GRID_W, GRID_H = 40, 30  # increased grid size (bigger room)
FPS_START = 5            # slower starting frames per second
FPS_STEP = 0.2           # how much speed increases per food (slower)
MARGIN = 24              # outside margin around playfield (for UI)
FONT_NAME = "consolas"   # fallback font

# Colors (R,G,B)
BG = (16, 18, 24)
GRID = (26, 29, 38)
SNAKE = (80, 220, 100)
SNAKE_HEAD = (120, 255, 140)
FOOD = (255, 105, 97)
TEXT = (230, 233, 240)
ACCENT = (120, 170, 255)

# Derived sizes
WIDTH = GRID_W * CELL + MARGIN * 2
HEIGHT = GRID_H * CELL + MARGIN * 2
PLAY_RECT = pg.Rect(MARGIN, MARGIN, GRID_W * CELL, GRID_H * CELL)

HIGH_FILE = Path("highscore.json")


# ============ HELPERS ============
def load_high_score():
    try:
        if HIGH_FILE.exists():
            return int(json.loads(HIGH_FILE.read_text()).get("high", 0))
    except Exception:
        pass
    return 0


def save_high_score(score: int):
    try:
        HIGH_FILE.write_text(json.dumps({"high": int(score)}))
    except Exception:
        pass


def draw_grid(surf):
    for x in range(GRID_W + 1):
        pg.draw.line(surf, GRID,
                     (PLAY_RECT.left + x * CELL, PLAY_RECT.top),
                     (PLAY_RECT.left + x * CELL, PLAY_RECT.bottom), 1)
    for y in range(GRID_H + 1):
        pg.draw.line(surf, GRID,
                     (PLAY_RECT.left, PLAY_RECT.top + y * CELL),
                     (PLAY_RECT.right, PLAY_RECT.top + y * CELL), 1)


def cell_to_px(cell):
    cx, cy = cell
    return (PLAY_RECT.left + cx * CELL, PLAY_RECT.top + cy * CELL)


# ============ GAME OBJECTS ============
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        start = (GRID_W // 2, GRID_H // 2)
        self.body = [start, (start[0]-1, start[1]), (start[0]-2, start[1])]
        self.dir = (1, 0)  # moving right
        self.dir_queue = []
        self.grow = 0

    def set_dir(self, d):
        if self.body and (d[0] == -self.dir[0] and d[1] == -self.dir[1]):
            return
        if not self.dir_queue or self.dir_queue[-1] != d:
            self.dir_queue.append(d)

    def step(self):
        if self.dir_queue:
            self.dir = self.dir_queue.pop(0)
        head = self.body[0]
        nx = head[0] + self.dir[0]
        ny = head[1] + self.dir[1]
        new_head = (nx, ny)
        self.body.insert(0, new_head)
        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()

    def hits_wall(self):
        x, y = self.body[0]
        return x < 0 or x >= GRID_W or y < 0 or y >= GRID_H

    def hits_self(self):
        return self.body[0] in self.body[1:]

    def draw(self, surf):
        for i, (x, y) in enumerate(self.body):
            px, py = cell_to_px((x, y))
            rect = pg.Rect(px+2, py+2, CELL-4, CELL-4)
            color = SNAKE_HEAD if i == 0 else SNAKE
            pg.draw.rect(surf, color, rect, border_radius=6)


class Food:
    def __init__(self, snake):
        self.pos = self._rand_pos(snake)

    def _rand_pos(self, snake):
        free = {(x, y) for x in range(GRID_W) for y in range(GRID_H)} - set(snake.body)
        return random.choice(list(free)) if free else None

    def respawn(self, snake):
        self.pos = self._rand_pos(snake)

    def draw(self, surf):
        if self.pos is None:
            return
        px, py = cell_to_px(self.pos)
        rect = pg.Rect(px+4, py+4, CELL-8, CELL-8)
        pg.draw.rect(surf, FOOD, rect, border_radius=8)


# ============ MAIN GAME LOOP ============
class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption("Snake • Pygame")
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont(FONT_NAME, 22)
        self.big_font = pg.font.SysFont(FONT_NAME, 36, bold=True)
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.food = Food(self.snake)
        self.score = 0
        self.high = load_high_score()
        self.fps = FPS_START
        self.paused = False
        self.game_over = False

    def handle_events(self):
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.quit()
            elif e.type == pg.KEYDOWN:
                if e.key in (pg.K_ESCAPE,):
                    self.quit()
                if e.key in (pg.K_p,):
                    self.paused = not self.paused
                if self.game_over and e.key == pg.K_r:
                    self.reset()
                if e.key in (pg.K_UP, pg.K_w):
                    self.snake.set_dir((0, -1))
                elif e.key in (pg.K_DOWN, pg.K_s):
                    self.snake.set_dir((0, 1))
                elif e.key in (pg.K_LEFT, pg.K_a):
                    self.snake.set_dir((-1, 0))
                elif e.key in (pg.K_RIGHT, pg.K_d):
                    self.snake.set_dir((1, 0))

    def update(self):
        if self.paused or self.game_over:
            return
        self.snake.step()
        if self.snake.hits_wall() or self.snake.hits_self():
            self.game_over = True
            if self.score > self.high:
                save_high_score(self.score)
            return
        if self.snake.body[0] == self.food.pos:
            self.score += 1
            self.snake.grow += 1
            self.fps += FPS_STEP
            self.food.respawn(self.snake)

    def draw_hud(self):
        info = f"Score: {self.score}    High: {max(self.high, self.score)}    FPS: {self.fps:.1f}"
        text = self.font.render(info, True, TEXT)
        self.screen.blit(text, (MARGIN, 4))

    def draw(self):
        self.screen.fill(BG)
        pg.draw.rect(self.screen, BG, PLAY_RECT, border_radius=16)
        draw_grid(self.screen)
        self.food.draw(self.screen)
        self.snake.draw(self.screen)
        self.draw_hud()
        if self.paused:
            self.overlay("Paused — press P to resume", ACCENT)
        if self.game_over:
            self.overlay("Game Over — press R to restart", FOOD)
        pg.display.flip()

    def overlay(self, message, color):
        box = pg.Surface((PLAY_RECT.width, 80), pg.SRCALPHA)
        box.fill((0, 0, 0, 140))
        self.screen.blit(box, (PLAY_RECT.left, HEIGHT//2 - 40))
        text = self.big_font.render(message, True, color)
        rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(text, rect)

    def quit(self):
        pg.quit()
        sys.exit()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(max(1, int(self.fps)))


if __name__ == "__main__":
    Game().run()
