import os.path
import sublime
import tempfile
import sublime_plugin
import subprocess

settings = None


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


class Settings:

    def __init__(self):
        package_settings = sublime.load_settings(
            "BeautifyRust.sublime-settings")
        package_settings.add_on_change("rustfmt", settings_changed)
        package_settings.add_on_change("run_on_save", settings_changed)
        package_settings.add_on_change("save_on_beautify", settings_changed)

        self.rustfmt = package_settings.get("rustfmt", which('rustfmt'))
        if self.rustfmt == None:
            sublime.error_message(
                "Beautify rust: can not find {0} in path.".format(package_settings.get("rustfmt", "rustfmt")))
        self.run_on_save = package_settings.get("run_on_save", False)
        self.save_on_beautify = package_settings.get("save_on_beautify", True)
        self.package_settings = package_settings

    def unload(self):
        self.package_settings.clear_on_change("rustfmt")
        self.package_settings.clear_on_change("run_on_save")
        self.package_settings.clear_on_change("save_on_beautify")


def plugin_loaded():
    global settings
    settings = Settings()


def plugin_unloaded():
    global settings
    if settings != None:
        settings.unload()
        settings = None


def settings_changed():
    global settings
    if settings != None:
        settings.unload()
        settings = None
    settings = Settings()


class BeautifyRustOnSave(sublime_plugin.EventListener):

    def on_pre_save(self, view):
        if settings.run_on_save:
            view.run_command("beautify_rust", {"save": False, "error": False})


class BeautifyRustCommand(sublime_plugin.TextCommand):

    def run(self, edit, error=True, save=True):
        self.filename = self.view.file_name()
        self.fname = os.path.basename(self.filename)
        if self.is_rust_file():
            self.run_format(edit)

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
            os.write(fd, bytes(buffer_text, 'UTF-8'))
            cmd_list = [settings.rustfmt, filename, "--write-mode=display"]
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
