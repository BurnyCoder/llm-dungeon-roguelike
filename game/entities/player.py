from game.entities.entity import Entity


class Player(Entity):
    """Player character class."""
    
    def __init__(self, name, x=0, y=0, hp=100, max_hp=100, attack=10):
        super().__init__(
            name=name,
            char="@",
            color_pair=2,
            x=x,
            y=y,
            blocks_movement=True,
            entity_type="player"
        )
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.inventory = []
        
    def render(self, renderer):
        """Render the player on the screen."""
        renderer.draw_tile(self.x, self.y, self.char, self.color_pair)
        
    def move(self, dx, dy, dungeon):
        """Move the player by delta x and delta y if the destination is walkable."""
        new_x = self.x + dx
        new_y = self.y + dy
        
        if dungeon.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True
        return False 