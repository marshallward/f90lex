class Token(str):
    # NOTE: Immutable types generally need __new__ implementations
    #   (At least that is my understanding...)
    def __new__(cls, value='', *args, **kwargs):
        tok = str.__new__(cls, value, *args)
        tok.head = []
        tok.tail = []
        tok.split = None
        return tok

    def __eq__(self, other):
        return self.lower() == other.lower()

    def __hash__(self):
        return hash(str(self).lower())


class PToken(Token):
    """Preprocessed Token which prints its origin macro."""
    def __init__(self, value='', pp=''):
        self.pp = pp

    def __str__(self):
        return self.pp
