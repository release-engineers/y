#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ruamel.yaml.comments import CommentedMap, CommentedSeq


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

    def root(self):
        if len(self.context_parents) == 0:
            return self.context
        else:
            return self.context_parents[0]

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
