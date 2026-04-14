#
# This file is based on the first part of the paper: it uses ordered pairs (2-tuples), otherwise known as "cons cells".
# The paper later introduces a notation for arbitrarily long lists, beacuse this notation quickly becomes impractical when trying to
# write actual programs. For this reason, not all functions are implemented - just the most basic ones from the paper, in 
# order to demonstrate the basic concepts.
#
# You can build arbitrarily long lists, and in fact everything else in LISP, by using these ordered pairs. On the hardware level, 
# each ordered pair represents a node in a linked list.
#
# Some assorted tips for reading the paper from a Python perspective:
# - S-expressions are simply nested ordered lists, with "atoms" (value instances) as leaves. This format later became the preferred standard for coding LISP.
# - M-expressions (meta-expressions) are lower-case and square bracketed. They act on the S-expressions. This is a more traditional mathematical notation of LISP and was not really used for coding.
# - an ordered pair is denoted with a dot. Commas represent the list shorthand for composing lists from these pairs.
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


def oneline(input):
	""" Squish a multiline string and remove all whitespace for parsing."""
	return ''.join(input.split())

def split_on_separator(input: str, separator="."):
	""" Split a parenthesized string into a 2-tuple. Discard the outer parentheses.
	 Defaults to the original paper's use of . to denote an ordered pair.
	 i.e: ((AB.C).D) returns a tuple of (AB.C) and (D)"""
	depth = 0
	for i, x in enumerate(input):
		if x == "(":
			depth += 1
		if x == ")":
			depth -= 1
		if depth == 1 and x == separator:
			return (input[1:i], input[i+1:-1])
	raise Exception("mismatched parentheses")


def eval(input: str):
	""" Evaluate an S-expression.
	Recurses into parentheses.
	"""
	if input[0] == "(":
		a, b = split_on_separator(input)

		if a == "CAR":
			a, b = split_on_separator(b)
			return (eval(a), None)
		elif a == "CDR":
			a, b = split_on_separator(b)
			return (eval(b), None)
		elif a == "CONS":
			sub_a, sub_b = split_on_separator(b)
			return (eval(sub_a), eval(sub_b))
		elif a == "EQ":
			sub_a, sub_b = split_on_separator(b)
			return (eval(sub_a) == eval(sub_b), None)		
		elif a == "COND":
			sub_a, sub_b = split_on_separator(b)
			test = eval(sub_a) # Returns a value and a terminating NIL
			eval_on_true = eval(sub_b)
			return (eval_on_true if test[0] else None, None)

		return (eval(a), eval(b))
	return f"'{input}"
		

if __name__ == '__main__':
	""" Try evaluating some expressions. Some of these are from the original paper."""
	print(eval("(A.((B.(C.NIL)).(D.NIL)))")) # returns (A,(B,(C,NIL)),(D, NIL)) - nothing to evaluate
	print(eval("(CAR.(X.Y))")) # returns X
	print(eval("(CAR.((CDR.(X.Y)).Z))")) # returns Y	
	print(eval("(CONS.((CAR.(A.B)).(CDR.(A.C))))")) # prints (A,C)
	print(eval("(CONS.((CONS.(A.B)).C))")) # prints ((A.B).C)
	print(eval(oneline("""
			 (CONS.(
			 	(CONS.(
			 		(CAR.(A.B)).
			 		(CDR.(A.C))
			 	)).D))"""))) # prints ((A.C).D)
	print(eval(oneline("""
			 (COND.(
			 	(EQ.(
			 		A.
			 		A)
			 	).TRUE))"""))) # prints (TRUE, NIL)
