#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark

parser = Lark('''%import common.NUMBER
                 %import common.SIGNED_NUMBER
                 %import common.ESCAPED_STRING
                 %import common.CNAME
                 %import common.WS

                 ?pipe: expression "|" pipe                        -> pipe
                     | expression

                 ?expression: math_prio3
                     | assignment
                     | reference
                     | constant
                 
                 ?assignment: reference "=" expression            -> assignment

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
                      | "null"                     -> null

                 ?reference: "$"            -> reference_root
                     | "$" subreference      -> reference_root_subreference
                     | subreference          -> reference_contextual_subreference

                 ?subreference: subreference accessor        -> subreference
                        | accessor

                 ?accessor: "." key                -> accessor_field_by_key
                    | "[" index "]"                -> accessor_element_by_index
                    | "["  "]"                     -> accessor_elements
                 ?index: NUMBER                    -> index

                 ?key: CNAME                       -> key
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe')


def demo(expression):
    print(expression)
    print(parser.parse(expression).pretty())


demo('.a.b.c[0] = 123')
demo('.a.b | .c[0]')
demo('"abcdefg"')
demo('true')
demo('false')
demo('1 + 2 - 3 * 4 / 5 % 6 ^ 7')
