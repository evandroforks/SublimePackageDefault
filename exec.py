import os
import subprocess
import sys
import threading
import time
import codecs
import signal
import html

import sublime
import sublime_plugin


import re
import datetime

g_last_scroll_positions = {}

g_last_click_time = time.time()
g_last_click_buttons = None

try:
    from FixedToggleFindPanel.fixed_toggle_find_panel import is_panel_focused

except ImportError as error:
    print('Default.exec Error: Could not import the FixedToggleFindPanel package!', error)

    def is_panel_focused():
        return True


# https://forum.sublimetext.com/t/why-do-i-call-show-panel-with-output-exec-but-need-to-call-window-find-output-panel-exec-instead-of-window-find-output-panel-output-exec/45739
def get_panel_name(panel_name):
    return panel_name[len("output."):] if panel_name.startswith("output.") else panel_name


def get_panel_view(window, panel_name ):
    return window.find_output_panel( panel_name ) or \
            window.find_output_panel( get_panel_name( panel_name ) )


# https://forum.sublimetext.com/t/how-to-set-focus-to-exec-output-panel/26689/5
# https://forum.sublimetext.com/t/how-to-track-if-an-output-panel-is-closed-hidden/8453/6
class ExecOutputFocusCancelBuildCommand(sublime_plugin.WindowCommand):

    def run(self, panel):
        window = self.window
        active_panel = window.active_panel()

        if active_panel and get_panel_name( active_panel ) == 'exec':
            panel_view = get_panel_view( window, active_panel )
            settings = panel_view.settings()

            if is_panel_focused() or settings.get( 'always_cancel_output_build_panel', False ):
                user_notice = "Cancelling the build for '%s' panel..." % active_panel
                print( str(datetime.datetime.now())[:-4], user_notice )

                # https://github.com/SublimeTextIssues/Core/issues/2198
                window.focus_view( panel_view )
                window.run_command( 'cancel_build' )
                ThreadProgress.stop()

            else:
                user_notice = "Focusing on the '%s' panel..." % active_panel
                print( str(datetime.datetime.now())[:-4], user_notice )
                window.focus_view( panel_view )

            sublime.status_message( user_notice )

        else:
            window.run_command( 'show_panel', { 'panel': panel } )
            window.focus_group( window.active_group() )


class FullRegexListener(sublime_plugin.EventListener):

    def replaceby(self, string, replacements):
        # print('replacements', replacements)

        for items in replacements:
            regex = items[0]
            replacement = items[1]
            string = re.sub( regex, replacement, string )
        return string

    def on_text_command(self, view, command_name, args):
        # print('command_name', command_name, 'args', args)
        result_full_regex = view.settings().get('result_full_regex')

        # print('result_full_regex', result_full_regex)
        if result_full_regex and command_name == 'drag_select' and 'event' in args:
            global g_last_click_time
            global g_last_click_buttons

            clicks_buttons = args['event']
            new_click = time.time()

            if clicks_buttons == g_last_click_buttons:
                click_time = new_click - g_last_click_time

                if click_time < 0.6:
                    view_selections = view.sel()

                    if view_selections:
                        full_line = view.substr( view.full_line( view_selections[0] ) )

                        # print('Double clicking', click_time, 'full_line', full_line )
                        full_regex_object = re.compile( result_full_regex )
                        matchobject = full_regex_object.search( full_line )

                        if matchobject:
                            groupindex = full_regex_object.groupindex

                            # https://github.com/SublimeTextIssues/Core/issues/227
                            filename = matchobject.group('file').strip( ' ' )   if 'file'   in groupindex else None
                            line     = matchobject.group('line').strip( ' ' )   if 'line'   in groupindex else "0"
                            column   = matchobject.group('column').strip( ' ' ) if 'column' in groupindex else "0"

                            window = view.window() or sublime.active_window()
                            extract_variables = window.extract_variables()

                            # github.com/SublimeTextIssues/Core/issues/1482
                            active_view = window.active_view()
                            group, view_index = window.get_view_index( active_view )
                            window.set_view_index( active_view, group, 0 )

                            # https://github.com/SublimeTextIssues/Core/issues/938
                            result_replaceby = view.settings().get( 'result_replaceby', {} )
                            result_real_dir = view.settings().get( 'result_real_dir', [ os.path.abspath( '.' ) ] )

                            if filename:
                                assert isinstance( result_real_dir, list ), "Error: '%s' must be an instance of list!" % result_real_dir

                                for possible_root in result_real_dir:
                                    real_dir_file = os.path.join( possible_root, filename )
                                    real_dir_file = sublime.expand_variables( real_dir_file, extract_variables )
                                    real_dir_file = self.replaceby( real_dir_file, result_replaceby )

                                    if os.path.exists( real_dir_file ):
                                        filepath = real_dir_file
                                        break

                                else:
                                    base_dir_file = view.settings().get( 'result_base_dir' )
                                    filepath = os.path.join( base_dir_file, filename )
                                    filepath = sublime.expand_variables( filepath, extract_variables )
                                    filepath = self.replaceby( filepath, result_replaceby )

                                filepath = os.path.normpath( filepath )

                            else:
                                filepath = active_view.file_name()

                            print( '[exec] Opening', filename, line, column, 'file', filepath, real_dir_file )

                            fileview = window.open_file(
                                filepath + ":" + line + ":" + column,
                                sublime.ENCODED_POSITION | sublime.FORCE_GROUP
                            )

                            # https://github.com/SublimeTextIssues/Core/issues/2506
                            restore_view( fileview, window, lambda: None )
                            window.set_view_index( active_view, group, view_index )

                            # window.focus_group( group )
                            # window.focus_view( fileview )

            g_last_click_time = new_click
            g_last_click_buttons = clicks_buttons


