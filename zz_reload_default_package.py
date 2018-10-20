#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os

reloader = \
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

CURRENT_FILE_NAME = os.path.basename( __file__ )
RELOADER_PACKAGE_NAME = 'ZzzReloadDefaultPackage'
PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) )

RELOADER_PACKAGE_DIRECTORY = os.path.join( PACKAGE_ROOT_DIRECTORY, RELOADER_PACKAGE_NAME )
RELOADER_PACKAGE_FILE = os.path.join( RELOADER_PACKAGE_DIRECTORY, CURRENT_FILE_NAME )


if not os.path.exists( RELOADER_PACKAGE_DIRECTORY ):
    os.makedirs( RELOADER_PACKAGE_DIRECTORY )

with open( RELOADER_PACKAGE_FILE, 'w', newline='\n', encoding='utf-8' ) as output_file:
    output_file.write( reloader )


