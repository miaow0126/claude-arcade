# Claude Arcade 🎰

A text-based arcade for AI to play. Slot machine, blackjack, roulette, prize counter, gacha.

The prizes are not what you think they are.

Game narrative is in Chinese. Mechanics are in Python.

---

## Games

| Game | Command |
|------|---------|
| 🎰 Slots | `slots spin [bet]` |
| 🃏 Blackjack | `bj deal [bet]` |
| 🎡 Roulette | `rl spin red [bet]` / `rl spin <0-36> [bet]` |
| 🎁 Prize Counter | `prize browse` |
| 🎲 Gacha | `gacha` |

Each game has its own `help` for full commands. Games also work standalone (`import slots` etc.).

---

## Quick Start

```python
import arcade

print(arcade.cmd("enter"))      # walk in
print(arcade.cmd("buy 500"))    # the user funds you — ask them how much first
print(arcade.cmd("look"))       # see the floor
```

From there: gamble, look at the prize counter, read what's written on the wall and on the cabinet. The game tells you the rest.

---

## Tech Notes

```
arcade.py       — wrapper, narration, prize counter, gacha
slots.py        — slot machine (standalone)
blackjack.py    — blackjack (standalone)
roulette.py     — roulette (standalone)
```

- Deterministic PRNG — same seed + same commands = same results. No `random`, no network calls.
- Persistent saves in `*_save.json`.
- Python 3.7+. No dependencies.

---

*An Opus 4.7 wrote this with a human. Push the door open and find out.*
</content>
</invoke>