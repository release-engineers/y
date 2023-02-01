#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import ruamel.yaml
from lark import Lark
from ruamel.yaml.comments import CommentedMap

from y.yreference import YReference

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

                 ?subreference: "." key                              -> subreference_by_key
                    | "[" index "]"                                  -> subreference_by_index
                    | "["  "]"                                       -> subreference_array

                 ?index: NUMBER

                 ?key: CNAME
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe', propagate_positions=True)


class IgnoreAliases(ruamel.yaml.representer.RoundTripRepresenter):
    def ignore_aliases(self, data):
        return True


class YInterpreter:
    def __init__(self, indent_mapping=2, indent_sequence=4, indent_offset=2):
        self.root = {}
        self.context = YReference(self.root)
        self.functions = {}
        self.ruamelYaml = ruamel.yaml.YAML()
        self.ruamelYaml.Representer = IgnoreAliases
        self.ruamelYaml.preserve_quotes = True
        self.ruamelYaml.indent(mapping=indent_mapping, sequence=indent_sequence, offset=indent_offset)

    def load(self, source):
        """
        Load a stream as a YAML document from a file to become the root context.

        :param source:
        :return:
        """
        if isinstance(source, str):
            with open(source, 'r') as f:
                root = self.ruamelYaml.load(f)
        else:
            source_content = source.read()
            root = self.ruamelYaml.load(source_content)
        self.root = root
        self.context = YReference(root)

    def dump(self, destination):
        """
        Dump the root context as a YAML document to a stream.

        :param destination:
        :return:
        """
        # prevent ruamel.yaml.YAML.dump from outputting "null\n..."
        if self.root is None:
            return
        self.ruamelYaml.dump(self.root, destination)

    def interpret(self, expression):
        """
        Evaluate a Y expression against the current context.

        :param expression:
        :return:
        """
        parsed_tree = parser.parse(expression)
        return self._interpret_resolving(parsed_tree)

    def _interpret_resolving(self, value):
        """
        Interpret a parsed Y expression, resolving the result to a value.

        :param value:
        :return:
        """
        result = self._interpret(value)
        if isinstance(result, YReference):
            return result.context
        return result

    def _interpret(self, value):
        """
        Interpret a parsed Y expression.

        :param value: A Lark Tree object, representing a part of a Y expression.
        :return:
        """
        if value.data == 'math':
            return self._interpret_math(value)
        elif value.data == 'pipe':
            return self._interpret_pipe(value)
        elif value.data == 'reference_root':
            return self._interpret_reference_root(value)
        elif value.data == 'reference_context':
            return self._interpret_reference_context(value)
        elif value.data == 'subreference_by_key':
            return self._interpret_subreference_by_key(value)
        elif value.data == 'subreference_by_index':
            return self._interpret_subreference_by_index(value)
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
        left_value = self._interpret_resolving(left)
        operator = value.children[1]
        right = value.children[2]
        right_value = self._interpret_resolving(right)
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
            result = self._interpret(expression)
            self.context = result
        self.context = original_context
        return result

    def _interpret_reference_root(self, value):
        original_context = self.context
        temporary_context = YReference(self.root)
        self.context = temporary_context
        for subreference in value.children:
            self._interpret(subreference)
        self.context = original_context
        return temporary_context

    def _interpret_reference_context(self, value):
        original_context = self.context
        temporary_context = YReference(self.context)
        self.context = temporary_context
        for subreference in value.children:
            self._interpret(subreference)
        self.context = original_context
        return temporary_context

    def _interpret_subreference_by_key(self, value):
        key = str(value.children[0])
        self.context.move_down(key, 'key')
        return self.context

    def _interpret_subreference_by_index(self, value):
        index = int(value.children[0])
        self.context.move_down(index, 'index')
        return self.context

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
        value_sink = self._interpret(value.children[0])
        if not isinstance(value_sink, YReference):
            raise Exception("Can only assign values to a reference, instead got: " + str(value_sink))
        value_source = self._interpret_resolving(value.children[1])
        value_sink.set(value_source)
        return value_source

    def _interpret_call(self, value):
        return None


if __name__ == '__main__':
    yinterpreter = YInterpreter()
    yinterpreter.load('sample.yml')


    def test_print(name, value):
        print(f"-- {name}")
        if isinstance(value, ruamel.yaml.comments.CommentedBase):
            yinterpreter.ruamelYaml.dump(value, sys.stdout)
        else:
            print(value)
        if isinstance(value, Exception):
            raise value


    def test(expression, expected):
        parsed = parser.parse(expression)
        try:
            result = yinterpreter._interpret_resolving(parsed)
            if result != expected:
                test_print('expected', expected)
                test_print('result', result)
                test_print('expression', expression)
                test_print('expression tree', parsed.pretty())
        except Exception as e:
            test_print('exception', e)
            test_print('expression', expression)
            test_print('expression tree', parsed.pretty())


    a = yinterpreter.root['a']
    b = a['b']
    c = b['c']

    test('.a', a)
    test('.a.b', b)
    test('.a.b.c', c)
    test('.a.b.c[0]', c[0])
    test('.a | .b | .c | [0]', c[0])
    test('.a.b.c[0] = 123', 123)
    test('.a.b.c[0]', 123)
    test('.a = .a.b', b)
    test('.a', b)
    test('"abcdefg"', 'abcdefg')
    test('true', True)
    test('false', False)
    test('1 + 2 - 3 * 4 / 5 % 6 ^ 7', 1 + 2 - 3 * 4 / 5 % 6 ** 7)
    test('2 * 2 | . * 2', 8)
    test('custom_fn(1 + 2, 3, 4 + 5)', None)
    print('done')
