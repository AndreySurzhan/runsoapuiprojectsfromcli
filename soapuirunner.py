from os import walk, path
import xml.etree.ElementTree as ET

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
