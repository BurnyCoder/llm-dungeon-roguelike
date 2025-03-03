import random
from typing import List, Dict, Any, Optional, Tuple


class Dungeon:
    """Represents a dungeon level with tiles and entities."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[0 for y in range(height)] for x in range(width)]
        self.entities = []
        self.npcs = []
        self.enemies = []
        self.items = []
        
        # Tile types:
        # 0: Wall
        # 1: Floor
        # 2: Stairs
        
    def render(self, renderer):
        """Render the dungeon tiles."""
        for x in range(self.width):
            for y in range(self.height):
                if self.tiles[x][y] == 0:  # Wall
                    renderer.draw_tile(x, y, "#")
                elif self.tiles[x][y] == 1:  # Floor
                    renderer.draw_tile(x, y, ".")
                elif self.tiles[x][y] == 2:  # Stairs
                    renderer.draw_tile(x, y, ">", 4)  # Yellow color
                    
    def render_entities(self, renderer):
        """Render all entities in the dungeon."""
        for entity in self.entities:
            entity.render(renderer)
            
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile is walkable (floor or stairs)."""
        # Check if in bounds
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        # Check if tile is floor or stairs
        if self.tiles[x][y] not in (1, 2):
            return False
            
        # Check if there's a blocking entity
        for entity in self.entities:
            if entity.x == x and entity.y == y and entity.blocks_movement:
                return False
                
        return True
        
    def is_level_exit(self, x: int, y: int) -> bool:
        """Check if a tile is the exit to the next level (stairs)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        return self.tiles[x][y] == 2
        
    def get_random_floor_tile(self) -> Tuple[int, int]:
        """Return a random walkable position."""
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            
            if self.is_walkable(x, y):
                return (x, y)
                
    def populate_entities(self, npc_generator, level: int = 0):
        """Populate the dungeon with NPCs and enemies."""
        # Clear existing entities
        self.entities = []
        self.npcs = []
        self.enemies = []
        
        # Calculate number of entities based on level
        num_npcs = random.randint(1, 2)
        num_enemies = 3 + level // 2  # More enemies in deeper levels
        
        # Create NPCs
        for _ in range(num_npcs):
            pos = self.get_random_floor_tile()
            npc = npc_generator.generate_npc(level)
            npc.x, npc.y = pos
            self.npcs.append(npc)
            self.entities.append(npc)
            
        # Create enemies
        for _ in range(num_enemies):
            pos = self.get_random_floor_tile()
            enemy = npc_generator.generate_enemy(level)
            enemy.x, enemy.y = pos
            self.enemies.append(enemy)
            self.entities.append(enemy)
            
    def update_entities(self, player):
        """Update all entities in the dungeon."""
        for entity in self.entities:
            entity.update(player)
            
    def get_adjacent_npc(self, x: int, y: int) -> Optional[Any]:
        """Get an NPC adjacent to the given position."""
        for npc in self.npcs:
            if abs(npc.x - x) <= 1 and abs(npc.y - y) <= 1:
                return npc
        return None
        
    def get_adjacent_enemy(self, x: int, y: int) -> Optional[Any]:
        """Get an enemy adjacent to the given position."""
        for enemy in self.enemies:
            if abs(enemy.x - x) <= 1 and abs(enemy.y - y) <= 1:
                return enemy
        return None
        
    def remove_entity(self, entity):
        """Remove an entity from the dungeon."""
        if entity in self.entities:
            self.entities.remove(entity)
            
        # Remove from specific lists
        if entity.entity_type == "npc" and entity in self.npcs:
            self.npcs.remove(entity)
        elif entity.entity_type == "enemy" and entity in self.enemies:
            self.enemies.remove(entity) 