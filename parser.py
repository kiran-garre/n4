from tokenizer import *

"""
program = (function | statement)*
function = "fn" ident "("param*")" : type body "end"
body = statement*
statement = assignment | if_stmt | expression

assignment = (ident ":" type "=" expression) | (ident "=" expression)
expression = primary (operator primary)*
primary = number | ident | "(" expression ")" | if_expr

if_stmt = "if" expression body "else" body "end"
return_stmt = "return" expression


For adding precedence:
expression = equality
equality   = comparison (("==" | "!=") comparison)*
comparison = term (("<" | ">" | "<=" | ">=") term)*
term       = factor (("+" | "-") factor)*
factor     = unary (("*" | "/") unary)*
unary      = ("-" | "!") unary | primary
"""

PARSER_RED_ERROR = "\033[1m\033[91mparse error:\033[0m"

class ParserException(Exception):
	def __init__(self, message="ParserException", line_number=0):
		self.message = message
		self.line_number = line_number
		super().__init__(self.message)

class Program:
	def __init__(self, contents):
		self.contents = contents

	def get_children(self):
		return self.contents
	
	def get_value(self):
		return 'program'

class FunctionDefinition:
	def __init__(self, name, params, return_type, body):
		self.name = name
		self.params = params
		self.return_type = return_type
		self.body = body

	def get_children(self):
		return [*self.params, self.body, self.return_type,]
	
	def get_value(self):
		return f"fn {self.name.literal}"

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
	
class WhileStatement:
	def __init__(self, condition, body):
		self.condition = condition
		self.body = body

	def get_children(self):
		return self.condition, self.body
	
	def get_value(self):
		return "while"

class IfStatement:
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
			return self.lhs, self.type, self.rhs
		return self.lhs, self.rhs

	def get_value(self):
		return "assign"
	
class FunctionCall:
	def __init__(self, name, args):
		self.name = name
		self.args = args

	def get_children(self):
		return self.args
	
	def get_value(self):
		return f"call {self.name.literal}"

class BinExpr:
	def __init__(self, left, op, right):
		self.op = op
		self.left = left
		self.right = right
	
	def get_children(self):
		return self.left, self.right
	
	def get_value(self):
		return self.op.literal
	
