from enum import Enum

class Kind(Enum):
	FULL = 0 # Full snapshot of an application.
	FULL_JIT = 1 # Full + JIT code
	FULL_AOT = 2 # Full + AOT code
	MESSAGE = 3 # A partial snapshot used only for isolate messaging.
	NONE = 4 # gen_snapshot
	INVALID = 5
 
	def __str__(self):
		if(self.value == 0):
			name = "Full (full snapshot of an application)"
		elif(self.value == 1):
			name = "Full JIT (full + JIT code)"
		elif(self.value == 2):
			name = "Full AOT (full + AOT code)"
		elif(self.value == 3):
			name = "Message (a partial snapshot used only for isolate messaging)"
		elif(self.value == 4):
			name = "None (gen_snapshot)"
		elif(self.value == 5):
			name = "Invalid"
		else:
			name = "Unknown"
 
		return name