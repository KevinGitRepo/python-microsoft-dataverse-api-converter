from enum import Enum

class Comparison(Enum):
    EQUAL = 'eq'
    NOT_EQUAL = 'ne'
    GREATER_THAN = 'gt'
    LESS_THAN = 'lt'
    GREATER_THAN_OR_EQUAL = 'ge'
    LESS_THAN_OR_EQUAL = 'le'

class LogicalOperation(Enum):
    AND = 'and'
    OR = 'or'
    NOT = 'not'

class QueryFunction(Enum):
    CONTAINS = 'contains'
    ENDSWITH = 'endswith'
    STARTSWITH = 'startswith'

def quote_only_strings(value) -> str:
    if isinstance(value, str):
        return f'{value}'
    return str(value)