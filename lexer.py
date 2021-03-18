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
        prior_tail = self.prior_tail
        statement = []
        line_continue = True

        while line_continue:
            line_continue = False

            # Gather lexemes for the next statement
            if self.cache:
                lexemes = self.cache
                self.cache = []
            else:
                line = next(self.source)
                lexemes = self.scanner.parse(line)

            # Reconstruct any line continuations
            if lexemes[0] == '&':
                # First check if split ends are separate by whitespace
                lx_split = prior_tail[0].isspace() or lexemes[1].isspace()
                if not lx_split:
                    # Try to reconstruct the potential tokens
                    # NOTE: scanner needs an endline, so we add then drop it
                    lx_join = statement[-1] + lexemes[1] + '\n'

                    # NOTE: The scanner has a "state" in that it tracks the
                    #   string delimiter across lines.  So we store this
                    #   delimiter before using it on this local string.
                    delim = self.scanner.prior_delim
                    new_lx = self.scanner.parse(lx_join)[:-1]
                    self.scanner.prior_delim = delim

                    lx_split = len(new_lx) > 1

                if not lx_split:
                    stok = statement[-1]
                    tok = Token(''.join(new_lx[:2]))

                    tok.head = stok.head

                    # Set up the interior liminal tokens (what a paradox!)
                    prior_tail.append('&')

                    sp = stok.split if stok.split else str(stok)
                    sp = sp + ''.join(prior_tail) + lexemes[1]
                    tok.split = sp
                    prior_tail = []

                    # Currently empty, but may be filled after iteration
                    tok.tail = prior_tail

                    # Assign the new reconstructed token
                    statement[-1] = tok

                    # XXX: Should new_lx[2:] be prepended here?  Does that
                    #   then mean that lexemes needs to start higher up?
                    lexemes = lexemes[2:]
                else:
                    # Append token and proceed as normal
                    prior_tail.append('&')
                    lexemes = lexemes[1:]

            # TODO: Preprocessing

            for lx in lexemes:
                if lx.isspace() or lx[0] == '!':
                    prior_tail.append(lx)

                elif lx == ';':
                    # Pull liminals and semicolons from the line
                    idx = lexemes.index(';')
                    for lx in lexemes[idx:]:
                        # NOTE: Line continuations after ; are liminals
                        if is_liminal(lx) or lx == '&':
                            prior_tail.append(lx)
                            idx += 1
                        else:
                            break

                    self.cache = lexemes[idx:]
                    self.prior_tail = prior_tail
                    break

                elif lx == '&':
                    idx = lexemes.index('&')
                    prior_tail += lexemes[idx:] + self.get_liminals()
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
                        if lx.split:
                            print(' split: {}'.format(repr(lx.split)))
                        print('  tail: {}'.format(lx.tail))

                    s = ''.join([
                        (lx.split if lx.split else lx) + ''.join(lx.tail)
                        for lx in stmt
                    ])
                print(repr(s))
                print(80*'-')
            else:
                # "Roundtrip" render
                s = ''.join([
                    (lx.split if lx.split else lx) + ''.join(lx.tail)
                    for lx in stmt
                ])
                print(s, end='')

    sys.exit()


if __name__ == '__main__':
    test_lexer()
