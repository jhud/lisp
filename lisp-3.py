# Python LISP interpreter based on the original 1960 John McCarthy paper:
# "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
# https://www-formal.stanford.edu/jmc/recursive.pdf
#
# This is the final development of the previous LISP interpreter - it 
# deviates from the material in the paper, and works more like a practical
# interpreter by performing discrete lexing and parsing steps over the input LISP.
# 
# This file was based on the following impelmentations:
# Simple lexing and parsing:
# https://zstix.io/posts/make-a-lisp-in-python/
#
# Recommended if you want a usable LISP which is still very close to the McCarthy paper:
# http://kjetilvalle.com/posts/original-lisp.html


# --- Commands

# QUOTE(x) do not evaulate X, but return it back up the parse tree. Used for defining lists or constants.
# ATOM(x) true if x is atomic
# EQ(x,y) boolean, compare 2 if atoms are equal
# CAR(x) return the 1st element of the tuple
# CDR(x) return 2nd element of the tuple
# CONS(x; y) construct a list of x and y
# EQ(x; y) compare x to y and return true if they are equal
# COND (x; y) if x is true then y
# (LAMBDA, list of parameters, body), argument 1, argument 2, ...) - lambda function
# LABEL name a lambda function by putting it into the environment


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

def apply(node, env):
	""" Apply a lambda function: ((LAMBDA, list of parameters, body), argument 1, argument 2, ...)
	The format of this is not explicitly defined in the original paper, but we assume
	that it fits the standard format of (FUNCTION,parameter,parameter,...).
	"""
	function, args = node[0], node[1:]
	_, params, body = function

	# Evaluate all the arguments and create an env dictionary containing the params passed to the function.
	evaluated_args = {name: eval(val, env) for name,val in zip(params, args)}

	# Merge the dicts and evaluate the function.
	new_env = {**env, **evaluated_args} # order matters - evaluated args override existing env values.
	return eval(body, new_env)


def label(node, env):
	""" 
	Put a lambda function into the environment: (LABEL, label, function)
	and then call it.
	Labelled functions allow the lambda to refer to itself, to be used in recursion.
	"""
	_, var_name, function = node[0]
	args = node[1:]
	new_env = env.copy()
	new_env[var_name] = node[0]
	return eval([function] + args, new_env)

def is_atom(exp): 
    return isinstance(exp, str)

def eval(node, env):
	""" Recursively evaluate an AST. """
	if type(node) is list:
		[fn, *args] = node

		if is_atom(fn):
			# Treat atoms as function names. Handle the minimal inbuilt functions needed to interpret LISP in LISP.
			match fn:
				case "ATOM":
					return "t" if is_atom(eval(args[0], env)) else "f"
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
				case "CONS":
					rhs = eval(args[1], env)
					if rhs == 'nil':
						rhs = []
					lhs = eval(args[0], env)
					return [lhs] + rhs
				case "COND":
					for p, e in args:
						if eval(p, env) == 't':
							return eval(e, env)
				case _:
					# Must be a labelled function if it is not inbuilt.
					function = env[fn]
					return eval([function] + args, env)

		elif node[0][0] == "LAMBDA":
			# A special case to handle lambda function.
			return apply(node, env)
		elif node[0][0] == "LABEL":
			# A special case to handle lambda function.
			return label(node, env)
	elif type(node) is str:
		return env[node] # Lookup the value of the variable in our environment
	else:
		raise ValueError(f"invalid node: {node}")


def interpret(program):
	""" Process a string and produce an output. This is how we execute our programs."""
	tokens = lex(program)
	tree = parse(tokens)
	if not tree:
		raise ValueError("Probably missing a closing parenthesis.")
	return eval(tree, env=dict())

if __name__ == '__main__':
	""" Try evaluating some expressions."""
	print(interpret("""
					(EQ,
			 		(CDR,
			 			(QUOTE,
			 				((QUOTE,X),(QUOTE,Y),(QUOTE,Z))
			 			)
			 		),
			 (QUOTE,X)
			 )
""")) # prints f
	print(interpret("""(CONS, (QUOTE,A), (QUOTE,((QUOTE,X),(QUOTE,Y),(QUOTE,Z))))""")) # prints A,X,Y.Z
	print(interpret("""(COND,((EQ,(QUOTE,a),(QUOTE,b)),(QUOTE,first))
         				 ((ATOM,(QUOTE,a)),(QUOTE,second)))""")) # prints second
	print(interpret("""
				 ((LAMBDA,(x,y),(CONS,x,(CDR,y))),(QUOTE,z),(QUOTE,(a,b,c)))
				 """)) # prints zbc
	print(interpret("""
   	(
	  (LABEL,GREET,(LAMBDA,(x),
                   (COND,
				 		((ATOM,x),(CONS,(QUOTE,hello),(CONS,x,(QUOTE,nil)))),
                        ((QUOTE,t),(GREET,(CAR,x)))))),
      (QUOTE,(world))
   	)
""")) # prints hello world, and if the passed parameter is a list, it will recurse to use the first item of the list.



