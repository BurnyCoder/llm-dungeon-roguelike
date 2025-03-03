import random
import json
import sys
import os
import pickle
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from portkey import claude37sonnet
from game.entities.npc import NPC, Enemy

# Templates for NPC/enemy generation
NPC_PROMPT_TEMPLATE = """
Generate a unique NPC for a roguelike fantasy game. The NPC should have:
- A creative name
- A distinct unique and interesting personality, potentially alien
- 3-5 dialogue options that reflect their personality
- A brief physical description, try to create alien looking or unique looking NPC

NPC should be appropriate for dungeon level {level} (higher level = more exotic/unusual).

Return the result as a JSON object with the following structure:
{{
  "name": "NPC's name",
  "personality": "Brief description of personality",
  "dialogue": ["Dialogue line 1", "Dialogue line 2", "Dialogue line 3"],
  "description": "Physical description"
}}

Be creative and avoid generic fantasy tropes.
"""

ENEMY_PROMPT_TEMPLATE = """
Generate a unique enemy for a roguelike fantasy game. The enemy should have:
- A creative name
- A distinct unique and interesting personality and behavior pattern, potentially alien
- Combat abilities appropriate for dungeon level {level} (higher = more powerful)
- A brief physical description, try to create alien or unique looking enemy

Return the result as a JSON object with the following structure:
{{
  "name": "Enemy's name",
  "personality": "Brief description of personality/behavior",
  "hp": number between 10-50 based on level,
  "attack": number between 5-15 based on level,
  "description": "Physical description",
  "behavior": "aggressive", "territorial", "ambusher", "cowardly", or "pack"
}}

Be creative and avoid generic fantasy tropes.
"""


