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


class YInterpreter:
    def __init__(self):
        self.root = {}
        self.context = self.root
        self.functions = {}
        self.ruamelYaml = ruamel.yaml.YAML()
        self.ruamelYaml.preserve_quotes = True

    def load(self, source):
        with open(source, 'r') as f:
            self.root = self.ruamelYaml.load(f)
            self.context = self.root

    def interpret(self, value):
        if value.data == 'math':
            return self._interpret_math(value)
        elif value.data == 'pipe':
            return self._interpret_pipe(value)
        elif value.data == 'reference_root':
            return self._interpret_reference_root(value)
        elif value.data == 'reference_context':
            return self._interpret_reference_context(value)
        elif value.data == 'subreference_field':
            return self._interpret_subreference_field(value)
        elif value.data == 'subreference_array_element':
            return self._interpret_subreference_array_element(value)
        elif value.data == 'subreference_array':
            return self._interpret_subreference_array(value)
        elif value.data == 'assignment':
            return self._interpret_assignment(value)
        elif value.data == 'call':
            return self._interpret_call(value)
        elif value.data == 'number':
            return YInterpreter._interpret_number(value)
        elif value.data == 'string':
            return YInterpreter._interpret_string(value)
        elif value.data == 'boolean_true':
            return YInterpreter._interpret_boolean_true(value)
        elif value.data == 'boolean_false':
            return YInterpreter._interpret_boolean_false(value)
        elif value.data == 'null':
            return YInterpreter._interpret_null(value)
        else:
            raise Exception("unknown value: " + value.data)

    def _interpret_math(self, value):
        left = value.children[0]
        left_value = self.interpret(left)
        operator = value.children[1]
        right = value.children[2]
        right_value = self.interpret(right)
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

    def _interpret_pipe(self, value):
        original_context = self.context
        result = self.context
        for expression in value.children:
            result = self.interpret(expression)
            self.context = result
        self.context = original_context
        return result

    def _interpret_reference_root(self, value):
        original_context = self.context
        self.context = self.root
        result = self.context
        for subreference in value.children:
            result = self.interpret(subreference)
            self.context = result
        self.context = original_context
        return result

    def _interpret_reference_context(self, value):
        original_context = self.context
        result = self.context
        for subreference in value.children:
            result = self.interpret(subreference)
            self.context = result
        self.context = original_context
        return result

    def _interpret_subreference_field(self, value):
        field = value.children[0]
        if field not in self.context:
            # TODO: Create only on assignment
            self.context[field] = {}
        return self.context[field]

    def _interpret_subreference_array_element(self, value):
        index = int(value.children[0])
        if index >= len(self.context):
            # TODO: Create only on assignment
            self.context[index] = {}
        return self.context[index]

    def _interpret_subreference_array(self, value):
        return self.context

    @staticmethod
    def _interpret_number(value):
        return float(value.children[0])

    @staticmethod
    def _interpret_string(value):
        return value.children[0][1:-1]

    @staticmethod
    def _interpret_boolean_true(value):
        return True

    @staticmethod
    def _interpret_boolean_false(value):
        return False

    @staticmethod
    def _interpret_null(value):
        return None

    def _interpret_assignment(self, value):
        pass

    def _interpret_call(self, value):
        pass


if __name__ == '__main__':
    yinterpreter = YInterpreter()
    yinterpreter.load('sample.yml')


    def test_print(name, value):
        print(f"-- {name}")
        if isinstance(value, ruamel.yaml.comments.CommentedBase):
            yinterpreter.ruamelYaml.dump(value, sys.stdout)
        else:
            print(value)


    def test(expression, expected):
        parsed = parser.parse(expression)
        try:
            result = yinterpreter.interpret(parsed)
            if expected is not None:
                if result != expected:
                    test_print('expected', expected)
                    test_print('result', result)
                    test_print('expression', expression)
                    test_print('expression tree', parsed.pretty())
        except Exception as e:
            test_print('exception', e)
            test_print('expression', expression)
            test_print('expression tree', parsed.pretty())


    test('.a', yinterpreter.root['a'])
    test('.a.b', yinterpreter.root['a']['b'])
    test('.a.b.c', yinterpreter.root['a']['b']['c'])
    test('.a.b.c[0]', yinterpreter.root['a']['b']['c'][0])
    test('.a.b.c[0] = 123', None)
    test('.a | .b', yinterpreter.root['a']['b'])
    test('"abcdefg"', 'abcdefg')
    test('true', True)
    test('false', False)
    test('1 + 2 - 3 * 4 / 5 % 6 ^ 7', 1 + 2 - 3 * 4 / 5 % 6 ** 7)
    test('custom_fn(1 + 2, 3, 4 + 5)', None)
