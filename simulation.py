# Class to represent the battle structure
# Core component of state in, state distribution out API

# Static elements are participants and their stats??
# Also holds data for global components, such as the bubble and turn
#	^^This is parsed from the state, but necessary for determining the next state

# One iteration of the simulation is the entire completion of one participant's action
#	^^This allows an AI to specify action policies for all members of combat

# For future development, this is also where rules for cheats will be held

# Provides functions for:
#	- Parsing a state object
#	- Advancing the battle state
#	- ^^Subcomponents of this, such as consume charms, resolve spell, etc.

# Current implementation question:
# The state class and simulation class are very similar, but used for different purposes. 
# The former is the data structure for handling battle data;
# Whereas the latter is a means of manipulating and generating new states.
# This means we generally only want to initalize simulation once, and create many states.
# The question lies if something like a member is to be modified at a deep iteration:
# How do we ensure this change is not reflected in subsequent recursive calls at a higher iter?

# New implemenation:
# Most of the data is held within the state object, however *static* data is linked outwards
# I.E. Combat members will specify an ID, which corresponds to a dictionary key within the
#   simulation class. The value of that key is the "stats" object for that member.
# Many state objects can be made, but only one instance of the simulation class should exist.
# The simulation class will then cross-reference the state and the member stats when
#   calculating further states

# TODO: Need implementation mechanic for enchants like nightbringer

from util import Position, Stats

class Simulation:
	def __init__(self):
		self.state = None
		self.stats = {}		# Dict of member stats (key: member_id;  value: <types.Stats>)
		self.spells = {}	# Dict of spells loaded to memory (key: spell_id;  value: <types.Spell)

		# -- NOT IMPLEMENTED UNTIL MUCH LATER --
		# Likely to be reformatted completely (so we don't run a loop on every action)
		self.pvp = False	# Alternative damage calculations and round handling for pvp
		self.cheats = []	# Array of <types.cheat>
	
	# Create a new state object
	def initState(self):
		pass
	
	# Load a state object
	# Simply set the object if type is state
	# Load from file if string (assuming path)
	# If file does not contain simulation data, assume that the data is just the state
	#   and call state.parse()
	def loadState(self):
		pass

	# Saves state data alongside other important data, like the member list and cheats
	# Members and cheats can be loaded individually (useful with GUI mode) or all at once
	#   from file (useful with model training applications)
	def saveState(self):
		pass

	# Primary simulation operation
	# Takes the current state and calculates a distribution of all possible child states
	def process(self):
		# Array of (state, chance) tuples to represent the outcome distribution
		output = []

		# Check for start of round components
		if (self.state.player == self.state.first):
			pass	# Need to duplicate a state above

	# Dummy function ideas for future reference
	# def getMemberPosition(self, memberID): pass
	# def getMemberState(self, position, memberID): pass
	def getCastingMember(self): pass
	def initMember(self): pass	# also loadMember