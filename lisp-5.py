# Python LISP interpreter based on the original 1960 John McCarthy paper:
# "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
# https://www-formal.stanford.edu/jmc/recursive.pdf
#
# Adds Common Lisp style macros
#
# Macros allow the language to be extended without modifying eval.
#
# Macros were not in the original paper, but they are a fundamental Lisp concept which
# addresses some of the inflexibility of the standard apply / eval loop. 
#
# Instead of macro parameters being evaluated as part of the apply step (i.e. applicative order evaluation), 
# they are substituted into the macro, and then the "patched" macro is evaluated.
#
# Previous commits of this interpreter used an old-school FEXPR macro system (i.e. you write macros like 
# normal functions, and substituting the parameters requires its own weird function). But because I already wrote 
# the quasiquote language feature, Common Lisp style macros (defined as a quoted list, not a function) 
# effectively come with it "for free". It's a very elegant synergy.
#
# For debugging, there is a macroexpand function, which will run the expansion without evaluating it.
#
# Note that this iteration of macros does not handle arbitrary numbers of parameters. But you can pass 
# lists and splice them using the ,@ token.

import re
from typing import Any

def lex(input):
	""" Tokenize the input string. """
	return re.findall(r",@|[()'`,]|[^\s()'`,]+", input)


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
	elif token == "`":
		return ['backquote', parse(tokens)]
	elif token == ",@":
		return ['commaat', parse(tokens)]
	elif token == ",":
		return ['comma', parse(tokens)]
	else:
		return token


def unparse(node):
	""" Produce tokens from Abstract Syntax Tree. Used for generating debug output in LISP."""
	if type(node) is list:
		listed = ""
		for x in node:
			listed += unparse(x) + " "
		return f"({listed[:-1]})"
	if is_atom(node):
		return node
	return node


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

def defmacro(args, env):
	""" Define a macro. Stores a special token 'macro' in the environment, which evalueates to a macro expansion."""
	name, params, body = args[0], args[1], args[2]
	env[name] = ["macro", params, body]
	return None


def macroexpand(node, env):
	""" Expand a macro. When we have quasiquote in our language, then we can
		implement Common Lisp style macros. These are trivial to expand.
		We simply evaluate the macro, which automatically 
		strips out the quotes and applies the parameters. We end up with
		Lisp code, ready to be evaled. """
	macro_def = node[0]     
	params = macro_def[1]
	body = macro_def[2]
	user_args = node[1:]

	substitutions = dict(zip(params, user_args))

	expanded_macro = eval(body, substitutions)

	return expanded_macro


def quasiquote(node, env) -> tuple[Any, bool]:
	""" Handle recursive backquote parsing.
		Returns a tuple of the constructed list, and whether it should be spliced into its parent list."""
	if is_atom(node):
		return node, False

	if len(node) > 0: 
		if node[0] == "comma":
			return eval(node[1], env), False
		elif node[0] == "commaat":
			return eval(node[1], env), True

	result = []
	for x in node:
		value, splice = quasiquote(x, env)
		if splice:
			result.extend(value)
		else:
			result.append(value)

	return result, False


def is_atom(exp): 
    return isinstance(exp, str)

