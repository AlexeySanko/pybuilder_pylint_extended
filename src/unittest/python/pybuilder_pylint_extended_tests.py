#   -*- coding: utf-8 -*-
#
#   This file is part of PyBuilder
#
#   Copyright 2011-2015 PyBuilder Team
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Unit tests for `pybuilder_pylint_extended` module
"""

import os
from os import path
import shutil
import tempfile
from unittest import TestCase

import mock
from pybuilder import core
from pybuilder.errors import BuildFailedException

from pybuilder_pylint_extended import (
    initialize_pylint_plugin,
    _run_pylint,
    execute_pylint)


class PylintPluginInitializationTests(TestCase):
    """  Test `initialize_pylint_plugin` function"""
    def setUp(self):
        self.project = core.Project("basedir")

    def test_should_set_default_values_when_initializing_plugin(self):  # pylint: disable=invalid-name
        """ Test that `initialize_pylint_plugin` set default properties"""
        initialize_pylint_plugin(self.project)
        expected_defaults = {
            "pylint_break_build": False,
            "pylint_ignore": [],
            "pylint_max_line_length": 80,
            "pylint_include_test_sources": True,
            "pylint_include_scripts": False,
            "pylint_score_threshold": None,
            "pylint_extra_args": []
        }
        for property_name, property_value in expected_defaults.items():
            self.assertEquals(
                self.project.get_property(property_name),
                property_value)

    def test_should_leave_user_specified_properties_when_initializing_plugin(   # pylint: disable=invalid-name
            self):
        """ Test that `initialize_pylint_plugin` doesn't override
            user-defined properties"""
        expected_properties = {
            "pylint_break_build": True,
            "pylint_ignore": ['a'],
            "pylint_max_line_length": 90,
            "pylint_include_test_sources": False,
            "pylint_include_scripts": True,
            "pylint_score_threshold": 10.0,
            "pylint_extra_args": ['a']
        }
        for property_name, property_value in expected_properties.items():
            self.project.set_property(property_name, property_value)
        initialize_pylint_plugin(self.project)
        for property_name, property_value in expected_properties.items():
            self.assertEquals(
                self.project.get_property(property_name),
                property_value)


@mock.patch("pylint.lint.Run")
def test__run_pylint(mock_run):
    """ Test `_run_pylint` function """
    _run_pylint(['a', 'b'])
    mock_run.assert_called_once_with(['a', 'b'], exit=False)


def _write_stub_file(file_path):
    with open(file_path, 'w') as file_:
        file_.write("import os")


class PylintPluginExecutionTests(TestCase):
    """ Test `execute_pylint` function """
    def setUp(self):
        self.basedir = tempfile.mkdtemp(suffix='pylint_plugin')
        self.project = core.Project(self.basedir)
        # set properties
        initialize_pylint_plugin(self.project)
        self.project.set_property("verbose", True)
        self.project.get_property("pylint_ignore").append('some-error')
        self.project.get_property("pylint_ignore").append('some-warning')
        self.project.set_property("pylint_exclude_patterns",
                                  "test.*?py")
        self.project.get_property("pylint_extra_args").append("--score=y")
        self.project.set_property("dir_source_main_python", "main")
        self.project.set_property("pylint_include_test_sources", True)
        self.project.set_property("dir_source_pytest_python", "pytest_tests")
        self.project.set_property("dir_source_integrationtest_python",
                                  "intg_tests")
        self.project.set_property("dir_source_unittest_python", "unit_tests")
        self.project.set_property("pylint_include_scripts", True)
        self.project.set_property("dir_source_main_scripts", "scripts")
        self.project.set_property("dir_reports", "reports")
        # add source file
        pkg_dir = path.join(self.basedir, 'main', 'pkg')
        os.makedirs(pkg_dir)
        self.source_file = path.join(pkg_dir, 'module.py')
        _write_stub_file(self.source_file)
        # add pytest file
        os.makedirs(path.join(self.basedir, 'pytest_tests'))
        self.pytest_file = path.join(
            self.basedir, 'pytest_tests', 'test.py')
        _write_stub_file(self.pytest_file)
        # add integration file
        os.makedirs(path.join(self.basedir, 'intg_tests'))
        self.intg_file = path.join(
            self.basedir, 'intg_tests', 'test.py')
        _write_stub_file(self.intg_file)
        # add unittest file
        os.makedirs(path.join(self.basedir, 'unit_tests'))
        self.unit_file = path.join(
            self.basedir, 'unit_tests', 'test.py')
        _write_stub_file(self.unit_file)
        # add script file
        os.makedirs(path.join(self.basedir, 'scripts'))
        self.script_file = path.join(self.basedir, 'scripts', 'script')
        _write_stub_file(self.script_file)
        # add reports dir
        os.makedirs(path.join(self.basedir, 'reports'))

    @mock.patch("pybuilder_pylint_extended._run_pylint",
                return_value=(10, 1, 1, 1, 1, 1))
    @mock.patch("pybuilder.utils.read_file", return_value=["some", "report"])
    def test_should_break_build_if_error(self, mock_read_file, mock_run):   # pylint: disable=invalid-name,unused-argument
        """ Test that plugin breaks build if fatal or error
            were found"""
        logger_mock = mock.Mock()
        with self.assertRaises(BuildFailedException) as context:
            execute_pylint(self.project, logger_mock)
        err_msg = str(context.exception)
        self.assertTrue(
            "pylint found 1 fatal(s) and 1 error(s)" in err_msg)
        mock_run.assert_called_once_with(
            [self.source_file, self.unit_file, self.intg_file, self.pytest_file,
             self.script_file, '--max-line-length=80', '--disable=some-error',
             '--disable=some-warning', "--ignore-patterns=test.*?py",
             '--score=y'])
        logger_mock.debug.assert_called_once()
        logger_mock.info.assert_called_with(
            "Pylint results: score:10, fatal:1, error:1, "
            "warning:1, refactor:1, convention:1")
        self.assertEqual(logger_mock.info.call_count, 2)
        self.assertEqual(logger_mock.warn.call_count, 2)

    @mock.patch("pybuilder_pylint_extended._run_pylint",
                return_value=(10, 0, 0, 1, 1, 1))
    @mock.patch("pybuilder.utils.read_file", return_value=["some", "report"])
    def test_should_break_build_if_warning(self, mock_read_file, mock_run):     # pylint: disable=invalid-name,unused-argument
        """ Test that plugin breaks build with `pylint_break_build`
            if warning/convention/refactoring were found"""
        self.project.set_property("pylint_break_build", True)
        logger_mock = mock.Mock()
        with self.assertRaises(BuildFailedException) as context:
            execute_pylint(self.project, logger_mock)
        err_msg = str(context.exception)
        self.assertTrue(
            ("pylint found 1 warning(s), 1 refactor(s) "
             "and 1 convention(s)") in err_msg)
        mock_run.assert_called_once_with(
            [self.source_file, self.unit_file, self.intg_file, self.pytest_file,
             self.script_file, '--max-line-length=80', '--disable=some-error',
             '--disable=some-warning', "--ignore-patterns=test.*?py",
             '--score=y'])
        logger_mock.debug.assert_called_once()
        logger_mock.info.assert_called_with(
            "Pylint results: score:10, fatal:0, error:0, "
            "warning:1, refactor:1, convention:1")
        self.assertEqual(logger_mock.info.call_count, 2)
        self.assertEqual(logger_mock.warn.call_count, 2)

    def test_should_break_build_if_score_threshold(self):   # pylint: disable=invalid-name
        """ Test that plugin breaks build if score less
            than threshold"""
        self.project.set_property("pylint_score_threshold", 10)
        logger_mock = mock.Mock()
        with self.assertRaises(BuildFailedException) as context:
            execute_pylint(self.project, logger_mock)
        err_msg = str(context.exception)
        self.assertTrue(
            "pylint current score -20.0 less then threshold 10" in err_msg)
        logger_mock.debug.assert_called_once()
        logger_mock.info.assert_called_with(
            "Pylint results: score:-20.0, fatal:0, error:0, "
            "warning:5, refactor:0, convention:10")
        self.assertEqual(logger_mock.info.call_count, 2)
        self.assertEqual(logger_mock.warn.call_count, 22)

    def tearDown(self):
        shutil.rmtree(self.basedir)
