#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import shutil
import filecmp

import textwrap
import threading

PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) )


def compare_text_with_file(input_text, file):
    """
        Return `True` when the provided text and the `file` contents are equal.
    """

    if os.path.exists( file ):

        with open( file, "r", encoding='utf-8' ) as file:
            text = file.read()
            return input_text == text


def create_reloader():
    reloader_code = \
    r"""
    import os
    from sublime_plugin import reload_plugin

    '''
    Reload overridden `Default.sublime-package` files because by default, Sublime Text on start up does
    not reload the overridden `Default` packages modules on `Packages/Default`.
    '''

    CURRENT_FILE_NAME = os.path.basename( __file__ )
    DEFAULT_PACKAGE_NAME = 'Default'

    PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) )
    DEFAULT_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, DEFAULT_PACKAGE_NAME )

    def reload_default_package():

        for file_name in os.listdir( DEFAULT_PACKAGE_DIRECTORY ):
            full_path = os.path.join( DEFAULT_PACKAGE_DIRECTORY, file_name )

            if not os.path.isdir( full_path ) \
                    and file_name != CURRENT_FILE_NAME:

                if file_name.endswith( '.py' ):
                    plugin_name = "%s.%s" % ( DEFAULT_PACKAGE_NAME, file_name[:-3] )
                    reload_plugin( plugin_name )

    reload_default_package()
    """
    reloader_code = textwrap.dedent(reloader_code).lstrip()

    CURRENT_FILE_NAME = os.path.basename( __file__ )
    RELOADER_PACKAGE_NAME = 'ZzzReloadDefaultPackage'

    RELOADER_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, RELOADER_PACKAGE_NAME )
    RELOADER_PACKAGE_FILE = os.path.join( RELOADER_PACKAGE_DIRECTORY, CURRENT_FILE_NAME )

    if not os.path.exists( RELOADER_PACKAGE_DIRECTORY ):
        os.makedirs( RELOADER_PACKAGE_DIRECTORY )

    if not compare_text_with_file(reloader_code, RELOADER_PACKAGE_FILE):

        with open( RELOADER_PACKAGE_FILE, 'w', newline='\n', encoding='utf-8' ) as output_file:
            print( "[zz_reload_default_package.py] Updating the plugin file: %s" % RELOADER_PACKAGE_FILE )
            output_file.write( reloader_code )


def create_settings_loader():
    notice_code = \
    """
    # 0 Settings Loader

    Loads a customized version of the Sublime Text settings before all the other packages.
    Then it allows other packages to override the customized Sublime Text settings.
    Otherwise,
    if this files are loaded with the package `Default`,
    they will override all the packages which have been loaded before this package.

    Thread:

    1. Is possible to package override a Sublime Text Default keybinding?
       https://forum.sublimetext.com/t/is-possible-to-package-override-a-sublime-text-default-keybinding/31688
    """
    notice_code = textwrap.dedent(notice_code).lstrip()

    SETTINGS_PACKAGE_NAME = '0_settings_loader'
    SETTINGS_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, SETTINGS_PACKAGE_NAME )

    README_PACKAGE_FILE = os.path.join( SETTINGS_PACKAGE_DIRECTORY, 'README.md' )
    DEFAULT_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, 'Default' )

    if not os.path.exists( SETTINGS_PACKAGE_DIRECTORY ):
        os.makedirs( SETTINGS_PACKAGE_DIRECTORY )

    if not compare_text_with_file(notice_code, README_PACKAGE_FILE):

        with open( README_PACKAGE_FILE, 'w', newline='\n', encoding='utf-8' ) as output_file:
            print( "[zz_reload_default_package.py] Updating the documentation file: %s" % README_PACKAGE_FILE )
            output_file.write( notice_code )

    settings_files = \
    [
        "Default (Linux).sublime-mousemap",
        "Default (OSX).sublime-keymap",
        "Default (OSX).sublime-mousemap",
        "Default (Windows).sublime-mousemap",
        "Default.sublime-keymap",
        "Preferences (Linux).sublime-settings",
        "Preferences (OSX).sublime-settings",
        "Preferences (Windows).sublime-settings",
        "Preferences.sublime-settings",
    ]

    for file in settings_files:
        full_path = os.path.join( DEFAULT_PACKAGE_DIRECTORY, file )
        full_destine_path = os.path.join( SETTINGS_PACKAGE_DIRECTORY, file )

        if os.path.exists( full_destine_path ):

            # https://stackoverflow.com/questions/254350/in-python-is-there-a-concise-way-of-comparing-whether-the-contents-of-two-text
            if filecmp.cmp( full_path, full_destine_path, shallow=False ):
                continue

        if not os.path.exists( full_path ):
            print( "[zz_reload_default_package.py] Error, the source setting file `%s` does not exists!" % full_path )
            continue

        print( "[zz_reload_default_package.py] Updating the setting file: %s" % full_path )
        shutil.copy( full_path, SETTINGS_PACKAGE_DIRECTORY )


def run_operations():
    create_reloader()
    create_settings_loader()


threading.Thread(target=run_operations).start()

