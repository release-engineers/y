#!/usr/bin/env python
# -*- coding: utf-8 -*-

from y.yinterpreter import YInterpreter
import sys


def usage():
    print("  y -- https://github.com/release-engineers/y")
    print()
    print("Usage: y [options] [-- <args>]")
    print("  -h, --help         Show this help message and exit")
    print("  -f, --file <file>  The file to load where '-' denotes stdin")
    print("  -i, --inplace      Edit a source file in place")
    print("  --indent-mapping <indent>  Indentation for mapping, default 2")
    print("  --indent-sequence <indent>  Indentation for sequence, default 4")
    print("  --indent-offset <offset>  Indentation offset, default 2")
    print("  -- <args>          Expression to evaluate")


def main():
    inplace = False
    file_reference = None
    expressions = []
    indent_mapping = 2
    indent_sequence = 4
    indent_offset = 2

    args = sys.argv[1:]

    if len(args) == 0:
        usage()
        exit(0)

    while len(args) > 0:
        arg = args.pop(0)
        if arg == '-h' or arg == '--help':
            usage()
            exit(0)
        elif arg == '-f' or arg == '--file':
            if file_reference is not None:
                print("Error: Multiple source files specified")
                usage()
                exit(1)
            file_reference = args.pop(0)
        elif arg == '-i' or arg == '--inplace':
            inplace = True
        elif arg == '--indent-mapping':
            indent_mapping = int(args.pop(0))
        elif arg == '--indent-sequence':
            indent_sequence = int(args.pop(0))
        elif arg == '--indent-offset':
            indent_offset = int(args.pop(0))
        elif arg == '--':
            expressions.extend(args)
            args.clear()
        else:
            expressions.append(arg)

    if file_reference is None:
        file_reference = '-'

    if inplace and file_reference == '-':
        print("Error: Cannot edit stdin in place")
        usage()
        exit(1)

    file = sys.stdin if file_reference == '-' else file_reference

    yinterpreter = YInterpreter(indent_mapping=indent_mapping,
                                indent_sequence=indent_sequence,
                                indent_offset=indent_offset)
    yinterpreter.load(file)
    for expression in expressions:
        yinterpreter.interpret(expression)

    if inplace:
        with open(file_reference, 'w') as file:
            yinterpreter.dump(file)
    else:
        yinterpreter.dump(sys.stdout)


if __name__ == '__main__':
    main()
