#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lark import Lark
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq
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

                 ?subreference: "." key                              -> subreference_by_key
                    | "[" index "]"                                  -> subreference_by_index
                    | "["  "]"                                       -> subreference_array

                 ?index: NUMBER

                 ?key: CNAME
                     | ESCAPED_STRING

                 %ignore WS
         ''', start='pipe', propagate_positions=True)


class YReference:
    """
    A reference to a value in a YAML document.
    Can be used to interact with YAML documents regardless of whether the value and its parent values exist.
    """

    def __init__(self, context):
        """
        :param context: Either a YReference or a dict
        """
        if isinstance(context, YReference):
            self.context = context.context
            self.context_parents = context.context_parents[:]
            self.context_parent_keys = context.context_parent_keys[:]
            self.context_parent_key_types = context.context_parent_key_types[:]
        else:
            self.context = context
            self.context_parents = []
            self.context_parent_keys = []
            self.context_parent_key_types = []

    def move_down(self, key, key_type):
        """
        :param key:
        :param key_type: Either 'key' or 'index'
        :return:
        """
        self.context_parents.append(self.context)
        self.context_parent_keys.append(key)
        self.context_parent_key_types.append(key_type)
        if key_type == 'key':
            if self.context is not None and key in self.context:
                self.context = self.context[key]
            else:
                self.context = None
        elif key_type == 'index':
            if self.context is not None and len(self.context) > key:
                self.context = self.context[key]
            else:
                self.context = None
        else:
            raise Exception("Unknown key type: " + key_type)

    def move_up(self):
        if len(self.context_parents) == 0:
            raise Exception("Cannot move up in context past the context root")
        self.context = self.context_parents.pop()
        self.context_parent_keys.pop()
        self.context_parent_key_types.pop()

    def _materialize_path_segment(self, i, value=None):
        ith_parent = self.context_parents[i]
        ith_key = self.context_parent_keys[i]
        ith_key_type = self.context_parent_key_types[i]
        if ith_key_type == 'key':
            if isinstance(ith_parent, CommentedMap):
                ith_parent[ith_key] = value
                if i == len(self.context_parents) - 1:
                    self.context = value
                else:
                    self.context_parents[i + 1] = value
            else:
                raise Exception(f"Cannot create key '{ith_key}' in non-mapping type, parent is {type(ith_parent)}")
        elif ith_key_type == 'index':
            if isinstance(ith_parent, CommentedSeq):
                ith_parent[ith_key] = value
                if i == len(self.context_parents) - 1:
                    self.context = value
                else:
                    self.context_parents[i + 1] = value
            else:
                raise Exception(f"Cannot create key '{ith_key}' in non-sequence type, parent is {type(ith_parent)}")

    def _materialize_path(self):
        for i in range(len(self.context_parents) - 1):
            ith_parent = self.context_parents[i]
            ith_key = self.context_parent_keys[i]
            ith_key_type = self.context_parent_key_types[i]
            if ith_key not in ith_parent:
                if ith_key_type == 'key':
                    self._materialize_path_segment(i, CommentedMap())
                elif ith_key_type == 'index':
                    self._materialize_path_segment(i, CommentedSeq())

    def set(self, value):
        """
        Set the value of the reference to the given value.
        :param value:
        :return:
        """
        self._materialize_path()
        self._materialize_path_segment(len(self.context_parents) - 1, value)


class YInterpreter:
    def __init__(self):
        self.root = {}
        self.context = YReference(self.root)
        self.functions = {}
        self.ruamelYaml = ruamel.yaml.YAML()
        self.ruamelYaml.preserve_quotes = True

    def load(self, source):
        """
        Load a YAML document from a file to become the root context.

        :param source:
        :return:
        """
        with open(source, 'r') as f:
            new_root = self.ruamelYaml.load(f)
            self.root = new_root
            self.context = YReference(new_root)

    def interpret(self, value):
        """
        Evaluate a Lark-parsed expression against the current context.

        :param value:
        :return:
        """
        result = self._interpret(value)
        if isinstance(result, YReference):
            return result.context
        return result

    def _interpret(self, value):
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
        left_value = self._interpret(left)
        operator = value.children[1]
        right = value.children[2]
        right_value = self._interpret(right)
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
            raise Exception("Can only assign values to a reference, instead got: " + str(reference))
        value_source = self._interpret(value.children[1])
        value_sink.set(value_source)
        return value_source

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
        if isinstance(value, Exception):
            raise value


    def test(expression, expected):
        parsed = parser.parse(expression)
        try:
            result = yinterpreter.interpret(parsed)
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
    test('.a | .b | .c | [0]', yinterpreter.root['a']['b']['c'][0])
    test('.a.b.c[0] = 123', 123)
    test('.a.b.c[0]', 123)
    test('"abcdefg"', 'abcdefg')
    test('true', True)
    test('false', False)
    test('1 + 2 - 3 * 4 / 5 % 6 ^ 7', 1 + 2 - 3 * 4 / 5 % 6 ** 7)
    test('custom_fn(1 + 2, 3, 4 + 5)', None)
