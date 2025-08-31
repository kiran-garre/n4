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
	TYPE = 102

	LEFT_PAREN = 200
	RIGHT_PAREN = 201
	NEWLINE = 206
	COMMA = 207
	EOF = 208

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
	'\n': TokenType.NEWLINE,
	',': TokenType.COMMA,
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
	'void',
	'byte',
	'short',
	'int',
	'long',
	'ubyte',
	'ushort',
	'uint',
	'ulong'
}

class TokenizerException(Exception):
	pass

class Token:
	def __init__(self, type, literal, line_number=-1):
		self.type = type
		self.literal = literal
		self.line_number = line_number

	def get_children(self):
		return None
	
	def get_value(self):
		return f"{self.literal}"

class Tokenizer:
	def __init__(self, source):
		self.tokens = []
		self.source = source
		self.idx = 0
		self.line_number = 1
		self.errors = []

	def display_errors(self):
		for error in self.errors:
			print(str(error))

	def peek(self):
		return self.source[self.idx]
	
	def consume(self):
		char = self.source[self.idx]
		self.idx += 1
		return char
	
	def reached_eof(self):
		return self.idx >= len(self.source)

	def read_ident(self):
		ident = []
		while self.peek().isalnum() or self.peek() == '_' and not self.reached_eof():
			ident.append(self.consume())
		return Token(TokenType.IDENT, "".join(ident), self.line_number)

	def read_number(self):
		number = []
		while self.peek().isnumeric() and not self.reached_eof():
			number.append(self.consume())
		return Token(TokenType.NUMBER, "".join(number), self.line_number)

	def consume_comment(self):
		while self.peek() != "\n" and not self.reached_eof():
			self.consume()
	
	def read_operator(self):
		op = self.consume()
		return Token(OPERATORS[op], op, self.line_number)
	
	def read_structure(self):
		st = self.consume()
		return Token(STRUCTURES[st], st, self.line_number)
	
	def resolve_keywords(self):
		for i in range(len(self.tokens)):
			if self.tokens[i].literal in KEYWORDS:
				self.tokens[i].type = KEYWORDS[self.tokens[i].literal]
			elif self.tokens[i].literal in TYPES:
				self.tokens[i].type = TokenType.TYPE

	def tokenize(self):
		while not self.reached_eof():
			if self.peek() in (' ', '\t'):
				self.consume()
			elif self.peek().isalpha() or self.peek() == '_':
				self.tokens.append(self.read_ident())
			elif self.peek().isnumeric():
				self.tokens.append(self.read_number())
			elif self.peek() == ';':
				self.consume_comment()
			elif self.peek() in OPERATORS:
				self.tokens.append(self.read_operator())
			elif self.peek() in STRUCTURES:
				if self.peek() == '\n':
					self.line_number += 1
				self.tokens.append(self.read_structure())
			else:
				self.errors.append(TokenizerException(f"invalid character: {self.peek()}"))
				self.consume()

		self.resolve_keywords()
		self.tokens.append(Token(TokenType.EOF, ''))
		

			

