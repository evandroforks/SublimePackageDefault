#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sublime

import io
import os
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

    new_sublime_module_contents = sublime_module_contents.replace(
            'raise IOError("resource not found")',
            'raise IOError("resource `%s` not found" % (name))' )

    if sublime_module_contents != new_sublime_module_contents:

        with io.open(sublime_module_path, 'w', newline=None) as destine_file:
            destine_file.write( new_sublime_module_contents )


def _monkey_patch_sublime_plugin(sublime_directory):
    pass

