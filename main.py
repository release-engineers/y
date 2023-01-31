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

                 ?subreference: "." key                              -> reference_field
                    | "[" index "]"                                  -> reference_array_element
                    | "["  "]"                                       -> reference_array

                 ?index: NUMBER

                 ?key: CNAME
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe', propagate_positions=True)


def interpret_number(value):
    return float(value.children[0])


def interpret_string(value):
    return value.children[0][1:-1]


def interpret_boolean_true(value):
    return True


def interpret_boolean_false(value):
    return False


def interpret_null(value):
    return None


mapping = {
    'number': interpret_number,
    'string': interpret_string,
    'boolean_true': interpret_boolean_true,
    'boolean_false': interpret_boolean_false,
    'null': interpret_null,
}


def interpret_any(value):
    if value.data in mapping:
        return mapping[value.data](value)
    else:
        raise Exception("Unknown value type: " + value.data)


def demo(expression):
    print("expression: " + expression)
    parsed = parser.parse(expression)
    try:
        interpreted = interpret_any(parsed)
        print("interpreted: " + str(interpreted))
        print()
    except Exception:
        print(parsed.pretty())


demo('.a.b.c[0] = 123')
demo('.a | .b | .c | [0]')
demo('"abcdefg"')
demo('true')
demo('false')
demo('1 + 2 - 3 * 4 / 5 % 6 ^ 7')
demo('target(1 + 2, 3, 4 + 5)')
