#!/usr/bin/env python

import itertools
import sys

from scanner import Scanner
from token import Token

#debug = False
debug = True

class Lexer(object):
    """An iterator which returns the lexemes from an input stream."""
    def __init__(self, source):
        self.source = source
        self.scanner = Scanner()

        # Split line cache
        self.cache = []

        # Gather leading liminal tokens before iteration
        self.prior_tail = self.get_liminals()

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        # Gather lexemes for the next statement
        if self.cache:
            lexemes = self.cache
            self.cache = []
        else:
            line = next(self.source)
            lexemes = self.scanner.parse(line)

        # TODO: Preprocessing

        prior_tail = self.prior_tail
        statement = []
        line_continue = True

        while line_continue:
            line_continue = False

            for lx in lexemes:
                if lx.isspace() or lx[0] == '!':
                    prior_tail.append(lx)

                elif lx == ';':
                    # Pull liminals and semicolons from the line
                    idx = lexemes.index(';')
                    for lx in lexemes[idx:]:
                        if is_liminal(lx):
                            prior_tail.append(lx)
                            idx += 1
                        else:
                            break

                    self.cache = lexemes[idx:]
                    self.prior_tail = prior_tail
                    break

                elif lx == '&':
                    # Stick with the simple case for now...
                    idx = lexemes.index('&')
                    prior_tail += lexemes[idx:]
                    lexemes = self.scanner.parse(next(self.source))
                    line_continue = True
                    break

                else:
                    tok = Token(lx)
                    tok.head = prior_tail

                    statement.append(tok)
                    prior_tail = tok.tail

        if not self.cache:
            statement[-1].tail.extend(self.get_liminals())
            self.prior_tail = statement[-1].tail

        return statement

    def get_liminals(self):
        lims = []
        for line in self.source:
            lexemes = self.scanner.parse(line)

            new_lims = itertools.takewhile(is_liminal, lexemes)
            lims += list(new_lims)

            stmt = itertools.dropwhile(is_liminal, lexemes)
            self.cache = list(stmt)
            if self.cache:
                break

        return lims


def is_liminal(lexeme):
    # XXX: Adding '&' here is incorrect.  We need to catch leading '&' lexemes
    #   and resolve the various reconstructions that can occur.
    #   It's only added here for now to resolve the most common cases.
    return lexeme.isspace() or lexeme[0] == '!' or lexeme == ';' or lexeme == '&'


def test_lexer():
    fname = sys.argv[1]

    if not debug:
        # Print header
        with open(fname) as src:
            lxr = Lexer(src)
            first_stmt = next(lxr)
            print(''.join(first_stmt[0].head), end='')

    # Print statements with tails
    with open(fname) as src:
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
