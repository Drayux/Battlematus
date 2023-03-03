# state.py
# Structure for the combat state vector (and subsequent sub-structures)
# Supports JSON-encoded I/O
# Members can be initalized from file

from json import load, loads
from json.decoder import JSONDecodeError as JSONError
from util import encodeJSON

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
	@classmethod
	# Handle different input formats
	# Ultimately returns a state dict
	def parse(cls, data: str):
		# First attempt to parse the string as a JSON-encoded dictionary
		try: return loads(data)
		except JSONError: pass

		# Otherwise, attempt to open the path
		try:
			with open(data) as f:
				return load(f)
		
		except (FileNotFoundError, JSONError):
			raise ValueError
	

	# Argument: 'data' can be...
	#   None for new state (with defaults)
	#   JSON-encoded string with partial (or full) data
	#   Filepath to JSON-encoded string
	def __init__(self, data = None):
		if isinstance(data, str):
			try: data = State.parse(data)
			except ValueError:
				print("WARNING: State data could not be parsed from json string or path")
		
		# Init state primitives
		self.round = getattr(data, "round", 1)		# NOTE: Pips should be acquired at the start of the player turn, if applicable
		self.first = getattr(data, "first", 0)		# Should be either 0 or 4 (wizards first or npcs first)
		self.player = getattr(data, "player", 0)	# Index of casting participant
		self.order = getattr(data, "order", None)	# Array of member IDs to define cast order (should be: [None for x in range(8)])
		if self.order is None: self.order = [None for x in range(8)]
		
		# Init state objects
		self.bubble = None		# Active global (represented as Modifier obj)
								# ^^Exception rule of "don't look up defaults" as this is a component of the sim calculations
		if hasattr(data, "bubble"): bubble = Modifier(data["bubble"])

		self.members = {}		# Dict of (member_id, member_data) : Allows >8 member states for battles that require it
		for memberid, memberdata in getattr(data, "members", {}).items():
			self.members[memberid] = Member(memberdata)
	
	def __str__(self):
		return encodeJSON(self)


# -- MODIFIER (Charm, Ward, etc.) OBJECT --
class Modifier:
	# These will not have explicit files, so only dictionary types are parsed*
	def __init__(self, data = None):
		# Pull the values from the dictionary
		pass

# -- CORE MEMBER OBJECT --