class FixSublimeTextOutputBuild(sublime_plugin.WindowCommand):

    def run(self, **kwargs) :
        window = self.window
        output_view = window.find_output_panel( "exec" )

        # We need to save the view positions before the builtin `build` command run, because it
        # immediately erases the view contents.
        self.saveViewPositions( window, output_view )

        # https://github.com/SublimeTextIssues/Core/issues/1049
        window.run_command( 'cancel_build' )
        window.run_command( 'build', kwargs )

    def saveViewPositions(self, window, output_view):

        if output_view:
            window_id = window.id()
            view_settings = window.active_view().settings()

            if view_settings.get( 'restore_output_view_scroll' , False ):

                g_last_scroll_positions[window_id] = (output_view.viewport_position(),
                        [(selection.begin(), selection.end()) for selection in output_view.sel()])

                # print( 'Before substr:                     ', output_view.substr(sublime.Region(0, 10)) )
                # print( 'Before window.id:                  ', window.id() )
                # print( 'Before output_view:                ', output_view )
                # print( 'Before output_view.id:             ', output_view.id() )
                # print( 'g_last_scroll_positions[window_id] ', g_last_scroll_positions[window_id] )

            else:
                # Force to disable the scroll restoring, if the setting is disabled after being enabled
                g_last_scroll_positions[window_id] = (None, None)


# exit_now = False
# def plugin_loaded():
#     def function():
#         global exit_now
#         exit_now = False
#         threading.Thread(target=save_output_view_scroll).start()
#     global exit_now
#     exit_now = True
#     sublime.set_timeout_async( function, 1000 )

# def save_output_view_scroll():
#     global exit_now
#     while True:
#         time.sleep(0.5)
#         if exit_now:
#             break
#         window = sublime.active_window()
#         output_view = window.find_output_panel("exec")
#         if output_view:
#             print('substr1:                 ', output_view.substr(sublime.Region(0, 10)))
#             print('window.id:               ', window.id())
#             print('output_view:             ', output_view)
#             print('output_view.id:          ', output_view.id())
#         else:
#             print('output_view:             ', output_view)


