#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark

parser = Lark('''%import common.NUMBER
                 %import common.SIGNED_NUMBER
                 %import common.ESCAPED_STRING
                 %import common.CNAME
                 %import common.WS

                 ?pipe: expression "|" pipe                          -> pipe
                     | expression

                 ?expression: math_prio3
                     | assignment
                     | reference
                     | constant
                     | call
                 
                 ?call: key "(" expression ( "," expression )* ")"   -> call

                 ?assignment: reference "=" expression               -> assignment

                 ?math_prio3: math_prio3 /\\+|-/ math_prio2          -> math
                      | math_prio2
                 ?math_prio2: math_prio2 /\\/|\\*|%/ math_prio1      -> math
                      | math_prio1
                 ?math_prio1: constant /\\^/ math_prio1              -> math
                     | constant
                     | reference

                 ?constant: NUMBER                                   -> number
                      | SIGNED_NUMBER                                -> number
                      | ESCAPED_STRING                               -> string
                      | "true"                                       -> boolean_true
                      | "false"                                      -> boolean_false
                      | "null"                                       -> null

                 ?reference: "$" subreference*                       -> reference_root
                     | "."                                           -> reference_context
                     | subreference+                                 -> reference_context_subreference

                 ?subreference: "." key                              -> field
                    | "[" index "]"                                  -> array_element
                    | "["  "]"                                       -> array

                 ?index: NUMBER                                      -> index

                 ?key: CNAME                                         -> key
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe', propagate_positions=True)


def demo(expression):
    print(expression)
    parsed = parser.parse(expression)
    print(parsed.pretty())


demo('.a.b.c[0] = 123')
demo('.a | .b | .c | [0]')
demo('"abcdefg"')
demo('true')
demo('false')
demo('1 + 2 - 3 * 4 / 5 % 6 ^ 7')
demo('target(1 + 2, 3, 4 + 5)')
