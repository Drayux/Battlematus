# state.py
# Structure for the combat state vector (and subsequent sub-structures)
# Supports JSON-encoded I/O
# Members can be initalized from file

from collections import deque

from util import encodeJSON, loadJSON
from datatypes import Pip, Status, EventType

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
		self.round = data.get("round", 0)		# NOTE: Pips should be acquired at the start of the player turn, if applicable
		self.first = data.get("first", 0)		# Should be either 0 or 4 (players or npcs first)

		# TODO: Handle pet maycasts (from member stats)
		self.eventidx = data.get("eventidx", 0)
		self.events = []					# List of pending "cast events" for the round
		for event in data.get("events", []):
			self.events.append(Event(event))

		# NOTE: Each member must have a unique member ID
		self.position = data.get("position")	# Array of member IDs to define cast order
		if self.position is None: self.position = [None for x in range(8)]
		# self.interrupts = data.get("interrupts", [])	# List of 
		
		# Init state objects
		self.bubble = data.get("bubble")		# Active global (represented as ref to Modifier via spellID)
		self.members = {}		# Dict of (member_id, member_data) : Allows >8 member states for battles that require it
		for memberid, memberdata in data.get("members", {}).items():
			self.members[memberid] = Member(memberdata)
	
	def __str__(self):
		return encodeJSON(self)

	# Gets the next event from the state (updates relevant fields)
	# Returns None if end of round
	def getEvent(self):
		# Always points to the "upcoming event"
		# AKA we insert interrupt events at this index and do not change the index
		if self.eventidx == len(self.events): return None
		event = self.events[self.eventidx]
		self.eventidx += 1

		# Skip events meant for following rounds
		if event.delay == 0: return event
		return self.getEvent()


# -- CORE MEMBER OBJECT --
class Member:
	# Atributes to parse from stats while loading:
	#    Health, Mana, Deck (main and side and archmastery selection)
	#	 Anything that can be a bonus, such as pips
	#    Everything else we can init to 'zero'
	def __init__(self, data = None):
		if data is None: data = {}
		assert isinstance(data, dict)

		# Init state primitives
		self.health = data.get("health", -1)
		# self.mana = getattr(data, "mana", -1)		# TODO if using mana, consider specification for inifinite mana (PvP / Mob)

		# Pips are enum type, so cast the value from the raw data
		pipsarr = [Pip(p) for p in data.get("pips", [])]
		if len(pipsarr) > 0:
			self.pips = [Pip.NONE for x in range(7)]
			self.gainPips(pipsarr)
		else: self.pips = None

		self.shads = data.get("shads", 0)
		self.shadprog = data.get("shadprog", 0)		# Current progress towards the next shadow pip (float 0 <= prog < 1)

		# Status is addressed by datatypes.Status
		self.status = data.get("status", [0, 0, 0])

		# Reference to Modifier types within spell_id
		self.aura = data.get("aura")
		self.charms = deque(data.get("charms", []))
		self.wards = deque(data.get("wards", []))
		
		self.tokens = deque()
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

		# Should the target be ressurected (base spell is 20%, so this would be 0.2)
		self.ressurection = data.get("ressurection", 0)

	def __str__(self):
		return encodeJSON(self)
	
	# Give the member new pips
	# NOTE: Assume array already sorted!
	# NOTE: Pips should only be via this method
	def gainPips(self, piparr):
		# Determine current pip count
		count = 0
		noobIdx = -1	# If a noob pip was found, save the index here
		for i, p in enumerate(self.pips):
			if p == Pip.NONE:
				count = i
				break
		
		for i, p in enumerate(piparr):
			idx = i + count
			if idx >= 7: 
				# TODO: Attempt to convert noob pip to power pip
				print("TODO: [state.py] gainPips(): pip conversion upon overflow")
				break
			self.pips[idx] = p
		
		self.sortPips()

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
	
	# Utility function for "counting" pips
	# Returns casting potential (with mastery, without mastery)
	def countPips(self):
		mastery = 0
		nonmastery = 0

		for p in self.pips:
			match p:
				case 9: break 
				case 0: 
					mastery += 1
					nonmastery += 1
				case other: 
					# total += (2 if mastery else 1)
					mastery += 2
					nonmastery += 1

		return (mastery, nonmastery)

	# Get the distribution of spells still in the deck
	# Use this to predict what is more or less likely to be drawn (probably for AI agent)
	# side -> Whether to use main deck or TCs
	def spellDistribution(self, side = False):
		dist = {}

		deck = self.side if side else self.deck
		for spell in deck:
			count = dist.get(spell, 0)
			dist[spell] = count + 1

		# TODO: Consider alteration of the return type as necessary
		return dist


# -- CAST EVENT OBJECT --
# TODO: Adjust for new structure
class Event:
	# Structure to manage cast events
	# Contents of data override other params
	def __init__(self, member = None, data = None):
		if data is None: data = {}

		self.type = data.get("type", EventType.PLAN)
		self.delay = data.get("delay", 0)
		self.member = data.get("member", member)
		self.spell = data.get("spell", None)

		# How the event should be ordered if carried across rounds
		# I really hate this implementation but I cannot think of anything that I like better
		# Extra event order possibilities: Start/end of round, start/end of turn, or interrupt
		self.local = data.get("local", True)		# Event happens before / after cast (alternatively the entire round)
		self.before = data.get("before", True)		# Event happens before local / global

		# NOTE: Event ordering refactor (for some point in the future)

		# I should be able to construct the event queue and then sort the events
		# So, each event needs some sort of value upon which to sort...
		# Fortunately, we know the order at creation, so this is obtainable.

		# Each value will be two parts: First is the index of the member the event is associated with
		# (as we cannot sort by the memberID itself without checking the position of each member: the
		# order is stored via the location in state.position)
		# And the second part, being the time relative to the member's turn

		# Each member turn should consist of at most one "CAST" event--this is time zero.
		# This value can be inferred for any situation I imagine possible (cheats we just know via
		# the cheat scripting, and nightbringer can be assumed to be -1, etc.)
		# Round events are before or after all members, so we use either -1 or some big number like 999

		# Finally, we have the process necessary to verify cross-round events:
		# Each time one of these events is about to be inserted, we must verify that the positions
		# array holds the member ID relevant to the event. (I.E. if our first ordering component is
		# 2, then we verify state.position[2] == self.member) else we throw out the event
	
	def __str__(self):
		return encodeJSON(self)