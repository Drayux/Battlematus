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
	PLANNING = 0	# Handle pip gain and card draw (if member has deck ; also enchants)
	TOKEN = 1		# "Pre-round" handle DOT / HOT 'tokens'
	CAST = 2		# Handle cast success and target (if stun, beguile, etc ; also consumes accuracy charms)
	CRITICAL = 3	# If spell can change health values, it can hit critical
	# --- 4, 5, 6, 7, 8 : all repeatable (in sequence) ---
	ACTION = 4		# Any spell action with random chance (i.e. damage distribution, charm RNG)
	OUTGOING = 5	# Consume charms and factor crit multiplier, global, caster aura, etc
	BLOCK = 6		# If spell was a critical cast, it might be blocked
	INCOMING = 7	# Consume target wards and factor pierce, block multipler, target aura, etc
	EFFECT = 8		# Apply spell effects (such as DOTs, stuns, pip changes to target, etc)
	# ----------------------------------------------------
	PIPS = 9		# Handle pip changes (includes cost of spell, whether it was dispelled, pip conserve chance)
	INTERRUPT = -1	# Boss cheats or pet maycasts
	#				^^It ocurred to me that interrupts happen as "turns" not within a given turn


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


# Enum for battle status (stunned, beguiled, confused)
# Int values are tuple (array) positions
class Status(IntEnum):
	STUNNED = 0
	BEGUILED = 1
	CONFUSED = 2


# -- SPELL REPRESENTATION --

# Enum for modification object types
# ^^All possible elements that could be changed by a modifier object (charm, global, etc.)
# TODO: Consider refactor for incoming versus outgoing
class ModType(IntEnum):
	DAMAGE_MULT = 0		# Outgoing
	DAMAGE_CAP = 1		# Incoming
	ACCURACY_MOD = 3
	HEALING_MULT = 4
	HEALING_CAP = 5
	ABSORB = 6
	RESIST_MOD = 7
	# Critical chance
	# pierce
	# pip chance
	# pip impede / bonus??
	# something for dispels


# Enum for spell config action types
class Action(IntEnum):
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
	def __init__(self, data):
		statRange = range(len(School.__members__))			# Length of arrays for school-specific stats

		print(data)

		# -- BASIC STATS --
		self.level = getattr(data, "level", 1)				# Player level (significant thanks to crit rating 🙂)
		self.health = getattr(data, "health", 500)			# Maximum health
		self.mana = getattr(data, "mana", 10)				# Maximum mana
		self.mastery = getattr(data, "mastery", None)		# School mastery (multiple masteries possible, hence array)
		if self.mastery is None: self.mastery = [False for x in statRange]

		# -- PRIMARY STATS --
		# NOTE: Some stats (like lunar damage) are implicit with global stats but not displayed in game!

		# Tuples of (damage multiplier, flat damage bonus) per datatypes.School
		damageRaw = getattr(data, "damage", None)
		if damageRaw is not None:
			for i, entry in enumerate(damageRaw):
				self.damage[i] = (entry[0], entry[1])
		else: self.damage = [(0, 0) for x in statRange]
		
		# Tuples of (resist multiplier, flat res) per datatypes.School
		resistRaw = getattr(data, "resist", None)
		if resistRaw is not None:
			for i, entry in enumerate(resistRaw):
				self.resist[i] = (entry[0], entry[1])
		else: self.resist = [(0, 0) for x in statRange]
		
		self.accuracy = getattr(data, "accuracy", None)		# Spell cast accuracy bonus
		if self.accuracy is None: self.accuracy = [0 for x in statRange]

		# -- SECONDARY STATS (page 1) --
		self.critical = getattr(data, "critical", None)		# Critical hit rating
		if self.critical is None: self.critical = [0 for x in statRange]

		self.block = getattr(data, "block", None)			# Critical block rating
		if self.block is None: self.block = [0 for x in statRange]

		self.pierce = getattr(data, "pierce", None)			# Armor piercing bonus
		if self.pierce is None: self.pierce = [0 for x in statRange]

		self.stunres = getattr(data, "stunres", 0)			# Stun resistance

		healingRaw = getattr(data, "healing", [0, 0])
		self.healing = (healingRaw[0], healingRaw[1])		# Healing I/O multiplier bonus

		# -- SECONDARY STATS (page 2) --
		self.pipcons = getattr(data, "critical", None)		# Pip conversion rating
		if self.critical is None: self.critical = [0 for x in statRange]

		self.powerpip = getattr(data, "powerpip", 0)		# Chance of obtaining a power pip
		self.shadpip = getattr(data, "shadpip", 0)			# Shadow pip rating
		self.archmastery = getattr(data, "archmastery", 0)	# Archmastery rating

		# -- TERTIARY STATS (not listed on profile) --
		self.startpips = getattr(data, "startpips", [])		# Bonus starting pips (array to support basic or power)
		self.maycasts = getattr(data, "maycasts", [])		# Pet maycast cheat IDs (TODO: Add pet happiness casts)

		self.amschool = getattr(data, "amschool", Pip.FIRE) # Initial deck archmastery selection
		self.deck = getattr(data, "deck", [])				# Starting deck (important for battle init and reshuffle)
		self.side = getattr(data, "side", [])				# Treasure cards deck


# -- MODIFIER (Charm, Ward, etc.) OBJECT --
class Modifier:
	# These will not have explicit files, so only dictionary types are parsed*
	def __init__(self, data = None):
		# Pull the values from the dictionary
		pass


# Object that houses the full spell data and action set
# Data stored statically and referenced when necessary
# Config file example at 'spells/storm/thundersnake.spell'
class Spell:
	pass


# Battle cheats type
# Specifies a 'script' to define a cheat condition
# Includes standard boss cheats, as well as pet maycasts
# -- NOT IMPLEMENTED UNTIL MUCH LATER --
class Cheat:
	def __init__(self):
		raise NotImplementedError("Battle cheats")