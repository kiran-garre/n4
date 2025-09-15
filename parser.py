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

FIRST_EXPR = {
	TokenType.IDENT,
	TokenType.NUMBER, 
	TokenType.LEFT_PAREN, 
	TokenType.STAR,
	TokenType.MINUS,
}
FIRST_BODY = FIRST_EXPR | {
	TokenType.IF, 
	TokenType.WHILE,
	TokenType.RETURN,
	TokenType.NEWLINE,
}

class ParserException(Exception):
	def __init__(self, message="ParserException", line_number=0):
		super().__init__(self.message)
		self.message = message
		self.line_number = line_number

class Type:
	size_map = {
		'void': 0,
		'ptr': 4,
		'byte': 1,
		'short': 2,
		'int': 4,
		'long': 8,
		'ubyte': 1,
		'ushort': 2,
		'uint': 4,
		'ulong': 8,
	}
	def __init__(self, name, size, signed=True):
		self.name = name
		self.size = size
		self.signed = signed

	@staticmethod
	def token_to_type(token: Token):
		return Type.literal_to_type(token.literal)
	
	@classmethod
	def literal_to_type(cls, literal: str):
		return Type(
			literal, 
			Type.size_map[literal],
			Type.literal_is_signed(literal)
		)

	@classmethod
	def literal_is_signed(cls, literal: str):
		return literal in ('ubyte', 'ushort', 'uint', 'ulong')
	
	def get_children(self):
		return None

	def get_value(self):
		return self.name
		

class PointerType(Type):
	def __init__(self, base_type):
		super().__init__(f"ptr<{base_type}>", 8, False)
		self.base_type = base_type

class ASTNode:
	def __init__(self, line=None):
		self.line = line

class Primary(ASTNode):
	def __init__(self, token):
		super().__init__(token.line_number)
		self.token = token
		self.dtype: Type = None
	
	def get_children(self):
		return self.token.get_children()
	
	def get_value(self):
		return f"{self.token.get_value()}: {self.dtype.name}"
	
	def get_name(self):
		return self.token.literal
	
class UnaryExpr(ASTNode):
	def __init__(self, op, operand):
		super().__init__(operand.line)
		self.op = op
		self.operand = operand

	def get_children(self):
		return [self.operand]
	
	def get_value(self):
		return self.op.literal

class BinExpr(ASTNode):
	def __init__(self, left, op, right):
		super().__init__(left.line)
		self.op = op
		self.left = left
		self.right = right
	
	def get_children(self):
		return self.left, self.right
	
	def get_value(self):
		return self.op.literal
	
class FunctionCall(ASTNode):
	def __init__(self, name: Primary, args):
		super().__init__(name.line)
		self.name = name
		self.args = args

	def get_children(self):
		return self.args
	
	def get_value(self):
		return f"call {self.name.get_name()}"
	
	def get_name(self):
		return self.name.get_name()
	
Expr = Primary | UnaryExpr | BinExpr | FunctionCall

class DefinitionStatement(ASTNode):
	def __init__(self, ident: Primary, rhs: Expr, type: Type):
		super().__init__(ident.line)
		self.ident = ident
		self.rhs = rhs
		self.type = type

	def get_children(self):
		return [self.rhs]

	def get_value(self):
		return f"define {self.ident.get_name()}: {self.type.name}"
	
class AssignmentStatement(ASTNode):
	def __init__(self, lhs: Expr, rhs: Expr):
		super().__init__(lhs.line)
		self.lhs = lhs
		self.rhs = rhs
	
	def get_children(self):
		return self.lhs, self.rhs

	def get_value(self):
		return "assign"
	
class IfStatement(ASTNode):
	def __init__(self, condition: Expr, true_body, false_body):
		super().__init__(condition.line)
		self.condition = condition
		self.true_body = true_body
		self.false_body = false_body

	def get_children(self):
		if self.false_body:
			return self.condition, self.true_body, self.false_body
		return self.condition, self.true_body
	
	def get_value(self):
		return "if"
	
class WhileStatement(ASTNode):
	def __init__(self, condition: Expr, body):
		super().__init__(condition.line)
		self.condition = condition
		self.body = body

	def get_children(self):
		return self.condition, self.body
	
	def get_value(self):
		return "while"
	
class ReturnStatement(ASTNode):
	def __init__(self, expr: Expr):
		super().__init__(expr.line)
		self.expr = expr

	def get_children(self):
		return [self.expr]
	
	def get_value(self):
		return "return"
	
Statement = DefinitionStatement | AssignmentStatement | IfStatement | WhileStatement | ReturnStatement

class Body(ASTNode):
	def __init__(self, statements: list[Statement]):
		if statements:
			super().__init__(statements[0].line)
		else:
			super().__init__(0)
		self.statements = statements
	
	def get_children(self):
		return self.statements
	
	def get_value(self):
		return "body"

class Param(ASTNode):
	def __init__(self, ident: Primary, type: Type):
		super().__init__(ident.line)
		self.ident = ident
		self.type = type

	def get_children(self):
		return None
	
	def get_value(self):
		return f"{self.ident.get_name()}: {self.type.name}"
	
	def get_name(self):
		return self.ident.get_name()
	
class FunctionDefinition(ASTNode):
	def __init__(self, name: Primary, params: list[Param], return_type: Type, body):
		super().__init__(name.line)
		self.name = name
		self.params = params
		self.return_type = return_type
		self.body = body

	def get_children(self):
		return [*self.params, self.body, self.return_type]
	
	def get_value(self):
		return f"fn {self.name.get_name()}"
	
	def get_name(self):
		return self.name.get_name()

