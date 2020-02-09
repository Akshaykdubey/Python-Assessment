from lxml2json import convert
import os
from lxml import etree
import json
import sys

path = os.getcwd()
os.chdir('assignment/dataset1/')


def xmltojson(file, sub_dir):
    '''Return json format data of the xml files'''

    with open(file, 'rb') as fd:
        xslt_content = fd.read()
        xslt_root = etree.XML(xslt_content)

        # To make sure the case has a value of List of dicts
        xml_data = convert(xslt_root, alwaysList=".//case")
    return xml_data


def propertiestoxml(file, sub_dir):
    '''Return json format data of the properties files'''

    properties_json = dict()
    with open(file, "r") as fp:
        for line in fp.readlines():
            split_data = line.split('=',)

            # Used to remove the \n characters from the o/p
            properties_json[split_data[0]] = split_data[1].split('\n')[0]

    return properties_json


def jsonmodxml(json_data, sub_dir, elk_json, filename):
    '''Return xml content to be used in the final json file'''

    for value in json_data['result']['suites']['suite']:
        json_file = dict()
        json_file['job_number'] = int(sub_dir)
        json_file['file'] = value['file']
        json_file['name'] = value['name']
        json_file['stdout'] = value['stdout']
        json_file['stderr'] = value['stderr']
        json_file['timestamp'] = value['timestamp']
        json_file['duration'] = value['duration']

        for values in value['cases']['case']:
            json_file_child = dict()
            json_xml_dummy = dict()
            json_file_child['className'] = values['className']
            json_file_child['skipped'] = values['skipped']
            json_file_child['duration'] = values['duration']
            json_file_child['testName'] = values['testName']
            json_file_child['id'] = (values['testName'] +
                                     '_' +
                                     values['className'])
            if values['failedSince'] != '0':
                json_file_child['passed'] = 0
            else:
                json_file['passed'] = 1
            json_xml_dummy = json_file.copy()
            json_xml_dummy.update(json_file_child)
            elk_json.append(json_xml_dummy)

    return elk_json


def finaljson(arg):
    '''Return the final json file used to import in ELK'''

    # Getting the path of the script
    file_path = os.path.dirname(os.path.join(sys.path[0],
                                os.path.basename(
                                    os.path.realpath(sys.argv[0]))))
    elk_json = list()
    for subdir, dirs, files in os.walk(os.getcwd()):
        elk_json_list_final = list()
        elk_json_list = list()
        elk_json_xml = dict()
        prop_json = dict()
        job_name = str()
        for file in files:
            filename = os.fsdecode(file)
            if filename.endswith(".xml"):
                filepath = subdir + os.sep + file
                sub_dir = os.path.basename(os.path.dirname(filepath))
                xml_json = xmltojson(filepath, sub_dir)
                elk_json_xml = jsonmodxml(xml_json, sub_dir,
                                          elk_json_list,
                                          filename)
            elif filename.endswith(".properties"):
                filepath = subdir + os.sep + file
                sub_dir = os.path.basename(os.path.dirname(filepath))
                prop_json = propertiestoxml(filepath, sub_dir)
                job_name = prop_json['job_name']

            # Merging xml and properties to a single json.
            for elk_json_xml_val in elk_json_xml:
                elk_json_xml_val.update(prop_json)

        # This is to make sure no blank dicts are inserted in the list
        if job_name:
            elk_json.append(elk_json_xml)
            elk_json_list_final.append(elk_json_xml)

        # This block creates the individual files in format
        # <job_name>_<job_number>.json
        # Making sure it creates/appends individual files if arg is passed as
        # an argument and job_name is required to be true else it might create
        # files for other sub directory.
        if arg and job_name:
            json_filename = job_name + '_' + os.path.basename(subdir) + '.json'
            path = file_path + os.sep + json_filename
            for filename in os.listdir(file_path):
                # Goes into 'if' when the <job_name>_<job_number>.json don't
                # exists
                if filename == json_filename and os.path.isfile(path):
                    # Can also append the data if thats the requirement
                    with open(path, 'w') as f:
                        print(json.dumps(elk_json_list_final[0],
                              indent=4, sort_keys=True), file=f)
                else:
                    with open(path, 'w') as f:
                        print(json.dumps(elk_json_list_final[0],
                              indent=4, sort_keys=True), file=f)
    if arg:
        return 1
    else:
        sub_dir_json = file_path + os.sep + 'stdout'
        # Dump the json data to stdout file when no argument is passed.
        with open(sub_dir_json, 'w') as f:
            print(json.dumps(elk_json[0], indent=4, sort_keys=True), file=f)


if __name__ == "__main__":

    # Check to make sure extra or invalid arguments are not passed
    if len(sys.argv) > 2:
        print("Error: Please provide no argument or argument 's' to generate",
              "the data ")
        print("\tNo argument: generates stdout with the json data")
        print("\ts: generates json data with the <job_name>_<job_number>.json",
              "tfile")
        sys.exit(0)

    # Making sure the argument is kept optional
    try:
        arg = sys.argv[1]
        if arg != '-s':
            string = "-s : generates json data with the" \
                     "<job_name>_<job_number>.json" \
                     "file"
            raise ValueError(string)
    except IndexError:
        arg = None

    finaljson(arg)
