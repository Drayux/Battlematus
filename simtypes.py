# Miscellaneous types relevant to various portions of the simulation

from enum import IntEnum

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


# Enum for healing stat
# Int values are tuple (array) positions
class Healing(IntEnum):
	IN = 0
	OUT = 1


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


# Enum for modification object types
# TODO: Consider refactor for incoming versus outgoing
class Buff(IntEnum):
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


# Member stats object
# Holds static member data for reference by Simulation class
class Stats:
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