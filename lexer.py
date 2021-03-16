#!/usr/bin/env python

import itertools
import sys
from scanner import Scanner
from token import Token

debug = False
#debug = True

class Lexer(object):
    """An iterator which returns the lexemes from an input stream."""
    def __init__(self, source):
        self.source = source
        self.scanner = Scanner()

        # Presumably needed for split lines (but not yet implemented)
        self.cache = []

        # Gather leading liminal tokens before iteration
        lims = self.get_liminals()
        self.prior_tail = lims

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        # Gather lexemes for the next statement
        if self.cache:
            lexemes = self.cache
        else:
            line = next(self.source)
            lexemes = self.scanner.parse(line)

        # TODO: Preprocessing

        header = self.prior_tail
        stmt = []
        prior_token = None
        for lx in lexemes:
            # Whitespace, comments
            if is_liminal(lx):
                if prior_token:
                    prior_token.tail.append(lx)
                # else:
                #   assert lx in header.split()[-1]
            # elif line continuation
            # elif semicolon
            else:
                tok = Token(lx)
                tok.head = prior_token.tail if prior_token else header

                stmt.append(tok)

                prior_token = tok

        # XXX: Does stmt always exist?  What if all comments?
        stmt[-1].tail.extend(self.get_liminals())
        self.prior_tail = stmt[-1].tail

        return stmt

    def get_liminals(self):
        lims = []
        self.source, lookahead = itertools.tee(self.source)

        for line in lookahead:
            lexemes = self.scanner.parse(line)
            for lx in lexemes:
                if is_liminal(lx):
                    lims.append(lx)
                else:
                    break

            # Move source forward if all tokens are liminal
            if all(is_liminal(lx) for lx in lexemes):
                next(self.source)
            else:
                break

        return lims


def is_liminal(lexeme):
    return lexeme.isspace() or lexeme[0] == '!'


def test_lexer():
    if not debug:
        # Print header
        with open('MOM.F90') as src:
            first_stmt = next(Lexer(src))
            print(''.join(first_stmt[0].head), end='')

    # Print statements with tails
    with open('MOM.F90') as src:
        for stmt in Lexer(src):
            if debug:
                # Lexemes + head/tail
                print('·'.join([lx for lx in stmt]))
                if stmt:
                    for lx in stmt:
                        print('lexeme: {}'.format(lx))
                        print('  head: {}'.format(lx.head))
                        print('  tail: {}'.format(lx.tail))

                s = ''.join([lx + ''.join(lx.tail) for lx in stmt])
                print(repr(s))
                print(80*'-')
            else:
                # "Roundtrip" render
                s = ''.join([lx + ''.join(lx.tail) for lx in stmt])
                print(s, end='')

    sys.exit()


if __name__ == '__main__':
    test_lexer()
