#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sublime
import sublime_plugin

import os
import sys
import shutil
import json
import time
import filecmp

import hashlib
import textwrap
import traceback
import threading

from collections import OrderedDict

skip_packing = False
_lock = threading.Lock()


try:
    from PackagesManager.package_control.package_manager import PackageManager
    from PackagesManager.package_control.package_disabler_iterator import IgnoredPackagesBugFixer

except ImportError:
    skip_packing = True

PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) )

SETTINGS_PACKAGE_NAME = '0_settings_loader'
SETTINGS_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, SETTINGS_PACKAGE_NAME )

README_PACKAGE_FILE = os.path.join( SETTINGS_PACKAGE_DIRECTORY, 'README.md' )
DEFAULT_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, 'Default' )

g_settings_files = \
[
    "Default (Linux).sublime-mousemap.hide",
    "Default (Linux).sublime-keymap.hide",
    "Default (OSX).sublime-keymap.hide",
    "Default (OSX).sublime-mousemap.hide",
    "Default (Windows).sublime-mousemap.hide",
    "Default (Windows).sublime-keymap.hide",
    "Preferences (Linux).sublime-settings.hide",
    "Preferences (OSX).sublime-settings.hide",
    "Preferences (Windows).sublime-settings.hide",
    "Preferences.sublime-settings.hide",
]


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
    import stat
    import shutil
    from sublime_plugin import reload_plugin

    '''
    Reload overridden `Default.sublime-package` files because by default, Sublime Text on start up does
    not reload the overridden `Default` packages modules on `Packages/Default`.
    '''

    VERSION = '1.0.0'
    CURRENT_FILE_NAME = os.path.basename( __file__ )
    DEFAULT_PACKAGE_NAME = 'Default'

    THIS_PACKAGE_ROOT = os.path.dirname( os.path.realpath( __file__ ) )
    PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) )

    DEFAULT_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, DEFAULT_PACKAGE_NAME )
    ORIGINAL_RELOADER_PATH = os.path.join( DEFAULT_PACKAGE_DIRECTORY, CURRENT_FILE_NAME )

    def safe_remove(path):

        try:
            os.remove( path )

        except Exception as error:
            print( "[zz_reload_default_package.py] Failed to remove `%s`. Error is: %s" % ( path, error) )

            try:
                delete_read_only_file(path)

            except Exception as error:
                print( "[zz_reload_default_package.py] Failed to remove `%s`. Error is: %s" % ( path, error) )

    def delete_read_only_file(path):
        _delete_read_only_file( None, path, None )

    def _delete_read_only_file(action, name, exc):
        os.chmod( name, stat.S_IWRITE )
        os.remove( name )

    def reload_default_package():

        for file_name in os.listdir( DEFAULT_PACKAGE_DIRECTORY ):
            full_path = os.path.join( DEFAULT_PACKAGE_DIRECTORY, file_name )

            if not os.path.isdir( full_path ) \
                    and file_name != CURRENT_FILE_NAME:

                if file_name.endswith( '.py' ):
                    plugin_name = "%s.%s" % ( DEFAULT_PACKAGE_NAME, file_name[:-3] )
                    reload_plugin( plugin_name )

    try:
        reload_default_package()

    except FileNotFoundError:
        pass

    # Remove itself if the Default package is not found
    if not os.path.exists( ORIGINAL_RELOADER_PATH ):
        print("[zz_reload_default_package.py] %s Uninstalling %s... Because the %s package was not found installed at %s." % (
                VERSION, THIS_PACKAGE_ROOT, DEFAULT_PACKAGE_NAME, ORIGINAL_RELOADER_PATH ) )
        shutil.rmtree( THIS_PACKAGE_ROOT, onerror=_delete_read_only_file )
    """
    reloader_code = textwrap.dedent(reloader_code).lstrip()

    CURRENT_FILE_NAME = os.path.basename( __file__ )
    RELOADER_PACKAGE_NAME = 'ZzzReloadDefaultPackage'

    RELOADER_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, RELOADER_PACKAGE_NAME )
    RELOADER_PACKAGE_FILE = os.path.join( RELOADER_PACKAGE_DIRECTORY, CURRENT_FILE_NAME )
    PYTHON_VERSION_FILE = os.path.join( RELOADER_PACKAGE_DIRECTORY, '.python-version' )

    if not os.path.exists( RELOADER_PACKAGE_DIRECTORY ):
        os.makedirs( RELOADER_PACKAGE_DIRECTORY )

    if not compare_text_with_file(reloader_code, RELOADER_PACKAGE_FILE):
        with open( PYTHON_VERSION_FILE, 'w', newline='\n', encoding='utf-8' ) as output_file:
            output_file.write( '3.8' )

        with open( RELOADER_PACKAGE_FILE, 'w', newline='\n', encoding='utf-8' ) as output_file:
            print( "[zz_reload_default_package.py] Updating the plugin file: %s" % RELOADER_PACKAGE_FILE )
            output_file.write( reloader_code )


def compute_file_hash(file_path):
    """ https://stackoverflow.com/questions/22058048/hashing-a-file-in-python """
    # BUF_SIZE is totally arbitrary, change for your app!
    # lets read stuff in 64kb chunks!
    BUF_SIZE = 65536
    sha256 = hashlib.sha256()

    with open( file_path, 'rb' ) as file:

        while True:
            data = file.read( BUF_SIZE )
            if not data: break
            sha256.update( data )

    return sha256.hexdigest()


