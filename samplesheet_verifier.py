"""
Script for checking sample sheet naming and contents.
Can be run as standalone script.
Also called by demultiplex.py (checks all runs not yet demultiplexed).
Also used in samplesheet upload webapp.

Script is run in 2 scenarios:

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
from collections import OrderedDict
import tempfile
import shutil
import logging
import automate_demultiplex_config as config

def arg_parse():
    """
    Parses arguments supplied by the command line.
        :return: (Namespace object) parsed command line attributes
    Creates argument parser, defines command line arguments, then parses supplied command line arguments using the
    created argument parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--samplesheet', type=str, required=True, dest = 'samplesheet', help="samplesheet")
    parser.add_argument('-t', '--type', type=str, required=True, dest = 'type',
                        help="script mode type (runfolder, or ss_upload")
    args = parser.parse_args()
    return args

class ValidSamplesheet:
    """
    Runs the checks. Called by webapp for uploaded samplesheets (uses name of file being uploaded), and called for runs
    not yet demultiplexed (uses path of expected samplesheet from demultiplex script)
    """
    def __init__(self, samplesheet_path):
        self.samplesheet_path = samplesheet_path
        self.results = OrderedDict()
        self.sequencer_ids = ["NB551068", "NB552085", "M02353", "M02631", "A01229"]

        # Split samplename on "_" delimiter
        self.samplesheet_elements = self.samplesheet_path.split("/")[-1].split("_")
        # samplesheet name flowcell ID element expected string patterns. pattern 1 is 9 zero's followed by 5
        # alphanumeric characters. Pattern 2 is 10 alphanumeric characters
        self.flowcell_id_patterns = [re.compile("^([0]){9}-([A-Z0-9]){5}$"), re.compile("^([A-Z0-9]){10}$")]
        # list of expected headers from '[Data]' section of samplesheet
        self.expected_data_headers =["Sample_ID", "Sample_Name", "index"]
        # to be populated with list of sample IDs from samplesheet
        self.sample_id_list = []
        # to be populated with list of sample names from samplesheet
        self.sample_name_list = []
        # to be populated with headers from data section
        self.data_headers = []
        self.runtype_list = ["WES", "NGS", "ADX", "ONC", "SNP", "PGT", "TSO"]
        self.valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        # to append any sample names or IDs to with invalid characters/runtypes/pannos
        self.invalid_characters = ""
        self.invalid_runtypes = ""
        self.invalid_pan_nos = ""

    def run_checks(self):
        """
        Calls the checks for each type of use of the script (runfolders in demultiplex script, and samplesheet upload
        app.
        If check is for demultiplex script, check the samplesheet is present then continue with rest of checks. If
        check is for samplesheet upload, no need to check whether ss present. If samplesheet contains expected number
        of elements, run rest of samplsheet name checks (performs check for each element of samplesheet name). If
        samplesheet is present and isn't empty, perform samplesheet contents checks
        """
        if self.check_ss_present():
            if self.check_ss_elements():
                self.check_first_ss_element()
                self.check_second_ss_element()
                self.check_third_ss_element()
                self.check_fourth_ss_element()
                self.check_fifth_ss_element()
            if self.check_ss_not_empty():
                self.check_unexpected_contents()
        return self.results

    def check_ss_present(self):
        """
        Checks for upload error (i.e. samplesheet for run not present). Appends info to dict. If samplesheet present
        returns true, else returns false.
        """
        if os.path.isfile(self.samplesheet_path):
            self.results["ss_present"] = True, "Samplesheet present. "
            return True
        else:
            self.results["ss_present"] = False, "SAMPLESHEET WITH SUPPLIED NAME NOT PRESENT. "
            return False

    def check_ss_elements(self):
        """
        If the samplesheet path exists, check that samplesheet name contains the expected number of elements. Return
        true if yes, return false if not, and append info to dict.
        """
        if len(self.samplesheet_elements) == 5:
            self.results["ss_elements"] = True, "Samplesheet name contains expected number of elements. "
            return True
        else:
            self.results["ss_elements"] = False, "SAMPLESHEET NAME DOES NOT CONTAIN EXPECTED NUMBER OF ELEMENTS. "
            return False

    def check_first_ss_element(self):
        """
        Checking element 1 of samplesheet (expected 6 digits present).
        """
        if self.samplesheet_elements[0].isdigit() and len(self.samplesheet_elements[0]) == 6:
            self.results["naming_element_1"] = True, "First element (date) of samplesheet name as expected. "
        else:
            self.results["naming_element_1"] = False, "FIRST ELEMENT (date) OF SAMPLESHEET NAME NOT AS EXPECTED. "

    def check_second_ss_element(self):
        """
        Checking element 2 of samplesheet (expected sequencer name matches list of allowed names in self.sequencer_ids)
        """
        if self.samplesheet_elements[1] in self.sequencer_ids:
            self.results["naming_element_2"] = True, "Second element (sequencer identifier) of samplesheet name as " \
                                                     "expected. "
        else:
            self.results["naming_element_2"] = False, "SECOND ELEMENT (sequencer identifier) OF SAMPLESHEET NAME NOT " \
                                                      "AS EXPECTED. "

    def check_third_ss_element(self):
        """
        Checking element 3 of sampleseheet (autoincrementing number - expected 4 digits)
        """
        if self.samplesheet_elements[2].isdigit() and len(self.samplesheet_elements[2]) == 4:
            self.results["naming_element_3"] = True, "Third element (autoincrementing number) of samplesheet name as " \
                                                     "expected. "
        else:
            self.results["naming_element_3"] = False, "THIRD ELEMENT (autoincrementing number) OF SAMPLESHEET NAME " \
                                                      "NOT AS EXPECTED. "

    def check_fourth_ss_element(self):
        """
        Checking element 4 of sampleseheet (flowcell ID - expected all alphanumeric, or numbers followed by dash
        then alphanumeric (no lower case))
        """
        if any(re.match(pattern, self.samplesheet_elements[3]) for pattern in self.flowcell_id_patterns):
            self.results["naming_element_4"] = True, "Fourth element (flowcell ID) of samplesheet name as expected. "
        else:
            self.results["naming_element_4"] = False, "FOURTH ELEMENT (flowcell ID) OF SAMPLESHEET NAME NOT AS " \
                                                      "EXPECTED. "

    def check_fifth_ss_element(self):
        """
        Checking element 5 of sampleseheet (matches string "Samplesheet.csv")
        """
        if self.samplesheet_elements[4] == "SampleSheet.csv":
            self.results["naming_element_5"] = True, "Fifth element ('SampleSheet.csv') of samplesheet name as " \
                                                     "expected. "
        else:
            self.results["naming_element_5"] = False, "FIFTH ELEMENT ('SampleSheet.csv') OF SAMPLESHEET NAME NOT AS " \
                                                      "EXPECTED. "

    def check_ss_not_empty(self):
        """
        Check if samplesheet is empty. Can be run within webapp.
        :return:
        """
        # check file is larger than 10kbytes
        if os.stat(self.samplesheet_path).st_size > 10:
            self.results["ss_not_empty"] = True, "Samplesheet not empty. "
            return True
        else:
            self.results["ss_not_empty"] = False, "SAMPLESHEET EMPTY (<10 bytes). "
            return False

    def get_data_section(self):
        """
        Parse data section of samplesheet from file
        """
        # reads samplesheet in reverse order and collects sample ID and sample name
        with open(self.samplesheet_path, 'r') as samplesheet_stream:
            for line in reversed(samplesheet_stream.readlines()):
                # If line contains table headers, stop looping through the file
                if any(header in line for header in self.expected_data_headers):
                    # check [Data] section has expected headers
                    self.data_headers = line.split(",")
                    self.check_data_headers()
                    break
                # skip empty lines (check first element of the line, after splitting on comma)
                elif len(line.split(",")[0]) < 2:
                    pass
                # If its a line containing a sample:
                else:
                    # Split line by columns
                    sample_details = line.split(",")
                    # Remove leading & trailing whitespace from sampleID and sampleName
                    # (bcl2fastq tolerates leading & trailing whitespace)
                    sample_id, sample_name = sample_details[0].strip(" "), sample_details[1].strip(" ")
                    # Append sample id and sample name to sampleStrings for testing
                    self.sample_id_list.append(sample_id)
                    self.sample_name_list.append(sample_name)

    def check_data_headers(self):
        """
        Checks [Data] section has expected headers, against self.expected_data_headers list.
        """
        if not all(header in self.data_headers for header in self.expected_data_headers):
            self.results["data_headers_present"] = False, "HEADERS MISSING FROM '[Data]' SECTION. "
        else:
            self.results["data_headers_present"] = True, "'[Data]' section headers as expected. "

    def check_unexpected_contents(self):
        """
        Extracts data section from samplesheet, and runs checks (check_data_headers, check_samplenames_match,
        check_samplenames_characters, check_samplenames_pannos, check_samplenames_runtypes). Checks are run on both
        Sample_Name and Sample_ID because Sample_Name is used by bcl2fastq but Sample_ID is used if Sample_Name is not
        present.
        """
        self.get_data_section()
        # run checks to see if samplename and sampleID match
        self.check_samplenames_match()

        for list in (self.sample_name_list, self.sample_id_list):
            if list == self.sample_name_list:
                type = "Sample_Name"
            elif list == self.sample_id_list:
                type = "Sample_ID"

            # run more in detail checks on each Sample_ID and Sample_Name
            self.check_samplenames_characters(list, type)
            self.check_samplenames_runtypes(list, type)
            self.check_samplenames_pannos(list, type)

        if self.invalid_characters:
            self.results["valid_characters"] = False, "SAMPLES CONTAIN INVALID CHARACTERS: " \
                                                      "{} ".format(self.invalid_characters)
        else:
            self.results["valid_characters"] = True, "Sample names and Sample IDs all contain valid characters. "

        if self.invalid_pan_nos:
            self.results["valid_pan_nos"] = False, "SAMPLES CONTAIN INVALID PAN NUMBERS: " \
                                                   "{} ".format(self.invalid_pan_nos)
        else:
            self.results["valid_pan_nos"] = True, "Sample names and Sample IDs all contain valid pan nos. "

        if self.invalid_runtypes:
            self.results["valid_runtypes"] = False, "SAMPLES CONTAIN INVALID RUNTYPES: " \
                                                    "{} ".format(self.invalid_runtypes)
        else:
            self.results["valid_runtypes"] = True, "Sample names and Sample IDs all contain valid runtypes. "

    def check_samplenames_match(self):
        """
        Check whether the names match between Sample_ID and Sample_Name in data section of samplesheet
        """
        if self.sample_id_list != self.sample_name_list:
            differences = "".join(map(str, (list(set(self.sample_id_list) - set(self.sample_name_list)))))
            self.results["ss_names_match"] = \
                False, "SAMPLES INCORRECTLY NAMED: One or more sample names and sample IDs do not match: Sample ID " \
                       "{} doesn't match corresponding sample name. ".format(differences)
        else:
            self.results["ss_names_match"] = True, "Sample names and Sample IDs all match. "

    def check_samplenames_characters(self, list, type):
        """
        Check sample names contain allowed characters from self.valid_chars
        """
        # loop through the characters of each sample string to check whether they use valid characters
        for sample in list:
            for char in sample:
                if not char in self.valid_chars:
                    self.invalid_characters += "{}: {}. ".format(type, sample)

    def check_samplenames_pannos(self, list, type):
        """
        Check sample names contain allowed pan numbers from config.panel_list number list.
        """
        for sample in list:
            # extract pan no (last element), check against config.panel list
            pan_no = re.sub(r'.*Pan', 'Pan', sample).split("_")[0]
            if pan_no not in config.panel_list:
                self.invalid_pan_nos += "{} ({}: {}). ".format(pan_no, type, sample)

    def check_samplenames_runtypes(self, list, type):
        """
        Check sample names contain allowed runtypes from self.runtype_list
        """
        for sample in list:
            # extract runtype (first element), strip numbers from string, check against self.runtype_list
            runtype = sample.split("_")[0]
            # if runtype contains digits, split to remove digits and anything after
            if any(chr.isdigit() for chr in runtype):
                runtype = re.split('(\d+)', runtype)[0]
            if runtype not in self.runtype_list:
                self.invalid_runtypes += "{}: {}. ".format(type, sample)


def run_ss_checks(samplesheet_path):
    SampleSheet = ValidSamplesheet(samplesheet_path)
    return SampleSheet.run_checks()

def main():
    # get arguments
    args = arg_parse()

    # RUN SAMPLESHEET CHECKS
    samplesheet_path = args.samplesheet
    SampleSheet = ValidSamplesheet(samplesheet_path)
    ss_check_results = SampleSheet.run_checks()
    print(ss_check_results)

if __name__ == '__main__':
    main()