from QueryHelper import Comparison, quote_only_strings, LogicalOperation, QueryFunction

class FilterCompare:
    def __init__(self, comparison: Comparison, column: str, value: int|float|str):
        self._column = column
        self._column_value = value
        self._comparison = comparison

    def __str__(self):
        return f'{self._column} {self._comparison.value} {quote_only_strings(self._column_value)}'

class FilterLogical:
    def __init__(self, logical: LogicalOperation, first_statement, second_statement = None):
        self._logical = logical
        self._first_statement = first_statement
        self._second_statement = second_statement
        self._formatted_str = ''

    def group(self):
        if self._logical != LogicalOperation.NOT:
            self._formatted_str = f'({self._first_statement} {self._logical.value} {self._second_statement})'
        return self

    def __str__(self):
        if self._formatted_str:
            return self._formatted_str
        if self._logical == LogicalOperation.NOT:
            return f'{self._logical.value} {self._first_statement}'
        return f'{self._first_statement} {self._logical.value} {self._second_statement}'

class FilterOData:
    def __init__(self, query: QueryFunction, field: str, value: str):
        self._query = query
        self._field = field
        self._column_value = value
        self._formatted_str = ''

    def negate(self):
        self._formatted_str = f'{LogicalOperation.NOT.value} {self._query.value}({self._field},\'{quote_only_strings(self._column_value)}\')'
        return self

    def __str__(self):
        if self._formatted_str:
            return self._formatted_str
        return f'{self._query.value}({self._field},\'{self._column_value}\')'

class FilterLambda:
    # TODO
    pass