def check_settings_changes():
    settings_package_file = os.path.join( sublime.installed_packages_path(), "%s.sublime-package" % SETTINGS_PACKAGE_NAME )
    if not os.path.exists( settings_package_file ): return True

    has_changed_hashes = False
    hashes_cache_path = os.path.join( sublime.cache_path(), "zz_reload_default_package.json" )

    clean_file_hashes = {}
    loaded_file_hashes = load_data_file( hashes_cache_path )

    for file_name in g_settings_files:
        file_path = os.path.join( DEFAULT_PACKAGE_DIRECTORY, file_name )
        current_hash = compute_file_hash( file_path )

        if file_name in loaded_file_hashes:

            if current_hash != loaded_file_hashes[file_name]:
                has_changed_hashes = True
                print( "[zz_reload_default_package.py] Hash change for setting file: %s" % file_path )

        else:
            has_changed_hashes = True

        clean_file_hashes[file_name] = current_hash

    if clean_file_hashes != loaded_file_hashes:
        write_data_file( hashes_cache_path, clean_file_hashes )

    return has_changed_hashes


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

    if not os.path.exists( SETTINGS_PACKAGE_DIRECTORY ):
        os.makedirs( SETTINGS_PACKAGE_DIRECTORY )

    if not compare_text_with_file(notice_code, README_PACKAGE_FILE):

        with open( README_PACKAGE_FILE, 'w', newline='\n', encoding='utf-8' ) as output_file:
            print( "[zz_reload_default_package.py] Updating the documentation file: %s" % README_PACKAGE_FILE )
            output_file.write( notice_code )

    for file in g_settings_files:
        full_path = os.path.join( DEFAULT_PACKAGE_DIRECTORY, file )
        full_destine_path = os.path.join( SETTINGS_PACKAGE_DIRECTORY, file.rstrip('.hide') )

        if os.path.exists( full_destine_path ):

            # https://stackoverflow.com/questions/254350/in-python-is-there-a-concise-way-of-comparing-whether-the-contents-of-two-text
            if filecmp.cmp( full_path, full_destine_path, shallow=False ):
                continue

        if not os.path.exists( full_path ):
            print( "[zz_reload_default_package.py] Error, the source setting file `%s` does not exists!" % full_path )
            continue

        print( "[zz_reload_default_package.py] Updating the setting file: %s" % full_path )
        shutil.copyfile( full_path, full_destine_path )

    print( "" )
    if skip_packing:
        print( "[zz_reload_default_package.py] Warning:\n"
              "    Skipping packing %s because PackagesManager was not found installed..." % SETTINGS_PACKAGE_NAME )
        return

    manager = PackageManager()
    settings_package_file = os.path.join( sublime.installed_packages_path(), "%s.sublime-package" % SETTINGS_PACKAGE_NAME )
    settings_package_cache = os.path.join( sublime.cache_path(), "%s.sublime-package" % SETTINGS_PACKAGE_NAME )

    if manager.create_package( SETTINGS_PACKAGE_NAME, sublime.cache_path() ):
        shutil.rmtree( SETTINGS_PACKAGE_DIRECTORY )
        print( "[zz_reload_default_package.py] Creating the package file %s" % settings_package_cache )

    else:
        print( "[zz_reload_default_package.py] Error: Could not create the package file %s" % settings_package_cache )

    for package in IgnoredPackagesBugFixer( [SETTINGS_PACKAGE_NAME], "upgrade" ):
        shutil.move( settings_package_cache, settings_package_file )

    print( "[zz_reload_default_package.py] Finished installing the package file %s" % settings_package_file )


def run_operations():

    if _lock.locked():
        print( "[zz_reload_default_package.py] Cannot run because it is already running!" )
        return

    _lock.acquire()

    try:
        create_reloader()

        if check_settings_changes():
            create_settings_loader()

        else:
            print( "[zz_reload_default_package.py] No changes in any settings file!" )

    except Exception:
        raise

    finally:
        _lock.release()


class ReloadHiddenDefaultSettingsCommand(sublime_plugin.WindowCommand):

    def run(self):
        print( "[zz_reload_default_package.py] Running Default Package Hidden Settings Reload..." )
        plugin_loaded()


def plugin_loaded():
    threading.Thread( target=run_operations ).start()


def write_data_file(file_path, dictionary_data):

    with open( file_path, 'w', newline='\n', encoding='utf-8' ) as output_file:
        json.dump( dictionary_data, output_file, indent='\t', separators=(',', ': ') )
        output_file.write('\n')


def load_data_file(file_path, wait_on_error=True):
    """
        Attempt to read the file some times when there is a value error. This could happen when the
        file is currently being written by Sublime Text.
    """
    dictionary_data = {}

    if os.path.exists( file_path ):
        maximum_attempts = 3

        while maximum_attempts > 0:

            try:
                with open( file_path, 'r', encoding='utf-8' ) as studio_channel_data:
                    return json.load( studio_channel_data, object_pairs_hook=OrderedDict )

            except ValueError as error:
                print( "[zz_reload_default_package.py] Error, maximum_attempts %d, load_data_file: %s, %s" % (
                        maximum_attempts, file_path, error ) )
                maximum_attempts -= 1

                if wait_on_error:
                    time.sleep( 0.1 )

        if maximum_attempts < 1:
            print( "[zz_reload_default_package.py] Error: maximum_attempts exausted on file_path: %s" % file_path )

    else:
        print( "[zz_reload_default_package.py] Error on load_data_file(1), the file '%s' does not exists! \n%s\n" % (
                file_path, "".join( traceback.format_stack() ) ) )

    return dictionary_data

