PyBuilder Pylint Extended Plugin [![Build Status](https://travis-ci.org/AlexeySanko/pybuilder_pylint_extended.svg?branch=master)](https://travis-ci.org/AlexeySanko/pybuilder_pylint_extended)
=======================

Plugin provides extended properties for Pylint tool

Behaviour
---------
Errors are errors: plugin always breaks build on any error or fatal.
Property `pylint_break_build` manage behaviour on warnings/refactors/conventions.

To suppress warnings, you can set a line-level comment:
```
dict = 'something awful'  # Bad Idea... pylint: disable=redefined-builtin
```
pylint warnings are each identified by a alphanumeric code (C0112) and a symbolic name (empty-docstring).
According [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html?showone=Lint#Lint) prefer the symbolic names in new code or when updating existing code.

Properties
----------
Plugin has next properties with provided defaults

| Name | Type | Default Value | Description |
| --- | --- | --- | --- |
| pylint_break_build | bool | False | Breaks build on any warnings/refactors/convention |
| pylint_ignore | list of symbolic names | [] | List of issues symbolic name for excluding |
| pylint_max_line_length | integer | 80 | Maximum row length |
| pylint_include_files | list of string | [] | List of files with relative path according project root directory which could be added to parsed |
| pylint_exclude_patterns | regex string | None | Pattern for excluding files from analysis |
| pylint_include_test_sources | bool | True | Include tests sources |
| pylint_include_scripts | bool | False | Include scripts |
| pylint_score_threshold | float | None | Score threshold, if result score less threshold - break build. `None` - to skip score check |
| pylint_extra_args | list of strings | [] | Additional arguments for pylint |