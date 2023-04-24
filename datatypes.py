# Miscellaneous types relevant to various portions of the simulation

from enum import IntEnum
# from util import encodeJSON

# -- SIMULATION CORE --

# Battle sigil member position
# Enum values are array indices
class Position(IntEnum):
	# Friendly members
	SUN = 0
	EYE = 1
	STAR = 2
	MOON = 3
	
	# Enemy members
	BLADE = 4
	KEY = 5
	GEM = 6
	SPIRAL = 7


# Enum for the battle stages
# Experimental component, planned use is as a component of the output vector
# These are specific to stochastic elements (many phases have important sub components)
# DeltaTree should consider only the phases: 2, 3, 4, 6, 8, and 9 ( 0 PENDING )
class Phase(IntEnum):
	PIPS = 0		# Handle pip changes
	PLANNING = 1	# Hand manipulation (enchants, discards, and TC draws)
	TOKEN = 2		# "Pre-round" handle DOT / HOT 'tokens'
	CAST = 3		# Handle cast success and target (if stun, beguile, etc ; also consumes accuracy charms ; update pip count)
	# CRITICAL = 4	# If spell can change health values, it can hit critical
	# --- 5 -> 9 : all repeatable (in sequence) ---
	ACTION = 5		# Any spell action with random chance (i.e. damage distribution, charm RNG)
	OUTGOING = 6	# Consume charms and factor crit multiplier, global, caster aura, etc
	BLOCK = 7		# If spell was a critical cast, it might be blocked
	INCOMING = 8	# Consume target wards and factor pierce, block multipler, target aura, etc
	EFFECT = 9		# Apply spell effects (such as DOTs, stuns, pip changes to target, etc)
	# ---------------------------------------------
	ROUND = -1		# Round update mechanics (like incrementing the round number)


# -- MEMBER STATS --

# Enum for class (school) stats
# Int values are tuple (array) positions
class School(IntEnum):
	FIRE = 0
	ICE = 1
	STORM = 2
	LIFE = 3
	DEATH = 4
	MYTH = 5
	BALANCE = 6
	SUN = 7
	MOON = 8
	STAR = 9
	SHADOW = 10


# Enum for healing stat
# Int values are tuple (array) positions
# TODO: Consider repurposing to "direction" (as this still applies to healing)
class Healing(IntEnum):
	IN = 0
	OUT = 1


# -- BATTLE STATE --

# Cast event types
class EventType(IntEnum):
	PLAN = -1		# Associated member should be presented the planning phase
	PASS = 0		# Member has selected pass
	CAST = 1		# Member will cast a spell like normal
	PET = 2			# Member's pet will cast a spell
	INTERRUPT = 3	# Boss performs an interrupt (Member should be none if the cast does not technically occur from the boss, pet maycasts also count here)
	EFFECT = 4		# Secondary spell effect like nightbringer or beguile (or possibly Guardian Angel TODO)

# Simple enum for pips
# School pip sorting order: balance, death, fire, ice, life, myth, storm
class Pip(IntEnum):
	NONE = 9		# Values for pip sorting and precedence
	BASIC = 0
	POWER = 1
	FIRE = 4
	ICE = 5
	STORM = 8
	LIFE = 6
	DEATH = 3
	MYTH = 7
	BALANCE = 2

	def __str__(self):
		match self.value:
			case 0: return "\033[38;5;15m⏺\033[0m"
			case 1: return "\033[38;5;3m⏺\033[0m"
			case 2: return "\033[38;5;52m⏺\033[0m"
			case 3: return "\033[38;5;237m⏺\033[0m"
			case 4: return "\033[38;5;202m⏺\033[0m"
			case 5: return "\033[38;5;87m⏺\033[0m"
			case 6: return "\033[38;5;41m⏺\033[0m"
			case 7: return "\033[38;5;229m⏺\033[0m"
			case 8: return "\033[38;5;129m⏺\033[0m"
			case other: return ""


# Enum for battle status (stunned, beguiled, confused)
# Int values are tuple (array) positions
class Status(IntEnum):
	STUNNED = 0
	BEGUILED = 1
	CONFUSED = 2


# Enum for the various types of manipulation a Delta type can perform to an attribute
class DeltaType(IntEnum):
	NONE = 0	# Take no action (for debugging purposes)
	RESET = 1   # Reset the attribute to the default value (needs some form of config to determine default value)
	ADD = 2		# Append something to a list (like a new blade or shield) / Apply a flat value (like flat damage)
	REMOVE = 3	# Remove an item from a list
	MULT = 4	# Apply a multiplier to a numerical value
	MIN = 5		# Apply a min(a, b) function to a numerical value
	MAX = 6		# Apply a max(a, b) function to a numerical value
	PIP = 7		# Apply a pip manipulation function


