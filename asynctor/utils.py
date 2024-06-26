class AttrDict(dict):
    """Support get dict value by attribution

    Usage::
        >>> d = AttrDict({'a': 1, 'b': {'c': 2, 'd': {'e': 3}}})
        >>> d.a == d['a'] == 1
        True
        >>> d.b.c == d['b']['c'] == 2
        True
        >>> d.b.d == d['b']['d'] == {'e': 3}
        True
        >>> d.b.d.e == d['b']['d']['e'] == 3
        True
        >>> dd = AttrDict({'keys': 2}, items=1)
        >>> list(dd.items()) == [('keys', 2), ('items', 1)]
        True
        >>> dd['items'] == 1
        True
        >>> list(dd.keys()) == ['keys', 'items']
        True
        >>> dd['keys'] == 2
        True
    """

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        exclude = set(dir(self)) | set(self.__dict__)
        for k, v in self.items():
            if not isinstance(k, str) or k in exclude:
                continue
            if isinstance(v, dict):
                v = self.__class__(v)
            self.__dict__.setdefault(k, v)

    def __str__(self) -> str:
        return super().__repr__()

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + super().__repr__() + ")"


def _test() -> None:  # pragma: no cover
    import doctest

    doctest.testmod(verbose=True)


if __name__ == "__main__":
    _test()
