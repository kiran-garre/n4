from enum import Enum

class TokenType(Enum):
	FN = 0
	IF = 1
	ELSE = 2
	WHILE = 3
	END = 4
	RETURN = 5

	IDENT = 100
	NUMBER = 101
	# TYPE = 102

	LEFT_PAREN = 200
	RIGHT_PAREN = 201

	COMMENT = 300

	PLUS = 400
	MINUS = 401
	STAR = 402
	SLASH = 403
	COLON = 404
	ASSIGN = 405

COMMENT_CHAR = ';'
OPERATORS = {
	'+': TokenType.PLUS,
	'-': TokenType.MINUS,
	'*': TokenType.STAR,
	'/': TokenType.SLASH,
	':': TokenType.COLON,
	'=': TokenType.ASSIGN,
}
STRUCTURES = {
	'(': TokenType.LEFT_PAREN,
	')': TokenType.RIGHT_PAREN,
}
KEYWORDS = {
	'fn': TokenType.FN,
	'if': TokenType.IF,
	'else': TokenType.ELSE,
	'while': TokenType.WHILE,
	'end': TokenType.END,
	'return': TokenType.RETURN
}
TYPES = {
	'byte',
	'short',
	'int',
	'long',
	'ubyte',
	'ushort',
	'uint',
	'ulong'
}

class Token:
	def __init__(self, type, literal):
		self.type = type
		self.literal = literal

class Tokenizer:
	def __init__(self):
		self.tokens = []

	def read_ident(self, source, idx):
		ident = []
		while source[idx].isalnum() or source[idx] == '_' and idx < len(source):
			ident.append(source[idx])
			idx += 1
		return Token(TokenType.IDENT, "".join(ident)), idx

	def read_number(self, source, idx):
		number = []
		while source[idx].isnumeric() and idx < len(source):
			number.append(source[idx])
			idx += 1
		return Token(TokenType.NUMBER, "".join(number)), idx

	def consume_comment(self, source, idx):
		while source[idx] != "\n" and idx < len(source):
			idx += 1
		return idx

	def operator_to_token(self, op):
		return Token(OPERATORS[op], op)
	
	def structure_to_token(self, st):
		return Token(STRUCTURES[st], st)
	
	def resolve_keywords(self):
		for i in range(len(self.tokens)):
			if self.tokens[i].literal in KEYWORDS:
				self.tokens[i].type = KEYWORDS[self.tokens[i].literal]
			elif self.tokens[i].literal in TYPES:
				self.tokens[i].type = TokenType.TYPE

	def tokenize(self, source: str):
		idx = 0
		while idx < len(source):
			c = source[idx]
			if c.isalpha() or c == '_':
				token, idx = self.read_ident(source, idx)
				self.tokens.append(token)
				continue
			elif c.isnumeric():
				token, idx = self.read_number(source, idx)
				self.tokens.append(token)
				continue
			elif c == ';':
				idx = self.consume_comment(source, idx)
				continue
			elif c in OPERATORS:
				self.tokens.append(self.operator_to_token(c))
			elif c in STRUCTURES:
				self.tokens.append(self.structure_to_token(c))
			idx += 1

		self.resolve_keywords()
		

			
path = "./example.n4"

with open(path, 'r') as file:
	content = file.read()

tokenizer = Tokenizer()
tokenizer.tokenize(content)
token_types = list(map(lambda x: x.type.name, tokenizer.tokens))
print(token_types)
			


	