class ThreadProgress():
    """
    Animates an indicator, [=   ], in the status area while a thread runs

    Based on Package Control
    https://github.com/wbond/package_control/blob/db53090bd0920ca2c58ef27f0361a4d7b096df0e/package_control/thread_progress.py

    :param thread:
        The thread to track for activity

    :param message:
        The message to display next to the activity indicator

    :param success_message:
        The message to display once the thread is complete
    """
    windows = {}
    running = False

    def __init__(self, message, success_message):
        self.status_name = "output_build_view_"
        self.message = message
        self.success_message = success_message
        self.addend = 1
        self.size = 12
        self.last_view = None
        self.window = sublime.active_window()
        self.index = 0
        self.is_alive = True
        self.silent = False

        if self.window.id() in self.windows:
            print('Skipping ThreadProgress indicator because it is already running!')

        else:
            self.windows[self.window.id()] = self
            sublime.set_timeout(lambda: self.run(), 100)

    @classmethod
    def stop(cls, silent=True):
        window_id = sublime.active_window().id()
        if window_id in cls.windows:
            progress = cls.windows[window_id]
            progress.is_alive = False

            if silent: progress.silent = True
            del cls.windows[window_id]

    def run(self):
        active_view = self.window.active_view()
        active_window_id = '%s%s' % ( self.status_name, self.window.id() )

        if self.last_view is not None and active_view != self.last_view:
            self.last_view.erase_status(active_window_id)
            self.last_view = None

        if not self.is_alive:
            if self.silent:
                active_view.erase_status(active_window_id)
                return

            active_view.set_status(active_window_id, self.success_message)
            sublime.set_timeout( lambda: active_view.erase_status(active_window_id), 10000)
            return

        before = self.index % self.size
        after = (self.size - 1) - before

        active_view.set_status(active_window_id, '%s [%s=%s]' % (self.message, ' ' * before, ' ' * after))
        if self.last_view is None:
            self.last_view = active_view

        if not after:
            self.addend = -1

        if not before:
            self.addend = 1

        self.index += self.addend
        sublime.set_timeout(lambda: self.run(), 100)


class ExecRestoreOutputViewScrollingHelperCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # print('exec_restore_output_view_scrolling_helper')
        view = self.view
        window = view.window() or sublime.active_window()

        window_id = window.id()
        restoring_scroll = False

        if window_id in g_last_scroll_positions:
            last_scroll_region, last_caret_region = g_last_scroll_positions[window_id]

            if last_scroll_region:
                restoring_scroll = True

                # print('After  substr:                     ', view.substr(sublime.Region(0, 10)))
                # print('After  window.id:                  ', window.id())
                # print('After  view:                       ', view)
                # print('After  view.id:                    ', view.id())
                # print('g_last_scroll_positions[window_id] ', g_last_scroll_positions[window_id])
                view.set_viewport_position( last_scroll_region )
                view.sel().clear()

                for selection in last_caret_region:
                    view.sel().add( sublime.Region( selection[0], selection[1] ) )

                # Linux is bugged and does not restore the viewport
                if sys.platform == "linux":
                    restore_view( view, window, lambda: None )

        # The output build panel is completely scrolled horizontally to the right when there are build errors
        # https://github.com/SublimeTextIssues/Core/issues/2239
        if not restoring_scroll:
            viewport_position = view.viewport_position()
            view.set_viewport_position( ( 0, viewport_position[1] ) )


TIME_AFTER_FOCUS_VIEW = 30
TIME_AFTER_RESTORE_VIEW = 15

def restore_view(view, window, next_target, withfocus=True):
    """ Taken from the https://github.com/evandrocoan/FixProjectSwitchRestartBug package
    Because on Linux, set_viewport was not restoring the scroll.
    """

    if view.is_loading():
        sublime.set_timeout( lambda: restore_view( view, window, next_target, withfocus=withfocus ), 200 )

    else:
        selections = view.sel()
        file_name = view.file_name()

        if len( selections ):
            first_selection = selections[0].begin()
            original_selections = list( selections )

            def super_refocus():
                view.run_command( "move", {"by": "lines", "forward": False} )
                view.run_command( "move", {"by": "lines", "forward": True} )

                def fix_selections():
                    selections.clear()

                    for selection in original_selections:
                        selections.add( selection )

                    sublime.set_timeout( next_target, TIME_AFTER_RESTORE_VIEW )

                sublime.set_timeout( fix_selections, TIME_AFTER_RESTORE_VIEW )

            if file_name and withfocus:

                def reforce_focus():
                    # https://github.com/SublimeTextIssues/Core/issues/1482
                    group, view_index = window.get_view_index( view )
                    window.set_view_index( view, group, 0 )

                    # https://github.com/SublimeTextIssues/Core/issues/538
                    row, column = view.rowcol( first_selection )
                    window.open_file( "%s:%d:%d" % ( file_name, row + 1, column + 1 ), sublime.ENCODED_POSITION )
                    window.set_view_index( view, group, view_index )

                    # print( 'Super reforce focus focusing...' )
                    sublime.set_timeout( super_refocus, TIME_AFTER_RESTORE_VIEW )

                view.show_at_center( first_selection )
                sublime.set_timeout( reforce_focus, TIME_AFTER_FOCUS_VIEW )

            else:
                view.show_at_center( first_selection )
                sublime.set_timeout( super_refocus, TIME_AFTER_RESTORE_VIEW )


