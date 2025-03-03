import random
from typing import List, Tuple, Dict, Any
from game.world.dungeon import Dungeon


class Room:
    """Represents a room in the dungeon."""
    
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1  # Top left x
        self.y1 = y1  # Top left y
        self.x2 = x2  # Bottom right x
        self.y2 = y2  # Bottom right y
        
    @property
    def center(self):
        """Return the center coordinates of the room."""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
        
    def intersects(self, other):
        """Check if this room intersects with another room."""
        return (
            self.x1 <= other.x2 and 
            self.x2 >= other.x1 and 
            self.y1 <= other.y2 and 
            self.y2 >= other.y1
        )


class MapGenerator:
    """Generates random dungeon maps."""
    
    def __init__(self, width=80, height=20):
        self.width = width
        self.height = height
        self.max_rooms = 10  # Maximum number of rooms
        self.min_room_size = 5  # Minimum size of each room
        self.max_room_size = 10  # Maximum size of each room
        
    def generate_dungeon(self, level=0) -> Dungeon:
        """Generate a new dungeon level."""
        # Create a new dungeon
        dungeon = Dungeon(self.width, self.height)
        
        # Fill dungeon with walls
        for x in range(self.width):
            for y in range(self.height):
                dungeon.tiles[x][y] = 0  # Wall
        
        # Generate rooms
        rooms: List[Room] = []
        num_rooms = 0
        
        for r in range(self.max_rooms):
            # Random room size
            w = random.randint(self.min_room_size, self.max_room_size)
            h = random.randint(self.min_room_size, self.max_room_size)
            
            # Random room position
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            new_room = Room(x, y, x + w, y + h)
            
            # Check if room overlaps with existing rooms
            for other_room in rooms:
                if new_room.intersects(other_room):
                    break
            else:
                # Room doesn't overlap, add it
                self._carve_room(dungeon, new_room)
                
                if num_rooms > 0:
                    # Connect to previous room
                    prev_x, prev_y = rooms[num_rooms - 1].center
                    curr_x, curr_y = new_room.center
                    
                    # Randomly decide whether to carve horizontal then vertical 
                    # or vertical then horizontal
                    if random.random() < 0.5:
                        self._carve_h_tunnel(dungeon, prev_x, curr_x, prev_y)
                        self._carve_v_tunnel(dungeon, prev_y, curr_y, curr_x)
                    else:
                        self._carve_v_tunnel(dungeon, prev_y, curr_y, prev_x)
                        self._carve_h_tunnel(dungeon, prev_x, curr_x, curr_y)
                
                rooms.append(new_room)
                num_rooms += 1
        
        # Place stairs down to next level
        # Place it in the last room
        if rooms:
            last_room = rooms[-1]
            sx, sy = last_room.center
            dungeon.tiles[sx][sy] = 2  # Stairs
            
        # Return the generated dungeon
        return dungeon
    
    def _carve_room(self, dungeon, room):
        """Carve a room in the dungeon."""
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                dungeon.tiles[x][y] = 1  # Floor
    
    def _carve_h_tunnel(self, dungeon, x1, x2, y):
        """Carve a horizontal tunnel."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            dungeon.tiles[x][y] = 1  # Floor
    
    def _carve_v_tunnel(self, dungeon, y1, y2, x):
        """Carve a vertical tunnel."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            dungeon.tiles[x][y] = 1  # Floor 