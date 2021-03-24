#!/usr/bin/env python
import os
import sys

from f90lex.lexer import Lexer

debug = False
#debug = True


def test_lexer():
    fname = sys.argv[1]

    # Print statements with tails
    with open(fname) as src:
        lexer = Lexer(src)
        if not debug:
            print(''.join(lexer.prior_tail), end='')

        for stmt in lexer:
            if debug:
                # Lexemes + head/tail
                print(' · '.join([lx for lx in stmt]))
                if stmt:
                    for lx in stmt:
                        print('lexeme: {}'.format(lx))
                        print('  head: {}'.format(lx.head))
                        if lx.split:
                            print(' split: {}'.format(repr(lx.split)))
                        if hasattr(lx, 'pp'):
                            print('    pp: {}'.format(repr(lx)))
                        print('  tail: {}'.format(lx.tail))

                    s = ''.join([
                        (lx.split if lx.split else str(lx)) + ''.join(lx.tail)
                        for lx in stmt
                    ])
                print(repr(s))
                print(80*'-')
            else:
                # "Roundtrip" render
                s = ''.join([
                    (lx.split if lx.split else str(lx)) + ''.join(lx.tail)
                    for lx in stmt
                ])
                print(s, end='')


if __name__ == '__main__':
    test_lexer()
    sys.exit()
