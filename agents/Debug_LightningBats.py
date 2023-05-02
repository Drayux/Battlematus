# -- AGENT INFO --
# TODO

# ================

from agent import Agent as Base
# from agent import AgentState

class Agent(Base):
    def selectSpell(self):
        # None indicates Pass; (TODO: -1 indicates pet willcast)
        return None
    
    def selectTarget(self):
        # None indicates no target selected (perfectly fine for AoE spells, selfcasts, etc.)
        return None