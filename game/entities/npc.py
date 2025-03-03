import random
from game.entities.entity import Entity
import portkey


class NPC(Entity):
    """Non-player character class."""
    
    def __init__(self, name, x=0, y=0, personality=None, dialogue=None, description=None, 
                 max_history_length=10):
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
        self.description = description or "A mysterious figure."
        self.current_dialogue_index = 0
        self.move_cooldown = 0
        self.move_cooldown_max = 5
        # Add conversation memory with configurable length
        self.conversation_history = []
        self.max_history_length = max_history_length
        
    def talk(self, player_query=None):
        """
        Return dialogue line.
        If player_query is provided, generate a response using Claude 3.7 Sonnet.
        Otherwise, return the next predefined dialogue line.
        """
        if player_query is None:
            # No query provided, use predefined dialogue
            if not self.dialogue:
                return "..."
                
            line = self.dialogue[self.current_dialogue_index]
            self.current_dialogue_index = (self.current_dialogue_index + 1) % len(self.dialogue)
            return line
        else:
            # Use Claude 3.7 Sonnet to generate a response
            prompt = self._build_npc_prompt(player_query)
            response = portkey.claude37sonnet(prompt)
            
            # Add to conversation history
            self.conversation_history.append({"query": player_query, "response": response})
            
            # Trim history if it gets too long
            if len(self.conversation_history) > self.max_history_length:
                self._trim_conversation_history()
                
            return response
    
    def _build_npc_prompt(self, player_query):
        """Build a prompt for Claude based on NPC personality and conversation history."""
        is_initial_greeting = player_query == "*You approach the character*"
        
        # Determine conversation context based on history length
        if len(self.conversation_history) == 0:
            conversation_context = "This is your first interaction with the player."
        elif len(self.conversation_history) < 3:
            conversation_context = "You've had a brief conversation with the player already."
        else:
            conversation_context = "You've been having an ongoing conversation with the player."
        
        prompt = f"""
You are roleplaying as {self.name}, a character in a fantasy roguelike dungeon game.

Character details:
- Name: {self.name}
- Personality: {self.personality}
- Description: {self.description}

Game context:
You are a character in a dungeon. The player character is an adventurer exploring this dungeon.
{conversation_context}
{'' if not is_initial_greeting else 'The player has just approached you, so greet them appropriately based on your personality.'}

Respond to the player's query in character, using first person perspective. 
Keep your response concise (1-3 sentences). Stay in character at all times.
Don't use any markers like "Character:" or quotation marks in your response.
Your personality should strongly influence how you respond.
Maintain continuity with the previous conversation if applicable.

Conversation history:
"""
        
        # Add conversation history if it exists
        history_to_include = min(len(self.conversation_history), 5)  # Include up to 5 previous exchanges
        
        if self.conversation_history:
            for exchange in self.conversation_history[-history_to_include:]:
                prompt += f"Player: {exchange['query']}\n"
                prompt += f"You: {exchange['response']}\n\n"
        
        # Add the current query, but handle initial greeting differently
        if is_initial_greeting:
            prompt += "Player has just approached you.\n"
            prompt += "You: "
        else:
            prompt += f"Player: {player_query}\n"
            prompt += "You: "
        
        return prompt
        
    def _trim_conversation_history(self):
        """
        Trim conversation history when it exceeds the maximum length.
        Keep the most recent exchanges and summarize older ones.
        """
        if len(self.conversation_history) <= self.max_history_length:
            return
            
        # Keep the most recent conversations (roughly 70% of max)
        keep_count = int(self.max_history_length * 0.7)
        history_to_keep = self.conversation_history[-keep_count:]
        
        # Summarize the older conversations if there are enough to summarize
        if len(self.conversation_history) - keep_count > 2:
            older_history = self.conversation_history[:(len(self.conversation_history) - keep_count)]
            
            # Create a summary of older conversations
            summary_prompt = f"""
You are an AI assistant helping to summarize parts of a conversation between a player and 
an NPC named {self.name} in a fantasy roguelike game.

Below are {len(older_history)} conversation exchanges that happened earlier in their conversation.
Please create a very concise summary (max 3 sentences) that captures the key points discussed.

Conversation to summarize:
"""
            for exchange in older_history:
                summary_prompt += f"Player: {exchange['query']}\n"
                summary_prompt += f"NPC: {exchange['response']}\n\n"
                
            summary = portkey.claude37sonnet(summary_prompt)
            
            # Add the summary as the first item in the conversation history
            self.conversation_history = [{"query": "*Earlier conversation*", 
                                         "response": f"*Summary: {summary}*"}] + history_to_keep
        else:
            # If there aren't enough older messages to summarize meaningfully, just keep the recent ones
            self.conversation_history = history_to_keep
        
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
    
    def __init__(self, name, x=0, y=0, hp=20, attack=5, behavior=None, personality=None, description=None,
                 max_history_length=10):
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
        self.description = description or "A menacing creature."
        self.move_cooldown = 0
        self.move_cooldown_max = 3
        self.detection_range = 8
        # Add conversation memory with configurable length
        self.conversation_history = []
        self.max_history_length = max_history_length
        
    def talk(self, player_query=None):
        """
        Return dialogue line from the enemy.
        If player_query is provided, generate a response using Claude 3.7 Sonnet.
        """
        if player_query is None:
            # Default aggressive response if no query provided
            return "The enemy growls menacingly."
        else:
            # Use Claude 3.7 Sonnet to generate a response
            prompt = self._build_enemy_prompt(player_query)
            response = portkey.claude37sonnet(prompt)
            
            # Add to conversation history
            self.conversation_history.append({"query": player_query, "response": response})
            
            # Trim history if it gets too long
            if len(self.conversation_history) > self.max_history_length:
                self._trim_conversation_history()
                
            return response
    
    def _build_enemy_prompt(self, player_query):
        """Build a prompt for Claude based on enemy personality and conversation history."""
        is_initial_greeting = player_query == "*You approach the enemy*"
        
        # Determine conversation context based on history length
        if len(self.conversation_history) == 0:
            conversation_context = "This is your first interaction with the player."
        elif len(self.conversation_history) < 3:
            conversation_context = "You've had a brief exchange with the player already."
        else:
            conversation_context = "You've been interacting with the player for some time."
        
        prompt = f"""
You are roleplaying as {self.name}, a hostile enemy creature in a fantasy roguelike dungeon game.

Character details:
- Name: {self.name}
- Personality: {self.personality}
- Behavior: {self.behavior}
- Description: {self.description}
- HP: {self.hp}/{self.max_hp}

Game context:
You are an enemy in a dungeon. The player character is an adventurer who has encountered you.
{conversation_context}
{'' if not is_initial_greeting else 'The player has just approached you. Respond with hostility, threats, or curiosity depending on your personality.'}

Respond to the player's query in character, using first person perspective. 
Keep your response concise (1-3 sentences). Stay in character at all times.
Don't use any markers like "Character:" or quotation marks in your response.
Your personality and behavior should strongly influence how you respond.
Be hostile, threatening, or aggressive, but you might also be curious about the player.
Maintain continuity with the previous conversation if applicable.

Conversation history:
"""
        
        # Add conversation history if it exists
        history_to_include = min(len(self.conversation_history), 5)  # Include up to 5 previous exchanges
        
        if self.conversation_history:
            for exchange in self.conversation_history[-history_to_include:]:
                prompt += f"Player: {exchange['query']}\n"
                prompt += f"You: {exchange['response']}\n\n"
        
        # Add the current query, but handle initial greeting differently
        if is_initial_greeting:
            prompt += "Player has just approached you.\n"
            prompt += "You: "
        else:
            prompt += f"Player: {player_query}\n"
            prompt += "You: "
        
        return prompt
        
    def _trim_conversation_history(self):
        """
        Trim conversation history when it exceeds the maximum length.
        Keep the most recent exchanges and summarize older ones.
        """
        if len(self.conversation_history) <= self.max_history_length:
            return
            
        # Keep the most recent conversations (roughly 70% of max)
        keep_count = int(self.max_history_length * 0.7)
        history_to_keep = self.conversation_history[-keep_count:]
        
        # Summarize the older conversations if there are enough to summarize
        if len(self.conversation_history) - keep_count > 2:
            older_history = self.conversation_history[:(len(self.conversation_history) - keep_count)]
            
            # Create a summary of older conversations
            summary_prompt = f"""
You are an AI assistant helping to summarize parts of a conversation between a player and 
an enemy named {self.name} in a fantasy roguelike game.

Below are {len(older_history)} conversation exchanges that happened earlier in their conversation.
Please create a very concise summary (max 3 sentences) that captures the key points discussed.

Conversation to summarize:
"""
            for exchange in older_history:
                summary_prompt += f"Player: {exchange['query']}\n"
                summary_prompt += f"Enemy: {exchange['response']}\n\n"
                
            summary = portkey.claude37sonnet(summary_prompt)
            
            # Add the summary as the first item in the conversation history
            self.conversation_history = [{"query": "*Earlier conversation*", 
                                         "response": f"*Summary: {summary}*"}] + history_to_keep
        else:
            # If there aren't enough older messages to summarize meaningfully, just keep the recent ones
            self.conversation_history = history_to_keep
    
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