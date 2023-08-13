import sys
import ruamel.yaml
from y.yinterpreter import YInterpreter, parser


def test_cli():
    yinterpreter = YInterpreter()
    yinterpreter.load('tests/sample.yml')

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
