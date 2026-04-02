# Python LISP interpreter based on the original 1960 John McCarthy paper:
# "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
# https://www-formal.stanford.edu/jmc/recursive.pdf
#
# This is the final development of the previous LISP interpreter - it 
# deviates from the material in the paper, and works more like a practical
# interpreter by performing discrete lexing and parsing steps over the input LISP.
# 
# - e is the body of a function in modern parlance
# - label(a, e) defines a function e named a
# - * means translate M-expression to an equivalent S-expression

# --- Commands

# QUOTE(x) do not evaulate X, but return it back up the parse tree. Used for defining lists or constants.
# ATOM(x) true if x is atomic
# EQ(x,y) boolean, compare 2 if atoms are equal
# CAR(x) return the 1st element of the tuple
# CDR(x) return 2nd element of the tuple
# CONS(x; y) make a tuple of x and y
# EQ(x; y) compare x to y and return true if they are equal
# COND (x; y) if x is true then y


from typing import List
import re


def lex(input):
	""" Tokenize the input string. """
	return re.findall(r"[()]|[^(), \n\t]+", input)


def parse(tokens):
	""" Construct Abstract Syntax Tree from tokens. """
	token = tokens.pop(0)
	if token == "(":
		result = []
		while len(tokens):
			if tokens[0] == ")":
				tokens.pop(0)
				return result
			else:
				result.append(parse(tokens))
	else:
		return token


def is_atom(exp): 
    return isinstance(exp, str)

def eval(node, env):
	""" Recursively evaluate an AST. """
	print(f"Evaluating {node}")
	if type(node) is list:
		[fn, *args] = node
		match fn:
			case "ATOM":
				return "t" if is_atom(eval(args[0])) else "f"
			case "QUOTE":
				return args[0]
			case "CAR":
				evaled = eval(args[0], env)
				return evaled[0]
			case "CDR":
				evaled = eval(args[0], env)
				if len(evaled) == 1:
					return "nil"
				return evaled[1:]
			case "EQ":
				lhs = eval(args[0], env)
				rhs = eval(args[1], env)
				return "t" if lhs == rhs and is_atom(lhs) else "f"
			case _:
				raise ValueError(f"Undefined function: {fn}")
	elif type(node) is str:
		return node # atom - eventually this should look up the value
	else:
		raise ValueError(f"invalid node: {node}")


def apply(program):
	tokens = lex(program)
	tree = parse(tokens)
	return eval(tree, env=dict())

if __name__ == '__main__':
	""" Try evaluating some expressions."""
	print(apply("""
					(EQ,
			 		(CDR,
			 			(QUOTE,
			 				(X,Y,Z)
			 			)
			 		),
			 X
			 )
"""))




