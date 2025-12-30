# Python LISP interpreter based on the original 1960 John McCarthy paper:
# "Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
# https://www-formal.stanford.edu/jmc/recursive.pdf
#
# This LISP variant is not designed to be particularly useful, correct, elegant, or readable; 
# it is a minimal implementation of S-expression LISP from the original paper, and should be read
# in conjunction with that.
# 
# Why write this? There is quite a jump from the original paper to all later practical LISP implementations.
# I couldn't find any minimal code examples of theoretical LISP from the original paper, so I wrote it in order
# to better appreciate how theoretical LISP became a practical programming language.
#
# I made this without reference to any future work - it uses ordered pairs (2-tuples), without the shorthand
# comma format for representing lists. Not all functions are implemented - just the most basic ones from the paper.
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
	""" Squish a multline string and remove all whitespace for parsing."""
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


def parse(input: str):
	""" Evaluate an S-expression.
	Recurses into parentheses.
	"""
	if input[0] == "(":
		a, b = split_on_separator(input)

		if a == "CAR":
			a, b = split_on_separator(b)
			return (parse(a), None)
		elif a == "CDR":
			a, b = split_on_separator(b)
			return (parse(b), None)
		elif a == "CONS":
			sub_a, sub_b = split_on_separator(b)
			return (parse(sub_a), parse(sub_b))
		elif a == "EQ":
			sub_a, sub_b = split_on_separator(b)
			return (parse(sub_a) == parse(sub_b), None)		
		elif a == "COND":
			sub_a, sub_b = split_on_separator(b)
			test = parse(sub_a) # Returns a value and a terminating NIL
			eval_on_true = parse(sub_b)
			return (eval_on_true if test[0] else None, None)

		return (parse(a), parse(b))
	return f"'{input}"
		

if __name__ == '__main__':
	""" Try evaluating some expressions. """
	#parse("(A.((B.(C.NIL)).(D.NIL)))")
	#parse("(CAR.(X.Y))") # returns X
	#parse("(CAR.((CDR.(X.Y)).Z))") # returns Y	
	#print(parse("(CONS.((CAR.(A.B)).(CDR.(A.C))))")) # returns (A,C)
	#print(parse("(CONS.((CONS.(A.B)).C))")) # returns ((A.B).C)
	#print(parse(oneline("""
			 (CONS.(
			 	(CONS.(
			 		(CAR.(A.B)).
			 		(CDR.(A.C))
			 	)).D))"""))) # returns ((A.C).D)
	print(parse(oneline("""
			 (COND.(
			 	(EQ.(
			 		A.
			 		A)
			 	).TRUE))"""))) # returns (TRUE, NIL)