# -- SPELL REPRESENTATION --

# Enum for modification object types
# ^^All possible elements that could be changed by a modifier object (charm, global, etc.)
# TODO: Consider refactor for incoming versus outgoing
class ModifierType(IntEnum):
	DAMAGE_MULT = 0		# Outgoing
	DAMAGE_CAP = 1		# Incoming
	ACCURACY_MOD = 3
	HEALING_MULT = 4
	HEALING_CAP = 5
	ABSORB = 6
	RESIST_MOD = 7
	MARK = 8			# For "stun blocks" that are nonfunctional and only an element of a boss' cheat
	# Critical chance
	# pierce
	# pip chance
	# pip impede / bonus??
	# something for dispels
	# flat damage bonus...etc, etc
	# aegis/indeminty


# Enum for spell config action types
class ActionType(IntEnum):
	CHARM = 0
	WARD = 1
	AURA = 2
	GLOBAL = 3
	DAMAGE = 4
	HEAL = 5			# Technically just negative damage, but seperate entries are used because
	#    					negative damage does not roll over (and different modifiers are consumed)
	LIFESTEAL = 6
	MANIPULATE = 7		# Reuse simtypes.Status for which manipulation
	MODIFY = 8			# Generic type for actions that directly modify state like donate power or donate shadow
	# 						that don't have counter spells (i.e. stuns have stun block, but there is no 'pip block')
	ENCHANT = 9			# Reference to modifier type


# Enum for spell config targets
# Spells like iron sultan will receive a list of targets (i.e. use TARGET_ENEMY)
class Target(IntEnum):
	SELF = 0
	TARGET_FRIEND = 1
	TARGET_ENEMY = 2
	ALL_FRIEND = 3
	ALL_ENEMY = 4


# -- CONTAINERS (for static elements) --
# Member stats object
# Holds static member data for reference by Simulation class
class Stats:
	# TODO: Consider system to parse stats from gear (likely a seperate tool to generate stat files)
	# NOTE: For level, if the stats describe a mob, then each rank counts for 5 levels: Basic, Advanced, Elite, (unused), Boss
	# 		^^Take rank * 5 for level of boss, subtract as necessary (R7B --> 5 * 7 = 35 ; R4A --> 5 * 4 - 3 = 17)
	def __init__(self, data = None):
		if data is None: data = {}
		assert isinstance(data, dict)
		statRange = range(len(School.__members__))	# Length of arrays for school-specific stats

		# -- BASIC STATS --
		self.name = data.get("name", "Magic Man")	# 'Pretty' name for UI
		self.level = data.get("level", 1)			# Player level (significant thanks to crit rating 🙂)
		self.health = data.get("health", 500)		# Maximum health
		self.mana = data.get("mana", 10)			# Maximum mana
		self.mastery = data.get("mastery")			# School mastery (multiple masteries possible, hence array)
		if self.mastery is None: self.mastery = [False for x in statRange]

		# -- PRIMARY STATS --
		# NOTE: Some stats (like lunar damage) are implicit with global stats but not displayed in game!

		# Tuples of (damage multiplier, flat damage bonus) per datatypes.School
		# TODO: Consider assertion for damage array being intended length
		damage = data.get("damage")
		if damage is None: self.damage = [(0, 0) for x in statRange]
		else: self.damage = [(x[0], x[1]) for x in damage]
		
		# Tuples of (resist multiplier, flat res) per datatypes.School
		# TODO: Consider assertion for resist array being intended length
		resist = data.get("resist")
		if resist is None: self.resist = [(0, 0) for x in statRange]
		else: self.resist = [(x[0], x[1]) for x in resist]
		
		self.accuracy = data.get("accuracy")		# Spell cast accuracy bonus
		if self.accuracy is None: self.accuracy = [0 for x in statRange]

		# -- SECONDARY STATS (page 1) --
		self.critical = data.get("critical")		# Critical hit rating
		if self.critical is None: self.critical = [0 for x in statRange]

		self.block = data.get("block")				# Critical block rating
		if self.block is None: self.block = [0 for x in statRange]

		self.pierce = data.get("pierce")			# Armor piercing bonus
		if self.pierce is None: self.pierce = [0 for x in statRange]

		self.stunres = data.get("stunres", 0)		# Stun resistance

		healing = data.get("healing", [0, 0])
		self.healing = (healing[0], healing[1])		# Healing I/O multiplier bonus

		# -- SECONDARY STATS (page 2) --
		self.pipcons = data.get("pipcons")			# Pip conversion rating
		if self.pipcons is None: self.pipcons = [0 for x in statRange]

		self.powerpip = data.get("powerpip", 0)		# Chance of obtaining a power pip
		self.shadpip = data.get("shadpip", 0)		# Shadow pip rating
		self.archmastery = data.get("archmastery", 0)	# Archmastery rating

		# -- TERTIARY STATS (not listed on profile) --
		self.startpips = [Pip(p) for p in data.get("startpips", [])]	# Bonus starting pips (array to support basic or power)
		self.maycasts = data.get("maycasts", [])	# Pet maycast cheat IDs (TODO: Add pet happiness casts)

		self.deck = data.get("deck", [])			# Starting deck (important for battle init and reshuffle)
		self.side = data.get("side", [])			# Treasure cards deck

		# Initial deck archmastery selection
		self.amschool = Pip(data.get("amschool", Pip.FIRE.value)) 

		# Miscellaneous simulation implementation components
		self.player = data.get("player", self.mana < 0)


