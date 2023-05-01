from abc import ABC as Abstract
from abc import abstractmethod

# Base class for a spell selection agent
# The only member data should be in the form of previous "history" which should not need explicit initalization
class Agent(Abstract):
	# Takes the memberID and state and saves references to helpful components
	def __init__(self, simulation, memberID):
		self._sim = simulation
		self.member = memberID
		self.cstate = simulation.state.members[memberID]
		self.cstats = simulation.stats[memberID]

	# Determines the potential targets for a cast event
	# This function is not built with the intent of being overridden
	def getTargets(self, memberID, state):
		# Categorize the battle members
		wizards = []
		raise NotImplementedError

	# Returns the selected spell (index) for the cast event
	# TODO: Needs parameter for the options...should these be determined beforehand?
	@abstractmethod
	def selectSpell(self): raise NotImplementedError("Base Agent : selectSpell()")

	# Returns the selected target(s) of a spell cast
	# TODO: Needs parameter for the options...should these be determined beforehand?
	@abstractmethod
	def selectTarget(self): raise NotImplementedError("Base Agent : selectTarget()")
