#   -*- coding: utf-8 -*-
#
#   Copyright 2017 Alexey Sanko
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
    Plugin which provides work with Pylint with extended list of
    PyBuilder project properties
"""
import sys

from pybuilder import core, utils
from pybuilder.errors import BuildFailedException
from pybuilder.plugins.python import (
    python_plugin_helper as pybuilder_python_plugin_helper)
from pylint import lint
from pybuilder_pylint_extended import (
    python_plugin_helper,
    version)

__author__ = 'Alexey Sanko'
__version__ = version.__version__

core.use_plugin("python.core")
core.use_plugin("analysis")


@core.init
def initialize_pylint_plugin(project):
    """ Init default plugin project properties. """
    project.plugin_depends_on("pylint")

    project.set_property_if_unset("pylint_break_build", False)
    project.set_property_if_unset("pylint_ignore", [])
    project.set_property_if_unset("pylint_max_line_length", 80)
    project.set_property_if_unset("pylint_include_files", [])
    project.set_property_if_unset("pylint_exclude_patterns", None)
    project.set_property_if_unset("pylint_include_test_sources", True)
    project.set_property_if_unset("pylint_include_scripts", False)
    project.set_property_if_unset("pylint_score_threshold", None)
    project.set_property_if_unset("pylint_extra_args", [])


def _run_pylint(args):
    execution_result = lint.Run(args, exit=False)
    pylint_stats = execution_result.linter.stats
    return (pylint_stats['global_note'], pylint_stats['fatal'],
            pylint_stats['error'], pylint_stats['warning'],
            pylint_stats['refactor'], pylint_stats['convention'])


@core.task("analyze")
def execute_pylint(project, logger):
    """
    Collect all source files and Pylint options according properties.
    Call Pylint after that and parse statistic.

    :param project: PyBuilder project object
    :param logger: PyBuilder project logger
    """
    logger.info("Executing pylint on project sources.")
    project.set_property_if_unset("pylint_verbose_output",
                                  project.get_property("verbose"))
    # add max line length
    pylint_args = ["--max-line-length=%s"
                   % project.get_property("pylint_max_line_length")]
    # add ignored messages
    if project.get_property("pylint_ignore"):
        for ignore in project.get_property("pylint_ignore"):
            pylint_args.append("--disable=%s" % ignore)
    # add ignore pattern
    if project.get_property("pylint_exclude_patterns"):
        pylint_args.append(
            "--ignore-patterns=%s"
            % project.get_property("pylint_exclude_patterns"))
    # add extra arguments
    pylint_args.extend(project.get_property("pylint_extra_args"))
    # collect files list
    files = python_plugin_helper.discover_affected_files(
        project.get_property("pylint_include_test_sources"),
        project.get_property("pylint_include_scripts"), project)
    # collect additionally included files
    included_files = [project.expand_path(file_name)
                      for file_name
                      in project.get_property("pylint_include_files")]
    # add files to arguments
    pylint_args = ([file_name for file_name in files]
                   + included_files + pylint_args)
    logger.debug("Calling pylint with: %s", pylint_args)
    # replace stdout/stderr with report files
    prev_stdout, prev_stderr = sys.stdout, sys.stderr
    report_file = project.expand_path("$dir_reports/pylint")
    sys.stdout = open(report_file, 'w')
    sys.stderr = open(project.expand_path("$dir_reports/pylint.err"), 'w')
    score, fatal, error, warning, refactor, convention = _run_pylint(
        pylint_args)
    # return original stdout/stderr
    sys.stdout.close()
    sys.stderr.close()
    sys.stdout, sys.stderr = prev_stdout, prev_stderr
    # write result to logger
    logger.info("Pylint results: score:%s, fatal:%s, error:%s, "
                "warning:%s, refactor:%s, convention:%s" %
                (score, fatal, error, warning, refactor, convention))
    if (project.get_property("pylint_verbose_output")
            and fatal + error + warning + refactor + convention > 0):
        pybuilder_python_plugin_helper.log_report(
            logger, "pylint", utils.read_file(report_file))
    # (C) convention, for programming standard violation
    # (R) refactor, for bad code smell
    # (W) warning, for python specific problems
    # (E) error, for much probably bugs in the code
    # (F) fatal, if an error occurred which prevented pylint from doing
    # errors are errors: break build in any case
    if fatal + error > 0:
        raise BuildFailedException(
            "pylint found %s fatal(s) and %s error(s)" % (fatal, error))
    # work with other types
    if (warning + refactor + convention > 0 and
            project.get_property("pylint_break_build")):
        raise BuildFailedException(
            "pylint found %s warning(s), %s refactor(s) and %s convention(s)"
            % (warning, refactor, convention))
    if (project.get_property("pylint_score_threshold")
            and score < project.get_property("pylint_score_threshold")):
        raise BuildFailedException(
            "pylint current score %s less then threshold %s"
            % (score, project.get_property("pylint_score_threshold")))
