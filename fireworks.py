#!/usr/bin/env python3
"""
Terminal Fireworks & Particle Physics Simulator
A real-time fireworks show rendered in your terminal with ANSI colors,
gravity physics, procedural explosions, and particle trails.

Controls:
  SPACE  - Launch a firework manually
  1-5    - Change explosion style
  +/-    - Adjust gravity
  c      - Toggle color mode (vivid / pastel / monochrome)
  t      - Toggle particle trails
  a      - Toggle auto-launch mode
  q/ESC  - Quit

No external dependencies — pure Python 3 + curses.
"""

import curses
import math
import random
import time
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Color Palettes ──────────────────────────────────────────────────────────

class ColorMode(Enum):
    VIVID = "vivid"
    PASTEL = "pastel"
    MONO = "monochrome"


VIVID_COLORS = [
    curses.COLOR_RED,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
    curses.COLOR_WHITE,
]

# We'll initialize custom pastel colors if terminal supports it
PASTEL_DEFS = [
    (200, 1000, 400, 400),   # soft red
    (201, 1000, 900, 300),   # peach
    (202, 400, 1000, 400),   # soft green
    (203, 400, 900, 1000),   # sky blue
    (204, 700, 400, 1000),   # lavender
    (205, 1000, 400, 800),   # pink
    (206, 1000, 1000, 600),  # cream
]


# ── Explosion Patterns ─────────────────────────────────────────────────────

class ExplosionStyle(Enum):
    SPHERICAL = "spherical"
    RING = "ring"
    STAR = "star"
    WILLOW = "willow"
    CHRYSANTHEMUM = "chrysanthemum"


STYLES = list(ExplosionStyle)
STYLE_NAMES = {
    ExplosionStyle.SPHERICAL: "Spherical",
    ExplosionStyle.RING: "Ring",
    ExplosionStyle.STAR: "Star",
    ExplosionStyle.WILLOW: "Willow",
    ExplosionStyle.CHRYSANTHEMUM: "Chrysanthemum",
}


# ── Particle Characters (by brightness) ────────────────────────────────────

SPARK_CHARS = [".", ":", "*", "o", "O", "@", "#"]
TRAIL_CHARS = [".", "`", "'", ","]
ROCKET_CHARS = ["|", "!", "¡", "│"]


# ── Data Structures ────────────────────────────────────────────────────────

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float          # seconds remaining
    max_life: float
    color_pair: int
    is_trail: bool = False
    is_rocket: bool = False
    brightness: float = 1.0
    drag: float = 0.98


@dataclass
class Firework:
    """A firework is a rocket that ascends, then explodes into particles."""
    rocket: Optional[Particle]
    particles: list[Particle] = field(default_factory=list)
    style: ExplosionStyle = ExplosionStyle.SPHERICAL
    exploded: bool = False
    target_y: float = 0.0
    color_pair: int = 1


# ── Physics & Simulation ──────────────────────────────────────────────────

