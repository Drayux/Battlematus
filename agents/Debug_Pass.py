# -- AGENT INFO --
# Basic debugging agent which will always pass if possible.

# ================

# Python packages are a little beyond my current scope of python understanding
# As such, this can probably implimented much better than this
from agent import Agent as Base
# from agent import AgentState

class Agent(Base):
    def select(self):
        return None