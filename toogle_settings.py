import sublime
import sublime_plugin

per_window_settings = {}
capture_new_window_from = None

def set_settings(window_views, active_view_settings):

    for view in window_views:

        for setting in active_view_settings:
            view.settings().set(setting, active_view_settings[setting])


class ToggleSettingsCommand(sublime_plugin.WindowCommand):
    """
    Given several settings, toggle their values.
    window.run_command("toggle_settings", {"settings": ["fold_buttons", "line_numbers"]})

    @param same_value, if True, will set either all setting to True or False, depending on the first
                        setting value.
    """

    def run(self, settings, same_value=True):
        if not isinstance(settings, list): settings = [settings]
        window_id = self.window.id()
        active_view_settings = {}

        per_window_settings[window_id] = active_view_settings
        active_view = self.window.active_view()
        first_setting_value = not active_view.settings().get(settings[0], False)

        for setting in settings:

            if same_value:
                active_view_settings[setting] = first_setting_value

            else:
                active_view_settings[setting] = not active_view.settings().get(setting, False)

        set_settings(self.window.views(), active_view_settings)


class ToggleSettingsCommandListener(sublime_plugin.EventListener):

    def on_new_async(self, view):
        global capture_new_window_from
        window = sublime.active_window()
        window_id = window.id()

        if capture_new_window_from is not None:
            active_view_settings = capture_new_window_from
            capture_new_window_from = None
            per_window_settings[window_id] = active_view_settings

            window_views = [window.active_view()]
            window_views.extend(window.views())
            set_settings(window_views, active_view_settings)

        elif window_id in per_window_settings:
            active_view_settings = per_window_settings[window_id]
            set_settings(window.views(), active_view_settings)

    def on_window_command(self, window, command_name, args):

        if command_name == "new_window":
            window_id = window.id()

            if window_id in per_window_settings:
                active_view_settings = per_window_settings[window_id]

                global capture_new_window_from
                capture_new_window_from = active_view_settings
