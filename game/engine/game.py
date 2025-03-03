import sys
import time
import os
import curses
import argparse
from typing import List, Dict, Any, Optional

from game.engine.input_handler import InputHandler
from game.engine.renderer import Renderer
from game.entities.player import Player
from game.entities.npc_generator import NPCGenerator
from game.world.dungeon import Dungeon
from game.world.map_generator import MapGenerator


class Game:
    """Main game engine class that manages the game state and loop."""
    
    def __init__(self, use_pregenerated=False, save_characters=True):
        self.running = False
        self.player = None
        self.dungeon = None
        self.current_level = 0
        self.input_handler = InputHandler()
        self.renderer = None
        self.npc_generator = NPCGenerator(
            use_pregenerated=use_pregenerated, 
            save_generated=save_characters
        )
        self.game_log = []
        self.max_log_size = 30
        self.use_pregenerated = use_pregenerated
        self.save_characters = save_characters
        self.viewing_history = False
        self.history_offset = 0
        
    def setup(self, stdscr):
        """Initialize game components."""
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.use_default_colors()
        
        # Initialize color pairs
        curses.init_pair(1, curses.COLOR_WHITE, -1)  # Default
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # Player
        curses.init_pair(3, curses.COLOR_RED, -1)    # Enemy
        curses.init_pair(4, curses.COLOR_YELLOW, -1) # Items
        curses.init_pair(5, curses.COLOR_BLUE, -1)   # NPCs
        
        # Setup renderer with the screen
        self.renderer = Renderer(stdscr)
        
        # Create player
        self.player = Player("Adventurer", x=1, y=1, hp=100, max_hp=100, attack=10)
        
        # Generate first dungeon level
        self._generate_new_level()
        
        self.running = True
        self.add_to_log("Welcome to Roguelike LLM Dungeon!")
        
        # Log character generation mode
        if self.use_pregenerated:
            self.add_to_log("Using pre-generated characters.")
        else:
            self.add_to_log("Generating new characters with Claude 3.7 Sonnet.")
            if self.save_characters:
                self.add_to_log("Characters will be saved for future use.")
        
        self.add_to_log("Use arrow keys to move, 't' to talk, 'f' to fight, 'q' to quit.")
    
    def _generate_new_level(self):
        """Generate a new dungeon level with NPCs and enemies."""
        map_gen = MapGenerator(width=80, height=20)
        self.dungeon = map_gen.generate_dungeon(level=self.current_level)
        
        # Place player in a valid position
        valid_pos = self.dungeon.get_random_floor_tile()
        self.player.x, self.player.y = valid_pos
        
        # Generate NPCs and enemies for this level
        self.dungeon.populate_entities(self.npc_generator, level=self.current_level)
    
    def add_to_log(self, message: str):
        """Add a message to the game log."""
        self.game_log.append(message)
        if len(self.game_log) > self.max_log_size:
            self.game_log.pop(0)
    
    def _view_dialogue_history(self, key=None):
        """View and navigate dialogue history."""
        if not self.viewing_history:
            # Enter history view mode
            self.viewing_history = True
            self.history_offset = 0
            self.add_to_log("--- DIALOGUE HISTORY (use UP/DOWN to scroll, ESC to exit) ---")
            return
            
        # Handle navigation in history view
        if key == "KEY_UP" and self.history_offset < len(self.game_log) - 10:
            self.history_offset += 1
        elif key == "KEY_DOWN" and self.history_offset > 0:
            self.history_offset -= 1
        elif key == "ESCAPE":
            # Exit history view
            self.viewing_history = False
            self.history_offset = 0
            self.add_to_log("--- EXITED DIALOGUE HISTORY ---")
            
    def handle_input(self, key):
        """Process user input."""
        if self.viewing_history:
            self._view_dialogue_history(key)
            return
            
        if key == 'q':
            # If characters are being saved, save one last time before quitting
            if self.save_characters:
                self.npc_generator.save_characters()
            self.running = False
            return
            
        # Movement
        if key == 'KEY_UP':
            self._try_move(0, -1)
        elif key == 'KEY_DOWN':
            self._try_move(0, 1)
        elif key == 'KEY_LEFT':
            self._try_move(-1, 0)
        elif key == 'KEY_RIGHT':
            self._try_move(1, 0)
        
        # Interaction
        elif key == 't':  # Talk
            self._interact_with_npc()
        elif key == 'f':  # Fight
            self._attack_enemy()
        elif key == 's':  # Save characters (manual save)
            if self.save_characters:
                self.npc_generator.save_characters()
                self.add_to_log("Characters saved to files.")
            else:
                self.add_to_log("Character saving is not enabled.")
        elif key == 'h':  # View dialogue history
            self._view_dialogue_history()
            
    def _try_move(self, dx, dy):
        """Try to move the player by delta x and y."""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check if the new position is valid
        if self.dungeon.is_walkable(new_x, new_y):
            self.player.x = new_x
            self.player.y = new_y
            
            # Check for level transitions
            if self.dungeon.is_level_exit(new_x, new_y):
                self.current_level += 1
                self.add_to_log(f"Descending to dungeon level {self.current_level + 1}...")
                self._generate_new_level()
    
    def _interact_with_npc(self):
        """Interact with an NPC if one is adjacent to the player."""
        npc = self.dungeon.get_adjacent_npc(self.player.x, self.player.y)
        if npc:
            dialogue = npc.talk()
            
            # Add NPC name as a separate line for clarity
            self.add_to_log(f"{npc.name}:")
            
            # Split long dialogue into multiple log entries
            if len(dialogue) > 70:
                words = dialogue.split()
                current_line = ""
                
                for word in words:
                    if len(current_line) + len(word) + 1 > 70:
                        self.add_to_log(f"  {current_line}")
                        current_line = word
                    else:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                
                if current_line:
                    self.add_to_log(f"  {current_line}")
            else:
                self.add_to_log(f"  {dialogue}")
        else:
            self.add_to_log("There's no one to talk to here.")
    
    def _attack_enemy(self):
        """Attack an enemy if one is adjacent to the player."""
        enemy = self.dungeon.get_adjacent_enemy(self.player.x, self.player.y)
        if enemy:
            damage = self.player.attack
            enemy.hp -= damage
            self.add_to_log(f"You attack {enemy.name} for {damage} damage!")
            
            if enemy.hp <= 0:
                self.add_to_log(f"You defeated {enemy.name}!")
                self.dungeon.remove_entity(enemy)
            else:
                # Enemy counterattack
                player_damage = enemy.attack
                self.player.hp -= player_damage
                self.add_to_log(f"{enemy.name} attacks you for {player_damage} damage!")
                
                if self.player.hp <= 0:
                    self.add_to_log("You have been defeated!")
                    self.running = False
        else:
            self.add_to_log("There's no enemy to attack here.")
            
    def update(self):
        """Update game state."""
        # AI updates for NPCs and enemies
        self.dungeon.update_entities(self.player)
            
    def render(self):
        """Render the current game state."""
        if not self.renderer:
            return
            
        self.renderer.clear()
        
        # Render dungeon
        self.dungeon.render(self.renderer)
        
        # Render entities
        self.dungeon.render_entities(self.renderer)
        
        # Render player
        self.player.render(self.renderer)
        
        # Render UI
        if self.viewing_history:
            # Display history view with offset
            history_view = self.game_log[-min(len(self.game_log), 20+self.history_offset):-self.history_offset] if self.history_offset > 0 else self.game_log[-min(len(self.game_log), 20):]
            self.renderer.draw_ui(
                player=self.player,
                dungeon_level=self.current_level + 1,
                log=history_view
            )
        else:
            # Normal game view
            self.renderer.draw_ui(
                player=self.player,
                dungeon_level=self.current_level + 1,
                log=self.game_log
            )
        
        self.renderer.refresh()
        
    def run(self, stdscr):
        """Main game loop."""
        self.setup(stdscr)
        
        while self.running:
            # Render current state
            self.render()
            
            # Get and handle input
            key = self.input_handler.get_input(stdscr)
            self.handle_input(key)
            
            # Update game state
            self.update()
            
            # Small delay to prevent CPU overuse
            time.sleep(0.05)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Roguelike LLM Dungeon")
    parser.add_argument(
        "--use-pregenerated", 
        action="store_true", 
        help="Use pre-generated characters instead of generating new ones"
    )
    parser.add_argument(
        "--no-save-characters", 
        action="store_true", 
        help="Disable saving generated characters to files"
    )
    return parser.parse_args()


def main():
    """Entry point for the game."""
    args = parse_arguments()
    game = Game(
        use_pregenerated=args.use_pregenerated,
        save_characters=not args.no_save_characters
    )
    curses.wrapper(game.run)


if __name__ == "__main__":
    main() 