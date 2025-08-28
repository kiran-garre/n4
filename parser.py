from tokenizer import *

"""
program = function*
function = "fn" ident "("param*")" : type body "end"
body = statement*
statement = assignment | expression
assignment = (idet ":" type "=" expression) | (ident "=" expression)
expression = primary (operator primary)*
primary = number | ident | "(" expression ")" | if_expr
if_expr = "if" expression expression "else" expression "end"

For adding precedence:
expression = equality
equality   = comparison (("==" | "!=") comparison)*
comparison = term (("<" | ">" | "<=" | ">=") term)*
term       = factor (("+" | "-") factor)*
factor     = unary (("*" | "/") unary)*
unary      = ("-" | "!") unary | primary
"""

class ParserException(Exception):
	pass

class Assignment:
	def __init__(self, lhs, type, rhs):
		self.lhs = lhs
		self.type = type
		self.rhs = rhs

class Expr:
	pass

class BinExpr(Expr):
	def __init__(self, left, op, right):
		self.op = op
		self.left = left
		self.right = right

class Primary(Expr):
	def __init__(self, token):
		self.token = token
		

class Parser:
	def __init__(self, tokens: list[Token]):
		self.tokens = tokens
		self.idx = 0

	def peek(self):
		return self.tokens[self.idx]
	
	def consume(self):
		token = self.tokens[self.idx]
		self.idx += 1
		return token

	def expect(self, *types):
		return self.peek().type in types
	
	def parse_assignment(self):
		if self.expect(TokenType.IDENT):
			ident = self.peek()

	def parse_expr(self):
		return self.parse_addition()

	def parse_addition(self):
		left = self.parse_factor()
		while self.expect(TokenType.STAR, TokenType.SLASH):
			op = self.consume()
			right = self.parse_factor()
			left = BinExpr(left, op, right)
		return left
	
	def parse_factor(self):
		left = self.parse_primary()
		while self.expect(TokenType.PLUS, TokenType.MINUS):
			op = self.consume()
			right = self.parse_primary()
			left = BinExpr(left, op, right)
		return left
	
	def parse_primary(self):
		if self.expect(TokenType.IDENT, TokenType.NUMBER):
			return Primary(self.consume())
		elif self.expect(TokenType.LEFT_PAREN):
			expr = self.parse_expr()
			if not self.expect(TokenType.RIGHT_PAREN):
				raise ParserException
			self.consume()
			return expr