def eval(node, env):
	""" Recursively evaluate an AST. """
	#print(f"Evaluating {node}")
	if type(node) is list:
		[fn, *args] = node

		if is_atom(fn):
			# In Lisp we always treat the first atom in a list as a function name.

			match fn:				
				case "quote":
					return args[0]
				case "backquote":
					# Return a list of quoted items. If there is a comma, then evaluate it instead.
					items, _ = quasiquote(args[0], env)
					return items
				case "atom":
					return "t" if is_atom(eval(args[0], env)) else "f"
				case "eq":
					lhs = eval(args[0], env)
					rhs = eval(args[1], env)
					return "t" if lhs == rhs and is_atom(lhs) else "f"
				case "car":
					evaled = eval(args[0], env)
					return evaled[0]
				case "cdr":
					evaled = eval(args[0], env)
					if len(evaled) == 1:
						return "nil"
					return evaled[1:]
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
				case "defmacro":
					return defmacro(args, env)
				case "macroexpand":
					macro_in = args[0]
					expression = eval(macro_in, env)
					macro_def = env[expression[0]] # fetch the macro from the environment.
					internal_node = [macro_def] + expression[1:] # do not mutate the expression list.
					return macroexpand(internal_node, env)
				case "print":
					value = eval(args[0], env)
					print(unparse(value))
					return value
				case _:
					# Must be a labelled function or macro if it is not inbuilt.
					try:
						function = env[fn]
					except KeyError:
						raise ValueError(f"Labelled function '{node}' not found. Available: {list(env.keys())}")
					
					if function[0] == "macro":
						# If this was a macro, then expand it and eval it.
						expanded = macroexpand([function] + args, env)
						return eval(expanded, env)

					return eval([function] + args, env)
		else:
			# Not an atom - this means it has a special meaning
			function_name = node[0][0]
			match function_name:
				case "lambda":
					# A special case to handle lambda function.
					return apply(node, env)
				case "label":
					# A special case to handle labelling a lambda function.
					return label(node, env)
				case _:
					raise ValueError(f"Cannot evaluate this list: {node}")
	elif type(node) is str:
		try:
			return env[node] # Lookup the value of the variable in our environment.
		except KeyError:
			raise ValueError(f"{node}: Variable '{node}' not found. Available: {env.keys()}")
	else:
		raise ValueError(f"invalid node: {node}")


def interpret(program, env=dict()):
	""" Process a string and produce an output. This is how we execute our programs."""
	tokens = lex(program)
	tree = parse(tokens)
	if not tree:
		raise ValueError("Probably missing a closing parenthesis.")
	result = eval(tree, env)
	return unparse(result)

def repl(env):
	""" Run in an endless loop of read, eval, print, loop. """
	print("Launching REPL...")
	while True:
		data = input("* ")
		if data == "\\quit":
			break
		try:
			print(interpret(data, env))
		except Exception as e:
			print(f"ERROR: {e}")
			#raise e # Uncomment to use the Python debugger for tracing errors

