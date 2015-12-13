# BeautifyRust

A binding for Sublime Text to the [Rustfmt](https://github.com/rust-lang-nursery/rustfmt).


### Requirements

1. Clone and build the [rustfmt](https://github.com/rust-lang-nursery/rustfmt)
2. Install the package through package control (or clone from git if you prefer): https://sublime.wbond.net/packages/BeautifyRust
3. If an error is encountered while processing the file or can not find `rustfmt` in path, following message `Beautify rust: can not find rustfmt in path.` is displayed. Open menu in your `Preferences -> Package settings -> BeautifyRust -> Settings - User`, and edit the settings file using below as a template:

```
{
  "run_on_save": false,
  "rustfmt": "/Users/user/.cargo/bin/rustfmt"
}
```

Contact
=======

https://github.com/vincenting/BeautifyRust
