import sublime
import sublime_plugin

per_window_settings = {}
capture_new_window_from = None

def set_settings(window_views, active_view_settings):

    for view in window_views:

        for setting in active_view_settings:
            # print('setting view', view.id(), 'active_view_settings', active_view_settings[setting])
            view.settings().set(setting, active_view_settings[setting])


class EraseWindowSettingsCommand(sublime_plugin.WindowCommand):

    def run(self):
        global per_window_settings
        per_window_settings = {}

        window = self.window
        window_settings = window.settings()

        active_view_settings = window_settings.get('toogle_settings', {})
        window_settings.set('toogle_settings', active_view_settings)


class IncrementSettingCommand(sublime_plugin.WindowCommand):
    """
    Given a setting name and a number, increment the setting by this number.
    window.run_command("increment_setting", {"setting": "font_size", "increment": 1})
    """

    def run(self, setting, increment):
        window = self.window
        window_id = self.window.id()

        window_settings = window.settings()
        active_view_settings = window_settings.get('toogle_settings', {})

        per_window_settings[window_id] = active_view_settings
        active_view = self.window.active_view()

        try:
            # print('running... active_view_settings', active_view_settings)
            setting_value = active_view.settings().get(setting, 0)
            new_value = setting_value + increment

            print('Changing setting', setting, 'from', setting_value, '->', new_value)
            active_view_settings[setting] = new_value

        except:
            print('[toogle_settings] Unexpected value for setting', setting, '->', setting_value)
            active_view_settings[setting] = increment

        window_settings.set('toogle_settings', active_view_settings)
        set_settings(self.window.views(), active_view_settings)


class ToggleSettingsCommand(sublime_plugin.WindowCommand):
    """
    Given several settings, toggle their values.
    window.run_command("toggle_settings", {"settings": ["fold_buttons", "line_numbers"]})

    @param same_value, if True, will set either all setting to True or False, depending on the first
                        setting value.
    """

    def run(self, settings, same_value=True):
        if not isinstance(settings, list): settings = [settings]
        window = self.window
        window_id = self.window.id()

        window_settings = window.settings()
        active_view_settings = window_settings.get('toogle_settings', {})

        per_window_settings[window_id] = active_view_settings
        active_view = self.window.active_view()
        first_setting_value = not active_view.settings().get(settings[0], False)

        # print('running... active_view_settings', active_view_settings)
        for setting in settings:

            if same_value:
                active_view_settings[setting] = first_setting_value

            else:
                active_view_settings[setting] = not active_view.settings().get(setting, False)

        window_settings.set('toogle_settings', active_view_settings)
        set_settings(self.window.views(), active_view_settings)


class ToggleSettingsCommandListener(sublime_plugin.EventListener):

    def on_new(self, view):
        self.on_load(view)

    def on_load(self, view):
        global capture_new_window_from
        window = sublime.active_window()
        window_id = window.id()
        # print("window_id", window_id, 'window_id in per_window_settings', window_id in per_window_settings)

        if capture_new_window_from is not None:
            active_view_settings = capture_new_window_from
            capture_new_window_from = None
            per_window_settings[window_id] = active_view_settings

            window_views = [window.active_view(), view]
            window_views.extend(window.views())
            set_settings(window_views, active_view_settings)

        elif window_id in per_window_settings:
            active_view_settings = per_window_settings[window_id]
            set_settings([view], active_view_settings)

        else:
            window_settings = window.settings()
            active_view_settings = window_settings.get('toogle_settings', {})
            # print('on_load... active_view_settings', active_view_settings)

            if active_view_settings:
                per_window_settings[window_id] = active_view_settings
                set_settings([view], active_view_settings)

    def on_window_command(self, window, command_name, args):
        # print('command_name', command_name)

        if command_name == "new_window":
            window_id = window.id()

            if window_id in per_window_settings:
                active_view_settings = per_window_settings[window_id]

                global capture_new_window_from
                capture_new_window_from = active_view_settings


class MinimapPerViewSettingEvent(sublime_plugin.EventListener):
    """
        The problem is that because hiding/showing the minimap is a window command, it affects every
        file in the window. https://forum.sublimetext.com/t/hide-minimap-for-certain-filetypes/24557
    """

    def on_activated(self, view):
        show_minimap = view.settings().get('show_minimap')

        if show_minimap:
            view.window().set_minimap_visible(True)

        elif show_minimap is not None:
            view.window().set_minimap_visible(False)


class ToggleMinimapPerWindow(sublime_plugin.WindowCommand):

    def run(self):
        settings = self.window.active_view().settings()
        show_minimap = not settings.get('show_minimap')
        settings.set('show_minimap', show_minimap)

        if show_minimap:
            self.window.set_minimap_visible(True)

        elif show_minimap is not None:
            self.window.set_minimap_visible(False)
