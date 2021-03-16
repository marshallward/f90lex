f90lex
======
   
f90lex is an attempt to build a roundtrip Fortran lexer (and maybe eventually a
parser).

A refactor of flint's scanner and lexer ("Tokenizer", "FortLines") into
something more manageable.

Also a sandbox to see how a simple lexer could be written as a portable
C library.

Goals:
* Streamline the chaotic logic of flint's lexer
* Preserve all non-semantic tokens (I call these "liminals")

Eventually to be absorbed into [flint](https://github.com/marshallward/flint).
