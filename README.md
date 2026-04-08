# Python LISP interpreter based on the original 1960 John McCarthy paper
"Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I"
https://www-formal.stanford.edu/jmc/recursive.pdf

This is a fascinating paper; many "new innovations" from the next 70 years of computer science are already laid out 
here, such as functional programming and garbage collection. It blew my mind the first time I realised that the 
short LISP m-expression on page 17 was the entire LISP interpreter itself.

## Why write this?
In my opinion, there is quite a jump from the original paper to all later practical LISP implementations.
I couldn't find any minimal code examples of theoretical LISP from the original paper.

I wrote this as a way for programmers to get their head around the mathematics of the paper, 
from a programmer's perspective, and to better appreciate how theoretical LISP became a practical programming language. 

I tried to write as much as I could without reference to any future work, only using what is found in the paper.

## The Python files
I built multiple implementations of increasing complexity, since the paper goes through multiple steps to arrive at a "final" language. 

The original paper does not give a definitive syntax for a usable language; it is a theoretical work. It was later adapted
into something practical. 
Therefore, these LISP variants are not to be particularly useful, correct, or elegant; 
they are possible interpretations of S-expression LISP from the original paper, and should be read
in conjunction with that.

## Disclaimer
Please do not take this code as a good example of a LISP implementation. I am not a mathematician, or particularly steeped in
compiler and grammar theory beyond the undergraduate level. I went for simplicity and faithfulness to the paper over good design.

