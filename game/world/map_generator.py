import random
from typing import List, Tuple, Dict, Any
from game.world.dungeon import Dungeon
from collections import deque


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
        self.rooms = []  # Store generated rooms for external access
        
    def generate_dungeon(self, level=0) -> Dungeon:
        """Generate a new dungeon level."""
        # Create a new dungeon
        dungeon = Dungeon(self.width, self.height)
        
        # Fill dungeon with walls
        for x in range(self.width):
            for y in range(self.height):
                dungeon.tiles[x][y] = 0  # Wall
        
        # Generate rooms
        self.rooms = []  # Reset rooms
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
            for other_room in self.rooms:
                if new_room.intersects(other_room):
                    break
            else:
                # Room doesn't overlap, add it
                self._carve_room(dungeon, new_room)
                
                if num_rooms > 0:
                    # Connect to previous room to ensure a path from start to end
                    prev_x, prev_y = self.rooms[num_rooms - 1].center
                    curr_x, curr_y = new_room.center
                    
                    # Randomly decide whether to carve horizontal then vertical 
                    # or vertical then horizontal
                    if random.random() < 0.5:
                        self._carve_h_tunnel(dungeon, prev_x, curr_x, prev_y)
                        self._carve_v_tunnel(dungeon, prev_y, curr_y, curr_x)
                    else:
                        self._carve_v_tunnel(dungeon, prev_y, curr_y, prev_x)
                        self._carve_h_tunnel(dungeon, prev_x, curr_x, curr_y)
                    
                    # Add some additional connections for redundancy (20% chance)
                    # This creates loops in the dungeon for more interesting navigation
                    if num_rooms > 1 and random.random() < 0.2:
                        # Connect to a random previous room
                        rand_room_idx = random.randint(0, num_rooms - 1)
                        rand_x, rand_y = self.rooms[rand_room_idx].center
                        
                        if random.random() < 0.5:
                            self._carve_h_tunnel(dungeon, curr_x, rand_x, curr_y)
                            self._carve_v_tunnel(dungeon, curr_y, rand_y, rand_x)
                        else:
                            self._carve_v_tunnel(dungeon, curr_y, rand_y, curr_x)
                            self._carve_h_tunnel(dungeon, curr_x, rand_x, rand_y)
                
                self.rooms.append(new_room)
                num_rooms += 1
        
        # Place stairs down to next level
        # Place it in the last room
        if self.rooms:
            last_room = self.rooms[-1]
            sx, sy = last_room.center
            dungeon.tiles[sx][sy] = 2  # Stairs
            
            # Verify path from first room to stairs
            if not self._verify_path(dungeon, self.rooms[0].center, (sx, sy)):
                # If no path exists, force create a direct path
                self._create_direct_path(dungeon, self.rooms[0].center, (sx, sy))
        
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
            
    def _verify_path(self, dungeon, start, end):
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
                if (dungeon.is_walkable(next_x, next_y) and 
                    (next_x, next_y) not in visited):
                    queue.append((next_x, next_y))
        
        # If queue is empty and end not found, no path exists
        return False
        
    def _create_direct_path(self, dungeon, start, end):
        """Create a direct path from start to end coordinates."""
        x1, y1 = start
        x2, y2 = end
        
        # First carve horizontal tunnel
        self._carve_h_tunnel(dungeon, x1, x2, y1)
        
        # Then carve vertical tunnel
        self._carve_v_tunnel(dungeon, y1, y2, x2) 