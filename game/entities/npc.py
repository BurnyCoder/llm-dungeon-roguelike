import random
from game.entities.entity import Entity


class NPC(Entity):
    """Non-player character class."""
    
    def __init__(self, name, x=0, y=0, personality=None, dialogue=None):
        super().__init__(
            name=name,
            char="N",
            color_pair=5,  # Blue
            x=x,
            y=y,
            blocks_movement=True,
            entity_type="npc"
        )
        self.personality = personality or "Neutral"
        self.dialogue = dialogue or ["Hello, adventurer."]
        self.current_dialogue_index = 0
        self.move_cooldown = 0
        self.move_cooldown_max = 5
        
    def talk(self):
        """Return the current dialogue line."""
        if not self.dialogue:
            return "..."
            
        line = self.dialogue[self.current_dialogue_index]
        self.current_dialogue_index = (self.current_dialogue_index + 1) % len(self.dialogue)
        return line
        
    def update(self, player):
        """Update NPC behavior."""
        # Occasionally move randomly
        self.move_cooldown -= 1
        if self.move_cooldown <= 0:
            # Reset cooldown
            self.move_cooldown = self.move_cooldown_max
            
            # Random movement
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            
            # Get the dungeon from the entity's position
            dungeon = player.dungeon if hasattr(player, "dungeon") else None
            
            if dungeon:
                new_x = self.x + dx
                new_y = self.y + dy
                
                if dungeon.is_walkable(new_x, new_y):
                    self.x = new_x
                    self.y = new_y


class Enemy(Entity):
    """Enemy character class."""
    
    def __init__(self, name, x=0, y=0, hp=20, attack=5, behavior=None, personality=None):
        super().__init__(
            name=name,
            char="E",
            color_pair=3,  # Red
            x=x,
            y=y,
            blocks_movement=True,
            entity_type="enemy"
        )
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.behavior = behavior or "aggressive"
        self.personality = personality or "Hostile"
        self.move_cooldown = 0
        self.move_cooldown_max = 3
        self.detection_range = 8
        
    def update(self, player):
        """Update enemy behavior."""
        # Reduce cooldown
        self.move_cooldown -= 1
        if self.move_cooldown <= 0:
            self.move_cooldown = self.move_cooldown_max
            
            # Get distance to player
            distance = self.distance_to(player)
            
            # If player is within detection range and visible
            if distance < self.detection_range:
                # Move towards player
                dungeon = player.dungeon if hasattr(player, "dungeon") else None
                if dungeon:
                    self.move_towards(player.x, player.y, dungeon)
            else:
                # Random movement
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                
                dungeon = player.dungeon if hasattr(player, "dungeon") else None
                if dungeon:
                    new_x = self.x + dx
                    new_y = self.y + dy
                    
                    if dungeon.is_walkable(new_x, new_y):
                        self.x = new_x
                        self.y = new_y 