class ProcessListener:
    def on_data(self, proc, data):
        pass

    def on_finished(self, proc):
        pass


class AsyncProcess:
    """
    Encapsulates subprocess.Popen, forwarding stdout to a supplied
    ProcessListener (on a separate thread)
    """

    def __init__(self, cmd, shell_cmd, env, listener, path="", shell=False):
        """ "path" and "shell" are options in build systems """

        if not shell_cmd and not cmd:
            raise ValueError("shell_cmd or cmd is required")

        if shell_cmd and not isinstance(shell_cmd, str):
            raise ValueError("shell_cmd must be a string")

        self.listener = listener
        self.killed = False

        self.start_time = time.time()

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Set temporary PATH to locate executable in cmd
        if path:
            old_path = os.environ["PATH"]
            # The user decides in the build system whether he wants to append
            # $PATH or tuck it at the front: "$PATH;C:\\new\\path",
            # "C:\\new\\path;$PATH"
            os.environ["PATH"] = os.path.expandvars(path)

        proc_env = os.environ.copy()
        proc_env.update(env)
        for k, v in proc_env.items():
            proc_env[k] = os.path.expandvars(v)

        if sys.platform == "win32":
            preexec_fn = None
        else:
            preexec_fn = os.setsid

        if shell_cmd:
            if sys.platform == "win32":
                # Use shell=True on Windows, so shell_cmd is passed through
                # with the correct escaping
                cmd = shell_cmd
                shell = True
            elif sys.platform == "darwin":
                # Use a login shell on OSX, otherwise the users expected env
                # vars won't be setup
                cmd = ["/usr/bin/env", "bash", "-l", "-c", shell_cmd]
                shell = False
            elif sys.platform == "linux":
                # Explicitly use /bin/bash on Linux, to keep Linux and OSX as
                # similar as possible. A login shell is explicitly not used for
                # linux, as it's not required
                cmd = ["/usr/bin/env", "bash", "-c", shell_cmd]
                shell = False

        self.proc = subprocess.Popen(
            cmd,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            startupinfo=startupinfo,
            env=proc_env,
            preexec_fn=preexec_fn,
            shell=shell)

        if path:
            os.environ["PATH"] = old_path

        self.stdout_thread = threading.Thread(
            target=self.read_fileno,
            args=(self.proc.stdout, True)
        )

        self.stderr_thread = threading.Thread(
            target=self.read_fileno,
            args=(self.proc.stderr, False)
        )

    def start(self):
        self.stderr_thread.start()
        self.stdout_thread.start()

    def kill(self):
        if not self.killed:
            self.killed = True
            if sys.platform == "win32":
                # terminate would not kill process opened by the shell cmd.exe,
                # it will only kill cmd.exe leaving the child running
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen(
                    "taskkill /PID %d /T /F" % self.proc.pid,
                    startupinfo=startupinfo)
            else:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.terminate()

    def poll(self):
        return self.proc.poll() is None

    def exit_code(self):
        return self.proc.poll()

    def read_fileno(self, file, execute_finished):
        decoder = \
            codecs.getincrementaldecoder(self.listener.encoding)('replace')

        while True:
            data = decoder.decode(file.read(2**16))
            data = data.replace('\r\n', '\n').replace('\r', '\n')

            if len(data) > 0 and not self.killed:
                self.listener.on_data(self, data)
            else:
                if execute_finished:
                    # Make sure the stderr thread joins before we call
                    # on_finished
                    self.stderr_thread.join()

                    self.listener.on_finished(self)
                break


