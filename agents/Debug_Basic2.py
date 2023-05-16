# -- AGENT INFO --
# Basic debugging agent which will always return the spell at the first index.
# Good for testing a single spell - Set the player stats as an NPC with their deck as a single spell

# ================

# Python packages are a little beyond my current scope of python understanding
# As such, this can probably implimented much better than this
from agent import Agent as Base
# from agent import AgentState

from random import random

class Agent(Base):
    def select(self):
        # return 0, 0

        spellIdx = None
        weights = [0.3, 0.2, 0.2]   # Pass = 0.3
        rand = random()
        cum = 0
        for i, x in enumerate(weights):
            cum += x
            if cum > rand: 
                spellIdx = i
                break
        
        # Blade is cast on self
        target = 0
        if spellIdx == 0:
            target = 4
        
        return spellIdx, target