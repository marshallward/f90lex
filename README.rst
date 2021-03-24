=================================
f90lex: a roundtrip Fortran lexer
=================================

A Python module for generating the lexical tokens of a Fortran source program.


About
=====

``f90lex`` is a Python module that provides a means for generating both the
semantic and liminal tokens of a Fortran source file.

I use *liminal* here to describe the non-semantic tokens which separate the
semantic ones.  This includes the whitespace, comments, and any preprocessing
statements which separate the semantic data.


Usage
=====

This module provides a ``Lexer`` iterator which is initialized with an input
stream (usually a source code file) and returns the next complete Fortran
statement.

Each statement is a list of semantic Fortran tokens.  In addition to its
identifier (symbol, etc), it also contains a ``head`` and ``tail`` which
contain any liminal tokens preceding or following the token.  The tokens can be
passed to a Fortran parser, and can also be used to re-construct the original
source.

For example, consider the following Fortran program:

.. code:: fortran

   program test
   integer :: x

   x = 1+2
   print*,x
   end

If we run the following code block:

.. code:: python

   with open('test.f90') as f:
       lexer = Lexer(f)
       for line in lexer:
           print(line)

Then we produce the following tokens::

   ['program', 'test']
   ['integer', '::', 'x']
   ['x', '=', '1', '+', '2']
   ['print', '*', ',', 'x']
   ['end']

Each element is a ``Token``, which contains its liminal tokens as metadata.
Example output is shown below.::

   lexeme: integer
     head: ['\n', '  ']
     tail: [' ']
   lexeme: ::
     head: [' ']
     tail: [' ']
   lexeme: x
     head: [' ']
     tail: ['\n', '  ', '\n', '  ']

Liminal tokens are doubly linked; each tokens ``head`` points to the same list
as the prior token's ``tail``.  The first and last token point to any liminals
at the beginning and the end of the file.

The liminals can be used to reconstruct the original source code.::

   'program test\n  '
   'integer :: x\n  \n  '
   'x = 1+2\n  '
   'print*,x\n'
   'end\n'


Supported features
==================

* Case-insensitive tests

  The token's case sensitivity is preserved, but its case-insensitive value is
  used in equality tests or dictionary hashing.

* Comments

  Comments are stored as liminals in the ``tail`` of the preceding token (or
  ``head`` of the following), and are gathered as a single parseable token.
  "Docstring"-style comments (such as used in Doxygen or FORD) can be inspected
  during parsing.

* Line continuation tokens (``&``)

  Line continuations using ``&``, including split tokens, are supported, and
  the full reconstructed statement is returned on each iteration.

* Statement terminators (``;``)

  Statement termination token (``;``) is supported, with each part of the token
  producing a separate statement, and the ``;`` stored as liminal.

  Repeated ``;`` tokens are gathered together; empty statements are not returned
  and are instead gathered as liminal tokens.

* Preprocessing

  Preprocessing of macros and headers is supported.  Macro functions and
  logical expressions are not yet supported.

  When a preprocessor token is encountered, the directive is stored as a
  liminal.  Any macros are stored and applied to future tokens.  Any statements
  contains in headers (via ``#include``) are returned, but are rendered as
  empty strings when printed as output. 


Background
==========

This project was developed to provide the flint_ Fortran analysis tool with a
complete roundtrip parser and provide a complete description of the source code
and its whitespace.  It also servers as a template for future lexer
development.

.. _flint:  https://github.com/marshallward/flint
