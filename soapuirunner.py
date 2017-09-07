import getopt
from os import walk, path
import platform
from subprocess import call
import sys
import xml.etree.ElementTree as ET
from smtpd import usage


CUSTOM_ARGS = [
    'prog',
    'excludesuites',
    'excludeprojects'
]


def get_list_of_soapui_projects(root_folder):
    """Function that returns list of the soapUI project files

    Args:
        root_folder (str): full folder path where all soapUI projects are. Could be nested

    Returns:
        soapui_projects (str[]): List of strings. Each string is full file path

    """
    soapui_projects = []
    if path.isfile(root_folder):
        if is_soapui_project_file(root_folder):
            return soapui_projects.append(root_folder)
    if path.isdir(root_folder):
        for (root_path, dirnames, filenames) in walk(root_folder):
            if filenames:
                for filename in filenames:
                    full_file_path = path.join(root_folder, filename)
                    if is_soapui_project_file(full_file_path):
                        soapui_projects.append(full_file_path)
            if dirnames:
                for dirname in dirnames:
                    soapui_projects.extend(get_list_of_soapui_projects(dirname))
    return soapui_projects


def build_list_of_soapui_projects(project_list, exclude=None):
    """Function that takes list of projects and
    returns list of the soapUI project files based on what needs to be excluded

        Args:
            project_list (str[]): List of strings. Each string is full file path
            exclude (?str[]): Optional. List of strings. Each string is soapUI project file name with extension

        Returns:
            project_list (str[]): List of strings. Each string is full file path

    """
    if exclude:
        exclude = exclude.split(',')
        for project_to_exclude in exclude:
            dirname = path.dirname(project_list[0])
            project_to_exclude = path.join(dirname, project_to_exclude)
            if project_to_exclude in project_list:
                project_list.pop(project_list.index(project_to_exclude))
    return project_list


def is_soapui_project_file(full_file_path):
    """Function that epaulets whether file is soapUI project

        Args:
            full_file_path (str): String that represents full file path with extension

        Returns:
            bool: True if it is soapUI project. False if opposite

    """
    filename_without_extension, file_extension = path.splitext(full_file_path)
    if file_extension == '.xml':
        xml_root_tag = ET.parse(full_file_path).getroot().tag
        # figure out that xml is soapUI project file
        if 'soapui-project' in xml_root_tag:
            return True
    return False


def get_list_of_suites_from_soapui_project(soapui_project_path):
    """Function that takes soapUI project file and returns list of test suites names that are in that project

        Args:
            soapui_project_path (str): String that represents full file path with extension

        Returns:
            test_suites (str): List of strings. Each string is suite name

    """
    root = ET.parse(soapui_project_path).getroot()
    test_suites = []
    for child in root:
        if 'testSuite' in child.tag:
            test_suites.append(child.attrib['name'])
    return test_suites


def build_list_of_suites(test_suite, suites_list, exclude=None):
    """Function that takes soapUI project file and returns list of test suites names that are in that project

        Args:
            soapui_project_path (str): String that represents full file path with extension

        Returns:
            test_suites (str): List of strings. Each string is suite name

    """
    if test_suite.endswith('*'):
        suites_list = [suite for suite in suites_list if test_suite[:-1] in suite]
        if exclude:
            exclude = exclude.split(',')
            for suite_to_exclude in exclude:
                if suite_to_exclude in suites_list:
                    suites_list.pop(suites_list.index(suite_to_exclude))
        return suites_list
    if test_suite in suites_list:
        return [test_suite]
    return None


def get_option_value(opts_list, opt_name):
    """Function that gets value from list of options with values based on option name

        Args:
            opts_list (tuple[]): List of tuples. Where each tuple it is pare of option name and corresponding value
                Example: [('-s', 'Test Suite'), (-r, '')]
            opt_name (str): Name of cli option that is passed when soapuirunner.py is called.
                Example: '-s'

        Returns:
            value [?str]: Value of given option. Can be None if option doesn't have value
    """
    for opt in opts_list:
        if opt[0] == opt_name:
            return opt[1]
    return None


def set_option_value(opts_list, opt_name, opt_value):
    """Function that gets value from list of options with values based on option name

        Args:
            opts_list (tuple[]): List of tuples. Where each tuple it is pare of option name and corresponding value
                Example: [('-s', 'Test Suite'), (-r, '')]
            opt_name (str): Name of cli option that is passed when soapuirunner.py is called.
                Example: '-s'

        Returns:
            value [?str]: Value of given option. Can be None if option doesn't have value
    """
    for opt in opts_list:
        i = opts_list.index(opt)
        if opt[0] == opt_name:
            opt = list(opt)
            opt[1] = opt_value
            opt = tuple(opt)
            opts_list.pop(i)
            opts_list.insert(i, opt)
    return opts_list


