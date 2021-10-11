

import os

import sublime
import sublime_plugin


class InstallPackageControlExtendedCommand(sublime_plugin.ApplicationCommand):
    filename = 'Package Control.sublime-package'
    manager_filename = 'PackagesManager.sublime-package'

    def run(self):
        sublime.run_command( "install_package_control" )

    def is_visible(self):
        package_control = not self.exists_packages_manager( self.filename )
        packages_manager = not self.exists_packages_manager( self.manager_filename )
        return package_control and packages_manager

    def exists_packages_manager(self, file_name):
        loose_packages_path = os.path.join(sublime.packages_path(), file_name.replace('.sublime-package', ''))
        installed_packages_path = os.path.join(sublime.installed_packages_path(), file_name)

        return os.path.exists(installed_packages_path) or os.path.exists(loose_packages_path)

