import curses
from typing import List, Dict, Any, Optional


class Renderer:
    """Handles rendering the game state to the terminal using curses."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # Game view dimensions
        self.game_width = 80
        self.game_height = 20
        
        # UI dimensions
        self.ui_height = 10  # Increased for more log lines
        
        # Calculate offsets to center the game view
        self.offset_y = 0
        self.offset_x = max(0, (self.width - self.game_width) // 2)
    
    def clear(self):
        """Clear the screen."""
        self.stdscr.clear()
    
    def refresh(self):
        """Refresh the screen to display changes."""
        self.stdscr.refresh()
        
    def draw_tile(self, x: int, y: int, char: str, color_pair: int = 1):
        """Draw a tile at the given coordinates with the specified character and color."""
        # Skip if coordinates are out of bounds
        if (x < 0 or x >= self.game_width or 
            y < 0 or y >= self.game_height):
            return
            
        try:
            self.stdscr.addstr(
                y + self.offset_y, 
                x + self.offset_x, 
                char, 
                curses.color_pair(color_pair)
            )
        except curses.error:
            # This can happen if trying to write to the bottom-right corner
            pass
            
    def draw_string(self, x: int, y: int, text: str, color_pair: int = 1):
        """Draw a string at the given coordinates with the specified color."""
        try:
            self.stdscr.addstr(
                y + self.offset_y, 
                x + self.offset_x, 
                text[:self.width - x - 1], 
                curses.color_pair(color_pair)
            )
        except curses.error:
            # This can happen if trying to write beyond the screen boundaries
            pass
            
    def draw_ui(self, player, dungeon_level: int, log: List[str]):
        """Draw the user interface elements."""
        # Draw separator line
        separator_y = self.game_height
        self.draw_string(0, separator_y, "-" * self.game_width)
        
        # Draw player stats
        stats_y = separator_y + 1
        hp_text = f"HP: {player.hp}/{player.max_hp}"
        level_text = f"Dungeon Level: {dungeon_level}"
        
        self.draw_string(2, stats_y, hp_text)
        self.draw_string(self.game_width - len(level_text) - 2, stats_y, level_text)
        
        # Draw game log - showing more lines
        log_y = stats_y + 1
        # Dynamically determine max lines based on terminal height
        available_space = self.height - log_y - 1
        max_display_lines = min(available_space, 8)  # Show up to 8 lines if space permits
        
        for i, message in enumerate(log[-max_display_lines:]):  # Show last N messages
            if i < max_display_lines:  # Ensure we don't overflow
                self.draw_string(2, log_y + i, message) 