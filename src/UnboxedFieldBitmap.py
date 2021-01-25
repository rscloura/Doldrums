class UnboxedFieldBitmap:
	def __init__(self, n):
		self.bitmap = n

	def get(self, position):
		if position >= 64:
			return False
		return ((self.bitmap >> position) & 1) != 0