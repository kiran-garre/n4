from parser import *

OPERATOR_TO_INSTRUCTION = {
	TokenType.PLUS: 			'add',
	TokenType.MINUS: 			'sub',
	TokenType.STAR: 			'mul',
	TokenType.SLASH: 			'div',
	TokenType.LESS: 			'lt',
	TokenType.GREATER: 			'gt',
	TokenType.LESS_EQUAL: 		'lte',
	TokenType.GREATER_EQUAL: 	'gte',
}

SEMANTIC_RED_ERROR = "\033[1m\033[91msemantic error:\033[0m"

# This is NOT an exception and cannot be caught
class SemanticError:
	def __init__(self, message, line_number):
		self.message = message
		self.line_number = line_number

class SemanticAnalyzer:
	def __init__(self, ast, filename):
		self.ast = ast
		self.filename = filename
		self.scope_stack = [dict()]
		self.reports = []
		self.reported = set()

	def display_errors(self):
		for error in self.reports:
			print(f"{self.filename}:{error.line_number}: {SEMANTIC_RED_ERROR} {error.message}")

	def report(self, name: str, message: str, line_number=0):
		if name in self.reported:
			return
		self.reports.append(SemanticError(message, line_number))
		self.reported.add(name)

	def access(self, node: Primary):
		name = node.get_name()
		for scope in reversed(self.scope_stack):
			if name in scope:
				node.dtype = scope[name]
				print(id(node))
				return
		self.report(name, f"'{name}' used before definition", node.line)

	def define(self, node: Primary, type: str):
		name = node.get_name()
		if name in self.scope_stack[-1]:
			self.report(name, f"redefinition of '{name}'", node.line)
			return
		self.scope_stack[-1][name] = type
		node.type = type

	def new_scope(self):
		self.scope_stack.append(dict())

	def end_scope(self):
		self.scope_stack.pop()

	def fitting_int_type(value):
		return "int"

	def postorder(self, node):
		"""
		Assumes that AST is syntactically correct.
		"""
		print(self.scope_stack)
		if isinstance(node, Primary):
			if node.token.token_type == TokenType.IDENT:
				print(id(node))
				self.access(node)
			elif node.token.token_type == TokenType.NUMBER:
				node.dtype = SemanticAnalyzer.fitting_int_type(node.token.literal)
		elif isinstance(node, UnaryExpr):
			self.postorder(node.operand)
		elif isinstance(node, BinExpr):
			self.postorder(node.left)
			self.postorder(node.right)
		elif isinstance(node, FunctionCall):
			self.access(node)
			for arg in node.args:
				self.postorder(arg)
		elif isinstance(node, AssignmentStatement):
			self.postorder(node.lhs)
			self.postorder(node.rhs)
		elif isinstance(node, DefinitionStatement):
			self.define(node.ident, node.type)
			self.postorder(node.rhs)
		elif isinstance(node, ReturnStatement):
			self.postorder(node.expr)
		elif isinstance(node, IfStatement):
			self.new_scope()
			self.postorder(node.condition)
			self.postorder(node.true_body)
			if node.false_body:
				self.postorder(node.false_body)
			self.end_scope()
		elif isinstance(node, WhileStatement):
			self.new_scope()
			self.postorder(node.condition)
			self.postorder(node.body)
			self.end_scope()
		elif isinstance(node, Body):
			for statement in node.statements:
				self.postorder(statement)
		elif isinstance(node, Param):
			self.define(node, node.type)
		elif isinstance(node, FunctionDefinition):
			self.define(node, node.return_type.literal)
			self.new_scope()
			for param in node.params:
				self.postorder(param)
			self.postorder(node.body)
			self.end_scope()
		elif isinstance(node, Program):
			for child in node.contents:
				self.postorder(child)
	
	def analyze(self):
		self.postorder(self.ast)
		

"""
IMPLEMENTATION DETAILS:

1. postorder() walk logic
Below I'll go through the logic for each case.

- If the node is a primary:
	We only care if the node is an identifier. If it is, we make sure that it
	exists in scope. Otherwise, we report an error.
- If the node is a unary expression:
	We recurse on the single operand.
- If the node is a binary expression:
	We recurse on the left and right sides to make sure every primary has been
	accessed.
- If the node is an assignment:
	If the left hand side is an identifier, it must be being assigned to,
	so we add it to our scope table with it's type or "any" if not specified. 
	Otherwise, every variable on the left side is being accessed, so we recurse 
	on the left side like normal. We also  recurse on the right side like 
	normal.
- If the node is a program:
	This is the starting node of an AST, so we recurse on each of the node's
	children.
"""