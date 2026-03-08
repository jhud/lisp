# Python LISP interpreter based on the original 1960 John McCarthy paper:
# "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
# https://www-formal.stanford.edu/jmc/recursive.pdf
#
# This is a development of my previous LISP interpreter - it uses the shorthand comma-format for defining arbitrary-length lists, instead
# of 2-tuple dot format.
# We dispense completely with the "." tuple, and only use the comma format, like the last half of the paper.
# 
# - e is the body of a function in modern parlance
# - label(a, e) defines a function e named a

# --- Commands

# ATOM(x) true if x is atomic
# EQ(x,y) boolean, compare 2 if atoms are equal
# CAR(x) return the 1st element of the tuple
# CDR(x) return 2nd element of the tuple
# CONS(x; y) make a tuple of x and y
# EQ(x; y) compare x to y and return true if they are equal
# COND (x; y) if x is true then y


from typing import List


def oneline(input):
	""" Squish a multline string and remove all whitespace for parsing."""
	return ''.join(input.split())

def split_list(input: str, separator=",") -> List:
	""" Split a parenthesized string into a Python list, to a depth of 1. Discard the outer parentheses.
	 Defaults to the original paper's use of , to denote an arbitrary-length list.
	 i.e: ((AB,C,D), E, F) returns a list of ["(AB,C,D)", "E", "F"]"""
	if input[0] != "(":
		raise Exception(f"Missing opening parenthesis for '{input}'")
	if input[-1] != ")":
		raise Exception(f"Missing closing parenthesis for '{input}'")
	
	ret = []
	parsed_to = 0
	depth = 0
	for i, x in enumerate(input):
		if x == "(":
			depth += 1
		if x == ")":
			depth -= 1
		elif depth == 1 and x == separator:
			ret.append(input[parsed_to+1:i])
			parsed_to = i

	ret.append(input[parsed_to+1:-1]) # Get the last item, up to the closing parenthesis
	return ret


def eval(input: str) -> List:
	""" Evaluate an S-expression.
	Recurses into parentheses.
	"""
	if input[0] == "(":
		splitted = split_list(input)
		first = splitted[0]

		if first == "CAR":
			return eval(splitted[1])[0]
		elif first == "CDR":
			return eval(splitted[1])[1]
		elif first == "CONS":
			if len(splitted) != 3:
				raise Exception(f"Need 2 parameters after CONS. Got {splitted}")
			first_parameter = eval(splitted[1])
			second_parameter = eval(splitted[2])
			return first_parameter + second_parameter
		elif first == "COND":
			splitted.pop(0)
			while len(splitted) > 0:
				conditional = split_list(splitted.pop(0))
				if eval(conditional[0]) == "TRUE":
					return eval(conditional[1])
			return "FALSE"
		elif first == "ATOM":
			return [splitted[1]]
		elif first == "EQ":
			first_parameter = eval(splitted[1])
			second_parameter = eval(splitted[2])
			if first_parameter == second_parameter:
				return "TRUE"
			return "FALSE"

		return [eval(x) for x in splitted]
	return [f"'{input}"]

if __name__ == '__main__':
	""" Try evaluating some expressions. Some of these are from the original paper."""
	print(eval("(A,(B,C),D)")) # returns [A,[B,C],D]
	print(eval("(CAR,((ATOM,X),(ATOM,Y)))")) # returns [X]
	print(eval("(CAR,(CDR,((ATOM,X),(ATOM,Y))),(ATOM,Z))")) # returns [Y]	
	print(eval("(CONS,(CAR,((ATOM,A),(ATOM,B))),(CDR,((ATOM,A),(ATOM,C))))")) # prints (A,C)
	print(eval("(CONS,(CONS,(ATOM,A),(ATOM,B)),(ATOM,C))")) # prints (A,B,C)
	print(eval(oneline("""
			 (CONS,
			 	(CONS,(CAR,(A,B)),(CDR,(A,C))),
				(ATOM,D)
			 )"""))) # prints ((A,C),D)
	print(eval("(COND,((EQ,(ATOM,A),(ATOM,B)),(ATOM,FOO)),((EQ,(ATOM,B),(ATOM,B)),(ATOM,BAR)))")) # prints BAR
