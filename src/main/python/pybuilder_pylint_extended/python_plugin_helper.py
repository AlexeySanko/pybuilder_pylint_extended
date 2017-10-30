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
    Functions copied from the same original PyBuilder module with
    changes according waiting Pull Requests
"""
import itertools

from pybuilder.plugins.python import python_plugin_helper


def discover_affected_files(include_test_sources, include_scripts, project):
    """
    Function collects all project source files
    :param include_test_sources: flag which force to add test sources to result
    :param include_scripts:  flag which force to add test scripts to result
    :param project: PyBuilder project
    :return: list of sources for the PyBuilder project
    """
    source_dir = project.expand_path("$dir_source_main_python")
    files = python_plugin_helper.discover_python_files(source_dir)

    if include_test_sources:
        if project.get_property("dir_source_unittest_python"):
            unittest_dir = project.expand_path("$dir_source_unittest_python")
            files = itertools.chain(files,
                                    python_plugin_helper.discover_python_files(
                                        unittest_dir))
        if project.get_property("dir_source_integrationtest_python"):
            integrationtest_dir = project.expand_path(
                "$dir_source_integrationtest_python")
            files = itertools.chain(files,
                                    python_plugin_helper.discover_python_files(
                                        integrationtest_dir))
        if project.get_property("dir_source_pytest_python"):
            pytest_dir = project.expand_path("$dir_source_pytest_python")
            files = itertools.chain(files,
                                    python_plugin_helper.discover_python_files(
                                        pytest_dir))
    if include_scripts and project.get_property("dir_source_main_scripts"):
        scripts_dir = project.expand_path("$dir_source_main_scripts")
        files = itertools.chain(files,
                                python_plugin_helper.discover_files_matching(
                                    scripts_dir, "*"))
    return files
