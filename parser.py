from tokenizer import *

"""
program = (function | statement)*
function = "fn" ident "("param*")" : type body "end"
body = statement*
statement = assignment | if_stmt | expression

assignment = (ident ":" type "=" expression) | (ident "=" expression)
expression = primary (operator primary)*
primary = number | ident | "(" expression ")" | if_expr

if_stmt = "if" expression body "else" expression "end"
return_stmt = "return" expression


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

class Function:
	def __init__(self, name, params, return_type, body):
		self.name = name
		self.params = params
		self.return_type = return_type
		self.body = body

	def get_children(self):
		return [*self.params, self.return_type, self.body]
	
	def get_value(self):
		return self.name

class Param:
	def __init__(self, ident, type):
		self.ident = ident
		self.type = type

	def get_children(self):
		None
	
	def get_value(self):
		return f"{self.ident.literal}: {self.type.literal}"

class Body:
	def __init__(self, statements):
		self.statements = statements
	
	def get_children(self):
		return self.statements
	
	def get_value(self):
		return "body"

class IfStmt:
	def __init__(self, condition, true_body, false_body):
		self.condition = condition
		self.true_body = true_body
		self.false_body = false_body

	def get_children(self):
		if self.false_body:
			return self.condition, self.true_body, self.false_body
		return self.condition, self.true_body
	
	def get_value(self):
		return "if"
	
class ReturnStatement:
	def __init__(self, expr):
		self.expr = expr

	def get_children(self):
		return [self.expr]
	
	def get_value(self):
		return "return"

class Assignment:
	def __init__(self, lhs, rhs, type=None):
		self.lhs = lhs
		self.rhs = rhs
		self.type = type
	
	def get_children(self):
		if self.type:
			return self.lhs, self.rhs, self.type
		return self.lhs, self.rhs

	def get_value(self):
		return "assign"

class BinExpr:
	def __init__(self, left, op, right):
		self.op = op
		self.left = left
		self.right = right
	
	def get_children(self):
		return self.left, self.right
	
	def get_value(self):
		return self.op.literal

class Primary:
	def __init__(self, token):
		self.token = token
	
	def get_children(self):
		if isinstance(self.token, Token):
			return None
		return self.token.get_children()
	
	def get_value(self):
		if isinstance(self.token, Token):
			return self.token.get_value()
		return None



class Parser:
	def __init__(self, tokens: list[Token]):
		self.tokens = tokens
		self.idx = 0
		self.errors = []

	def peek(self, ahead=0):
		if self.idx >= len(self.tokens):
			return None
		return self.tokens[self.idx + ahead]
	
	def consume(self):
		if self.idx >= len(self.tokens):
			return None
		token = self.tokens[self.idx]
		self.idx += 1
		return token

	def expect(self, *types) -> bool:
		if not self.peek():
			return False
		return self.peek().type in types
	
	def require(self, type):
		if not self.peek():
			raise ParserException(f"expected {type}, got EOF")
		if self.peek().type != type:
			raise ParserException(f"expected {type}, got {self.peek().type}")
		return self.consume()

	def display_errors(self):
		for error in self.errors:
			print(error)

	def consume_line(self):
		while self.consume() not in (TokenType.NEWLINE, None):
			continue
			
	
	

	def parse_program(self):
		return self.parse_body()
	
	def parse_function(self):
		self.require(TokenType.FN)
		name = self.require(TokenType.IDENT)
		self.require(TokenType.LEFT_PAREN)
		params = self.parse_params()
		self.require(TokenType.RIGHT_PAREN)
		self.require(TokenType.COLON)
		return_type = self.require(TokenType.TYPE)
		self.require(TokenType.NEWLINE)
		body = self.parse_statement()
		self.require(TokenType.END)
		return Function(name, params, return_type, body)

	def parse_params(self):
		params =[]
		while self.expect(TokenType.IDENT):
			ident = self.consume()
			self.require(TokenType.COLON)
			type = self.require(TokenType.TYPE)
			params.append(Param(ident, type))
			if not self.expect(TokenType.RIGHT_PAREN):
				self.require(TokenType.COMMA)
		return params
	
	def parse_body(self):
		statements = []
		while self.expect(TokenType.IDENT, TokenType.NUMBER, TokenType.IF, TokenType.LEFT_PAREN):
			try:
				statements.append(self.parse_statement())
			except ParserException as e:
				self.errors.append(str(e))
				self.consume_line()
		return Body(statements)
	
	def parse_statement(self):
		statement = None
		if self.expect(TokenType.IDENT):
			if self.peek(1).type in (TokenType.COLON, TokenType.ASSIGN):
				statement = self.parse_assignment()
			else:
				statement = self.parse_expr()
		elif self.expect(TokenType.IF):
			statement = self.parse_if_statement()
		elif self.expect(TokenType.RETURN):
			statement = self.parse_return_statement()
		if statement:
			self.require(TokenType.NEWLINE)
		return statement
				

	def parse_if_statement(self):
		self.require(TokenType.IF)
		condition = self.parse_expr()
		self.require(TokenType.NEWLINE)
		if_body = self.parse_statement()
		else_body = None
		if self.expect(TokenType.ELSE):
			self.consume()
			self.require(TokenType.NEWLINE)
			else_body = self.parse_statement()
		self.require(TokenType.END)
		self.require(TokenType.NEWLINE)
		return IfStmt(condition, if_body, else_body)
	
	def parse_return_statement(self):
		self.require(TokenType.RETURN)
		return ReturnStatement(self.parse_expr())
	
	def parse_assignment(self):
		type = None
		ident = self.require()
		if self.peek(1).type == TokenType.COLON:
			self.consume() # consume colon
			type = self.require(TokenType.TYPE)
		self.require(TokenType.ASSIGN)
		expr = self.parse_expr()
		return Assignment(ident, expr, type)

	def parse_expr(self):
		expr = self.parse_addition()
		return expr

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
			self.consume()
			expr = self.parse_expr()
			self.require(TokenType.RIGHT_PAREN)
			return expr
		else:
			raise ParserException("Expected primary expression")


