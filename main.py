#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark
import ruamel.yaml
import sys

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
                     | subreference+                                 -> reference_context

                 ?subreference: "." key                              -> subreference_field
                    | "[" index "]"                                  -> subreference_array_element
                    | "["  "]"                                       -> subreference_array

                 ?index: NUMBER

                 ?key: CNAME
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe', propagate_positions=True)

context_process = {}
context_pipe = context_process
mapping = {}


def interpret_any(value):
    if value.data in mapping:
        interpreter = mapping[value.data]
        return interpreter(value)
    else:
        raise Exception("unknown value: " + value.data)


# -- math

def interpret_math(value):
    left = value.children[0]
    left_value = interpret_any(left)
    operator = value.children[1]
    right = value.children[2]
    right_value = interpret_any(right)
    if operator == '+':
        return left_value + right_value
    elif operator == '-':
        return left_value - right_value
    elif operator == '*':
        return left_value * right_value
    elif operator == '/':
        return left_value / right_value
    elif operator == '%':
        return left_value % right_value
    elif operator == '^':
        return left_value ** right_value
    else:
        raise Exception("unknown operator: " + operator)


# -- pipe

def interpret_pipe(value):
    global context_pipe
    original_context_pipe = context_pipe
    for expression in value.children:
        result = interpret_any(expression)
        context_pipe = result
    context_pipe = original_context_pipe


# -- references

def interpret_reference_root(value):
    result = context_process
    for subreference in value.children:
        subreference_interpreter = mapping[subreference.data]
        result = subreference_interpreter(subreference, result)
    return result


def interpret_reference_context(value):
    result = context_pipe
    for subreference in value.children:
        subreference_interpreter = mapping[subreference.data]
        result = subreference_interpreter(subreference, result)
    return result


def interpret_subreference_field(value, context):
    field = value.children[0]
    if field not in context:
        context[field] = {}
    return context[field]


def interpret_subreference_array_element(value, context):
    index = int(value.children[0])
    if index >= len(context):
        context[index] = {}
    return context[index]


def interpret_subreference_array(value, context):
    return context


# -- constants

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


mapping['math'] = interpret_math
mapping['pipe'] = interpret_pipe
mapping['reference_root'] = interpret_reference_root
mapping['reference_context'] = interpret_reference_context
mapping['subreference_field'] = interpret_subreference_field
mapping['subreference_array_element'] = interpret_subreference_array_element
mapping['subreference_array'] = interpret_subreference_array
mapping['number'] = interpret_number
mapping['string'] = interpret_string
mapping['boolean_true'] = interpret_boolean_true
mapping['boolean_false'] = interpret_boolean_false
mapping['null'] = interpret_null

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True


def demo(expression):
    print("expression: " + expression)
    parsed = parser.parse(expression)
    if parsed.data in mapping:
        interpreted = mapping[parsed.data](parsed)
        # if interpreted is a ruamel yaml class, dump it
        if isinstance(interpreted, ruamel.yaml.comments.CommentedBase):
            print("yaml:")
            yaml.dump(interpreted, sys.stdout)
        print("interpreted: " + str(interpreted))
        print()
    else:
        print(parsed.pretty())


with open("sample.yml", 'r') as f:
    context_process = yaml.load(f)
    context_pipe = context_process

demo('.a.b.c[0]')
demo('.a.b.c[0] = 123')
demo('.a | .b | .c | [0]')
demo('"abcdefg"')
demo('true')
demo('false')
demo('1 + 2 - 3 * 4 / 5 % 6 ^ 7')
demo('target(1 + 2, 3, 4 + 5)')
