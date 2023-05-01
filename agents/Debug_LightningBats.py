# -- AGENT INFO --
# Basic debugging agent which will always cast Lightning Bats or discard everything else

# ================

# Python packages are a little beyond my current scope of python understanding
# As such, this can probably implimented much better than this
from agent import Agent as Base

class Agent(Base):
    def __init__(self):
        print("Success initializing passing agent class!")
    
    def selectSpell(self):
        return super().selectSpell()
    
    def selectTarget(self):
        return super().selectTarget()