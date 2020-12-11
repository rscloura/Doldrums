#FIXME: needs to be implemented decently from scratch
from ClassId import ClassId

spacing = '    '

def printClass(snapshot, clazz):
	return

class DartClass():
	def __init__(self, snapshot, clazz):
		self.name = snapshot.references[clazz['name']]['data']
		self.superType = DartType(snapshot, snapshot.references[clazz['superType']])
		self.typeParameters = list(map(lambda i: DartType(snapshot, snapshot.references[i]), snapshot.references[clazz['typeParameters']]['types']) if clazz['typeParameters'] != 1 else [])
		self.interfaces = list(map(lambda i: DartType(snapshot, snapshot.references[i]), snapshot.references[clazz['interfaces']]['data']))
		self.functions = list(map(lambda f: DartFunction(snapshot, snapshot.references[f]), snapshot.references[clazz['functions']]['data']))

	def __str__(self):
		s = 'class ' + self.name
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
		for function in self.functions:
			s += spacing + str(function) + '\n\n'
		return s.strip() + '\n}'

class DartFunction():
	def __init__(self, snapshot, function):
		self.name = snapshot.references[function['name']]['data']
		self.resultType = DartType(snapshot, snapshot.references[function['resultType']]).name
		self.typeParameters = list(map(lambda i: DartType(snapshot, snapshot.references[i]), snapshot.references[function['parameterTypes']]['data']))
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
	def __init__(self, snapshot, typee):
		if typee['cid'] is ClassId.TYPE:
			if typee['isBase']:
				self.name = typee['name']
			else:
				self.name = snapshot.references[snapshot.classes[snapshot.references[typee['typeClassId']]['value']]['name']]['data']
		elif typee['cid'] is ClassId.TYPE_PARAMETER:
			if typee['isBase']:
				self.name = typee['name']
			else:
				self.name = snapshot.references[typee['name']]['data']

	def __str__(self):
		return self.name