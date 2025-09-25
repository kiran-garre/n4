from tokenizer import *
from parser import *
from semantic_analyzer import *
from ssa_parser import *
from PrettyPrint import PrettyPrintTree

path = "example.n4"

with open(path, 'r') as file:
	content = file.read()

tokenizer = Tokenizer(content, path)
tokenizer.tokenize()
# token_types = list(map(lambda x: x.token_type.name, tokenizer.tokens))

parser = Parser(tokenizer.tokens, path)
parser.parse_program()

semantic_analyzer = SemanticAnalyzer(parser.ast, path)
semantic_analyzer.analyze()

tokenizer.display_errors()
parser.display_errors()
semantic_analyzer.display_errors()

print()
pt = PrettyPrintTree(lambda x: x.get_children(), lambda x: x.get_value())
pt(parser.ast)
print()