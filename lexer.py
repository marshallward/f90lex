#!/usr/bin/env python

from collections import OrderedDict
import itertools

from scanner import Scanner
from ftoken import Token, PToken

debug = False
#debug = True

# Just for tesitng
import os
import sys


class Lexer(object):
    """An iterator which returns the lexemes from an input stream."""
    def __init__(self, source):
        self.source = source
        self.include = None

        self.scanner = Scanner()

        # Split line cache
        self.cache = []

        # Preprocessor macros
        # NOTE: Macros are applied in order of #define, so use OrderedDict
        self.defines = OrderedDict()

        # Parser flow control
        # XXX: This probably does not need to be an object property, and
        #   could be returned from preprocess() to get_liminals()
        self.stop_parsing = False

        # Gather leading liminal tokens before iteration
        self.prior_tail = self.get_liminals()

        # Preprocess the liminals preceding the first statement
        preproc = (lx for lx in self.prior_tail if lx[0] == '#')
        for pp in preproc:
            self.preprocess(pp)

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
                # NOTE: This can only happen on the final iteration.
                #   This is because we call get_liminals() at __init__(), and
                #   then conditionally call it again if cache is empty.
                #
                # The one exception is the final line, for which the internal
                # for-loop returns nothing.
                #
                # In all conceivable cases, next(source) raises StopIteration.
                # But for now, I will leave this in case of the unforeseen.

                # Preprocessing
                # XXX: Preprocessing has an "head-tail" problem, where we need
                #   to resolve both before and after each iteration.
                #   Here we are preprocessing the final liminal tail
                preproc = (lx for lx in self.prior_tail if lx[0] == '#')
                for pp in preproc:
                    self.preprocess(pp)

                line = next(self.source)
                lexemes = self.scanner.parse(line)

            # Reconstruct any line continuations
            if lexemes[0] == '&':
                # First check if the split is separated by whitespace
                lx_split = prior_tail[0].isspace() or lexemes[1].isspace()

                # If no separating whitespace, try to split via Scanner
                if not lx_split:
                    new_lx = resplit_tokens(statement[-1], lexemes[1])
                    lx_split = len(new_lx) > 1

                # The token has been split, try to reconstruct it here.
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
                    lexemes = lexemes[2:]
                else:
                    # Store '&' as liminal and proceed as normal
                    prior_tail.append('&')
                    lexemes = lexemes[1:]

            # Build tokens from lexemes
            for lx in lexemes:
                if lx.isspace() or lx[0] == '!':
                    prior_tail.append(lx)

                elif lx == ';':
                    # Pull liminals and semicolons from the line
                    idx = lexemes.index(';')
                    for lxm in lexemes[idx:]:
                        # NOTE: Line continuations after ; are liminals
                        if is_liminal(lxm) or lxm == '&':
                            prior_tail.append(lxm)
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
                    # NOTE: This is probably happening later than it should;
                    #   Preprocessing is handled in liminals!
                    if lx in self.defines:
                        ptoks = [PToken(lxm) for lxm in self.defines[lx]]
                        ptoks[0].head = prior_tail
                        prior_tail = ptoks[-1].tail
                        ptoks[0].pp = lx

                        statement.extend(ptoks)
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

            new_lims = list(itertools.takewhile(is_liminal, lexemes))
            lims += new_lims

            # Apply preprocessing to set up subsequent statements
            if new_lims and new_lims[0][0] == '#':
                self.preprocess(new_lims[0])

            # Statements are liminals if preprocessing has suspended parsing
            stmt = list(itertools.dropwhile(is_liminal, lexemes))
            if self.stop_parsing:
                lims += stmt
            else:
                self.cache = stmt
                if self.cache:
                    break

        return lims

    def preprocess(self, line):
        assert line[0] == '#'
        line = line[1:]

        words = line.strip().split(None, 2)
        directive = words[0]

        # Macros

        if directive == 'define':
            macro_name = words[1]
            replacement = words[2] if len(words) == 3 else ''

            # My berk scanner needs an endline
            scanner = Scanner()
            lexemes = scanner.parse(replacement + '\n')

            # NOTES:
            # - We currently do not track whitespace created by macros.
            # - This also strips the endline.
            pp_lexemes = [lx for lx in lexemes if not lx.isspace()]

            self.defines[macro_name] = pp_lexemes

        elif directive == 'undef':
            identifier = words[1]
            try:
                self.defines.pop(identifier)
            except KeyError:
                # Useful, but perhaps too aggressive.
                # print('f90lex: warning: unset identifier {} was never '
                #       'defined.'.format(identifier))
                pass

        # Conditionals (stop_parsing not yet implemented (if ever))

        # TODO (#if #elif)
        #elif directive == 'if':
        #    expr = line.strip().split(None, 1)[1]

        elif directive == 'ifdef':
            macro = line.split(None, 1)[1]
            if macro not in self.defines:
                self.stop_parsing = True

        elif directive == 'ifndef':
            macro = line.split(None, 1)[1]
            if macro in self.defines:
                self.stop_parsing = True

        elif directive == 'else':
            self.stop_parsing = not self.stop_parsing

        elif directive == 'endif':
            self.stop_parsing = False

        # Headers (this can't possibly be working...)

        elif directive.startswith('include'):
            # This directive uniquely does not require a whitespace delimiter.
            if directive != 'include':
                inc_fpath = directive.replace('include', '', 1)
                words[0] = 'include'
                words.insert(1, inc_fpath)

            assert (words[1][0], words[1][-1]) in (('"', '"'), ('<', '>'))
            inc_fname = words[1][1:-1]

            ## First check current directory
            #curdir = os.path.dirname(self.path)
            #test_fpath = os.path.join(curdir, inc_fname)

            #inc_path = None
            #if os.path.isfile(test_fpath):
            #    inc_path = test_fpath
            #elif self.project:
            #    # Scan the project directories for the file
            #    for idir in self.project.directories:
            #        test_fpath = os.path.join(idir, inc_fname)
            #        if os.path.isfile(test_fpath):
            #            inc_path = test_fpath
            ## else: do not bother looking

            # XXX: Temporarily look in the current directory
            inc_path = inc_fname if os.path.isfile(inc_fname) else None

            if inc_path:
                with open(inc_path) as inc:
                    lexer = Lexer(inc)
                    lexer.defines = self.defines
                    self.include = lexer
            else:
                print('f90lex: Include file {} not found; skipping.'
                      ''.format(inc_fname))

        # What else is there?  #pragma, #line, #error, ... ?

        else:
            print('f90lex: unsupported preprocess directive: {}'
                  ''.format(line).rstrip())


def is_liminal(lexeme):
    return lexeme.isspace() or lexeme[0] in '!#' or lexeme == ';'


def resplit_tokens(first, second):
    # NOTE: Scanner needs an endline, and split strings expect line
    #   continuations in order to track the delimiter across multiple lines, so
    #   we append these when needed.
    str_split = first[0] in '\'"' and second[-1] != first[0]
    if str_split:
        lx_join = first + second + '&' + '\n'
    else:
        lx_join = first + second + '\n'

    scanner = Scanner()
    new_lx = scanner.parse(lx_join)

    # NOTE: Remove the redudant Scanner markup tokens
    if str_split:
        new_lx = new_lx[:-2]
    else:
        new_lx = new_lx[:-1]

    return new_lx


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
