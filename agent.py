from abc import ABC as Abstract
from abc import abstractmethod

# Base class for a spell selection agent
# The only member data should be in the form of previous "history" which should not need explicit initalization
class Agent(Abstract):
	# Takes the memberID and state and saves references to helpful components
	# TODO: Support cast history (involves saving and loading with simulation data)
	def __init__(self, simulation, memberID):
		self._sim = simulation
		self.member = memberID
		self.cstate = simulation.state.members[memberID]
		self.cstats = simulation.stats[memberID]
		# self.astate = AgentState()

	def __str__(self):
		# This is probably a hacky solution, consider refactoring
		# The goal is to return the filename associated with the agent (same value one would use to init this class within Simulation)
		return self.__module__.split(".")[-1]

	# Determines the potential targets for a cast event
	# This function is not built with the intent of being overridden (excluding wild cheats like HoH)
	# spell -> spellID of intended cast
	def getTargets(self):
		# Categorize the battle members
		friendlies = []
		opponents = []

		# TODO: Determine if threat impacts the available selections

	# Returns tuple of selected spell (index) and target index (or list of target indexes)
	@abstractmethod
	def select(self): raise NotImplementedError("Base Agent : select()")

	# Returns the selected spell (index) for the cast event
	# TODO: Needs parameter for the options...should these be determined beforehand?
	# @abstractmethod
	# def selectSpell(self): raise NotImplementedError("Base Agent : selectSpell()")

	# Returns the selected target(s) of a spell cast
	# TODO: Needs parameter for the options...should these be determined beforehand?
	# @abstractmethod
	# def selectTarget(self): raise NotImplementedError("Base Agent : selectTarget()")


# Simple class for storing the Agent's state
# Basically an array of (spellID, target) tuples indexed by round number
# Provides helper functions for better interfacing with the Agent class
class AgentState:
	def __init__(self, data = None):
		if data is not None:
			print("TODO: Agent state history file I/O")
		
		self._data = []
	
	# Getter method for the internal data array
	# Returns None if a selection has yet to be made
	def getSpell(self, round):
		if round >= len(self._data): return None