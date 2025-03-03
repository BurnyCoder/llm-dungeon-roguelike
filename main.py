#!/usr/bin/env python3
"""
Roguelike Dungeon with LLM-Generated NPCs and Enemies
A roguelike game where NPCs and enemies have personalities and behaviors
generated by Claude 3.7 Sonnet.

Usage:
  python main.py                        # Generate and save new characters with Claude
  python main.py --no-save-characters   # Generate characters without saving them
  python main.py --use-pregenerated     # Use pre-generated characters instead of generating new ones
  
Controls:
  Arrow keys: Move the player character
  t: Talk to adjacent NPCs
  f: Fight adjacent enemies
  s: Save character data (manual save)
  h: View dialogue history (use UP/DOWN to scroll, ESC to exit)
  q: Quit the game
"""

import sys
import os
from game.engine.game import main

if __name__ == "__main__":
    main() 