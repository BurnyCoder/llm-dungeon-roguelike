import curses


class InputHandler:
    """Handles user input for the game."""
    
    def __init__(self):
        # Map of special key codes to string representations
        self.key_mapping = {
            curses.KEY_UP: "KEY_UP",
            curses.KEY_DOWN: "KEY_DOWN",
            curses.KEY_LEFT: "KEY_LEFT",
            curses.KEY_RIGHT: "KEY_RIGHT",
            curses.KEY_ENTER: "KEY_ENTER",
            27: "ESCAPE",  # ESC key
        }
    
    def get_input(self, stdscr):
        """Get input from the user and return a string representation."""
        # Set timeout for getch (non-blocking input)
        stdscr.timeout(100)
        
        try:
            key_code = stdscr.getch()
            
            # No input
            if key_code == -1:
                return None
                
            # Handle special keys
            if key_code in self.key_mapping:
                return self.key_mapping[key_code]
                
            # Handle standard characters
            try:
                return chr(key_code)
            except ValueError:
                return None
                
        except Exception as e:
            # Log error or handle as needed
            return None 