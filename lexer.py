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

        header = self.prior_tail
        statement = []
        prior_token = None
        for lx in lexemes:
            if lx.isspace() or lx[0] == '!':
                if prior_token:
                    prior_token.tail.append(lx)
                # else:
                #   assert lx in self.prior_tail
            # elif line continuation
            #     TODO!
            elif lx == ';':
                # Pull liminals and semicolons from the line
                # Can I use get_liminals here?
                idx = lexemes.index(';')
                for lx in lexemes[idx:]:
                    if is_liminal(lx):
                        if prior_token:
                            prior_token.tail.append(lx)
                        idx += 1
                    else:
                        break

                self.cache = lexemes[idx:]
                if prior_token:
                    self.prior_tail = prior_token.tail
                break
            else:
                tok = Token(lx)
                tok.head = prior_token.tail if prior_token else header

                statement.append(tok)

                prior_token = tok

        if not self.cache:
            statement[-1].tail.extend(self.get_liminals())
            self.prior_tail = statement[-1].tail

        return statement

    def get_liminals(self):
        lims = []
        for line in self.source:
            lexemes = self.scanner.parse(line)
            is_lim = lambda lx: is_liminal(lx)

            new_lims = itertools.takewhile(is_liminal, lexemes)
            lims += list(new_lims)

            stmt = itertools.dropwhile(is_liminal, lexemes)
            self.cache = list(stmt)
            if self.cache:
                break

        return lims


def is_liminal(lexeme):
    return lexeme.isspace() or lexeme[0] == '!' or lexeme == ';'


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
