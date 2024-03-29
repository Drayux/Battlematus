# state.py
# Structure for the combat state vector (and subsequent sub-structures)
# Supports JSON-encoded I/O
# Members can be initalized from file

from collections import deque
from random import random

from util import encodeJSON, loadJSON
from datatypes import Pip, StatusEffect, EventType

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
	# TODO: When implimenting cast agent history, embed said data within THIS class
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
	# TODO: Missing shadow spell components including transformations, dark nova, and backlash
	# TODO: Track spells such that a TC cannot be discarded the same round it is drawn
	def __init__(self, data = None):
		if data is None: data = {}
		assert isinstance(data, dict)

		# Init state primitives
		self.health = data.get("health", -1)
		# self.mana = getattr(data, "mana", -1)		# TODO if using mana, consider specification for inifinite mana (PvP / Mob)

		# DEPRICATED PIPS SYSTEM
		# Pips are enum type, so cast the value from the raw data
		# pipsarr = [Pip(p) for p in data.get("pips", [])]
		# if len(pipsarr) > 0:
		# 	self.pips = [Pip.NONE for x in range(7)]
		# 	self.gainPips(pipsarr)
		# else: self.pips = None

		self.pips = data.get("pips", None)

		self.shads = data.get("shads", 0)
		self.shadprog = data.get("shadprog", 0)		# Current progress towards the next shadow pip (float 0 <= prog < 1)

		# Status is addressed by datatypes.StatusEffect
		self.status = data.get("status", [0, 0, 0])

		# Reference to Modifier types within spell_id
		self.aura = data.get("aura")
		self.charms = deque(data.get("charms", []))
		self.wards = deque(data.get("wards", []))
		
		self.tokens = deque()
		tokens = data.get("tokens")
		# TODO: Apparently tokens can also be protected so we need to handle that
		if isinstance(tokens, list):							# TODO: Determine what stats should be tracked (such as pierce??)
			for t in tokens: self.tokens.append((t[0], t[1]))	# Tokens are tuple of (Rounds remaining, damage)

		# Deck is array of spell_ids, in the shuffled order
		# The first seven cards are the client's hand, the latter are available to draw
		self.deck = data.get("deck")		# If None, parse from member stats during initState()
		self.side = data.get("side")		# If None, parse from member stats during initState()
		self.hand = data.get("hand", 7)		# Scalar to specify the number of cards in the player's hand (all deck manipulations happen via this class)

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
	
	# Give the member new pips from a list
	# Assume input list specifies precedence
	# NOTE: The precedence of giving school pips is unknown
	def gainPips(self, piparr):
		# Count the number of pips currently owned
		count = 7
		for x in self.pips:
			if count <= 0: return
			count -= x
		
		# Obtain pips (TODO: Consider sorting this with a known order?)
		for i, pip in enumerate(piparr):
			if i >= count: return
			assert isinstance(pip, Pip)
			self.pips[pip.value] += 1

	# TODO: Generate pips for the member (traditionally start of round)
	# Optional variables are available in the member state
	# TODO: Add components for archmastery
	def generatePips(self, count, chance = -1):
		pass

	# Give the member new pips
	# NOTE: Assume array already sorted!
	# NOTE: Pips should only be via this method
	def gainPipsOLD(self, piparr):
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

	# TODO: PIP CONSUMPTION UPON SPELL CAST
	# Will consume pips up to a spell cost (even if spell cost exceeds possessed pips)
	# Returns scalar value of pips consumed (basically only relevant for X-cost spells)
	def consumePips(self, cost, mastery = True, scost = 0, apply = False):
		# TODO: Anything with archmastery pips or X casting cost
		# TODO: Shadow pip consumption

		total = cost[0]
		power = 0
		if mastery: power = min(self.pips[1], int(total / 2))
		basic = total - (2 * power)

		# Start by consuming basic pips, using powers as overflow
		if basic > self.pips[0]:
			power += basic - self.pips[0]
			basic = self.pips[0]

		if power > self.pips[1]:
			return -1
		
		if apply:
			self.pips[0] -= basic
			self.pips[1] -= power

		return basic + (power * (2 if mastery else 1))


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

	# Returns index of spell in hand matching a certain id (array if multiple or None if nothing)
	# enchants -> Whether to include enchanted versions (-1 no enchants, 0 both, 1 only enchants)
	def getSpellIndex(self, spellID, enchants = 0):
		ret = []
		for i, spell in self.deck:
			if i >= self.hand: break

			incl = enchants * (1 if isinstance(spell, tuple) else -1)
			if incl >= 0: ret.append(i)
		
		if len(ret) == 0: return None
		if len(ret) == 1: return ret[0]
		return ret

	# Discard a spell at the specified index
	# idx -> Index of spell to discard
	# spellData -> Reference to simulation's spells dict (for determining if spell can be discarded)
	# Returns True if success, else False
	def discardSpell(self, idx, spellData):
		pass

	# Enchant a spell at the specified index
	# idxBase -> Index of spell to be enchanted
	# idxEnch -> Index of the enchant spell to be applied to the spell at idxBase
	# spellData -> Reference to simulation's spells dict (for determining if spell can be discarded)
	# Returns True if success, else False
	def enchantSpell(self, idxBase, idxEnch, spellData):
		pass

	# Get the distribution of spells still in the deck
	# Use this to predict what is more or less likely to be drawn (probably for AI agent)
	# side -> Whether to use main deck or TCs
	def calcSpellDist(self, side = False):
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
		self.target = data.get("target", None)

		# How the event should be ordered if carried across rounds
		# I really hate this implementation but I cannot think of anything that I like better
		# Extra event order possibilities: Start/end of round, start/end of turn, or interrupt
		self.local = data.get("local", True)		# Event happens before / after cast (alternatively the entire round)
		self.before = data.get("before", True)		# Event happens before local / global
		# self.order  <--  Primary ordering scalar
		# self.priority  <--  Secondary ordering scalar

		# NOTE: Event ordering refactor (for some point in the future)

		# I should be able to construct the event queue and then sort the events
		# So, each event needs some sort of value upon which to sort...
		# Fortunately, we know the order at creation, so this is obtainable.

		# Each value will be two parts: First is the index of the member the event is associated with
		# (as we cannot sort by the memberID itself without checking the position of each member: the
		# order is stored via the location in state.position)
		# And the second part, being the time relative to the member's turn

		# Each member turn should consist of at most one "CAST/PLAN" event--this is time zero.
		# This value can be inferred for any situation I imagine possible (cheats we just know via
		# the cheat scripting, and nightbringer can be assumed to be -1, etc.)
		# Round events are before or after all members, so we use either -1 or some big number like 999

		# Finally, we have the process necessary to verify cross-round events:
		# Each time one of these events is about to be inserted, we must verify that the positions
		# array holds the member ID relevant to the event. (I.E. if our first ordering component is
		# 2, then we verify state.position[2] == self.member) else we throw out the event
	
	def __str__(self):
		return encodeJSON(self)