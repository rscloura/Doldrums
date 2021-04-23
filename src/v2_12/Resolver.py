#FIXME: needs to be implemented decently from scratch
from v2_12.ClassId import ClassId

spacing = '    '

class DartClass():
	def __init__(self, snapshot, clazz):
		self.name = DartString(snapshot, clazz['name'])
		self.superType = DartType(snapshot, clazz['superType'])
		self.typeParameters = list(map(lambda i: DartType(snapshot, i), DartType(snapshot, clazz['typeParameters']).types))
		self.interfaces = list(map(lambda i: DartType(snapshot, i), DartArray(snapshot, clazz['interfaces']).data))
		self.functions = list(map(lambda f: DartFunction(snapshot, f), DartArray(snapshot, clazz['functions']).data))
		self.fields = list(map(lambda i: DartField(snapshot, i), DartArray(snapshot, clazz['fields']).data))

	def __str__(self):
		s = 'class ' + str(self.name)
		if self.typeParameters != []:
			s += '<'
			s += ', '.join(list(map(lambda i: str(i), self.typeParameters)))
			s += '>'
		if str(self.superType) != 'Null':
			s += ' extends ' + str(self.superType)
		if self.interfaces != []:
			s += ' implements '
			for interface in self.interfaces:
				s += str(interface) + ', '
			s = s[:-2]
		s += ' {\n'
		for field in self.fields:
			s += spacing + str(field) + '\n'
		s += '\n'
		for function in self.functions:
			s += spacing + str(function) + '\n\n'
		return s.strip() + '\n}'

class DartFunction():
	def __init__(self, snapshot, refId):
		function = snapshot.references[refId]
		self.name = snapshot.references[function['name']]['data']
		self.resultType = DartType(snapshot, DartType(snapshot, function['signature']).resultType).name
		self.typeParameters = list(map(lambda i: DartType(snapshot, i), DartArray(snapshot, DartType(snapshot, function['signature']).parameterTypes).data))
		self.codeOffset = snapshot.instructionsOffset + snapshot.references[function['code']]['entryPoint']

	def __str__(self):
		s = str(self.resultType)
		s += ' ' + self.name + '('
		if self.typeParameters != []:
			s += ', '.join(list(map(lambda i: str(i), self.typeParameters)))
		s += ') {\n'
		s += 2 * spacing + 'Code at absolute offset: ' + hex(self.codeOffset) + '\n'
		s += spacing + '}'
		return s

class DartType():
	def __init__(self, snapshot, refId):
		typee = snapshot.references[refId]
		if typee['cid'] is ClassId.TYPE:
			if typee['isBase']:
				self.name = typee['name']
				self.types = []
				self.resultType = 1
				self.parameterTypes = 1
			else:
				self.name = snapshot.references[snapshot.classes[snapshot.references[typee['typeClassId']]['value']]['name']]['data']
		elif typee['cid'] is ClassId.TYPE_PARAMETER:
			if typee['isBase']:
				self.name = typee['name']
			else:
				self.name = snapshot.references[typee['name']]['data']
			try:
				self.types = typee['types']
			except:
				self.types = []
		elif typee['cid'] is ClassId.FUNCTION_TYPE:
			if 'isBase' in typee.keys() and typee['isBase']:
				self.name = typee['name']
				self.resultType = typee['name']
				self.types = []
			else:
				self.name = "FuncType"
				self.resultType = typee['resultType']
				self.parameterTypes = typee['parameterTypes']
		elif typee['cid'] is ClassId.TYPE_ARGUMENTS:
			if 'isBase' in typee.keys() and typee['isBase']:
				self.name = typee['name']
				self.types = []
			else:
				self.name = "TypeArgs"
				self.types = typee['types']

	def __str__(self):
		return self.name

class DartField():
	def __init__(self, snapshot, refId):
		field = snapshot.references[refId]
		self.name = DartString(snapshot, field['name']).data
		self.type = DartType(snapshot, field['type'])

	def __str__(self):
		return str(self.type) + ' ' + self.name

class DartString():
	def __init__(self, snapshot, refId):
		self.data = snapshot.references[refId]['data']

	def __str__(self):
		return self.data

class DartArray():
	def __init__(self, snapshot, refId):
		try:
			self.data = snapshot.references[refId]['data']
		except:
			self.data = []