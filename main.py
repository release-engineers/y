#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark

parser = Lark('''%import common.NUMBER
                 %import common.SIGNED_NUMBER
                 %import common.ESCAPED_STRING
                 %import common.CNAME
                 %import common.WS
                 ?pipe: expression "|" pipe
                     |  expression "|" expression
                 ?expression: constant
                     | "$"                         -> element_root
                     | "."                         -> element
                     | "." key                     -> element_at_key
                     | "[" key "]"                 -> element_at_index
                     | expression "=" expression   -> set
                     | expression "+" expression   -> math_add
                     | expression "-" expression   -> math_subtract
                     | expression "*" expression   -> math_multiply
                     | expression "/" expression   -> math_divide
                     | expression "%" expression   -> math_modulo
                     | expression "^" expression   -> math_power
                 ?key: CNAME
                     | ESCAPED_STRING
                 ?constant: NUMBER                 -> number
                      | ESCAPED_STRING             -> string
                      | SIGNED_NUMBER              -> number
                 %ignore WS
         ''', start='pipe')

print(parser.parse('$'
                   '| .'
                   '| .a'
                   '| [a]'
                   '| .a = 1'
                   '| 1 + 1'
                   '| 1 - 1'
                   '| 1 * 1'
                   '| 1 / 1'
                   '| 1 % 1'
                   '| 1 ^ 1').pretty())