class Program(ASTNode):
	def __init__(self, contents: list[Statement | FunctionDefinition]):
		super().__init__(1)
		self.contents = contents

	def get_children(self):
		return self.contents
	
	def get_value(self):
		return 'program'

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
		return self.peek().token_type in types
	
	def require(self, type: TokenType):
		if self.peek().token_type != type:
			raise ParserException(f"expected {type}, got {self.peek().token_type}", self.peek().line_number)
		return self.consume()

	def display_errors(self):
		for error in self.errors:
			print(f"{self.filename}:{error.line_number}: {PARSER_RED_ERROR} {error}")

	def recover(self):
		while not self.expect(TokenType.EOF):
			if self.consume() in (TokenType.NEWLINE, TokenType.END, TokenType.ELSE):
				return

	def parse_program(self):
		contents = []
		while not self.expect(TokenType.EOF):
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
		name = self.parse_primary(TokenType.IDENT)
		self.require(TokenType.LEFT_PAREN)
		params = self.parse_params()
		self.require(TokenType.RIGHT_PAREN)
		self.require(TokenType.COLON)
		return_type = Type.token_to_type(self.require(TokenType.TYPE))
		self.require(TokenType.NEWLINE)
		body = self.parse_body()
		self.require(TokenType.END)
		return FunctionDefinition(name, params, return_type, body)

	def parse_params(self):
		params = []
		while self.expect(TokenType.IDENT):
			ident = self.parse_primary(TokenType.IDENT)
			self.require(TokenType.COLON)
			type = Type.token_to_type(self.require(TokenType.TYPE))
			params.append(Param(ident, type))
			if not self.expect(TokenType.RIGHT_PAREN):
				self.require(TokenType.COMMA)
		return params
	
	def parse_body(self):
		statements = []
		while self.expect(*FIRST_BODY):	
			try:
				if self.expect(TokenType.NEWLINE):
					self.consume()
					continue
				statements.append(self.parse_statement())
			except ParserException as e:
				self.errors.append(e)
				self.recover()
		return Body(statements)
	
	def parse_statement(self):
		statement = None
		if self.expect(TokenType.IDENT, TokenType.NUMBER, TokenType.STAR):
			if self.peek(1).token_type == TokenType.COLON:
				statement = self.parse_definition()
			else:
				statement = self.parse_expr()
				if self.expect(TokenType.ASSIGN):
					statement = self.parse_assignment(statement)
		elif self.expect(TokenType.IF):
			statement = self.parse_if_statement()
		elif self.expect(TokenType.WHILE):
			statement = self.parse_while_statement()
		elif self.expect(TokenType.RETURN):
			statement = self.parse_return_statement()
		if not statement:
			self.recover()
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
		if isinstance(expr, Primary) and expr.token.token_type == TokenType.IDENT:
			return True
		elif isinstance(expr, UnaryExpr) and expr.op.token_type == TokenType.STAR:
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
	
	def parse_assignment(self, lhs):
		if not Parser.expr_is_valid_lvalue(lhs):
			raise ParserException("invalid lvalue", self.peek().line_number)
		self.require(TokenType.ASSIGN)
		rhs = self.parse_expr()
		return AssignmentStatement(lhs, rhs)
	
	def parse_definition(self):
		name = self.parse_primary(TokenType.IDENT)
		self.require(TokenType.COLON)
		type = Type.token_to_type(self.require(TokenType.TYPE))
		self.require(TokenType.ASSIGN)
		rhs = self.parse_expr()
		return DefinitionStatement(name, rhs, type)
	
	def parse_function_call(self):
		name = self.parse_primary(TokenType.IDENT)
		self.require(TokenType.LEFT_PAREN)
		args = []
		while self.expect(*FIRST_EXPR):
			ident = self.consume()
			args.append(ident)
			if not self.expect(TokenType.RIGHT_PAREN):
				self.require(TokenType.COMMA)
		self.require(TokenType.RIGHT_PAREN)
		return FunctionCall(name, args)

	def parse_expr(self):
		if self.expect(TokenType.IDENT) and self.peek(1).token_type == TokenType.LEFT_PAREN:
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
		while self.expect(TokenType.PLUS, TokenType.MINUS):
			op = self.consume()
			right = self.parse_factor()
			left = BinExpr(left, op, right)
		return left
	
	def parse_factor(self):
		left = self.parse_unary()
		while self.expect(TokenType.STAR, TokenType.SLASH):
			op = self.consume()
			right = self.parse_unary()
			left = BinExpr(left, op, right)
		return left
	
	def parse_unary(self):
		if self.expect(TokenType.STAR, TokenType.MINUS, TokenType.AMPERSAND):
			op = self.consume()
			operand = self.parse_primary()
			return UnaryExpr(op, operand)
		return self.parse_primary()
	
	def parse_primary(self, type=None):
		if type and not self.expect(type):
			self.require(type)
		if self.expect(TokenType.IDENT, TokenType.NUMBER):
			return Primary(self.consume())
		elif self.expect(TokenType.LEFT_PAREN):
			self.consume()
			expr = self.parse_expr()
			self.require(TokenType.RIGHT_PAREN)
			return expr
		else:
			raise ParserException("expected primary expression", self.peek().line_number)