# Object to represent Charm, Ward, etc.
# Basically a simple struct with a type and a value
class Modifier:
	# These do not have explicit files, they are a part of spell files
	def __init__(self, modtype, value):
		self.type = ModiferType(modtype)
		self.value = value
	
	# TODO: Consider some form of...
	# def apply(self, calculation_values): pass

# Object to represent a spell action
# Very basic structure, similar to modifier
class Action:
	def __init__(self, actiontype, target, data, condition = None):
		self.type = ActionType(actiontype)
		self.target = Target(target)
		self.data = data
		self.condition = condition

# Object that houses the full spell data and action set
# Data stored statically and referenced when necessary
# Config file example at 'spells/storm/thundersnake.spell'
class Spell:
	def __init__(self, data):
		assert isinstance(data, dict)

		# Unlike the state representation, we expect spell definitions to be mostly complete
		self.valid = True

		# Name of the spell
		self.spell = data.get("spell")
		if self.spell is None:
			print(f"WARNING: Spell has no spellID entry 'spell'")
			self.valid = False
			return

		# Cast chance (assumed to be 100%)
		self.rate = data.get("rate", 1.0)

		# School associated with the spell
		self.school = data.get("school")
		if self.school is None:
			print(f"WARNING: Spell {self.spell} has no entry 'school'")
			self.valid = False
			return
		
		# Normal pip cost
		self.cost = data.get("cost", [])
		if len(self.cost) != 9:
			print(f"WARNING: Spell {self.spell} has invalid entry for 'cost' (expected array length of 9)")
			self.valid = False
			return

		# Shadow pip cost (assumed to be zero)
		self.scost = data.get("scost", 0)

		# Can the spell be enchanted (Gear and specialty spells cannot, assume this is the case)
		self.enchantable = data.get("enchantable", False)

		# Core spell data
		self.modifiers = {}
		self.actions = []

		# -- Process the spell modifier types --
		mods = data.get("modifiers", {})
		if not isinstance(mods, dict):
			print(f"WARNING: Spell {self.spell} has invalid modifier list (expecting dict or null)")
			self.valid = False
			return

		for modID, modData in mods.items():
			modtype = modData.get("type")
			value = modData.get("value")

			if modtype is None or value is None:
				print(f"WARNING: Spell {self.spell} has invalid modifier '{modID}'")
				self.valid = False
				return
			
			self.modifiers[modID] = Modifier(modtype, value)
		
		# -- Process the spell action types --
		acts = data.get("actions", [])
		if not isinstance(acts, list) or len(acts) < 1:
			print(f"WARNING: Spell {self.spell} has invalid or missing action list")
			self.valid = False
			return
		
		for i, action in enumerate(acts):
			if not isinstance(action, dict):
				print(f"WARNING: Spell {self.spell} has invalid action at index {i}")
				self.valid = False
				return
			
			actiontype = action.get("type")
			target = action.get("target")
			data = action.get("data")		# We don't find out if this is formatted incorrectly until later
			condition = action.get("condition")

			if actiontype is None or target is None or data is None:
				print(f"WARNING: Spell {self.spell} has invalid action at index {i}")
				self.valid = False
				return
			
			self.actions.append(Action(actiontype, target, data, condition))


# Battle cheats type
# Specifies a 'script' to define a cheat condition
# Includes standard boss cheats, as well as pet maycasts
# -- NOT IMPLEMENTED UNTIL MUCH LATER --
class Cheat:
	def __init__(self):
		raise NotImplementedError("Battle cheats")