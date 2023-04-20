# Class to represent the battle structure
# Core component of state in, state distribution out API

# One iteration of the simulation is the entire completion of one participant's action
#	^^This allows an AI to specify action policies for all members of combat

from json import load, loads, dump
from json.decoder import JSONDecodeError as JSONError
from os import path as ospath
from random import seed, random, uniform

from state import State, Member, Event
from datatypes import Position, Phase, Spell, Stats, Pip, EventType
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

	def __repr__(self):
		ret = "--------- BATTLE SIMULATION ---------"

		# Get the casting player
		casterID = ""
		try: casterID = self.state.events[self.state.eventidx].member
		except IndexError as _: pass

		# Print the battle circle
		members = []
		for i, m in enumerate(self.state.position):
			if i == 0: ret += "FRIENDLIES:  "
			elif i == 4: ret += "\nOPPONENTS:  "
			if m is None: continue
			
			# name = "'" + self.stats[m].name + "'"
			name = self.stats[m].name
			ret += ('\033[4m' if m == casterID else '') + name + ('\033[0m' if m == casterID else '') + "   "
			members.append(m)
		
		# Print the members
		ret += "\n-------------------------------------"
		# ret += "MEMBERS:"
		for i, mID in enumerate(members):
			if i > 0: ret += "\n"

			mstats = self.stats[mID]
			mstate = self.state.members[mID]

			# Pips string
			pipsstr = ""
			for p in mstate.pips:
				if p == Pip.NONE: break
				pipsstr += str(p) + " "

			ret += f"\n\033[1m{mstats.name}\033[0m"
			ret += f"\nHealth: {mstate.health} / {mstats.health}"
			ret += f"\nPips: {pipsstr} {mstate.countPips()}"
		
		return ret

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

		if memberState.pips is None:
			memberState.pips = [Pip.NONE for x in range(7)]
			memberState.gainPips(stats.startpips)

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
	# If pos < 0: don't put member into battle circle
	def addMember(self, memberID: str, pos = -1):
		assert self.state is not None
		newMember = Member(None)
		self.state.members[memberID] = newMember
		self.loadStats(memberID, newMember)
		if pos <= 0: 
			print("WARNING: New member created without position in battle!")
			return
		
		assert self.state.position[pos] == None
		self.state.position[pos] = memberID

	# If a member dies, their state resets
	# Use health = -1 to ressurect to "full"
	# Use health > 0 if they reset to a certain value
	# NOTE: This check should be ran when damage is dealt
	#       We want to assume that the member has the state we want if ressurected
	def resetMember(self, memberID, health = 0):
		mstateOld = self.state.members[memberID]
		mstateNew = Member()

		# Important overrides
		mstateNew.health = health
		memberState.pips = [Pip.NONE for x in range(7)]

		# Copy over values that do not reset
		mstateNew.amschool = mstateOld.amschool
		mstateNew.deck = mstateOld.deck
		mstateNew.side = mstateOld.side
		

	# --- CORE SIMULATION OPERATION ---

	# Primary simulation operation
	# Takes the current state and calculates a distribution of all possible child states
	# ^^Iteration size is *one* member turn
	def process(self):
		# output = DeltaTree(self.state)
		raise NotImplementedError("Delta tree processing")

	# Simulate one player round via means of random selection, and update the state immediately
	# This function exists mostly for the sake of debugging, and determining the structure for the deltatree
	# selection --> tuple (or array of tuples) for spell selection (spell idx, target idx)
	#    ^^if enchant, array of tuples should be used; target idx becomes index of spell (assuming enchant is not yet consumed)
	# Return True if battle should continue, else False
	def simulate(self, selection = None, randseed = None):
		if isinstance(randseed, int): seed(seed)

		# -- Update round components --
		event = self.state.getEvent()
		evaluation = self.evalState()
		if event is None: 
			self.updateRound()

			# Only check for victory at the start of a round
			# Possible for a player to be beguiled and cast rebirth, healing enemy team
			if evaluation >= 1:
				print("Player victory!")
				return False
			if evaluation <= -1:
				print("Enemy victory :(")
				return False

			event = self.state.getEvent()

		# If event is still none, the battle is over but we've failed to detect that
		assert event is not None

		# Get the caster of interest
		caster = event.member					# MemberID of player's turn that we are simulating
		cstate = self.state.members[caster]		# Reference to caster's state (within the full sim state)
		cstats = self.stats[caster]				# Reference to the caster's stats

		print(f"ROUND: {self.state.round}")	# TODO: Add caster index to output
		print("CASTER:", caster)
		print("EVAL:", evaluation)
		print()

		# TODO: Somewhere in here, make sure the member can cast at all (they might be out of health)

		# -- PHASE 2 (Planning phase) --
		print("-- PHASE TWO : PLANNING --")
		# TODO: Determine / present acceptable cast choices
		# TODO: Allow manipulation via discards or enchants
		# ^^loop
		# TODO: Gather list of targets

		# -- PHASE 3 (Token handling) --
		print("-- PHASE THREE : TOKENS --")
		# TODO: Update health (and charms/wards) from tokens (processIncoming() for each)

		# -- PHASE 4 (Cast) --
		print("-- PHASE FOUR : CAST --")
		# TODO: Check for stun
		# TODO: Validate pip cost (can the spell be cast)
		# TODO: Verify / update targets (checks for confused / beguiled)
		# TODO: Handle dispels and accuracy modifiers
		# TODO: Consume pips if dispel or success
		# TODO: Perform critical check

		# -- PHASE 5 (Spell Processing) --

		
	# -- SIMULATION OPERATION UTILITY --

	# Trivial state evaluation operation
	# Returns 1 if players have won or -1 if enemy has won
	# Else the evaluation will be between -1 and 1
	# NOTE: Simulation member function because future implimentations require a reference to member stats
	def evalState(self):
		friendlyHealth = 0
		enemyHealth = 0

		# These will be 4 in 99.9% of cases
		# TODO: Hall of heros :)
		numFriendly = 4
		numEnemy = 4

		# TODO: Add "potential damage" multiplier

		index = 0

		# Determine strength of friendlies
		for x in range(numFriendly):
			member = self.state.position[index]
			index += 1
			if member is None: continue
			
			health = self.state.members[member].health
			assert health >= 0
			friendlyHealth += health

		# Determine strength of enemies
		for x in range(numEnemy):
			member = self.state.position[index]
			index += 1
			if member is None: continue
			
			health = self.state.members[member].health
			assert health >= 0
			enemyHealth += health
		
		# It is possible that both sides die in the same round
		# The game considers this as an enemy victory
		total = friendlyHealth + enemyHealth
		if total == 0: return -1

		return (friendlyHealth - enemyHealth) / total

	# Called when a new round is started
	# Kills off dead members
	# Generates predetermined cheat interrupts
	# Updates battle components such as primary pip gain
	def updateRound(self):
		self.state.round += 1

		# Kill dead members and generate primary events
		eventsNew = []
		posLen = len(self.state.position)
		base = self.state.first
		for x in range(posLen):
			idx = (base + x) % posLen

			memberID = self.state.position[idx]
			if memberID is None: continue

			mstate = self.state.members[memberID]
			mstats = self.stats[memberID]

			# Remove the NPC if 'defeated'
			if mstate.health <= 0:
				# Human players remain in the battle (but not minions)
				if not mstats.player:
					self.state.position[idx] = None
				# TODO: else reset state
				continue

			# Add the planning phase
			eventsNew.append(Event(memberID))

			# Update the member's state
			# -- PIPS --
			piparr = []		# Pips to gain (for Member.gainPips() )

			# TODO: Check for pip bonus stat (thinking sugar rush cheat from those cube bois)

			# Generate pip based off of powerpip stat
			# TODO: Determine method for bosses lie hades who conditionally gain an extra with consideration for his pp chance
			print(f"Generating pip for member {memberID} with chance {mstats.powerpip}", end = ": ")
			if mstats.powerpip > random(): 
				piparr.append(Pip.POWER)
				print("POWER")
			else: 
				piparr.append(Pip.BASIC)
				print("BASIC")

			# TODO: Check for pip maximum

			mstate.gainPips(piparr)

			# TODO: Convert to powpip to ampip if conditions are met (else update progression)
			# TODO: Generate shadow pip if conditions are met (else update progression)


		# Update round-transient events
		# This is the implementation that I hate, but in reality, it's akin to insertion sort
		for event in self.state.events:
			if event.delay > 0:
				event.delay -= 1

				if not event.local:
					# Event happens at the start or end of round
					if event.before: eventsNew.insert(0, event)
					else: eventsNew.append(event)
					continue

				# Find the index in which to insert the event
				insertIdx = -1
				for idx, e in enumerate(eventsNew):
					if not (e.type == EventType.PLAN or e.type == EventType.PASS or e.type == EventType.CAST): continue
					if e.member == event.member:
						# Adjust index if effect cast is before or after turn
						# TODO: This will currently reverse the order of multiple "after casts"
						insertIdx = idx + (0 if e.before else 1)
						break
				
				# If this fails, then the member was not in the fight and the interrupt is invalidated
				if insertIdx >= 0: eventsNew.insert(insertIdx, event)

		# TODO: Handle cheats (ex: belloq's start of round cheat)

		self.state.events = eventsNew
		self.state.eventidx = 0

	# Handle outgoing effects (damage pretty much)
	# Requires reference to caster's state and caster's stats
	def processOutgoing(self, cstate, cstats):
		pass

	# Handle incoming effects (also damage)
	# Requires reference to targets's state and targets's stats
	def processIncoming(self, tstate, tstats):
		pass

	# Determine if combat is over
	# Returns negative if 'player' victory; 0 if battle is still going; positive if 'NPC' victory
	# UPDATES state.player
	# TODO: Refactor to split nextCaster() mechanic and win condition
	def getNextCasterOLD(self, length = 8):
		state = self.state		# Reference for clarity
		if length < 0: length = len(state.position)

		dead = 0				# Number of 'dead' players per side
		x = state.player
		for i in range(1, length):
			idx = (x + i) % length
			player = state.order[idx]
			if player is None:
				dead += 1
				
			# Wizard's engine finishes all casts per 'side' even if battle was already won
			else:
				state.player = idx
				return 0
			
			# Check dead counter
			if dead >= 4: return -1 if x <= 3 else 1
			elif i % 4 == 3: dead = 0
		
		print("WARNING: battleWon() did not return in the loop!")
		return 0


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


# Class that represents a change to a state
# type -> datatypes.DeltaType representing the modification to the attribute
# attr -> Attribute to be modified
# data -> The value relevant to the specified change
# class Delta:
# 	def __init__(self, type, attr, data): pass

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
		self.state = state		# TODO needs deepcopy or helper function (leaning to copying upon apply())
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