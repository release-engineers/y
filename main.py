#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark

parser = Lark('''%import common.NUMBER
                 %import common.SIGNED_NUMBER
                 %import common.ESCAPED_STRING
                 %import common.CNAME
                 %import common.WS

                 ?pipe: expression "|" pipe        -> pipe
                     |  expression "|" expression  -> pipe

                 ?expression: math_prio3
                     | reference
                     | constant

                 ?math_prio3: math_prio3 ("+"|"-") math_prio2     -> math_prio3
                      | math_prio2
                 ?math_prio2: math_prio2 ("/"|"*"|"%") math_prio1 -> math_prio2
                      | math_prio1
                 ?math_prio1: constant "^" math_prio1             -> math_prio1
                     | constant
                     | reference

                 ?constant: NUMBER                 -> number
                      | SIGNED_NUMBER              -> number
                      | ESCAPED_STRING             -> string
                      | "true"                     -> boolean_true
                      | "false"                    -> boolean_false

                 ?reference: "$"                   -> context_root
                     | "."                         -> context
                     | "." key                     -> context_child_by_key
                     | "[" index "]"               -> context_child_by_index
                 
                 ?index: NUMBER                    -> index

                 ?key: CNAME                       -> key
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe')

print(parser.parse('$'
                   '| .'
                   '| .a'
                   '| [0]'
                   '| "abcdefg"'
                   '| true'
                   '| false'
                   '| 1 + 2 - 3 * 4 / 5 % 6 ^ 7').pretty())
