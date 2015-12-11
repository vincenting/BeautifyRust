import os.path
import sublime
import sublime_plugin
import sys
import re
import subprocess

settings = None


class Settings:

    def __init__(self):
        package_settings = sublime.load_settings(
            "BeautifyRust.sublime-settings")
        package_settings.add_on_change("rustfmt", settings_changed)
        package_settings.add_on_change("run_on_save", settings_changed)
        package_settings.add_on_change("save_on_beautify", settings_changed)

        self.rustfmt = package_settings.get("rustfmt", "rustfmt")
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
        print("helo world")

    def run_format():
        pass
