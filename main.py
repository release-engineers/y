#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark

parser = Lark('''%import common.NUMBER
                 %import common.SIGNED_NUMBER
                 %import common.ESCAPED_STRING
                 %import common.CNAME
                 %import common.WS
                 ?expression: constant
                     | "." key                     -> element_by_key
                     | "[" key "]"                 -> element_by_key
                     | expression "|" expression   -> pipe
                     | expression "=" expression   -> set
                     | expression "+" expression   -> math_add
                     | expression "-" expression   -> math_subtract
                     | expression "*" expression   -> math_multiply
                     | expression "/" expression   -> math_divide
                     | expression "%" expression   -> math_modulo
                     | expression "^" expression   -> math_power
                 ?key: CNAME
                     | ESCAPED_STRING
                 ?constant: NUMBER
                      | ESCAPED_STRING
                      | SIGNED_NUMBER
                 %ignore WS
         ''', start='expression')

res = parser.parse('2 + 3 - 4').pretty()
print(res)
