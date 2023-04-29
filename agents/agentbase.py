from abc import ABC as Abstract
from abc import abstractmethod

# Base class for a spell selection agent
# The only member data should be in the form of previous "history" which should not need explicit initalization
class Agent(Abstract):
	# Determines the potential targets for a cast event
	# This function is not built with the intent of being overwritten 
	def getTargets(self, memberID, state):
		# Categorize the battle members
		wizards = []
		raise NotImplementedError

	# Returns the selected spell for the cast event
	# TODO: Needs parameter for the options...should these be determined beforehand?
	@abstractmethod
	def selectSpell(self): return None

	# Returns the selected target(s) of a spell cast
	# TODO: Needs parameter for the options...should these be determined beforehand?
	@abstractmethod
	def selectTarget(self): return None
