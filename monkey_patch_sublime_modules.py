#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sublime

import io
import os
import re
import threading


def plugin_loaded():
    threading.Thread(target=_monkey_patch_sublime_modules).start()


def _monkey_patch_sublime_modules():

    try:
        sublime_directory = os.path.dirname( sublime.executable_path() )

        _monkey_patch_sublime(sublime_directory)
        _monkey_patch_sublime_plugin(sublime_directory)

    except:
        pass
        # raise


def _monkey_patch_sublime(sublime_directory):
    sublime_module_path = os.path.join( sublime_directory, "sublime.py" )

    with io.open(sublime_module_path, 'r', newline=None) as model_file:
        sublime_module_contents = model_file.read()

    # https://github.com/SublimeTextIssues/Core/issues/2113
    new_sublime_module_contents = re.sub(
            r'raise IOError("resource not found")',
            r'raise IOError("resource `%s` not found" % (name))',
            sublime_module_contents)

    # https://github.com/SublimeTextIssues/Core/issues/2949
    new_sublime_module_contents = re.sub(
            r'(?m)^(\s+)return self.view_id != 0\n(?=[\s\n]+def is\_valid\(self\):)',
            r'\1return self.view_id != 0 and not not len( self )\n',
            sublime_module_contents)

    if sublime_module_contents != new_sublime_module_contents:

        with io.open(sublime_module_path, 'w', newline=None) as destine_file:
            destine_file.write( new_sublime_module_contents )


def _monkey_patch_sublime_plugin(sublime_directory):
    sublime_module_path = os.path.join( sublime_directory, "sublime_plugin.py" )

    with io.open(sublime_module_path, 'r', newline=None) as model_file:
        sublime_module_contents = model_file.read()

    # https://github.com/SublimeTextIssues/Core/issues/2930
    new_sublime_module_contents = re.sub(
            r'(?m)^(\s+)return\n(\s+)raise\n$',
            r'\1return\n\2raise TypeError( "%s, %s" % ( type(self), e ) )\n',
            sublime_module_contents)

    if sublime_module_contents != new_sublime_module_contents:

        with io.open(sublime_module_path, 'w', newline=None) as destine_file:
            destine_file.write( new_sublime_module_contents )
