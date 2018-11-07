
import os
import sublime
import sublime_plugin


class PlatformEditSettings(sublime_plugin.WindowCommand):

    def run(self):
        platform        = sublime.platform()
        packages_folder = sublime.packages_path()

        if platform in ("linux", "windows"):
            setting_file = os.path.join( packages_folder, "Default", "Default.sublime-keymap" )

        else:
            setting_file = os.path.join( packages_folder, "Default", "Default (%s).sublime-keymap" % platform )

        self.window.run_command( "edit_settings",
            {
                "base_file": setting_file,
                "default": "[\n\t$0\n]\n"
            }
        )

