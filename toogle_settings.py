import sublime
import sublime_plugin

per_window_settings = {}
capture_new_window_from = None

try:
    from FixedToggleFindPanel.fixed_toggle_find_panel import get_panel_view
    from FixedToggleFindPanel.fixed_toggle_find_panel import is_panel_focused

except ImportError as error:
    print('Default.toggle_settings Error: Could not import the FixedToggleFindPanel package!', error)

    def get_panel_view(window, panel_name):
        return None

    def is_panel_focused():
        return False


def set_settings(window_views, view_settings):

    for view in window_views:

        for setting in view_settings:
            # print('setting view', view.id(), 'view_settings', view_settings[setting])
            view.settings().set(setting, view_settings[setting])


def get_views(view, window, skip_panel=False):
    views = window.views()

    if not skip_panel:
        active_panel = window.active_panel()

        # https://github.com/SublimeTextIssues/Core/issues/2929
        if active_panel and active_panel != 'console':
            panel_view = get_panel_view( window, active_panel )

            if panel_view:
                views.append( panel_view )

    if not is_panel_focused():
        is_widget = view.settings().get( 'is_widget' )

        if not is_widget:
            views.append( view )

    return views


class EraseWindowSettingsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global per_window_settings
        view = self.view
        window = view.window()

        window_settings = window.settings()
        window_views = get_views( view, window )

        toggle_settings = window_settings.get( 'toggle_settings', {} )
        toggle_settings.update( window_settings.get( 'toggle_settings_for_panel', {} ) )

        for setting in toggle_settings:
            print('Erasing window', window.id(), 'setting', setting)

            for view in window_views:
                view.settings().erase(setting)

        per_window_settings = {}
        window_settings.set( 'toggle_settings', per_window_settings )
        window_settings.set( 'toggle_settings_for_panel', {} )


class IncrementSettingCommand(sublime_plugin.TextCommand):
    """
    Given a setting name and a number, increment the setting by this number.
    window.run_command("increment_setting", {"setting": "font_size", "increment": 1})
    """

    def run(self, edit, setting, increment, view_only):
        view = self.view
        window = view.window()
        window_id = window.id()

        is_widget = view.settings().get( 'is_widget' )
        if is_widget:
            view = window.active_view()

        if view_only:

            if is_panel_focused():
                window_settings = window.settings()
                toggle_settings = window_settings.get( 'toggle_settings_for_panel', {} )

            else:
                view_settings = view.settings()
                toggle_settings = view_settings.get( 'toggle_settings', {} )

        else:
            window_settings = window.settings()
            toggle_settings = window_settings.get( 'toggle_settings', {} )
            per_window_settings[window_id] = toggle_settings

        try:
            # print('running... toggle_settings', toggle_settings)
            setting_value = view.settings().get( setting, 0 )
            new_value = setting_value + increment

            print( 'Changing setting', setting, 'from', setting_value, '->', new_value )
            toggle_settings[setting] = new_value

        except:
            print( '[toggle_settings] Unexpected value for setting', setting, '->', setting_value )
            toggle_settings[setting] = increment

        if view_only:
            views = [view]

            if is_panel_focused():
                window_settings.set( 'toggle_settings_for_panel', toggle_settings )

            else:
                view_settings.set( 'toggle_settings', toggle_settings )

        else:
            toggle_settings_for_panel = window_settings.get( 'toggle_settings_for_panel', {} )
            skip_panel = setting in toggle_settings_for_panel

            views = get_views( view, window, skip_panel )
            window_settings.set( 'toggle_settings', toggle_settings )

        set_settings( views, toggle_settings )


class ToggleSettingsCommand(sublime_plugin.TextCommand):
    """
    Given several settings, toggle their values.
    window.run_command("toggle_settings", {"settings": ["fold_buttons", "line_numbers"]})

    @param same_value, if True, will set either all setting to True or False, depending on the first
                        setting value.
    """

    def run(self, settings, same_value, view_only):
        if not isinstance(settings, list): settings = [settings]
        view = self.view
        window = view.window()
        window_id = window.id()

        is_widget = view.settings().get( 'is_widget' )
        if is_widget:
            view = window.active_view()

        if view_only:

            if is_panel_focused():
                window_settings = window.settings()
                toggle_settings = window_settings.get( 'toggle_settings_for_panel', {} )

            else:
                view_settings = view.settings()
                toggle_settings = view_settings.get( 'toggle_settings', {} )

        else:
            window_settings = window.settings()
            toggle_settings = window_settings.get( 'toggle_settings', {} )
            per_window_settings[window_id] = toggle_settings

        first_setting_value = not view.settings().get( settings[0], False )

        # print('running... toggle_settings', toggle_settings)
        for setting in settings:

            if same_value:
                toggle_settings[setting] = first_setting_value

            else:
                toggle_settings[setting] = not view.settings().get( setting, False )

        if view_only:
            views = [view]

            if is_panel_focused():
                window_settings.set( 'toggle_settings_for_panel', toggle_settings )

            else:
                view_settings.set( 'toggle_settings', toggle_settings )

        else:
            toggle_settings_for_panel = window_settings.get( 'toggle_settings_for_panel', {} )
            skip_panel = setting in toggle_settings_for_panel

            views = get_views( view, window, skip_panel )
            window_settings.set( 'toggle_settings', toggle_settings )

        set_settings( views, toggle_settings )


class ToggleSettingsCommandListener(sublime_plugin.EventListener):

    def on_new(self, view):
        # https://github.com/SublimeTextIssues/Core/issues/2906
        self.on_load(view)

    def on_load(self, view):
        global capture_new_window_from
        window = view.window()
        window_id = window.id()

        # print("window_id", window_id, 'window_id in per_window_settings', window_id in per_window_settings)
        if capture_new_window_from is not None:
            toggle_settings = capture_new_window_from
            capture_new_window_from = None
            per_window_settings[window_id] = toggle_settings

            window_views = [window.active_view(), view]
            window_views.extend(window.views())
            set_settings(window_views, toggle_settings)

        elif window_id in per_window_settings:
            toggle_settings = per_window_settings[window_id]
            set_settings([view], toggle_settings)

        else:
            window_settings = window.settings()
            toggle_settings = window_settings.get('toggle_settings', {})
            # print('on_load... toggle_settings', toggle_settings)

            if toggle_settings:
                per_window_settings[window_id] = toggle_settings
                set_settings([view], toggle_settings)

    def on_window_command(self, window, command_name, args):
        # print('command_name', command_name)

        if command_name == "new_window":
            window_id = window.id()

            if window_id in per_window_settings:
                toggle_settings = per_window_settings[window_id]

                global capture_new_window_from
                capture_new_window_from = toggle_settings

    def on_post_window_command(self, window, command_name, args):
        # print('command_name', command_name)

        if command_name == "show_panel":
            active_panel = window.active_panel()

            if active_panel:
                view = get_panel_view( window, active_panel )

                if view:
                    window_settings = window.settings()
                    toggle_settings = window_settings.get( 'toggle_settings', {} )

                    toggle_settings.update( window_settings.get( 'toggle_settings_for_panel', {} ) )
                    set_settings([view], toggle_settings)


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
