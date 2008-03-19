class Token(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __add__(self, other):
        return TokenStream(self, other)

    def __iadd__(self, other):
        return TokenStream(self, other)

    def __iter__(self):
        return iter((self.name, self.value))
    

class TokenStream(object):

    def __init__(self, *arg):
        self._tokens = list(arg)

    def __str__(self):
        return ''.join([t.value for t in self._tokens])

    def __iter__(self):
        for t in self._tokens:
            yield (t.name, t.value)

    def __len__(self):
        return len(self._tokens)

    def __add__(self, other):
        print other, list(other)
        try:
            for name, value in other:
                self._tokens.append(Token(name, value))
        except (TypeError, ValueError):
            try:
                (name, value) = other
                self._tokens.append(Token(name, value))
            except TypeError:
                raise TypeError("Can't add %r to TokenStream" % other.__class__)
        return self
        
