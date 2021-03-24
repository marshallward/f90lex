#!/usr/bin/env python
import sys

from f90lex.scanner import Scanner


def test_scanner():
    fname = sys.argv[1]

    scanner = Scanner()
    with open(fname) as f:
        for line in f:
            lexemes = scanner.parse(line)
            print(' · '.join([repr(lx)[1:-1] for lx in lexemes]))


if __name__ == '__main__':
    test_scanner()
