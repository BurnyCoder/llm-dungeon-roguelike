class Entity:
    """Base class for all game entities."""
    
    def __init__(
        self,
        name: str,
        char: str = "?",
        color_pair: int = 1,
        x: int = 0,
        y: int = 0,
        blocks_movement: bool = False,
        entity_type: str = "generic"
    ):
        self.name = name
        self.char = char
        self.color_pair = color_pair
        self.x = x
        self.y = y
        self.blocks_movement = blocks_movement
        self.entity_type = entity_type
        
    def render(self, renderer):
        """Render the entity to the screen."""
        renderer.draw_tile(self.x, self.y, self.char, self.color_pair)
        
    def update(self, player):
        """Update the entity state - to be overridden by subclasses."""
        pass
        
    def distance_to(self, other_entity) -> float:
        """Calculate the Euclidean distance to another entity."""
        return ((self.x - other_entity.x) ** 2 + (self.y - other_entity.y) ** 2) ** 0.5
        
    def move_towards(self, target_x: int, target_y: int, dungeon) -> bool:
        """Move the entity one step towards the target position."""
        dx = 0
        dy = 0
        
        if self.x < target_x:
            dx = 1
        elif self.x > target_x:
            dx = -1
            
        if self.y < target_y:
            dy = 1
        elif self.y > target_y:
            dy = -1
            
        # Try to move diagonally first
        if dx != 0 and dy != 0:
            if dungeon.is_walkable(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy
                return True
                
        # Try to move horizontally
        if dx != 0:
            if dungeon.is_walkable(self.x + dx, self.y):
                self.x += dx
                return True
                
        # Try to move vertically
        if dy != 0:
            if dungeon.is_walkable(self.x, self.y + dy):
                self.y += dy
                return True
                
        return False 