def get_platform_name():
    """Function that returns platform/operation system type

        Returns:
            platform_type (str): Can be 'unix' or 'win'
    """
    platform_name = platform.system().lower()
    platform_types = {
        'unix': [
            'linux',
            'linux2',
            'darwin'  # mac os x
        ],
        'win': [
            'win32',
            'win64',
            'windows'
        ]
    }
    for platform_type, platform_names in platform_types.items():
        for name in platform_names:
            if name == platform_name:
                return platform_type


def build_string_of_options(argv):
    """Function that builds and returns sting that will be used as 'options' argument for
    getopt.getopt(args, options[, long_options]) based on passed arguments excluding custom args

        Args:
            argv (str[]): List of strings. Each string is cli option name with possible values
                Example: ['-sTestSuite', '-r', -I, '--excludesuites=TestSuite1']

        Returns:
            options [str]:
                Example: 's:rI'
    """
    # parse arguments to build list of options for getopt
    options = ''
    for option in argv[:-1]:
        # ignore custom args
        if any(arg in option for arg in CUSTOM_ARGS):
            continue
        if len(option) == 2:
            option = option[1:2]
        else:
            option = option[1:2] + ':'
        if options == '':
            options = option
        else:
            options = options + option
    return options


def build_command_to_run_soapui(soapui_project_path, args, program=None):
    """Function that builds and returns list of stings that will be used by os.call

        Args:
            soapui_project_path (str): String that represents full file path with extension
            args (tuple[]): List of tuples. Where each tuple it is pare of option name and corresponding value
                Example: [('-s', 'Test Suite'), (-r, '')]
            program (?str): Optional. String that represents full file path to testrunner.bat or testrunner.sh
                By default final command will have testrunner.sh or testrunner.bat based on os type

        Returns:
            command [str[]]:
                Example: '['testrunner.sh', '-sSmoke-test1', '-r', '-I',
                 '/Users/user/Projects/SoapUI/MK_API_clone1.xml']'
    """
    # setup default program to run soapUI from cli
    if program is None:
        platform_name = get_platform_name()
        if platform_name == 'unix':
            program = 'testrunner.sh'
        if platform_name == 'win':
            program = 'testrunner.bat'
    command = [program]
    if args is not None:
        for arg in args:
            if not any(argument in arg[0] for argument in CUSTOM_ARGS):
                command.append(''.join(arg))
    command.append(soapui_project_path)
    return command


def main(argv):
    """Main function that aggregates calls of all private functions in that package to execute generated cli command
        based on params that were specified

        Args:
            argv (str[]): List of strings. Each string is cli option name with possible values
                Example: ['-sTestSuite', '-r', -I, '--excludesuites=TestSuite1']

        Returns:
            status code
    """
    soapui_root_dir = argv[-1:][0]
    options = build_string_of_options(argv)
    result = []
    try:
        opts, args = getopt.getopt(argv[:-1], options, [arg + '=' for arg in CUSTOM_ARGS])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)  # cli syntax error
    # get test suite name from arguments
    original_test_suite_name = get_option_value(opts, '-s')
    projects_to_exclude = get_option_value(opts, '--excludeprojects')
    suites_to_exclude = get_option_value(opts, '--excludesuites')
    soapui_projects_list = get_list_of_soapui_projects(soapui_root_dir)
    soapui_projects_list = build_list_of_soapui_projects(soapui_projects_list, projects_to_exclude)
    for soapui_project in soapui_projects_list:
        # if test suite has * at the end of the name that means we need to run all test suite started with name
        test_suite_name = original_test_suite_name
        test_suite_names = get_list_of_suites_from_soapui_project(soapui_project)
        test_suite_names = build_list_of_suites(test_suite_name, test_suite_names, suites_to_exclude)
        if test_suite_names:
            for test_suite_name in test_suite_names:
                # run soapui project with params
                set_option_value(opts, '-s', test_suite_name)
                program = get_option_value(opts, '--prog')
                command_to_run = build_command_to_run_soapui(soapui_project, opts, program)
                print(command_to_run)
                #result.append(call(command_to_run))
                set_option_value(opts, '-s', original_test_suite_name)
    if all(i > 0 for i in result):
        sys.exit(1)  # if something fails


if __name__ == "__main__":
    main(sys.argv[1:])

"""
TODO:

- readme
"""
