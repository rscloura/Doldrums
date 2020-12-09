class DartClass():
	def __init__(self, snapshot, clazz):
		self.name = snapshot.references[clazz['name']]['data']
		self.functions = list(map(lambda f: DartFunction(snapshot, snapshot.references[f]), snapshot.references[clazz['functions']]['data']))
		self.interfaces = list(map(lambda i: DartType(snapshot, snapshot.references[i]), snapshot.references[clazz['interfaces']]['data']))

class DartFunction():
	def __init__(self, snapshot, function):
		self.name = snapshot.references[function['name']]['data']
		self.resultType = DartType(snapshot, snapshot.references[function['resultType']]).name

class DartType():
	def __init__(self, snapshot, typee):
		self.name = snapshot.references[snapshot.classes[snapshot.references[typee['typeClassId']]['value']]['name']]['data']