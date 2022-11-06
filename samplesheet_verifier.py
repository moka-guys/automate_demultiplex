# coding=utf-8
""" Script for checking sample sheet naming and contents.

Uses the seglh-naming library. And adds further lab-specific checks e.g. whether sequencer IDs and runtypes match
those in allowed list from the config file. Collects all errors in an errors list (ValidSamplesheet.errors)
"""

import argparse
import os
import re
from collections import defaultdict
import tempfile
import shutil
import logging
import automate_demultiplex_config as config
import adlogger #import ADLoggers, get_runfolder_log_config
from seglh_naming.sample import Sample
from seglh_naming.samplesheet import Samplesheet
import string


def arg_parse():
    """ Parses arguments supplied by the command line.
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


class ValidSamplesheet(object):
    """ Runs the checks. Called by webapp for uploaded samplesheets (uses name of file being uploaded),
    and called for runs not yet demultiplexed (uses path of expected samplesheet from demultiplex script)
    """
    def __init__(self, ss_path):
        self.ss_path = ss_path
        self.ss_obj = ''
        self.pannumbers = []
        self.tso = ''
        self.samples = defaultdict(str) # store sample IDs and sample names from samplesheet
        self.errors = defaultdict(list) # store errors
        self.data_headers = [] # populate with headers from data section
        self.missing_headers = [] # populate with missing headers
        self.expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        self.ss_checks()


    def ss_checks(self):
        """ Run checks at samplesheet and sample level.
        Performs required extra checks for checks not included in seglh-naming
        """
        if self.check_ss_present():
            self.ss_obj = self.check_ss_name()
            if self.ss_obj:
                self.check_sequencer_id()
            if self.check_ss_contents():
                self.get_data_section()
                self.check_expected_headers()
                # check sample id or sample name columns are not missing before doing sample validation
                self.comp_samplenameid()
                for key in self.samples.keys(): # run checks at the sample level
                    for sample in self.samples[key]:
                        sample_obj = self.check_sample(sample, key)
                        if sample_obj:
                            self.check_pannos(sample, key, sample_obj)
                            self.check_runtypes(sample, key, sample_obj)
                self.check_tso()


    def check_ss_present(self):
        """ Checks for upload error (i.e. samplesheet for run not present). Appends info to dict.
        If samplesheet present returns true, else returns false.
        """
        if os.path.isfile(self.ss_path):
            return True
        else:
            self.errors["sspresent_err"].append("Samplesheet with supplied name not present ({})".format(self.ss_path))


    def check_ss_name(self):
        """ Validate samplesheet names using seglh-naming Samplesheet module.
        """
        try:
            self.ss_obj = Samplesheet.from_string(self.ss_path)
        except Exception as e:
            self.errors["ssname_err"].append(str(e))
        return self.ss_obj


    def check_sequencer_id(self):
        """ Check element 2 of samplesheet
        (expected sequencer name matches list of allowed names in config.sequencer_ids)
        """
        if self.ss_obj.sequencerid not in config.sequencer_ids:
            self.errors["sequencerid_err"].append("Sequencer id not in allowed list "
                                                  "({}, {})".format(self.ss_obj, self.ss_obj.sequencerid))


    def check_ss_contents(self):
        """ Check if samplesheet is empty (<10kbytes)
        """
        if os.stat(self.ss_path).st_size > 10:
            return True
        else:
            self.errors["sscontents_err"].append("Samplesheet empty (<10 bytes)")


    def get_data_section(self):
        """ Parse data section of samplesheet from file
        Reads samplesheet in reverse order and collects sample ID and sample name
        """
        sample_ids = []
        sample_names = []
        with open(self.ss_path, 'r') as samplesheet_stream:
            for line in reversed(samplesheet_stream.readlines()):
                # If line contains table headers, stop looping through the file
                if any(header in line for header in self.expected_data_headers):
                    self.data_headers = line.split(",")
                    break
                elif len(line.split(",")[0]) < 2: # skip empty lines
                    pass
                else: # contains sample
                    sample_details = line.split(",")
                    sample_id, sample_name = sample_details[0], sample_details[1]
                    # Append sample id and sample name to sampleStrings for testing
                    sample_ids.append(sample_id)
                    sample_names.append(sample_name)
        self.samples["Sample_ID"] = sample_ids
        self.samples["Sample_Name"] = sample_names


    def check_expected_headers(self):
        """ Checks [Data] section has expected headers, against self.expected_data_headers list.
        """
        if not all(header in self.data_headers for header in self.expected_data_headers):
            self.missing_headers = list(set(self.expected_data_headers).difference(self.data_headers))
            self.errors["headers_err"].append("Header(/s) missing from [Data] "
                                              "section: '{}'".format(','.join(self.missing_headers)))


    def comp_samplenameid(self):
        """ Check whether the names match between Sample_ID and Sample_Name in data section of samplesheet
        """
        if self.samples["Sample_ID"] != self.samples["Sample_Name"]:
            differences = ", ".join(map(str, (list(set(self.samples["Sample_ID"]) - set(self.samples["Sample_Name"])))))
            self.errors["samplenameid_err"].append("Sample ID, Sample Name do not match: ({})".format(differences))


    def check_sample(self, sample, key):
        """ Validate sample names using seglh-naming Sample module.
        Checks run on Sample_Name and Sample_ID; Sample_Name is used by bcl2fastq and Sample_ID is used if
        Sample_Name is not present.
        """
        try:
            sample_obj = Sample.from_string(sample)
            return sample_obj
        except Exception as e:
            self.errors["sample_err"].append("{}: {}".format(key, str(e)))


    def check_pannos(self, sample, key, sample_obj):
        """ Check sample names contain allowed pan numbers from config.panel_list number list.
        """
        # extract pan no (last element), check against config.panel list
        self.pannumbers.append(sample_obj.panelnumber)
        if sample_obj.panelnumber not in config.panel_list:
            self.errors["panno_err"].append("Pan number not in allowed list: "
                                            "{} ({}: {})".format(sample_obj.panelnumber, key, sample))


    def check_runtypes(self, sample, key, sample_obj):
        """ Check sample names contain allowed runtypes from config.runtype_list
        """
        runtype = re.match("^[A-Z]*", sample_obj.libraryprep) # extract first group of capitalised characters
        if runtype.group(0) not in config.runtype_list:
             self.errors["runtypes_err"].append("Runtype not in allowed list ({}, {})".format(sample, key))


    def check_tso(self):
        """ Returns True if TSO sample
        """
        if any(item in self.pannumbers for item in config.tso500_panel_list):
            self.tso = True



def main():
    args = arg_parse()
    ss = ValidSamplesheet(args.samplesheet)
    for key in ss.errors.keys():
        print(', '.join(ss.errors[key]))

    print(ss.tso)

if __name__ == '__main__':
    main()