class NPCGenerator:
    """Generates NPCs and enemies using LLMs."""
    
    def __init__(self, use_pregenerated=False, save_generated=True):
        # Cache generated NPCs/enemies to avoid redundant API calls during testing
        self.npc_cache = {}
        self.enemy_cache = {}
        self.use_pregenerated = use_pregenerated
        self.save_generated = save_generated
        
        # Paths for saved characters
        self.data_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../game/data')))
        self.npc_file = self.data_dir / 'npcs.json'
        self.enemy_file = self.data_dir / 'enemies.json'
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Pre-generated character storage
        self.pregenerated_npcs = {}
        self.pregenerated_enemies = {}
        
        # Load pre-generated characters if option is enabled
        if self.use_pregenerated:
            self.load_pregenerated_characters()
    
    def load_pregenerated_characters(self):
        """Load pre-generated NPCs and enemies from files."""
        # Load NPCs
        if self.npc_file.exists():
            try:
                with open(self.npc_file, 'r') as f:
                    self.pregenerated_npcs = json.load(f)
                print(f"Loaded {len(self.pregenerated_npcs)} pre-generated NPCs.")
            except Exception as e:
                print(f"Error loading pre-generated NPCs: {e}")
                self.pregenerated_npcs = {}
        
        # Load enemies
        if self.enemy_file.exists():
            try:
                with open(self.enemy_file, 'r') as f:
                    self.pregenerated_enemies = json.load(f)
                print(f"Loaded {len(self.pregenerated_enemies)} pre-generated enemies.")
            except Exception as e:
                print(f"Error loading pre-generated enemies: {e}")
                self.pregenerated_enemies = {}
    
    def save_characters(self):
        """Save generated NPCs and enemies to files."""
        # Save NPCs
        if self.npc_cache:
            try:
                with open(self.npc_file, 'w') as f:
                    json.dump(self.npc_cache, f, indent=2)
                print(f"Saved {len(self.npc_cache)} NPCs to {self.npc_file}.")
            except Exception as e:
                print(f"Error saving NPCs: {e}")
        
        # Save enemies
        if self.enemy_cache:
            try:
                with open(self.enemy_file, 'w') as f:
                    json.dump(self.enemy_cache, f, indent=2)
                print(f"Saved {len(self.enemy_cache)} enemies to {self.enemy_file}.")
            except Exception as e:
                print(f"Error saving enemies: {e}")
    
    def generate_npc(self, level: int = 1) -> NPC:
        """Generate an NPC using Claude 3.7 Sonnet or from pre-generated data."""
        # Check if we should use pre-generated NPCs
        if self.use_pregenerated:
            level_key = f"npc_level_{level}"
            # Find NPCs for this level
            level_npcs = [k for k in self.pregenerated_npcs.keys() if k.startswith(level_key)]
            if level_npcs:
                # Randomly choose one of the pre-generated NPCs
                cache_key = random.choice(level_npcs)
                npc_data = self.pregenerated_npcs[cache_key]
                return self._create_npc_from_data(npc_data, level)
        
        # Generate a new NPC
        # Check cache first
        cache_key = f"npc_level_{level}_{random.randint(1, 10000)}"
        if cache_key in self.npc_cache:
            npc_data = self.npc_cache[cache_key]
        else:
            # Generate NPC using LLM
            prompt = NPC_PROMPT_TEMPLATE.format(level=level)
            try:
                response = claude37sonnet(prompt)
                # Extract JSON from response
                npc_data = self._extract_json(response)
                # Cache result
                self.npc_cache[cache_key] = npc_data
                
                # Save to file if option is enabled
                if self.save_generated:
                    self.save_characters()
                    
            except Exception as e:
                print(f"Error generating NPC: {e}")
                # Fallback to default NPC
                return self._create_default_npc(level)
        
        return self._create_npc_from_data(npc_data, level)
    
    def _create_npc_from_data(self, npc_data: dict, level: int) -> NPC:
        """Create an NPC instance from data."""
        return NPC(
            name=npc_data.get("name", f"NPC Level {level}"),
            personality=npc_data.get("personality", "Mysterious"),
            dialogue=npc_data.get("dialogue", ["Hello, adventurer."])
        )
    
    def generate_enemy(self, level: int = 1) -> Enemy:
        """Generate an enemy using Claude 3.7 Sonnet or from pre-generated data."""
        # Check if we should use pre-generated enemies
        if self.use_pregenerated:
            level_key = f"enemy_level_{level}"
            # Find enemies for this level
            level_enemies = [k for k in self.pregenerated_enemies.keys() if k.startswith(level_key)]
            if level_enemies:
                # Randomly choose one of the pre-generated enemies
                cache_key = random.choice(level_enemies)
                enemy_data = self.pregenerated_enemies[cache_key]
                return self._create_enemy_from_data(enemy_data, level)
        
        # Generate a new enemy
        # Check cache first
        cache_key = f"enemy_level_{level}_{random.randint(1, 10000)}"
        if cache_key in self.enemy_cache:
            enemy_data = self.enemy_cache[cache_key]
        else:
            # Generate enemy using LLM
            prompt = ENEMY_PROMPT_TEMPLATE.format(level=level)
            try:
                response = claude37sonnet(prompt)
                # Extract JSON from response
                enemy_data = self._extract_json(response)
                # Cache result
                self.enemy_cache[cache_key] = enemy_data
                
                # Save to file if option is enabled
                if self.save_generated:
                    self.save_characters()
                    
            except Exception as e:
                print(f"Error generating enemy: {e}")
                # Fallback to default enemy
                return self._create_default_enemy(level)
        
        return self._create_enemy_from_data(enemy_data, level)
    
    def _create_enemy_from_data(self, enemy_data: dict, level: int) -> Enemy:
        """Create an Enemy instance from data."""
        return Enemy(
            name=enemy_data.get("name", f"Enemy Level {level}"),
            hp=enemy_data.get("hp", 10 + level * 5),
            attack=enemy_data.get("attack", 5 + level),
            behavior=enemy_data.get("behavior", "aggressive"),
            personality=enemy_data.get("personality", "Hostile")
        )
    
    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response text."""
        try:
            # Try to find JSON object in the text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fall back to default values
                return {}
        except json.JSONDecodeError:
            # Fall back to default values
            return {}
    
    def _create_default_npc(self, level: int) -> NPC:
        """Create a default NPC if generation fails."""
        return NPC(
            name=f"Dungeon Dweller {level}",
            personality="Mysterious",
            dialogue=[
                "Welcome, traveler.",
                "These dungeons hold many secrets.",
                "Be careful as you venture deeper."
            ]
        )
    
    def _create_default_enemy(self, level: int) -> Enemy:
        """Create a default enemy if generation fails."""
        return Enemy(
            name=f"Dungeon Monster {level}",
            hp=10 + level * 5,
            attack=5 + level,
            behavior="aggressive",
            personality="Hostile"
        ) 