if __name__ == '__main__':
	""" Try evaluating some expressions."""


	env = dict()

	# Add the remaining functions needed to implement LISP eval and add it
	interpret("""
		   (progn 
			(defun caar (lst) (car (car lst)))
			(defun cddr (lst) (cdr (cdr lst)))
			(defun cadr (lst) (car (cdr lst)))
			(defun cdar (lst) (cdr (car lst)))
			(defun cadar (lst) (car (cdr (car lst))))
			(defun caddr (lst) (car (cdr (cdr lst))))
			(defun caddar (lst) (car (cdr (cdr (car lst)))))
		   
			(defun append (x y)
				(cond ((null x) y)
					('t (cons (car x) (append (cdr x) y)))))

			(defun assoc (var lst)
				(cond
					((null lst) key_error)
					((eq (caar lst) var) (cadar lst))
					('t (assoc var (cdr lst)))))
		   
			(defun eval (exp env)
			(cond
				((atom exp) (assoc exp env))
				((atom (car exp))
				(cond
				((eq (car exp) 'quote) (cadr exp))
				((eq (car exp) 'atom)  (atom (eval (cadr exp) env)))
				((eq (car exp) 'eq)    (eq   (eval (cadr exp) env)
												(eval (caddr exp) env)))
				((eq (car exp) 'car)   (car  (eval (cadr exp) env)))
				((eq (car exp) 'cdr)   (cdr  (eval (cadr exp) env)))
				((eq (car exp) 'cons)  (cons (eval (cadr exp) env)
												(eval (caddr exp) env)))
				((eq (car exp) 'cond)  (evcon (cdr exp) env))
				('t (eval (cons (assoc (car exp) env)
									(cdr exp))
							env))))
				((eq (caar exp) 'label)
				(eval (cons (caddar exp) (cdr exp))
						(cons (pair (cadar exp) (car exp)) env)))
				((eq (caar exp) 'lambda)
				(eval (caddar exp)
						(append (zip (cadar exp) (evlis (cdr exp) env))
								env)))))

			(defun evcon (c env)
			(cond ((eval (caar c) env)
					(eval (cadar c) env))
					('t (evcon (cdr c) env))))

			(defun evlis (m env)
			(cond ((null m) 'nil)
					('t (cons (eval  (car m) env)
							(evlis (cdr m) env)))))
		   	)
			
		   """, env)

	# Add some utility functions
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

  	(defun pair (x y)
  		(cons x (cons y 'nil)))

	(defun zip (x y)
		(cond ((and (null x) (null y)) 'nil)
			((and (not (atom x)) (not (atom y)))
			(cons (pair (car x) (car y))
				(zip (cdr x) (cdr y))))))

	(defun reverse (input)
		(
		   (label flip (lambda (in out) 
                   (cond ((atom in) out)
                         ('t (flip (cdr in) (cons (car in) out)))
		   )))
		   input 'nil
		)
	)
		   
	(defun replace (input search new_value)
	(cond
		((atom input)
		(cond ((eq input search) new_value)
			('t input)))
		('t
		(cons (replace (car input) search new_value)
			(replace (cdr input) search new_value)))))
)
		   """, env)
	
	# Add some useful macros.
	# For a proper if, we need to selectively evaluate the parameters. This would be impossible with a
	# function, because the parameters would be immediately evaluated, but easy with a macro.
	interpret("""
(progn
	(defmacro if (predicate value alternative)
		`(cond
			(,predicate ,value)
			('t ,alternative)
		)
	)
		   
	(defmacro unless (predicate value)
    	`(cond
      		((not ,predicate) ,value)
      		('t 'f)))
)""", env)

	#repl(env)

	# Check how our unless macro will be expanded
	print(interpret("""
	(macroexpand '(unless 't will_give_error))""", env))

	# Now run it - should return f
	print(interpret("""
  (unless 't will_give_error)
	""", env))

	# Check our if
	print(interpret("""
  (if 't
    'it_was_true
	'it_was_false))
				 """, env))
	
	# Check how a more complicated if macro will be expanded
	print(interpret("""
				 (macroexpand '(if (eq 'foo 'flob) 'im_true (cdr '('foo 'bar))))""", env))
	
	print(interpret("""
				 (if (eq 'foo 'flob) 'im_true (cdr '('foo 'bar)))""", env))
	
	print(interpret("""`(foo bar ,(cdr '('apple 'banana 'carrot)) ,@(cons 'a '('b 'c)))""", env))

	print(interpret("""`(foo bar ,(cdr '('apple 'banana 'carrot)))""", env))


	# Do something x+1 times, using unary encoding
	times_test = """
(progn
	(defmacro times (thing num)
	`(
		   (label do-it (lambda (count) 
				 (progn
					,thing
                   	(cond ((atom count) 't)
                         ('t (do-it (cdr count)))))))
			,num)
			)
	 
	(times 
		(times 
			(print `(Hi there ,(cdr '('foo 'bar)))) 
			'(a a)) 
		'(a a))
)"""
	print(interpret(times_test, env)) # prints many outputs

	auto_functions = """
(progn
	(defmacro make-functions (name name2)
	`(progn
			(defun ,name () (print '(Hi there from ,name)))
			(defun ,name2 () (print '(Hi there from ,name2)))
		)
	)
	 
	(make-functions foo bar)
	(foo)
	(bar) 
	(foo)
	(bar)
	(make-functions doo daa)
	(foo)
	(bar)
	(doo)
	(daa)
)"""
	print(interpret(auto_functions, env)) # We have many side effects because of the progn and print, so it prints again at the end.