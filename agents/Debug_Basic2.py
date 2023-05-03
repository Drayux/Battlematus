# -- AGENT INFO --
# Basic debugging agent which will always return the spell at the first index.
# Good for testing a single spell - Set the player stats as an NPC with their deck as a single spell

# ================

# Python packages are a little beyond my current scope of python understanding
# As such, this can probably implimented much better than this
from agent import Agent as Base
# from agent import AgentState

class Agent(Base):
    def select(self):
        return 0, 0