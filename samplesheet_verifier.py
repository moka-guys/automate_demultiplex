"""
Script for checking sample sheet naming and contents. Script is run in 2 scenarios:

1) Early warning as soon as the samplesheet is uploaded (to be run in a webapp which the scientists will use to upload
    the samplesheet)

    After already_demultiplexed() has been called - call from the loop_through_runs function - check all runfolders
    that have not yet been demultiplexed for a matching samplesheet without errors and throw any necessary error
    messages.

2) Pre-demultiplex check

    The idea is that the script will be called in place of the look_for_sample_sheet (/check_valid_samplesheet)
    function in the automate_demultiplex script (called on line 253). If it passes the checks in the script,
    run_demultiplexing() will be called, if not the run will be skipped over (error messages would be sent in
    samplesheet_checker.py saying that ready to demultiplex but it can't begin because ___)
"""

# Naming checking functions are only useable by the webapp
# The demultiplex.py uses the runfolder name to create the expected samplesheet name - so the check exists function
# is useful for this but the other checking functions are not

import argparse
import os
import re
import pandas as pd
from collections import OrderedDict
import tempfile
import git
import shutil
import logging

def arg_parse():
    """
    Parses arguments supplied by the command line.
        :return: (Namespace object) parsed command line attributes
    Creates argument parser, defines command line arguments, then parses supplied command line arguments using the
    created argument parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--runfolder', type=str, required=True, dest='runfolder',
                        help="directory containing runfolders")
    parser.add_argument('-s', '--samplesheet', type=str, required=True, dest = 'samplesheet',
                        help="samplesheet")
    args = parser.parse_args()
    return args


def run_checks(samplesheet_path):
    """
    Runs the checks
    """
    # if samplesheet present, record this and continue with other checks
    if check_uploaded(samplesheet_path):
        print("Samplesheet successfully uploaded\n")
        check_naming(samplesheet_path)
        if check_not_empty(samplesheet_path):
            check_header(samplesheet_path)
            check_reads(samplesheet_path)
            check_settings(samplesheet_path)
            check_data(samplesheet_path)
    else:
        print("ERROR: Samplesheet was not uploaded\n")

def check_uploaded(samplesheet_path):
    """
    Check samplesheet for run is present. Can be run within webapp.
    :return:
    """
    if os.path.isfile(samplesheet_path):
        return True

def check_naming(samplesheet_path):
    """
    Check the saved sample sheet is named correctly so that metadata can be extracted by the pipeline
    Element 1: 6 digits
    Element 2: Sequencer name that matches list of allowed names
    Element 3: 4 digits
    Element 4: All alphanumeric, or numbers followed by a dash and then alphanumeric. (no lower case)
    Element 5: "SampleSheet.csv"
    """
    error = ""
    sequencer_ids = ["NB551068", "NB552085", "M02353", "M02631", "A01229"]
    # pattern 1 is 9 zero's followed by - followed by 5 alphanumeric characters
    # pattern 2 is 10 alphanumeric characters
    flowcell_ids = ["^([0]){9}-([A-Z0-9]){5}$", "^([A-Z0-9]){10}$"]
    # Split samplename on "_" delimiter
    samplesheet_elements = samplesheet_path.split("/")[-1].split("_")

    # if samplesheet name contains expected number of elements, carry out rest of checks
    if not len(samplesheet_elements)==4:
        # checking element 1
        if not samplesheet_elements[0].isnumeric() and not len(samplesheet_elements[0])==6:
            error += "First element of samplesheet incorrect. "

        # checking sequence identifier
        if samplesheet_elements[1] not in sequencer_ids:
            error += "Sequencer identifier incorrect. "

        # checking autoincrementing number
        if not samplesheet_elements[2].isnumeric() and not len(samplesheet_elements[2])==4:
            error += "Autoincrementing number not as expected. "

        # checking flowcell ID
        pattern_1 = re.compile(flowcell_ids[0])
        pattern_2 = re.compile(flowcell_ids[1])
        if not (pattern_1.match(samplesheet_elements[3]) or pattern_2.match(samplesheet_elements[3])):
            error += "Flowcell ID not as expected. "

        # Checking 5th element
        if not samplesheet_elements[4] == "SampleSheet.csv":
            error += "End of samplesheet does not match 'SampleSheet.csv'. "
    else:
        error = "Samplesheet name does not contain the expected number of elements."

    # create message depending on results of the above checks:
    if not error:
        print("Samplesheet named according to naming conventions\n")
    else:
        print("ERROR - SAMPLESHEET NOT NAMED ACCORDING TO NAMING CONVENTIONS: {}\n".format(error))

def check_not_empty(samplesheet_path):
    """
    Check the samplesheet is not empty. Can be run within webapp.
    :return:
    """
    # check file is larger than 10kbytes
    if os.stat(samplesheet_path).st_size > 10:
        print("Samplesheet contains data as expected\n")
        return True
    else:
        print("ERROR: Samplesheet is empty\n")

def extract_column(samplesheet_path):
    # extract elements from first column in file to list
    with open(samplesheet_path) as infile:
        samplesheet_columns = []
        for line in infile:
            samplesheet_columns.append((line.split(",")[0]))
    return samplesheet_columns

def check_header(samplesheet_path):
    """
    Checks the header section of the samplesheet is present as expected.
    """
    expected_header_rows = ["[Header]", "IEMFileVersion", "Investigator Name", "Experiment Name", "Date",
                            "Workflow", "Application", "Assay", "Description", "Chemistry"]
    samplesheet_column = extract_column(samplesheet_path)

    if all(row_element in samplesheet_column for row_element in expected_header_rows):
        print("Samplesheet section '[Header]' present as expected, containing expected sections\n")
    else:
        print("UNEXPECTED SAMPLESHEET CONTENTS: '[Header]' section not as expected - expected rows missing\n")

def check_reads(samplesheet_path):
    """
    Checks the reads section of the samplesheet is present as expected.
    """
    samplesheet_column = extract_column(samplesheet_path)

    # get index of reads element in list, and use this to access the two elements after (these should be numeric
    # reads values)
    if "[Reads]" in samplesheet_column:
        index = samplesheet_column.index("[Reads]")
        sub_list = [samplesheet_column[index + 1], samplesheet_column[index + 2]]
        # this regex specifies a number between 1-999
        numeric_pattern = re.compile("^([0-9]){1,3}$")
        # check if reads is a row, and the two rows after match the numeric pattern specified
        if ("[Reads]" in samplesheet_column, numeric_pattern.match(sub_list[1]) == True,
            numeric_pattern.match(sub_list[1]) == True):
            print("Samplesheet section '[Reads]' present as expected, and reads lengths within expected range\n")
    else:
        print("UNEXPECTED SAMPLESHEET CONTENTS: '[Reads]' section not as expected - expected rows missing\n")

def check_settings(samplesheet_path):
    """
    Checks the settings section of the samplesheet is present as expected.
    """
    samplesheet_column = extract_column(samplesheet_path)

    if "[Settings]" in samplesheet_column:
        print("Samplesheet section '[Settings]' present as expected\n")
    else:
        print("UNEXPECTED SAMPLESHEET CONTENTS: '[Settings]' section not as expected - expected rows missing\n")

def check_data(samplesheet_path):
    """
    Checks data section of samplesheet - data headers are as expected, samples named using allowed characters.
    Check sample names contain allowed pan numbers from pan number list.
    """
    expected_data_headers =["Sample_ID", "Sample_Name", "I7_Index_ID", "index", "I5_Index_ID", "index2"]
    sample_id_list = []
    sample_name_list = []

    # reads samplesheet in reverse order and collects sample ID and sample name
    with open(samplesheet_path, 'r') as samplesheet_stream:
        for line in reversed(samplesheet_stream.readlines()):
            # If line contains table headers, stop looping through the file
            if any(header in line for header in expected_data_headers):
                # check [Data] section has expected headers
                columns = line.split(",")
                if all(header in columns for header in expected_data_headers):
                    print("Samplesheet section '[Data]' contains expected column headers\n")
                else:
                    print("UNEXPECTED SAMPLESHEET CONTENTS: '[Data]' section not as expected - headers "
                          "missing\n".format(columns))
                break

            # skip empty lines (check first element of the line, after splitting on comma)
            elif len(line.split(",")[0]) < 2:
                pass
            # If its a line containing a sample:
            else:
                # Split line by columns
                columns = line.split(",")
                # Remove leading & trailing whitespace from sampleID and sampleName
                # (bcl2fastq tolerates leading & trailing whitespace)
                sample_id, sample_name = columns[0].strip(" "), columns[1].strip(" ")
                # Append sample id and sample name to sampleStrings for testing
                sample_id_list.append(sample_id)
                sample_name_list.append(sample_name)

        # run more in detail checks on each Sample_ID and Sample_Name and return results
        invalid_runtypes, invalid_pan_nos, invalid_characters = check_sample_naming(sample_name_list, sample_id_list)


        if invalid_characters:
            print("ERROR - SAMPLES CONTAIN INVALID CHARACTERS: {}\n".format(invalid_characters))
        else:
            print("Samples within samplesheet named using valid characters\n")

        if invalid_pan_nos:
            print("ERROR - SAMPLES CONTAIN INVALID PAN NOS: {}\n".format(invalid_pan_nos))
        else:
            print("Samples within samplesheet named using valid pan numbers\n")

        if invalid_runtypes:
            print("ERROR - SAMPLES CONTAIN INVALID RUNTYPES: {}\n".format(invalid_pan_nos))
        else:
            print("Samples within samplesheet named using valid run types\n")


def check_sample_naming(sample_name_list, sample_id_list):
    """
    Takes sample name as input and performs checks
    """
    config = import_config(github_repo="https://github.com/moka-guys/automate_demultiplex",
                                   github_file="automate_demultiplex_config.py")
    runtype_list = ["WES", "NGS", "ADX", "ONC", "SNP", "ONEPGT"]
    valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    invalid_characters = []
    invalid_runtypes = []
    invalid_pan_nos = []

    # Check whether the names match between Sample_ID and Sample_Name
    if sample_name_list != sample_id_list:
        print("ERROR - SAMPLES INCORRECTLY NAMED: One or more sample names and sample IDs do not match\n")
    else:
        print("Sample ID and name match for all samples, as expected\n")

    # loop through each list in turn and perform further checks
    for list in (sample_name_list, sample_id_list):
        if list == sample_name_list:
            type = "Sample_Name"
        elif list == sample_id_list:
            type = "Sample_ID"

        # loop through the characters of each sample string to check whether they use valid characters
        for sample in list:
            for char in sample:
                if not char in valid_chars:
                    invalid_characters.append("{}: {}".format(type, sample))

        # extract pan no (last element) and runtype (first element), strip numbers from runtype string, check
        # against config.panel list and runtype_list
        pan_no = sample.split("_")[-1]
        # strip numbers from runtype string
        runtype = sample.split("_")[0]
        # if runtype contains digits, split to remove digits and anything after
        if any(chr.isdigit() for chr in runtype):
            runtype = re.split('(\d+)', runtype)[0]

        if runtype not in runtype_list:
            invalid_runtypes.append("{}: {}".format(type, sample))
        if pan_no not in config.panel_list:
            invalid_pan_nos.append("{} - {}: {}".format(type, sample, pan_no))

    return invalid_runtypes, invalid_pan_nos, invalid_characters


def import_config(github_repo, github_file):
    """
    Clones the config file from automate_demultiplex and imports the file as a module. Makes the panel list accessible
        :param github_repo:     (str) Https link to github repository
        :param github_file:     (str) Name of file of interest
    Creates a temporary dir, clones into that dir, copies the desired file from that dir, and removes the temporary
    dir.
    """
    tempdirpath = tempfile.mkdtemp()
    git.Repo.clone_from(github_repo, tempdirpath, branch='Production', depth=1)
    shutil.move(os.path.join(tempdirpath, github_file), os.path.join(os.getcwd(), github_file))
    shutil.rmtree(tempdirpath)
    import automate_demultiplex_config as config
    return config


def main():
    # get arguments
    args = arg_parse()

    # RUN SAMPLESHEET CHECKS
    samplesheet_path = args.samplesheet
    run_checks(samplesheet_path)

    # RUN RUNFOLDER CHECKS


if __name__ == '__main__':
    main()