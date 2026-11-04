class Filter:
    def __init__(self, filter_string: str) -> None:
        self._filter_string = filter_string

    def __str__(self):
        return f'$filter={self._filter_string}'