class UnaryExpr:
	def __init__(self, op, operand):
		self.op = op
		self.operand = operand

	def get_children(self):
		return [self.operand]
	
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
	def __init__(self, tokens: list[Token], filename):
		self.tokens = tokens
		self.filename = filename
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
		if self.peek().type != type:
			raise ParserException(f"expected {type}, got {self.peek().type}", self.peek().line_number)
		return self.consume()

	def display_errors(self):
		for error in self.errors:
			print(f"{self.filename}:{error.line_number}: {PARSER_RED_ERROR} {error}")

	def synchronize(self):
		while not self.expect(TokenType.EOF):
			if self.consume() in (TokenType.NEWLINE, TokenType.END, TokenType.ELSE):
				return

	def parse_program(self):
		contents = []
		while not self.expect(TokenType.EOF):
			print(self.idx, self.peek().type)
			try:
				if self.expect(TokenType.NEWLINE):
					self.consume()
				elif self.expect(TokenType.FN):
					contents.append(self.parse_function())
				else:
					contents.append(self.parse_statement())
			except ParserException as e:
				self.errors.append(e)
		return Program(contents)
	
	def parse_function(self):
		self.require(TokenType.FN)
		name = self.require(TokenType.IDENT)
		self.require(TokenType.LEFT_PAREN)
		params = self.parse_params()
		self.require(TokenType.RIGHT_PAREN)
		self.require(TokenType.COLON)
		return_type = self.require(TokenType.TYPE)
		self.require(TokenType.NEWLINE)
		body = self.parse_body()
		self.require(TokenType.END)
		return FunctionDefinition(name, params, return_type, body)

	def parse_params(self):
		params = []
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
		while self.expect(
			TokenType.IDENT,
			TokenType.NUMBER, 
			TokenType.IF, 
			TokenType.WHILE,
			TokenType.LEFT_PAREN, 
			TokenType.RETURN,
			TokenType.NEWLINE,
			TokenType.STAR
		):	
			try:
				if self.expect(TokenType.NEWLINE):
					self.consume()
					continue
				statements.append(self.parse_statement())
			except ParserException as e:
				self.errors.append(e)
				self.synchronize()
		return Body(statements)
	
	def parse_statement(self):
		statement = None
		if self.expect(TokenType.IDENT, TokenType.NUMBER, TokenType.STAR):
			statement = self.parse_expr()
			if self.expect(TokenType.ASSIGN, TokenType.COLON):
				if not Parser.expr_is_valid_lvalue(statement):
					raise ParserException("invalid lvalue", self.peek().line_number)
				statement = self.parse_assignment(statement)
		elif self.expect(TokenType.IF):
			statement = self.parse_if_statement()
		elif self.expect(TokenType.WHILE):
			statement = self.parse_while_statement()
		elif self.expect(TokenType.RETURN):
			statement = self.parse_return_statement()
		if not statement:
			self.synchronize()
			raise ParserException(f"expected a statement", self.peek().line_number)
		self.require(TokenType.NEWLINE)
		return statement
				
	def parse_while_statement(self):
		self.require(TokenType.WHILE)
		condition = self.parse_expr()
		self.require(TokenType.NEWLINE)
		body = self.parse_body()
		self.require(TokenType.END)
		return WhileStatement(condition, body)
	
	def expr_is_valid_lvalue(expr):
		if isinstance(expr, Primary) and expr.token.type == TokenType.IDENT:
			return True
		elif isinstance(expr, UnaryExpr) and expr.op.type == TokenType.STAR:
			return True
		return False
	
	def parse_if_statement(self):
		self.require(TokenType.IF)
		condition = self.parse_expr()
		self.require(TokenType.NEWLINE)
		if_body = self.parse_body()
		else_body = None
		if self.expect(TokenType.ELSE):
			self.consume()
			self.require(TokenType.NEWLINE)
			else_body = self.parse_body()
		self.require(TokenType.END)
		return IfStatement(condition, if_body, else_body)
	
	def parse_return_statement(self):
		self.require(TokenType.RETURN)
		return ReturnStatement(self.parse_expr())
	
	def parse_assignment(self, ident):
		type = None
		if self.peek().type == TokenType.COLON:
			self.consume() # consume colon
			type = self.require(TokenType.TYPE)
		self.require(TokenType.ASSIGN)
		expr = self.parse_expr()
		return Assignment(ident, expr, type)
	
	def parse_function_call(self):
		name = self.require(TokenType.IDENT)
		self.require(TokenType.LEFT_PAREN)
		args = []
		while self.expect(TokenType.IDENT):
			ident = self.consume()
			args.append(ident)
			if not self.expect(TokenType.RIGHT_PAREN):
				self.require(TokenType.COMMA)
		self.require(TokenType.RIGHT_PAREN)
		return FunctionCall(name, args)

	def parse_expr(self):
		if self.expect(TokenType.IDENT) and self.peek(1).type == TokenType.LEFT_PAREN:
			return self.parse_function_call()
		return self.parse_comparison()
	
	def parse_comparison(self):
		left = self.parse_addition()
		while self.expect(
			TokenType.LESS, 
			TokenType.GREATER, 
			TokenType.LESS_EQUAL, 
			TokenType.GREATER_EQUAL
		):
			op = self.consume()
			right = self.parse_addition()
			left = BinExpr(left, op, right)
		return left

	def parse_addition(self):
		left = self.parse_factor()
		while self.expect(TokenType.STAR, TokenType.SLASH):
			op = self.consume()
			right = self.parse_factor()
			left = BinExpr(left, op, right)
		return left
	
	def parse_factor(self):
		left = self.parse_unary()
		while self.expect(TokenType.PLUS, TokenType.MINUS):
			op = self.consume()
			right = self.parse_unary()
			left = BinExpr(left, op, right)
		return left
	
	def parse_unary(self):
		if self.expect(TokenType.STAR, TokenType.MINUS):
			op = self.consume()
			operand = self.parse_primary()
			return UnaryExpr(op, operand)
		return self.parse_primary()
	
	def parse_primary(self):
		if self.expect(TokenType.IDENT, TokenType.NUMBER):
			return Primary(self.consume())
		elif self.expect(TokenType.LEFT_PAREN):
			self.consume()
			expr = self.parse_expr()
			self.require(TokenType.RIGHT_PAREN)
			return expr
		else:
			raise ParserException("expected primary expression", self.peek().line_number)


