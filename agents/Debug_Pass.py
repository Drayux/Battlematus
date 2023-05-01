# -- AGENT INFO --
# Basic debugging agent which will always pass if possible.

# ================

# Python packages are a little beyond my current scope of python understanding
# As such, this can probably implimented much better than this
from agent import Agent as Base

class Agent(Base):
    def selectSpell(self):
        return super().selectSpell()
    
    def selectTarget(self):
        return super().selectTarget()