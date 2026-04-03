# Python LISP interpreter based on the original 1960 John McCarthy paper:
# "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
# https://www-formal.stanford.edu/jmc/recursive.pdf
#
# Based on Kjetil Valle's parser to make it look more like practical LISP,
# and give some quality-of-life improvements outside the paper.
#
# - uses lowercase
# - spaces instead of commas
# - adds function management
# 
# This file was based on the following implementations:
# Simple lexing and parsing:
# https://zstix.io/posts/make-a-lisp-in-python/
#
# Recommended if you want a usable LISP which is still very close to the McCarthy paper:
# http://kjetilvalle.com/posts/original-lisp.html


import re


def lex(input):
	""" Tokenize the input string. """
	return re.findall(r"[()']|[^() \n\t']+", input)


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
	elif token == "'":
		return ['quote', parse(tokens)]
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

def defun(args, env):
	""" Define function. Modifies the global environment. """
	name, params, body = args[0], args[1], args[2]
	env[name] = ["label", name, ["lambda", params, body]]
	return name

def is_atom(exp): 
    return isinstance(exp, str)

def eval(node, env):
	""" Recursively evaluate an AST. """
	if type(node) is list:
		[fn, *args] = node

		if is_atom(fn):
			# Treat atoms as function names. Handle the minimal inbuilt functions needed to interpret LISP in LISP.
			match fn:
				case "atom":
					return "t" if is_atom(eval(args[0], env)) else "f"
				case "quote":
					return args[0]
				case "car":
					evaled = eval(args[0], env)
					return evaled[0]
				case "cdr":
					evaled = eval(args[0], env)
					if len(evaled) == 1:
						return "nil"
					return evaled[1:]
				case "eq":
					lhs = eval(args[0], env)
					rhs = eval(args[1], env)
					return "t" if lhs == rhs and is_atom(lhs) else "f"
				case "cons":
					rhs = eval(args[1], env)
					if rhs == 'nil':
						rhs = []
					lhs = eval(args[0], env)
					return [lhs] + rhs
				case "cond":
					for p, e in args:
						if eval(p, env) == 't':
							return eval(e, env)
				case "defun":
					return defun(args, env)
				case "progn":
					for expression in args:
						result = eval(expression, env)
					return result
				case _:
					# Must be a labelled function if it is not inbuilt.
					function = env[fn]
					return eval([function] + args, env)

		elif node[0][0] == "lambda":
			# A special case to handle lambda function.
			return apply(node, env)
		elif node[0][0] == "label":
			# A special case to handle lambda function.
			return label(node, env)
	elif type(node) is str:
		return env[node] # Lookup the value of the variable in our environment
	else:
		raise ValueError(f"invalid node: {node}")


def interpret(program, env=dict()):
	""" Process a string and produce an output. This is how we execute our programs."""
	tokens = lex(program)
	tree = parse(tokens)
	if not tree:
		raise ValueError("Probably missing a closing parenthesis.")
	return eval(tree, env)

if __name__ == '__main__':
	""" Try evaluating some expressions."""


	env = dict()
	interpret("""
		   (progn 
(defun null (x)
	(eq x 'nil))
		   
(defun and (x y)
    (cond (x (cond (y 't) ('t 'f)))
          ('t 'f)))

(defun or (x y)
    (cond (x 't) 
          ('t (cond (y 't) ('t 'f)))))

(defun not (x)
    (cond (x 'f)
          ('t 't)))

		   )
		   """, env)
	
	print(interpret("(null '(foo bar))", env))
	print(interpret("(and 't 't)", env))
	
	print(interpret("""
					(eq
			 		(cdr 'X 'Y 'Z) 'X)
""")) # prints f
	print(interpret("""(cons 'A '(X Y Z))""")) # prints A,X,Y.Z
	print(interpret("""	(cond
				 		 	((eq 'a 'b) 'first)
         					((atom 'a) 'second)
				 		)""")) # prints second
	print(interpret("""
  ((lambda (x y) (cons x (cdr y)))
       'z
       '(a b c))
 """)) # prints zbc
	print(interpret("""
   ((label greet (lambda (x) 
                   (cond ((atom x) 
                           (cons 'hello (cons x 'nil)))
                         ('t (greet (car x))))))
    '(world))
 """)) # prints hello world, and if the passed parameter is a list, it will recurse to use the first item of the list.



