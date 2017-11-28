'''
The official executor API for validation test and full test scripts.
'''

import os
import sys
import importlib
import pexpect

from . import server
from .compiler import call_compiler, call_make, GCC
from .config import read_config
from .execution import kill_longrunning, shell_execution
from .running import RunningProgram
from .exceptions import JobException, RunningProgramException
from .filesystem import has_file

import logging
logger = logging.getLogger('opensubmitexec')

UNSPECIFIC_ERROR = -9999


class Job():
    '''
    A OpenSubmit job to be run by the test machine.
    '''

    # The current executor configuration.
    _config = None
    # Talk to the configured OpenSubmit server?
    _online = None

    # Download source for the student sub
    submission_url = None
    # Download source for the validator
    validator_url = None
    # The working directory for this job
    working_dir = None
    # The timeout for execution, as demanded by the server
    timeout = None
    # The OpenSubmit submission ID
    submission_id = None
    # The OpenSubmit submission file ID
    file_id = None
    # Did the validator script sent a result to the server?
    result_sent = False
    # Action requested by the server (legacy)
    action = None
    # Name of the submitting student
    submitter_name = None
    # Student ID of the submitting student
    submitter_student_id = None
    # Names of the submission authors
    author_names = None
    # Name of the study program of the submitter
    submitter_studyprogram = None
    # Name of the course where this submission was done
    course = None
    # Name of the assignment where this job was done
    assignment = None

    # The base name of the validation / full test script
    # on disk, for importing.
    _validator_import_name = 'validator'

    @property
    # The file name of the validation / full test script
    # on disk, after unpacking / renaming.
    def validator_script_name(self):
        return self.working_dir + self._validator_import_name + '.py'

    def __init__(self, config=None, online=True):
        if config:
            self._config = config
        else:
            self._config = read_config()
        self._online = online

    def __str__(self):
        '''
        Nicer logging of job objects.
        '''
        return str(vars(self))

    def _run_validate(self):
        '''
        Execute the validate() method in the test script belonging to this job.
        '''
        assert(os.path.exists(self.validator_script_name))
        old_path = sys.path
        sys.path = [self.working_dir] + old_path
        # logger.debug('Python search path is now {0}.'.format(sys.path))
        module = importlib.import_module(self._validator_import_name)

        # Looped validator loading in the test suite demands this
        importlib.reload(module)

        # make the call
        try:
            module.validate(self)
        except Exception as e:
            # get more info
            text_student = None
            text_tutor = None
            error_code = UNSPECIFIC_ERROR
            if type(e) is RunningProgramException:
                # Some problem with pexpect.
                if type(e.real_exception) == pexpect.EOF:
                    if e.instance._spawn.exitstatus:
                        error_code = e.instance._spawn.exitstatus
                    text_student = "Your program terminated unexpectedly."
                    text_tutor = "The student program terminated unexpectedly."
                elif type(e.real_exception) == pexpect.TIMEOUT:
                    text_student = "The execution of your program was cancelled, since it took longer than {0} seconds. ".format(self.timeout)
                    text_tutor = "The execution of the program was cancelled due to the timeout of {0} seconds. ".format(self.timeout)
                else:
                    text_student = "Unexpected problem during the execution of your program. {0}".format(str(e.real_exception))
                    text_tutor = "Unkown exception during the execution of the student program. {0}".format(str(e.real_exception))
                output = str(e.instance._spawn.before, encoding='utf-8')
                text_student += "\n\nOutput so far: " + output
                text_tutor += "\n\nOutput so far: " + output
            elif type(e) is JobException:
                # Some problem with our own code
                text_student = e.info_student
                text_tutor = e.info_tutor
            else:
                # Something really unexpected
                text_student = "Internal problem while validating your submission. {0}".format(str(e))
                text_tutor = "Unknown exception while running the validator. {0}".format(str(e))
            # We got the text. Report the problem.
            self._send_result(text_student, text_tutor, error_code)
            return
        # no unhandled exception during the execution of the validator
        if not self.result_sent:
            logger.debug("Validation script forgot result sending.")
            self.send_pass_result()
        # roll back
        sys.path = old_path

    def _send_result(self, info_student, info_tutor, error_code):
        post_data = [("SubmissionFileId", self.file_id),
                     ("Message", info_student),
                     ("Action", self.action),
                     ("MessageTutor", info_tutor),
                     ("ExecutorDir", self.working_dir),
                     ("ErrorCode", error_code),
                     ("Secret", self._config.get("Server", "secret")),
                     ("UUID", self._config.get("Server", "uuid"))
                     ]
        logger.debug(
            'Sending result to OpenSubmit Server: ' + str(post_data))
        if self._online:
            server.send(self._config, "/jobs/", post_data)
        self.result_sent = True

    def send_fail_result(self, info_student, info_tutor):
        self._send_result(info_student, info_tutor, UNSPECIFIC_ERROR)

    def send_pass_result(self,
                         info_student="All tests passed. Awesome!",
                         info_tutor="All tests passed."):
        self._send_result(info_student, info_tutor, 0)

    def delete_binaries(self):
        '''
        Scans the submission files in the self.working_dir for
        binaries and deletes them.
        Returns the list of deleted files.
        '''
        raise NotImplementedError

    def run_configure(self, mandatory=True):
        '''
        Runs the configure tool configured for the machine in self.working_dir.
        '''
        logger.debug("Running configure ...")
        if not has_file(self.working_dir, 'configure'):
            raise FileNotFoundError("Could not find a configure script for execution.")
        logger.info("Running ./configure in " + self.working_dir)
        try:
            prog = RunningProgram(self, 'configure')
            prog.expect_end()
        except Exception:
            if mandatory:
                raise




    def run_make(self, mandatory=True):
        '''
        Runs the make tool configured for the machine in self.working_dir.
        '''
        logger.debug("Running make ...")
        result = call_make(self.working_dir)
        if mandatory and not result.is_ok():
            raise JobException(result)

    def run_compiler(self, compiler=GCC, inputs=None, output=None):
        '''
        Runs the compiler in self.working_dir.
        '''
        logger.debug("Running compiler ...")
        result = call_compiler(self.working_dir, compiler, output, inputs)
        if not result.is_ok():
            raise JobException(result)

    def run_build(self, compiler=GCC, inputs=None, output=None):
        self.run_configure(mandatory=False)
        self.run_make(mandatory=False)
        self.run_compiler(compiler=compiler,
                          inputs=inputs,
                          output=output)

    def spawn_program(self, name, arguments=[], timeout=30, exclusive=False):
        '''
        Spawns a program in the working directory and allows
        interaction with it. Returns a RunningProgram object.

        The caller can demand exclusive execution on this machine.
        '''
        logger.debug("Spawning program for interaction ...")
        if exclusive:
            kill_longrunning(self.config)

        return RunningProgram(self.working_dir, name, arguments, timeout)

    def run_program(self, name, arguments=None, timeout=30, exclusive=False):
        '''
        Runs a program in the working directory to completion.

        The caller can demand exclusive execution on this machine.

        Returns a Result object.
        '''
        logger.debug("Running program to completion ...")
        if type(name) is str:
            name = [name]
        if arguments:
            assert(type(arguments is list))
            cmdline = name + arguments
        else:
            cmdline = name

        if exclusive:
            kill_longrunning(self.config)

        result = shell_execution(cmdline, self.working_dir, timeout=timeout)
        if not result.is_ok():
            raise JobException(result)

    def find_keywords(self, keywords, filepattern):
        '''
        Searches self.working_dir for files containing specific keywords.
        Expects a list of keywords to be searched for and the file pattern
        (*.c) as parameters.
        Returns the names of the files containing all of the keywords.
        '''
        raise NotImplementedError

    def ensure_files(self, filenames):
        '''
        Searches the student submission for specific files.
        Expects a list of filenames. Returns a boolean indicator.
        '''
        logger.debug("Testing {0} for the following files: {1}".format(
            self.working_dir, filenames))
        dircontent = os.listdir(self.working_dir)
        for fname in filenames:
            if fname not in dircontent:
                return False
        return True
