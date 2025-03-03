import sys
import time
import os
import curses
import argparse
from typing import List, Dict, Any, Optional
from collections import deque

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
        self.max_log_size = 100
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
        
        # Place player in a valid position in the first room
        # This ensures the player starts in a location that has a path to the stairs
        if not hasattr(map_gen, 'rooms') or not map_gen.rooms:
            # Fallback to random position if no rooms were generated
            valid_pos = self.dungeon.get_random_floor_tile()
        else:
            # Place player in the first room
            first_room = map_gen.rooms[0]
            center_x, center_y = first_room.center
            valid_pos = (center_x, center_y)
            
        self.player.x, self.player.y = valid_pos
        
        # Generate NPCs and enemies for this level
        self.dungeon.populate_entities(self.npc_generator, level=self.current_level)
        
        # Verify that a path exists from player to stairs
        # Find stairs
        stairs_pos = None
        for x in range(self.dungeon.width):
            for y in range(self.dungeon.height):
                if self.dungeon.tiles[x][y] == 2:  # Stairs
                    stairs_pos = (x, y)
                    break
            if stairs_pos:
                break
                
        if stairs_pos:
            # Use the path verification from map_generator
            
            # Verify that a path exists using BFS
            has_path = self._verify_path((self.player.x, self.player.y), stairs_pos)
            
            if not has_path:
                # Force create a path if necessary
                self._create_direct_path((self.player.x, self.player.y), stairs_pos)
                self.add_to_log("Emergency path to stairs created!")
            else:
                self.add_to_log(f"Level {self.current_level} generated with valid path to exit.")
    
    def _verify_path(self, start, end):
        """
        Use BFS to verify that a path exists from start to end.
        Returns True if a path exists, False otherwise.
        """
        # Create a visited set
        visited = set()
        queue = deque([start])
        
        # Directions: up, right, down, left
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        
        while queue:
            current = queue.popleft()
            
            if current == end:
                return True
                
            if current in visited:
                continue
                
            visited.add(current)
            
            # Check all adjacent tiles
            for dx, dy in directions:
                next_x, next_y = current[0] + dx, current[1] + dy
                
                # Check if walkable and not visited
                if (self.dungeon.is_walkable(next_x, next_y) and 
                    (next_x, next_y) not in visited):
                    queue.append((next_x, next_y))
        
        # If queue is empty and end not found, no path exists
        return False
        
    def _create_direct_path(self, start, end):
        """Create a direct path from start to end coordinates."""
        x1, y1 = start
        x2, y2 = end
        
        # First carve horizontal tunnel
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.dungeon.tiles[x][y1] = 1  # Floor
        
        # Then carve vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.dungeon.tiles[x2][y] = 1  # Floor
    
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
            # Scroll larger amounts with UP key
            self.history_offset += 5
        elif key == "KEY_DOWN" and self.history_offset > 0:
            # Scroll larger amounts with DOWN key
            self.history_offset = max(0, self.history_offset - 5)
        elif key == "ESCAPE":
            # Exit history view
            self.viewing_history = False
            self.history_offset = 0
            self.add_to_log("--- EXITED DIALOGUE HISTORY ---")
            
    def handle_input(self, key):
        """Handle player input."""
        # Skip if viewing dialogue history
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
        elif key == 't':  # Talk to NPCs or enemies
            self._talk_to_character()
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
    
    def _talk_to_character(self):
        """Interact with an NPC or enemy if one is adjacent to the player."""
        # First check for NPCs
        npc = self.dungeon.get_adjacent_npc(self.player.x, self.player.y)
        if npc:
            self._interact_with_npc(npc)
            return
            
        # Then check for enemies
        enemy = self.dungeon.get_adjacent_enemy(self.player.x, self.player.y)
        if enemy:
            self._interact_with_enemy(enemy)
            return
            
        # No one to talk to
        self.add_to_log("There's no one to talk to here.")
    
    def _interact_with_npc(self, npc=None):
        """Interact with an NPC."""
        # If no NPC is provided, try to get one from the player's position
        if npc is None:
            npc = self.dungeon.get_adjacent_npc(self.player.x, self.player.y)
            if not npc:
                self.add_to_log("There's no NPC to talk to here.")
                return
                
        # Initial greeting if this is the first interaction
        if not hasattr(self, 'current_npc') or self.current_npc != npc:
            self.current_npc = npc
            
            # Generate initial greeting with Claude 3.7 Sonnet
            initial_greeting = npc.talk("*You approach the character*")
            
            # Add NPC name as a separate line for clarity
            self.add_to_log(f"{npc.name}:")
            
            # Split long dialogue into multiple log entries
            self._display_dialogue(initial_greeting)
            
            # Prompt player for response
            self.add_to_log("(Type your response and press Enter, or just press Enter to leave)")
            
            # Enter conversation mode
            self._get_player_input()
        else:
            # Already in conversation with this NPC
            self._get_player_input()
    
    def _interact_with_enemy(self, enemy=None):
        """Interact with an enemy."""
        # If no enemy is provided, try to get one from the player's position
        if enemy is None:
            enemy = self.dungeon.get_adjacent_enemy(self.player.x, self.player.y)
            if not enemy:
                self.add_to_log("There's no enemy to talk to here.")
                return
                
        # Initial greeting if this is the first interaction
        if not hasattr(self, 'current_enemy') or self.current_enemy != enemy:
            self.current_enemy = enemy
            
            # Generate initial greeting with Claude 3.7 Sonnet
            initial_greeting = enemy.talk("*You approach the enemy*")
            
            # Add enemy name as a separate line for clarity
            self.add_to_log(f"{enemy.name}:")
            
            # Split long dialogue into multiple log entries
            self._display_dialogue(initial_greeting)
            
            # Prompt player for response
            self.add_to_log("(Type your response and press Enter, or just press Enter to leave)")
            self.add_to_log("(WARNING: Talking does not prevent combat!)")
            
            # Enter conversation mode
            self._get_player_input_enemy()
        else:
            # Already in conversation with this enemy
            self._get_player_input_enemy()
    
    def _get_player_input(self):
        """Get text input from the player for NPC conversation."""
        if not self.renderer or not hasattr(self, 'current_npc'):
            return
            
        # Save current game state
        was_viewing_history = self.viewing_history
        self.viewing_history = False
        
        # Get input from the player
        curses.echo()  # Show typed characters
        curses.curs_set(1)  # Show cursor
        
        # Create input area at the bottom of the screen
        h, w = self.renderer.stdscr.getmaxyx()
        input_win = curses.newwin(1, w, h-1, 0)
        input_win.clear()
        input_win.addstr(0, 0, "> ")
        input_win.refresh()
        
        # Get player input (up to 70 chars)
        input_str = ""
        input_pos = 2  # Start after "> "
        
        while True:
            # Render current state to keep display updated
            self.render()
            input_win.clear()
            input_win.addstr(0, 0, f"> {input_str}")
            input_win.move(0, input_pos)
            input_win.refresh()
            
            # Get key
            try:
                key = input_win.getkey()
            except:
                continue
                
            # Process key
            if key == "\n" or key == "\r":  # Enter key
                break
            elif key == "KEY_BACKSPACE" or key == "\b" or key == "\x7f":
                if input_pos > 2:
                    input_str = input_str[:-1]
                    input_pos -= 1
            elif len(input_str) < 70 and key.isprintable():
                input_str += key
                input_pos += 1
                
        # Clean up input mode
        curses.noecho()
        curses.curs_set(0)  # Hide cursor
        self.viewing_history = was_viewing_history
                
        # Exit input mode if input is empty
        if not input_str.strip():
            self.current_npc = None
            self.add_to_log("You end the conversation.")
            return
        else:
            # Get response from the NPC and display it
            self.add_to_log(f"You: {input_str}")
            response = self.current_npc.talk(input_str)
            
            self.add_to_log(f"{self.current_npc.name}:")
            self._display_dialogue(response)
            
            # Continue conversation
            self.add_to_log("(Type your response and press Enter, or just press Enter to leave)")
            
            # Recursively call this function to continue the conversation
            self._get_player_input()
    
    def _get_player_input_enemy(self):
        """Get text input from the player for enemy conversation."""
        if not self.renderer or not hasattr(self, 'current_enemy'):
            return
            
        # Save current game state
        was_viewing_history = self.viewing_history
        self.viewing_history = False
        
        # Get input from the player
        curses.echo()  # Show typed characters
        curses.curs_set(1)  # Show cursor
        
        # Create input area at the bottom of the screen
        h, w = self.renderer.stdscr.getmaxyx()
        input_win = curses.newwin(1, w, h-1, 0)
        input_win.clear()
        input_win.addstr(0, 0, "> ")
        input_win.refresh()
        
        # Get player input (up to 70 chars)
        input_str = ""
        input_pos = 2  # Start after "> "
        
        while True:
            # Render current state to keep display updated
            self.render()
            input_win.clear()
            input_win.addstr(0, 0, f"> {input_str}")
            input_win.move(0, input_pos)
            input_win.refresh()
            
            # Get key
            try:
                key = input_win.getkey()
            except:
                continue
                
            # Process key
            if key == "\n" or key == "\r":  # Enter key
                break
            elif key == "KEY_BACKSPACE" or key == "\b" or key == "\x7f":
                if input_pos > 2:
                    input_str = input_str[:-1]
                    input_pos -= 1
            elif len(input_str) < 70 and key.isprintable():
                input_str += key
                input_pos += 1
        
        # Clean up input mode
        curses.noecho()
        curses.curs_set(0)  # Hide cursor
        self.viewing_history = was_viewing_history
                
        # Exit input mode if input is empty
        if not input_str.strip():
            self.current_enemy = None
            self.add_to_log("You end the conversation.")
            return
        else:
            # Get response from the enemy and display it
            self.add_to_log(f"You: {input_str}")
            response = self.current_enemy.talk(input_str)
            
            self.add_to_log(f"{self.current_enemy.name}:")
            self._display_dialogue(response)
            
            # Continue conversation
            self.add_to_log("(Type your response and press Enter, or just press Enter to leave)")
            
            # Recursively call this function to continue the conversation
            self._get_player_input_enemy()
    
    def _display_dialogue(self, dialogue):
        """Split and display dialogue in the game log."""
        # Break longer dialogue into manageable chunks to ensure everything is displayed
        words = dialogue.split()
        current_line = ""
        
        for word in words:
            # If adding this word would exceed the line limit
            if len(current_line) + len(word) + 1 > 70:
                # Add the current line to the log and start a new one
                self.add_to_log(f"  {current_line}")
                current_line = word
            else:
                # Add the word to the current line
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        # Make sure to add the last line if there's anything left
        if current_line:
            self.add_to_log(f"  {current_line}")
    
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
            # Display history view with offset - increased from 20 to 30 lines
            history_view = self.game_log[-min(len(self.game_log), 30+self.history_offset):-self.history_offset] if self.history_offset > 0 else self.game_log[-min(len(self.game_log), 30):]
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
                log=self.game_log[-min(len(self.game_log), 20):]  # Only show the most recent 20 lines in normal view
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