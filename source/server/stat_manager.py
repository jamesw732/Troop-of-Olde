class StatManager:
    def __init__(self, gamestate):
        self.gamestate = gamestate

    def update_max_ratings(self, char):
        """Adjust max ratings, for example after receiving a stat update."""
        char.maxhealth = char.statichealth
        char.maxenergy = char.staticenergy
        char.health = min(char.maxhealth, char.health)
        char.energy = min(char.maxenergy, char.energy)

    def increase_health(self, char, amt):
        """Function to be used whenever increasing character's health"""
        char.health = min(char.maxhealth, char.health + amt)

    def reduce_health(self, char, amt):
        """Function to be used whenever decreasing character's health

        Todo: If health <= 0, add to list of characters to kill"""
        char.health -= amt

    def apply_state_diff(self, char, state, remove=False):
        """Apply attrs to a destination object by adding/subtracting the attrs
        
        char: Character"""
        for attr, val in state.items():
            if hasattr(char, attr):
                original_val = getattr(char, attr)
            else:
                original_val = 0
            if remove:
                setattr(char, attr, original_val - val)
            else:
                setattr(char, attr, original_val + val)
        self.update_max_ratings(char)

