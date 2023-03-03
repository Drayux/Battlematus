# Battlematus Simulation
# Core operation (for running simulation as standalone)
# Simulation API is imported
# Author: Liam "Drayux" Dempsey

import sys

if __name__ == "__main__":
	# -- PARSE ARGS --
	# Launch external tool if requested
	# Temporary means of calling this for testing
	if sys.argv[1] == "edit":
		import editor
		editor.startEditor()
		exit()

	# -- INIT SIMULATION --
	# Generate participants

	# Load initial state (Default: New battle instance)