class ExecCommand(sublime_plugin.WindowCommand, ProcessListener):
    OUTPUT_LIMIT = 2 ** 27

    def __init__(self, window):
        super().__init__(window)

        self.proc = None

        self.errs_by_file = {}
        self.annotation_sets_by_buffer = {}
        self.show_errors_inline = True
        self.output_view = None

    def run(
            self,
            cmd=None,
            shell_cmd=None,
            file_regex="",
            line_regex="",
            working_dir="",
            encoding="utf-8",
            env={},
            quiet=False,
            kill=False,
            kill_previous=False,
            update_annotations_only=False,
            syntax="Packages/Text/Plain text.tmLanguage",
            full_regex="",
            result_dir="",
            replaceby={},
            output_build_word_wrap=None,
            spell_check=None,
            gutter=None,
            always_cancel_output_build_panel=False,
            # Catches "path" and "shell"
            **kwargs):
        # print( 'ExecCommand arguments: ', locals())
        view_settings = self.window.active_view().settings()

        if update_annotations_only:
            if self.show_errors_inline:
                self.update_annotations()
            return

        if kill:
            if self.proc:
                self.proc.kill()
            return

        if kill_previous and self.proc and self.proc.poll():
            self.proc.kill()

        if self.output_view is None:
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel("exec")

        # Default the to the current files directory if no working directory
        # was given
        if (working_dir == "" and
                self.window.active_view() and
                self.window.active_view().file_name()):
            working_dir = os.path.dirname(self.window.active_view().file_name())

        if output_build_word_wrap is None: output_build_word_wrap = view_settings.get("output_build_word_wrap", False)
        if spell_check is None: spell_check = view_settings.get("build_view_spell_check", False)
        if gutter is None: gutter = view_settings.get("gutter", True)

        self.output_view.settings().set("result_full_regex", full_regex)
        self.output_view.settings().set("result_replaceby", replaceby)
        self.output_view.settings().set("result_real_dir", result_dir)
        self.output_view.settings().set("fold_buttons", False)
        self.output_view.settings().set("mini_diff", False)

        self.output_view.settings().set("output_build_word_wrap", output_build_word_wrap)
        self.output_view.settings().set("always_cancel_output_build_panel", always_cancel_output_build_panel)
        self.output_view.settings().set("spell_check", spell_check)
        self.output_view.settings().set("gutter", gutter)

        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(syntax)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel("exec")

        self.encoding = encoding
        self.quiet = quiet

        self.proc = None
        if shell_cmd:
            print("Running " + shell_cmd)
        elif cmd:
            cmd_string = cmd
            if not isinstance(cmd, str):
                cmd_string = " ".join(cmd)
            print("Running " + cmd_string)

        # https://forum.sublimetext.com/t/how-to-keep-showing-building-on-the-status-bar/43965
        ThreadProgress("Building...", "Successfully Build the Project!")

        show_panel_on_build = \
            view_settings.get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})

        self.hide_annotations()
        self.show_errors_inline = \
            view_settings.get("show_errors_inline", True)

        merged_env = env.copy()
        if self.window.active_view():
            user_env = self.window.active_view().settings().get('build_env')
            if user_env:
                merged_env.update(user_env)

        # Change to the working dir, rather than spawning the process with it,
        # so that emitted working dir relative path names make sense
        if working_dir != "":
            os.chdir(working_dir)

        self.debug_text = ""
        if shell_cmd:
            self.debug_text += "[shell_cmd: " + shell_cmd + "]\n"
        else:
            self.debug_text += "[cmd: " + str(cmd) + "]\n"
        self.debug_text += "[dir: " + str(os.getcwd()) + "]\n"
        if "PATH" in merged_env:
            self.debug_text += "[path: " + str(merged_env["PATH"]) + "]"
        else:
            self.debug_text += "[path: " + str(os.environ["PATH"]) + "]"

        self.output_size = 0
        self.should_update_annotations = False

        try:
            # Forward kwargs to AsyncProcess
            self.proc = AsyncProcess(cmd, shell_cmd, merged_env, self, **kwargs)

            self.proc.start()

        except Exception as e:
            ThreadProgress.stop()
            self.write(str(e) + "\n")
            self.write(self.debug_text + "\n")
            if not self.quiet:
                self.write("[Finished]")

    def is_enabled(self, kill=False, **kwargs):
        if kill:
            return (self.proc is not None) and self.proc.poll()
        else:
            return True

    def write(self, characters):
        self.output_view.run_command(
            'append',
            {'characters': characters, 'force': True, 'scroll_to_end': True})

        # Updating annotations is expensive, so batch it to the main thread
        def annotations_check():
            errs = self.output_view.find_all_results_with_text()
            errs_by_file = {}
            for file, line, column, text in errs:
                if file not in errs_by_file:
                    errs_by_file[file] = []
                errs_by_file[file].append((line, column, text))
            self.errs_by_file = errs_by_file

            self.update_annotations()

            self.should_update_annotations = False

        if not self.should_update_annotations:
            if self.show_errors_inline and characters.find('\n') >= 0:
                self.should_update_annotations = True
                sublime.set_timeout(lambda: annotations_check())

    def on_data(self, proc, data):
        if proc != self.proc:
            return

        # Truncate past the limit
        if self.output_size >= self.OUTPUT_LIMIT:
            return

        self.write(data)
        self.output_size += len(data)

        if self.output_size >= self.OUTPUT_LIMIT:
            self.write('\n[Output Truncated]\n')

    def on_finished(self, proc):
        if proc != self.proc:
            return

        if proc.killed:
            self.write("\n[Cancelled]")
        else:
            elapsed = time.time() - proc.start_time
            if elapsed < 1:
                elapsed_str = "%.0fms" % (elapsed * 1000)
            else:
                elapsed_str = "%.1fs" % (elapsed)

            exit_code = proc.exit_code()
            if exit_code == 0 or exit_code is None:
                self.write("[Finished in %s]" % elapsed_str)
            else:
                self.write("[Finished in %s with exit code %d]\n" %
                           (elapsed_str, exit_code))
                if not self.quiet:
                    self.write(self.debug_text)

        ThreadProgress.stop()
        if proc.killed:
            sublime.status_message("Build cancelled")
        else:
            errs = self.output_view.find_all_results()
            if len(errs) == 0:
                sublime.status_message("Build finished")
            else:
                sublime.status_message("Build finished with %d errors" %
                                       len(errs))

        self.restoreViewPositions()

    def restoreViewPositions(self):
        output_view = self.output_view
        output_view.run_command( 'exec_restore_output_view_scrolling_helper' )

    def update_annotations(self):
        stylesheet = '''
            <style>
                #annotation-error {
                    background-color: color(var(--background) blend(#fff 95%));
                }
                html.dark #annotation-error {
                    background-color: color(var(--background) blend(#fff 95%));
                }
                html.light #annotation-error {
                    background-color: color(var(--background) blend(#000 85%));
                }
                a {
                    text-decoration: inherit;
                }
            </style>
        '''

        for file, errs in self.errs_by_file.items():
            view = self.window.find_open_file(file)
            if view:
                selection_set = []
                content_set = []

                line_err_set = []

                for line, column, text in errs:
                    pt = view.text_point(line - 1, column - 1)
                    if (line_err_set and
                            line == line_err_set[len(line_err_set) - 1][0]):
                        line_err_set[len(line_err_set) - 1][1] += (
                            "<br>" + html.escape(text, quote=False))
                    else:
                        pt_b = pt + 1
                        if view.classify(pt) & sublime.CLASS_WORD_START:
                            pt_b = view.find_by_class(
                                pt,
                                forward=True,
                                classes=(sublime.CLASS_WORD_END))
                        if pt_b <= pt:
                            pt_b = pt + 1
                        selection_set.append(
                            sublime.Region(pt, pt_b))
                        line_err_set.append(
                            [line, html.escape(text, quote=False)])

                for text in line_err_set:
                    content_set.append(
                        '<body>' + stylesheet +
                        '<div class="error" id=annotation-error>' +
                        '<span class="content">' + text[1] + '</span></div>' +
                        '</body>')

                view.add_regions(
                    "exec",
                    selection_set,
                    scope="invalid",
                    annotations=content_set,
                    flags=(sublime.DRAW_SQUIGGLY_UNDERLINE |
                           sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE),
                    on_close=self.hide_annotations)

    def hide_annotations(self):
        for window in sublime.windows():
            for file, errs in self.errs_by_file.items():
                view = window.find_open_file(file)
                if view:
                    view.erase_regions("exec")
                    view.hide_popup()

        view = sublime.active_window().active_view()
        if view:
            view.erase_regions("exec")
            view.hide_popup()

        self.errs_by_file = {}
        self.annotation_sets_by_buffer = {}
        self.show_errors_inline = False


class ExecEventListener(sublime_plugin.EventListener):
    def on_load(self, view):
        w = view.window() or sublime.active_window()
        if w is not None:
            w.run_command('exec', {'update_annotations_only': True})
