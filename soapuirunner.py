import getopt
from os import walk, path
import sys
import xml.etree.ElementTree as ET
from smtpd import usage

root_folder = '/Users/user/Projects/SoapUI'


def get_list_of_soapui_projects(root_folder):
    soapui_projects = []

    for (root_path, dirnames, filenames) in walk(root_folder):
        if filenames:
            for filename in filenames:
                filename_without_extension, file_extension = path.splitext(filename)
                if file_extension == '.xml':
                    full_file_path = path.join(root_path, filename)
                    xml_root_tag = ET.parse(full_file_path).getroot().tag
                    # figure out that xml is soapUI project file
                    if 'soapui-project' in xml_root_tag:
                        soapui_projects.append(full_file_path)

        if dirnames:
            for dirname in dirnames:
                soapui_projects.extend(get_list_of_soapui_projects(dirname))

    return soapui_projects


def get_list_of_suites_from_soapui_project(soapui_project_path):
    root = ET.parse(soapui_project_path).getroot()
    test_suites = []

    for child in root:
        if 'testSuite' in child.tag:
            test_suites.append(child.attrib['name'])

    return test_suites


def build_list_of_suites(test_suite, suites_list):
    if test_suite.endswith('*'):
        return [suite for suite in suites_list if test_suite[:-1] in suite]

    return [test_suite]


def get_option_value(opts_list, opt_name):
    return [opt for opt in opts_list if opt[0] == opt_name][0][1]


def set_option_value(opts_list, opt_name, opt_value):
    for opt in opts_list:
        i = opts_list.index(opt)
        if opt[0] == opt_name:
            opt = list(opt)
            opt[1] = opt_value
            opt = tuple(opt)
            opts_list.pop(i)
            opts_list.insert(i, opt)

    return opts_list


def build_string_of_options(argv):
    # parse arguments to build list of options for getopt
    options = ''
    for option in argv[:-1]:
        if len(option) == 2:
            option = option[1:2]
        else:
            option = option[1:2] + ':'

        if options == '':
            options = option
        else:
            options = options + option

    return options


def get_command_to_run_soapui(soapui_project_path, args):
    command_to_execute = 'testrunner.bat'
    params_for_command = ''

    if args is not None:
        for arg in args:
            params_for_command = params_for_command + ' ' + ''.join(arg)

    command_to_execute = command_to_execute + params_for_command + ' ' + soapui_project_path

    return command_to_execute


def main(argv):
    soapui_root_dir = argv[-1:][0]
    options = build_string_of_options(argv)

    try:
        opts, args = getopt.getopt(argv[:-1], options)
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    # get test suite name from arguments
    test_suite_name_from_cli = get_option_value(opts, '-s')

    soapip_projects_list = get_list_of_soapui_projects(soapui_root_dir)

    for soapui_project in soapip_projects_list:
        # if test suite has * at the end of the name that means we need to run all test suite started with name
        test_suite_names = get_list_of_suites_from_soapui_project(soapui_project)
        test_suite_names = build_list_of_suites(test_suite_name_from_cli, test_suite_names)
        for test_suite_name in test_suite_names:
            # run soapui project with params
            opts = set_option_value(opts, '-s', test_suite_name)
            print(get_command_to_run_soapui(soapui_project, opts))

            pass


if __name__ == "__main__":
    main(sys.argv[1:])

"""
- run command in python
- readme
"""
