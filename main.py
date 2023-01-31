#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark

parser = Lark('''?expression: value
                     | expression "|" expression   -> pipe
                     | expression "=" expression   -> set
                     | expression "+" expression   -> add
                     | expression "-" expression   -> subtract
                 ?value: NUMBER           -> number
                      | SIGNED_NUMBER     -> number
                 %import common.NUMBER
                 %import common.SIGNED_NUMBER
                 %import common.WS
                 %ignore WS
         ''', start='expression')

res = parser.parse('2 + 3 - 4').pretty()
print(res)
