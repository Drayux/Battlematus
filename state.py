# state.py
# Structure for the combat state vector (and subsequent sub-structures)
# Supports JSON-encoded I/O
# Members can be initalized from file

from util import encodeJSON, loadJSON
from datatypes import Pip, Status

# NOTE: For awhile I had been really committed to this idea of having defaults that wouldn't be stored
#		if the value were unchanged. I liked this idea in hopes that it would save the memory usage
# 		when considering many many copies of states. The problem however, is that in a language like
# 		Python, it is impractical to do this as every check for a value would go through twice as many
#		operations. I had then considered this with regard to other traits like copying states, saving
#		states, and so on, but I have ruled them out for similar reasons.
#
#		At this point, the benefit to what remains of this system is backwards compatibility, so that
#		old state files can be loaded into a version of this sim with new battle components.

# -- CORE STATE OBJECT --
class State:
	# Argument: 'data' can be...
	#   None for new state (with defaults)
	#   JSON-encoded string with partial (or full) data
	#   Filepath to JSON-encoded string
	def __init__(self, data = None):
		if data is None: data = {}
		if isinstance(data, str):
			print("WARNING: Attempting to load state from unparsed string")
			try: data = loadJSON(data)["state"]
			except (ValueError, KeyError):
				print("WARNING: State data could not be parsed from json string or path")
		assert isinstance(data, dict)
		
		# Init state primitives
		self.round = data.get("round", 1)		# NOTE: Pips should be acquired at the start of the player turn, if applicable
		self.first = data.get("first", 0)		# Should be either 0 or 4 (wizards first or npcs first)
		self.player = data.get("player", 0)		# Index of casting participant

		# TODO: "Next player" should be parsed from order and a list of pending interrupts
		self.order = data.get("order")			# Array of member IDs to define cast order (should be: [None for x in range(8)])
		if self.order is None: self.order = [None for x in range(8)]
		
		# Init state objects
		self.bubble = data.get("bubble")		# Active global (represented as ref to Modifier via spellID)
		self.members = {}		# Dict of (member_id, member_data) : Allows >8 member states for battles that require it
		for memberid, memberdata in data.get("members", {}).items():
			self.members[memberid] = Member(memberdata)
	
	def __str__(self):
		return encodeJSON(self)


# Modifer moved to datatypes.py
# ^^spell should be specified in there as well

# -- CORE MEMBER OBJECT --
class Member:
	# Atributes to parse from stats while loading:
	#    Health, Mana, Deck (main and side and archmastery selection)
	#    Everything else we can init to 'zero'
	def __init__(self, data = None):
		if data is None: data = {}
		assert isinstance(data, dict)

		# Init state primitives
		self.health = data.get("health", -1)
		# self.mana = getattr(data, "mana", -1)		# TODO if using mana, consider specification for inifinite mana (PvP / Mob)

		# Pips are enum type, so cast the value from the raw data
		pips = data.get("pips")
		if pips is None: self.pips = [Pip.NONE for x in range(7)]
		else:
			assert len(pips) == 7
			self.pips = [Pip(x) for x in pips]

		self.shads = data.get("shads", 0)
		self.shadprog = data.get("shadprog", 0)		# Current progress towards the next shadow pip (float 0 <= prog < 1)

		# Status is addressed by datatypes.Status
		self.status = data.get("status", [0, 0, 0])

		# Reference to Modifier types within spell_id
		self.aura = data.get("aura")
		self.charms = data.get("charms", [])
		self.wards = data.get("wards", [])

		self.tokens = []
		tokens = data.get("tokens")
		if isinstance(tokens, list):							# TODO: Determine what stats should be tracked (such as pierce??)
			for t in tokens: self.tokens.append((t[0], t[1]))	# Tokens are tuple of (Rounds remaining, damage)

		# Deck is array of spell_ids, in the shuffled order
		# The first seven cards are the client's hand, the latter are available to draw
		# The shuffle should be randomized for every "battle" but consistent so that states at depth
		#    can be accurately evaluated
		# TODO: We may need some sort of way for reshuffle to keep the same seed??
		#    ^^In retrospect, probably not as only one transition will be required for a given tree
		#    Other trees are likely to differ as different spells may have been cast before a reshuffle
		# TODO: Consider a system for the future AI agent that can weight based off of what might be drawn,
		#    and not what is drawn. (If using this alongside a battle, for example)
		#    An ML model can likely be trained without this consideration
		# NOTE: Deck shuffling to be handlied 'as needed' via one iteration of fisher-yates
		self.deck = data.get("deck")		# If None, parse from member stats during initState()
		self.side = data.get("side")		# If None, parse from member stats during initState()

		# Archmastery components
		self.amschool = Pip(data.get("amschool", Pip.NONE.value))	# The selected archmastery school (note that Pip.BASIC and Pip.POWER are invalid selections)
		self.amprog = data.get("amprog", 0)							# Progress toward next archmastery pip (float; > 1.0 means pip is stored as per the game mechanic)

		# -- NOT IMPLEMENTED UNTIL MUCH LATER --
		# Threat is the likelihood of an enemy to target the member
		# Various actions in the battle (such as attacking or casting charms)
		#    will change this value, but it does not actually impact any other portion
		#    of the state beyond what the AI selects for the state transition
		# TODO: Determine a value for this that would be accurate to the ingame system
		#    is it random, does it limit ability to cast at all (like with pacify)?
		self.threat = data.get("threat", 0)

	def __str__(self):
		return encodeJSON(self)
	
	# Counting sort for player pips (makes consumption logic trivial)
	def sortPips(self, length = 7):
		assert len(self.pips) == length
		counts = [0 for x in range(len(Pip.__members__))]		# Should be 10
		for pip in self.pips: counts[pip.value] += 1

		countIdx = 0
		orderIdx = 0
		while orderIdx < length:
			if counts[countIdx] == 0: 
				countIdx += 1
				continue
			self.pips[orderIdx] = Pip(countIdx)
			orderIdx += 1
			counts[countIdx] -= 1
	
	# Get the distribution of spells still in the deck
	# Use this to predict what is more or less likely to be drawn (probably for AI agent)
	# side -> Whether to use main deck or TCs
	def spellDistribution(self, side = False):
		dist = {}

		deck = self.side if side else self.deck
		for spell in deck:
			count = getattr(dist, spell, 0)
			dist[spell] = count + 1

		# TODO: Consider alteration of the return type as necessary
		return dist
