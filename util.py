# Utility functions for handling data I/O and API logic

from enum import IntEnum

from json import load, loads
from json.decoder import JSONDecodeError as JSONError

# Recursively convert object to JSON string
def encodeJSON(obj, omitNone = False):
	match obj:
		# We need to pull the value out of the enum (matches to int() by default)
		case IntEnum(): return str(obj.value)

		# Primitives
		case bool(): return str(obj).lower()
		case str(): return '\"' + str + '\"'
		case int(): return str(obj)
		case None: return "null"

		# Iterable types
		# I think this creates a new string object for every addition
		# Which is frusterating because I'd swear there should be a faster way to do this
		# But I probably have to break python to do so and honestly, I won't use this function beyond initilization
		case list():
			out = ""
			for item in obj:
				out += ', ' + encodeJSON(item)
			return "[" + out[2:] + "]"
		
		case tuple():
			out = ""
			for item in obj:
				out += ', ' + encodeJSON(item)
			return "[" + out[2:] + "]"

		case dict():
			out = ""
			for (key, value) in obj.items():
				if omitNone and (value is None): continue
				out += ', \"' + str(key) + '\": ' + encodeJSON(value)
			return "{" + out[2:] + "}"

	# Otherwise we're a fancy class
	ret = None
	try: ret = obj.__dict__
	except AttributeError: 
		print(f"Error occurred whilst coverting object of type {type(obj)} to JSON str")
	return encodeJSON(ret)


# Load simulation data via handling different input formats
# Ultimately returns a dictionary of memberIDs, spellIDs, and the state dict
def loadJSON(data: str):
	# First attempt to parse the string as a JSON-encoded dictionary
	try: return loads(data)
	except JSONError: pass

	# Otherwise, attempt to open the path
	try:
		with open(data) as f: return load(f)
	
	except (FileNotFoundError, JSONError):
		raise ValueError