class FireworkSim:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.fireworks: list[Firework] = []
        self.gravity = 15.0
        self.show_trails = True
        self.auto_launch = True
        self.color_mode = ColorMode.VIVID
        self.current_style_idx = 0
        self.auto_timer = 0.0
        self.auto_interval = 0.6  # seconds between auto launches
        self.frame_count = 0
        self.start_time = time.monotonic()
        self.running = True

        # Terminal setup
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(16)  # ~60 FPS target
        self.height, self.width = stdscr.getmaxyx()

        self._init_colors()

    def _init_colors(self):
        """Initialize color pairs for the terminal."""
        curses.start_color()
        curses.use_default_colors()

        # Basic vivid color pairs (1-7)
        for i, color in enumerate(VIVID_COLORS):
            curses.init_pair(i + 1, color, -1)

        # Dim color pair for trails
        curses.init_pair(8, curses.COLOR_WHITE, -1)

        # Try to init pastel colors if we have enough colors
        self.has_pastels = False
        if curses.can_change_color() and curses.COLORS >= 256:
            try:
                for color_id, r, g, b in PASTEL_DEFS:
                    curses.init_color(color_id, r, g, b)
                for i, (color_id, _, _, _) in enumerate(PASTEL_DEFS):
                    curses.init_pair(10 + i, color_id, -1)
                self.has_pastels = True
            except curses.error:
                pass

    def _random_color_pair(self) -> int:
        if self.color_mode == ColorMode.MONO:
            return 8
        elif self.color_mode == ColorMode.PASTEL and self.has_pastels:
            return random.randint(10, 10 + len(PASTEL_DEFS) - 1)
        else:
            return random.randint(1, len(VIVID_COLORS))

    def launch(self, style: Optional[ExplosionStyle] = None):
        """Launch a new firework from the bottom of the screen."""
        self.height, self.width = self.stdscr.getmaxyx()

        x = random.uniform(self.width * 0.15, self.width * 0.85)
        target_y = random.uniform(self.height * 0.1, self.height * 0.45)
        color = self._random_color_pair()
        chosen_style = style or random.choice(STYLES)

        rocket = Particle(
            x=x,
            y=float(self.height - 2),
            vx=random.uniform(-1.5, 1.5),
            vy=-(random.uniform(35, 55)),
            life=3.0,
            max_life=3.0,
            color_pair=color,
            is_rocket=True,
            drag=0.99,
        )

        fw = Firework(
            rocket=rocket,
            style=chosen_style,
            target_y=target_y,
            color_pair=color,
        )
        self.fireworks.append(fw)

    def _explode(self, fw: Firework):
        """Generate explosion particles based on the firework's style."""
        if fw.rocket is None:
            return

        cx, cy = fw.rocket.x, fw.rocket.y
        style = fw.style
        color = fw.color_pair
        num_particles = random.randint(40, 90)

        if style == ExplosionStyle.SPHERICAL:
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(8, 30)
                fw.particles.append(Particle(
                    x=cx, y=cy,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(1.0, 2.5),
                    max_life=2.5,
                    color_pair=color,
                    drag=0.96,
                ))

        elif style == ExplosionStyle.RING:
            for i in range(num_particles):
                angle = (2 * math.pi * i) / num_particles
                speed = random.uniform(18, 25)
                fw.particles.append(Particle(
                    x=cx, y=cy,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(1.2, 2.0),
                    max_life=2.0,
                    color_pair=color,
                    drag=0.97,
                ))

        elif style == ExplosionStyle.STAR:
            points = random.choice([5, 6, 8])
            for i in range(num_particles):
                angle = (2 * math.pi * i) / num_particles
                # Create star shape: alternate between long and short arms
                arm = 1.0 if (i % (num_particles // points)) < (num_particles // points // 2) else 0.4
                speed = random.uniform(15, 28) * arm
                fw.particles.append(Particle(
                    x=cx, y=cy,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(1.0, 2.2),
                    max_life=2.2,
                    color_pair=color,
                    drag=0.96,
                ))

        elif style == ExplosionStyle.WILLOW:
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5, 18)
                fw.particles.append(Particle(
                    x=cx, y=cy,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed - 5,  # upward bias
                    life=random.uniform(2.0, 4.0),
                    max_life=4.0,
                    color_pair=color,
                    drag=0.985,  # less drag = longer trails
                ))

        elif style == ExplosionStyle.CHRYSANTHEMUM:
            # Dense burst with secondary sparks
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(10, 35)
                fw.particles.append(Particle(
                    x=cx, y=cy,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(1.5, 3.0),
                    max_life=3.0,
                    color_pair=color,
                    drag=0.975,
                ))
            # Inner burst with different color
            alt_color = self._random_color_pair()
            for _ in range(num_particles // 3):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5, 12)
                fw.particles.append(Particle(
                    x=cx, y=cy,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=random.uniform(2.0, 3.5),
                    max_life=3.5,
                    color_pair=alt_color,
                    drag=0.97,
                ))

        fw.exploded = True
        fw.rocket = None

    def _spawn_trail(self, p: Particle):
        """Spawn a fading trail particle behind a moving particle."""
        if not self.show_trails:
            return None
        return Particle(
            x=p.x + random.uniform(-0.3, 0.3),
            y=p.y + random.uniform(-0.2, 0.2),
            vx=0, vy=0,
            life=random.uniform(0.2, 0.5),
            max_life=0.5,
            color_pair=p.color_pair,
            is_trail=True,
            drag=1.0,
        )

    def update(self, dt: float):
        """Update all firework physics for one frame."""
        self.height, self.width = self.stdscr.getmaxyx()

        # Auto-launch
        if self.auto_launch:
            self.auto_timer += dt
            if self.auto_timer >= self.auto_interval:
                self.auto_timer = 0.0
                count = random.choices([1, 2, 3], weights=[5, 3, 1])[0]
                for _ in range(count):
                    self.launch()

        alive_fireworks = []
        for fw in self.fireworks:
            # Update rocket
            if fw.rocket and not fw.exploded:
                r = fw.rocket
                r.vy += self.gravity * dt * 0.3  # rockets fight gravity
                r.vx *= r.drag
                r.vy *= r.drag
                r.x += r.vx * dt
                r.y += r.vy * dt
                r.life -= dt

                # Explode when reaching target or slowing down
                if r.y <= fw.target_y or r.vy >= -2 or r.life <= 0:
                    self._explode(fw)
                else:
                    # Spawn rocket trail
                    trail = self._spawn_trail(r)
                    if trail:
                        fw.particles.append(trail)

            # Update explosion particles
            alive_particles = []
            new_trails = []
            for p in fw.particles:
                if not p.is_trail:
                    p.vy += self.gravity * dt
                p.vx *= p.drag
                p.vy *= p.drag
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.life -= dt
                p.brightness = max(0, p.life / p.max_life)

                if p.life > 0:
                    alive_particles.append(p)
                    # Spawn trails for active (non-trail) particles
                    if not p.is_trail and random.random() < 0.3:
                        trail = self._spawn_trail(p)
                        if trail:
                            new_trails.append(trail)

            fw.particles = alive_particles + new_trails

            # Keep firework if it still has content
            if fw.rocket or fw.particles:
                alive_fireworks.append(fw)

        self.fireworks = alive_fireworks

    def render(self):
        """Render all particles to the terminal."""
        self.stdscr.erase()
        h, w = self.height, self.width

        # Render ground line
        try:
            ground_char = "═" * (w - 1)
            self.stdscr.addstr(h - 1, 0, ground_char, curses.color_pair(8) | curses.A_DIM)
        except curses.error:
            pass

        # Collect all drawable particles
        for fw in self.fireworks:
            # Draw rocket
            if fw.rocket and not fw.exploded:
                self._draw_particle(fw.rocket, h, w)

            # Draw explosion particles
            for p in fw.particles:
                self._draw_particle(p, h, w)

        # HUD
        self._draw_hud(h, w)

        self.stdscr.refresh()
        self.frame_count += 1

    def _draw_particle(self, p: Particle, h: int, w: int):
        """Draw a single particle on screen."""
        sx, sy = int(round(p.x)), int(round(p.y))

        if sx < 0 or sx >= w - 1 or sy < 0 or sy >= h - 1:
            return

        # Choose character based on type and brightness
        if p.is_trail:
            char = random.choice(TRAIL_CHARS)
            attr = curses.color_pair(p.color_pair) | curses.A_DIM
        elif p.is_rocket:
            char = random.choice(ROCKET_CHARS)
            attr = curses.color_pair(p.color_pair) | curses.A_BOLD
        else:
            idx = min(int(p.brightness * (len(SPARK_CHARS) - 1)), len(SPARK_CHARS) - 1)
            char = SPARK_CHARS[idx]
            if p.brightness > 0.7:
                attr = curses.color_pair(p.color_pair) | curses.A_BOLD
            elif p.brightness > 0.3:
                attr = curses.color_pair(p.color_pair)
            else:
                attr = curses.color_pair(p.color_pair) | curses.A_DIM

        try:
            self.stdscr.addstr(sy, sx, char, attr)
        except curses.error:
            pass

    def _draw_hud(self, h: int, w: int):
        """Draw the heads-up display with stats and controls."""
        elapsed = time.monotonic() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        total_particles = sum(
            len(fw.particles) + (1 if fw.rocket else 0)
            for fw in self.fireworks
        )

        style_name = STYLE_NAMES[STYLES[self.current_style_idx]]
        auto_str = "ON" if self.auto_launch else "OFF"
        trails_str = "ON" if self.show_trails else "OFF"

        info_lines = [
            f" 🎆 Terminal Fireworks  |  FPS: {fps:.0f}  |  Particles: {total_particles}  |  Fireworks: {len(self.fireworks)} ",
            f" Style: {style_name} [1-5]  |  Auto: {auto_str} [a]  |  Trails: {trails_str} [t]  |  Gravity: {self.gravity:.1f} [+/-]  |  Color: {self.color_mode.value} [c]  |  [SPACE] launch  [q] quit ",
        ]

        for i, line in enumerate(info_lines):
            try:
                x = max(0, (w - len(line)) // 2)
                attr = curses.color_pair(8) | curses.A_DIM
                self.stdscr.addstr(i, x, line[:w-1], attr)
            except curses.error:
                pass

    def handle_input(self):
        """Process keyboard input."""
        try:
            key = self.stdscr.getch()
        except curses.error:
            return

        if key == ord('q') or key == 27:  # q or ESC
            self.running = False
        elif key == ord(' '):
            self.launch(STYLES[self.current_style_idx])
        elif key == ord('a'):
            self.auto_launch = not self.auto_launch
        elif key == ord('t'):
            self.show_trails = not self.show_trails
        elif key == ord('c'):
            modes = list(ColorMode)
            idx = (modes.index(self.color_mode) + 1) % len(modes)
            self.color_mode = modes[idx]
        elif key == ord('+') or key == ord('='):
            self.gravity = min(50.0, self.gravity + 1.0)
        elif key == ord('-') or key == ord('_'):
            self.gravity = max(1.0, self.gravity - 1.0)
        elif ord('1') <= key <= ord('5'):
            self.current_style_idx = key - ord('1')

    def run(self):
        """Main simulation loop."""
        last_time = time.monotonic()

        while self.running:
            now = time.monotonic()
            dt = min(now - last_time, 0.05)  # cap dt to avoid physics blowup
            last_time = now

            self.handle_input()
            self.update(dt)
            self.render()


def main(stdscr: curses.window):
    sim = FireworkSim(stdscr)
    sim.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🎆 Thanks for watching the show!\n")
