
import os

import sublime
import sublime_plugin


class PlatformEditSettings(sublime_plugin.WindowCommand):

    def run(self, **kwargs):
        # platform        = sublime.platform()
        # packages_folder = sublime.packages_path()
        # setting_file = os.path.join( packages_folder, "0_settings_loader", "Default (%s).sublime-keymap" % platform )

        base_file = kwargs.get('base_file')
        default = kwargs.get('default')

        base_file = base_file.replace('.sublime-keymap', '.sublime-keymap.hide')
        base_file = base_file.replace('.sublime-settings', '.sublime-settings.hide')

        # print('base_file', base_file)
        # print('default', default)

        self.window.run_command( "edit_settings",
            {
                "base_file": base_file,
                "default": default
            }
        )

