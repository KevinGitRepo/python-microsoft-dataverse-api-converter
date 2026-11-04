from Select import Select
from QueryHelper import *
from FilterItems import *
from Filter import Filter
from Select import Select

select_list = ['first', 'second', 'third']
select_statement = Select(select_list)

filter_compare = FilterCompare(Comparison.EQUAL, 'date', '10/23/1013')
filter_odata = FilterOData(QueryFunction.CONTAINS, 'your', 'fast').negate()
filter_logical = FilterLogical(LogicalOperation.AND, filter_compare, FilterCompare(Comparison.EQUAL, 'doatre', '10/23/1231')).group()
filter_logical_2 = FilterLogical(LogicalOperation.OR, FilterCompare(Comparison.LESS_THAN, 'd', '10'), filter_logical)
filter_total = FilterLogical(LogicalOperation.AND, filter_odata, filter_logical_2.group())

filer_statement = FilterLogical(logical=LogicalOperation.NOT, first_statement='first')

print(Filter(str(filter_compare)))
print(Select(select_list))