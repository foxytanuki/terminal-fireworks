# 🎆 Terminal Fireworks

A real-time fireworks & particle physics simulator that runs entirely in your terminal. Pure Python, zero dependencies.

## Features

- **5 explosion styles** — Spherical, Ring, Star, Willow, Chrysanthemum
- **Real-time particle physics** — gravity, drag, velocity, brightness decay
- **Particle trails** — fading sparkle trails behind every particle
- **3 color modes** — Vivid (ANSI), Pastel (256-color), Monochrome
- **Adjustable gravity** — watch particles float or plummet
- **Auto-launch mode** — sit back and enjoy the show
- **60 FPS rendering** — smooth curses-based terminal rendering
- **Live HUD** — FPS counter, particle count, active controls

## Quick Start

```bash
python3 fireworks.py
```

That's it. No `pip install`, no venv, no config. Just run it.

**Requirements:** Python 3.10+ (uses `dataclasses`, `match` on enums, `list[]` generics)

## Controls

| Key | Action |
|-----|--------|
| `SPACE` | Launch a firework manually |
| `1`-`5` | Switch explosion style |
| `+` / `-` | Increase / decrease gravity |
| `c` | Cycle color mode (vivid → pastel → mono) |
| `t` | Toggle particle trails |
| `a` | Toggle auto-launch |
| `q` / `ESC` | Quit |

## Explosion Styles

1. **Spherical** — Classic burst in all directions
2. **Ring** — Evenly spaced particles forming an expanding ring
3. **Star** — Alternating long/short arms creating a star shape
4. **Willow** — Slow, drooping particles with long trails (like a weeping willow)
5. **Chrysanthemum** — Dense dual-color burst with an inner and outer shell

## How It Works

Each firework goes through two phases:

1. **Rocket phase** — A particle launches from the bottom of the screen with upward velocity, leaving a trail. When it reaches its target altitude or loses momentum, it detonates.

2. **Explosion phase** — Dozens of particles spawn at the detonation point with velocities determined by the chosen style. Each particle is subject to:
   - **Gravity** pulling it downward
   - **Drag** slowing it over time
   - **Brightness decay** — characters transition from `#` → `@` → `O` → `o` → `*` → `:` → `.` as they fade
   - **Trail spawning** — stationary dim particles left behind the moving ones

The simulation runs at ~60 FPS with delta-time physics, so it looks smooth regardless of system speed.

## Tips

- **Maximize your terminal** for the best experience — the simulator scales to your terminal size
- **Use a dark background** — the ANSI colors pop best on dark terminals
- **Try Willow style** (`4`) with trails on — it's gorgeous
- **Crank up gravity** (`+` key) for dramatic cascading effects

## License

MIT — do whatever you want with it.
