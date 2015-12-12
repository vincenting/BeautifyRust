import os.path
import sublime
import tempfile
import sublime_plugin
import subprocess

SETTINGS_FILE = "BeautifyRust.sublime-settings"


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


save_without_beautify = False

class BeautifyRustOnSave(sublime_plugin.EventListener):

    def on_pre_save(self, view):
        global save_without_beautify
        if sublime.load_settings(SETTINGS_FILE).get("run_on_save", False) and not save_without_beautify:
            return view.run_command("beautify_rust", {"save": False})
        save_without_beautify = False
        return


class BeautifyRustCommand(sublime_plugin.TextCommand):

    def run(self, edit, save=True):
        global save_without_beautify
        self.filename = self.view.file_name()
        self.fname = os.path.basename(self.filename)
        self.settings = sublime.load_settings(SETTINGS_FILE)
        if self.is_rust_file():
            self.run_format(edit)
            if save and self.settings.get("save_on_beautify", True):
                save_without_beautify = True
                sublime.set_timeout(lambda: self.view.run_command("save"), 0)


    def is_rust_file(self):
        return self.fname.endswith(".rs")

    def pipe(self, cmd):
        cwd = os.path.dirname(self.filename)
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        beautifier = subprocess.Popen(
            cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo)
        out = beautifier.communicate()[0].decode('utf8')
        return (out, beautifier.wait())

    def run_format(self, edit):
        buffer_region = sublime.Region(0, self.view.size())
        buffer_text = self.view.substr(buffer_region)
        exit_code = -1
        if buffer_text == "":
            return
        fd, filename = tempfile.mkstemp()
        try:
            rustfmt_bin = which(self.settings.get("rustfmt", "rustfmt"))
            if rustfmt_bin == None:
                return sublime.error_message(
                    "Beautify rust: can not find {0} in path.".format(self.settings.get("rustfmt", "rustfmt")))
            os.write(fd, bytes(buffer_text, 'UTF-8'))
            cmd_list = [rustfmt_bin, filename, "--write-mode=display"]
            (output, exit_code) = self.pipe(cmd_list)
            os.close(fd)
        finally:
            os.remove(filename)
        if exit_code == 0:
            self.save_viewport_state()
            fix_lines = '\n'.join(output.splitlines()[2:])
            self.check_valid_output(fix_lines)
            self.view.replace(edit, buffer_region, fix_lines)
            self.reset_viewport_state()
        else:
            print("failed: exit_code:", exit_code, output)
            sublime.error_message(
                "Beautify rust: rustfmt process call failed. See log (ctrl + `) for details.")

    def check_valid_output(self, text):
        if text == "":
            msg = "invalid output. Check your rustfmt interpreter settings"
            raise Exception(msg)

    def save_viewport_state(self):
        self.previous_selection = [(region.a, region.b)
                                   for region in self.view.sel()]
        self.previous_position = self.view.viewport_position()

    def reset_viewport_state(self):
        self.view.set_viewport_position((0, 0,), False)
        self.view.set_viewport_position(self.previous_position, False)
        self.view.sel().clear()
        for a, b in self.previous_selection:
            self.view.sel().add(sublime.Region(a, b))
