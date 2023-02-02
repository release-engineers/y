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

                 ?expression: "(" expression ")"
                     | expression "|" expression                     -> pipe
                     | math_prio3
                     | math_prio2
                     | math_prio1
                     | assignment
                     | reference
                     | constant
                     | call

                 ?call: key "(" expression ( "," expression )* ")"   -> call

                 ?assignment: expression "=" expression              -> assignment

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
         ''', start='expression', propagate_positions=True)


class RuamelPatchIgnoreAliases(ruamel.yaml.representer.RoundTripRepresenter):
    """
    Don't use YAML aliases and anchors, at all.
    """

    def ignore_aliases(self, data):
        return True


def ruamel_patch_reset_open_ended(self, *args, **kw):
    """
    Reset the open_ended flag after writing a plain value to prevent Ruamel from outputting document end markers.
    """
    self.write_plain_org(*args, **kw)
    self.open_ended = False


class YInterpreter:
    def __init__(self, indent_mapping=2, indent_sequence=4, indent_offset=2):
        self.root = {}
        self.context = YReference(self.root)
        self.functions = {}
        self.ruamelYaml = ruamel.yaml.YAML()
        self.ruamelYaml.Representer = RuamelPatchIgnoreAliases
        self.ruamelYaml.preserve_quotes = True
        self.ruamelYaml.Emitter.write_plain_org = self.ruamelYaml.Emitter.write_plain
        self.ruamelYaml.Emitter.write_plain = ruamel_patch_reset_open_ended
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
        elif not source.isatty():
            source_content = source.read()
            root = self.ruamelYaml.load(source_content)
        else:
            root = self.ruamelYaml.load("{}")
        self.root = root
        self.context = YReference(root)

    def dump(self, value, destination):
        """
        Dump the root context as a YAML document to a stream.

        :param value:
        :param destination:
        :return:
        """
        self.ruamelYaml.dump(value, destination)

    def interpret(self, expression):
        """
        Evaluate a Y expression against the current context.

        :param expression:
        :return:
        """
        parsed_tree = parser.parse(expression)
        (result, read_write) = self._interpret_resolving(parsed_tree)
        # after write actions an end-user would expect to see the document root with the changes applied
        if read_write:
            return self.root
        return result

    def _interpret_resolving(self, value):
        """
        Interpret a parsed Y expression, resolving the result to a value.

        :param value:
        :return: (result, read_write) where result is the value of the expression and read_write is a boolean indicating
        whether the expression was interpreted as a read(False) or write(True) operation.
        """
        (result, read_write) = self._interpret(value)
        if isinstance(result, YReference):
            return result.context, read_write
        return result, read_write

    def _interpret(self, value):
        """
        Interpret a parsed Y expression.

        :param value: A Lark Tree object, representing a part of a Y expression.
        :return: (result, read_write) where result is the value of the expression and read_write is a boolean indicating
        whether the expression was interpreted as a read(False) or write(True) operation.
        """
        if value.data == 'math':
            return self._interpret_math(value), False
        elif value.data == 'pipe':
            return self._interpret_pipe(value), False
        elif value.data == 'reference_root':
            return self._interpret_reference_root(value), False
        elif value.data == 'reference_context':
            return self._interpret_reference_context(value), False
        elif value.data == 'subreference_by_key':
            return self._interpret_subreference_by_key(value), False
        elif value.data == 'subreference_by_index':
            return self._interpret_subreference_by_index(value), False
        elif value.data == 'subreference_array':
            return self._interpret_subreference_array(value), False
        elif value.data == 'assignment':
            return self._interpret_assignment(value), True
        elif value.data == 'call':
            return self._interpret_call(value), False
        elif value.data == 'number':
            return YInterpreter._interpret_number(value), False
        elif value.data == 'string':
            return YInterpreter._interpret_string(value), False
        elif value.data == 'boolean_true':
            return YInterpreter._interpret_boolean_true(value), False
        elif value.data == 'boolean_false':
            return YInterpreter._interpret_boolean_false(value), False
        elif value.data == 'null':
            return YInterpreter._interpret_null(value), False
        else:
            raise Exception("unknown value: " + value.data)

    def _interpret_math(self, value):
        left = value.children[0]
        left_value, _ = self._interpret_resolving(left)
        operator = value.children[1]
        right = value.children[2]
        right_value, _ = self._interpret_resolving(right)
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
            result, _ = self._interpret(expression)
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
        value_sink, _ = self._interpret(value.children[0])
        if not isinstance(value_sink, YReference):
            raise Exception("Can only assign values to a reference, instead got: " + str(value_sink))
        value_source, _ = self._interpret_resolving(value.children[1])
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
            result, _ = yinterpreter._interpret_resolving(parsed)
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
    test('.d = 2 | . * 2', 4)
    test('.d', 2)
    test('(.e = 2) | . * 2', 4)
    test('.e', 2)
    test('.f = (2 | . * 2)', 4)
    test('.f', 4)
    test('custom_fn(1 + 2, 3, 4 + 5)', None)
    print('done')
