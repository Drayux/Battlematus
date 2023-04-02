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

from json import load, loads, dump
from json.decoder import JSONDecodeError as JSONError
from os import path as ospath
from random import uniform

from state import State, Member
from datatypes import Position, Phase, Spell, Stats, Pip
from util import loadJSON

class Simulation:
	def __init__(self, path = None):
		# self.state = None
		self.stats = {}		# Dict of member stats (key: member_id;  value: <types.Stats>)
		self.spells = {}	# Dict of spells loaded to memory (key: spell_id;  value: <types.Spell)

		# -- NOT IMPLEMENTED UNTIL MUCH LATER --
		# Likely to be reformatted completely (so we don't run a loop on every action)
		self.pvp = False	# Alternative damage calculations and round handling for pvp
		self.cheats = {}	# Dict of <types.cheat>

		if isinstance(path, str): self.load(path)
		else: self.state = State()

	# Load the simulation data from a file
	# TODO CREATE DIRECTORY AND FILETYPE ASSUMPTION
	def load(self, path):
		data = None
		print("path:", path)
		try: data = loadJSON(path)
		except ValueError:
			print("WARNING: Simulation data could not be parsed from json string or path")
			return

		# Initialize the state
		self.state = State(data["state"])
		for mID, mState in self.state.members.items():
			self.loadStats(mID, mState)
	
	# Saves state data alongside other important data, like the member list and cheats
	# Members and cheats can be loaded individually (useful with GUI mode) or all at once
	#   from file (useful with model training applications)
	# TODO CREATE DIRECTORY AND FILETYPE ASSUMPTION
	def save(self, path):
		# Define the output file structure
		# loads(dumps(state)) is a bit weird, but an easy way to convert our class to a dict using our method
		# ^^We don't want to save all of the attributes of the simulation class
		data = {
			"state": loads(str(self.state))
		}

		with open(path, "w") as f:
			json.dump(data, f)
	
	# Load the stats associated with a state member
	# Returns reference to data stored in self.stats dict
	def loadStats(self, memberID, memberState):
		# Parse memberID into path
		# TODO: Make sure this works on windows
		partialPath = memberID.replace(".", "/") + ".stats"
		path = ospath.join(".", "members", partialPath)
		print("Loading member stats from", path)

		# Create the stats object
		data = None
		try: 
			with open(path) as f: data = load(f)
		except (FileNotFoundError, JSONError):
			print(f"WARNING: Stats data {path} could not be parsed")

		stats = Stats(data)
		self.stats[memberID] = stats

		# Populates unset values with respect to stats in the state (not likely to be called if coming from loadData)
		if memberState.health < 0: memberState.health = stats.health
		# if memberState.mana < 0: memberState.mana = stats.mana
		if memberState.amschool == Pip.NONE: memberState.amschool = stats.amschool
		if memberState.deck is None: memberState.deck = stats.deck.copy()
		if memberState.side is None: memberState.side = stats.side.copy()

		# Load the cheats associated with the stats object
		print("TODO: [simulation.py] loadStats(): generate cheat types and save them to sim data")

		return stats

	# Load a spell file (spells will be loaded as needed, not at initialization)
	# Returns reference to loaded spell
	def loadSpell(self, spellID):
		partialPath = spellID.replace(".", "/") + ".spell"
		path = ospath.join(".", "spells", partialPath)
		print("Loading spell from", path)

		# Create the spell object
		data = None
		try: 
			with open(path) as f: data = load(f)
		except (FileNotFoundError, JSONError):
			print(f"WARNING: Spell data {path} could not be parsed")
			return
		spell = Spell(data)
		self.spells[spellID] = spell

		# TODO: Figure out what to do with modifier types
		#    ^^Pretty sure they will be stored in an array in the Spell() class and referenced via index

		return spell

	# For use with building a state "from scratch"
	# Loads member stats and adds an entry into the state
	def addMember(self, memberID: str):
		assert self.state is not None
		newMember = Member(None)
		self.state.members[memberID] = newMember
		self.loadStats(memberID, newMember)

	# --- CORE SIMULATION OPERATION ---

	# Primary simulation operation
	# Takes the current state and calculates a distribution of all possible child states
	def process(self):
		# Array of (state, chance) tuples to represent the outcome distribution
		output = []

		# Check for start of round components
		if (self.state.player == self.state.first):
			pass	# Need to duplicate a state above

	# ---------------------------------

	# Dummy utility (API) function ideas for future reference
	# def getMemberPosition(self, memberID): pass
	# def getMemberState(self, position, memberID): pass
	def getCastingMember(self): pass


# Helper class for the DeltaTree
# Implements core tree structure
class Node:
	# def __init__(self, parent, data):
	def __init__(self, deltas, phase = -1):
		# assert (parent is None) or isinstance(parent, Node)
		# parent.addChild(self)
		self.deltas = deltas
		self.children = None
		self.phase = phase

	def __iter__(self):
		if self.children is None: raise StopIteration
		for tup in self.children:
			yield tup

	# 'Chance' should be the fractional probability of selection (i.e. children should total to 1.0)
	def newChild(self, deltas, chance = 0, phase = -1):
		self.addChild(Node(deltas, phase), chance)
	
	def addChild(self, node, chance = 0):
		assert isinstance(node, Node)
		if self.children is None:
			self.children = []
		self.children.append((node, chance))


# Class to represent a 'state delta tree'
# This is the return type of a state progression evaluation
# Contains a copy of the original state before the conversion
#   and a tree of delta lists, split for each stochastic element
# Delta list is [(value, delta)]
# ^^For static elements such as charms, use a value of -1 to indicate 
#   that the charm has been removed (0 for no change; 1 for added)
# This type should not be necessary to import in other files

# NOTE: Deltas should generally be represented before calculation
# Specifically relevant with pips: specify only the spell type and cost in the delta list
# For damage, the multiplier can be calculated but the change should be left 'raw' ??
# Majority of the calculation in Simulation.process() should be chance distributions
class DeltaTree:
	def __init__(self, state):
		assert isinstance(state, State)
		self.state = state.copy()		# TODO needs deepcopy or helper function
		self.root = Node(None)
	
	def select(self, gen = None):
		if gen is None: 
			gen = uniform(0, 1)		# TODO should be uniform random variate 0 <= x <= 1 ??
			
		total = 0
		for i, child in enumerate(self.root):
			total += child[1]
			if total >= gen: return i	# Change this to > if the variate cannot be exactly 1
		
		print(f"WARNING: Delta list weights add up to less than 1 (Phase: {self.root.phase})")
		return 0

	# TODO
	# Selection is index of child to apply
	# All delta list items are parsed and modified in the state
	# self.root becomes the new child (after the effects have been applied)
	#    (we only apply the effects of the child so root could be None but doesn't actually need to be updated)
	def apply(self, selection):
		raise NotImplementedError("DeltaTree.apply()")