# coding=utf-8
""" Script for checking sample sheet naming and contents.

Uses the seglh-naming library. And adds further lab-specific checks e.g. whether sequencer IDs and runtypes match
those in lists of allowed IDs. Collects all errors in an errors list (ValidSamplesheet.errors)
"""

import argparse, os, re
from collections import defaultdict
from seglh_naming.sample import Sample
from seglh_naming.samplesheet import Samplesheet


def arg_parse():
    """ Parses arguments supplied by the command line.
        :return: (Namespace object) parsed command line attributes
    Creates argument parser, defines command line arguments, then parses supplied command line arguments using the
    created argument parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--samplesheet', type=str, required=True,
                        dest='samplesheet', help="Samplesheet to validate")
    parser.add_argument('-p', '', type=list, required=True, dest='panel_list',
                        help="List of allowed panel numbers")
    parser.add_argument('-r', '--runtype', type=list, required=True, dest='runtype_list')
    parser.add_argument('-t', '--tso500panel_list', type=list, required=True, dest='tso500panel_list',
                        help="List of tso500 panel numbers")
    args = parser.parse_args()
    return args


class SamplesheetCheck(object):
    """ Runs the checks. Called by webapp for uploaded samplesheets (uses name of file being uploaded),
    and called for runs not yet demultiplexed (uses path of expected samplesheet from demultiplex script)

    Methods:
        ss_checks()
            Run checks at samplesheet and sample level
        check_ss_present()
            Checks for upload error (i.e. samplesheet for run not present)
        check_ss_name()
            Validate samplesheet names using seglh-naming Samplesheet module
        check_sequencer_id()
            Check element 2 of samplesheet (sequencer name matches list of allowed names in self.sequencerid_list)
        check_ss_contents()
            Check if samplesheet is empty (<10kbytes)
        get_data_section()
            Parse data section of samplesheet from file
        check_expected_headers()
            Check [Data] section has expected headers, against self.expected_data_headers list
        comp_samplenameid()
            Check whether names match between Sample_ID and Sample_Name in data section of samplesheet
        check_illegal_chars()
            Returns true if illegal characters present
        check_sample()
            Validate sample names using seglh-naming Sample module.
        check_pannos()
            Check sample names contain allowed pan numbers from self.panel_list number list
        check_runtypes()
            Check sample names contain allowed runtypes from self.runtype_list
        check_tso()
            Returns True if TSO sample
    """

    def __init__(self, ss_path, sequencerid_list, panel_list, runtype_list, tso500panel_list):
        self.ss_path = ss_path
        self.ss_obj = ''
        self.pannumbers = []
        self.tso = ''
        self.samples = defaultdict(str)  # Store sample IDs and sample names from samplesheet
        self.errors = defaultdict(list)  # Store errors
        self.data_headers = []  # Populate with headers from data section
        self.missing_headers = []  # Populate with missing headers
        self.expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        self.sequencerid_list = sequencerid_list
        self.panel_list = panel_list
        self.runtype_list = runtype_list
        self.tso500panel_list = tso500panel_list

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
                # Check sample id or sample name columns are not missing before doing sample validation
                self.comp_samplenameid()
                for key in self.samples.keys():  # Run checks at the sample level
                    for sample in self.samples[key]:
                        self.check_illegal_chars(sample, key)
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
        """ Check element 2 of samplesheet (sequencer name matches list of allowed names in self.sequencerid_list)
        """
        if self.ss_obj.sequencerid not in self.sequencerid_list:
            self.errors["sequencerid_err"].append("Sequencer id not in allowed list "
                                                  "({}, {})".format(self.ss_obj, self.ss_obj.sequencerid))

    def check_ss_contents(self):
        """ Check if samplesheet is empty (<10kbytes)
        """
        if os.stat(self.ss_path).st_size > 10:
            return True
        else:
            self.errors["ssempty_err"].append("Samplesheet empty (<10 bytes)")

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
                elif len(line.split(",")[0]) < 2:  # skip empty lines
                    pass
                else:  # Contains sample
                    try:
                        sample_details = line.split(",")
                        sample_id, sample_name = sample_details[0], sample_details[1]

                        # Append sample id and sample name to sampleStrings for testing
                        sample_ids.append(sample_id)
                        sample_names.append(sample_name)
                    except Exception as e:
                        self.errors["get_data_err"].append("Exception raised while parsing data section: {}".format(e))
        self.samples["Sample_ID"] = sample_ids
        self.samples["Sample_Name"] = sample_names

    def check_expected_headers(self):
        """ Check [Data] section has expected headers, against self.expected_data_headers list.
        """
        if not all(header in self.data_headers for header in self.expected_data_headers):
            self.missing_headers = list(set(self.expected_data_headers).difference(self.data_headers))
            self.errors["headers_err"].append("Header(/s) missing from [Data] "
                                              "section: '{}'".format(','.join(self.missing_headers)))

    def comp_samplenameid(self):
        """ Check whether names match between Sample_ID and Sample_Name in data section of samplesheet
        """
        differences = ", ".join(map(str, (list(set(self.samples["Sample_ID"]) - set(self.samples["Sample_Name"])))))
        if differences:
            self.errors["samplenameid_err"].append("The following Sample IDs do not match the "
                                                   "corresponding Sample Name: ({})".format(differences))

    def check_illegal_chars(self, sample, key):
        """ Returns true if illegal characters present
        """
        valid_chars = '^[A-Za-z0-9_-]+$'
        if not re.match(valid_chars, sample):
            self.errors["validchars_err"].append("Sample name contains invalid characters ({}: {})".format(key, sample))

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
        """ Check sample names contain allowed pan numbers from self.panel_list number list.
        """
        self.pannumbers.append(sample_obj.panelnumber)
        if sample_obj.panelnumber not in self.panel_list:
            self.errors["panno_err"].append("Pan number not in allowed list: "
                                            "{} ({}: {})".format(sample_obj.panelnumber, key, sample))

    def check_runtypes(self, sample, key, sample_obj):
        """ Check sample names contain allowed runtypes from self.runtype_list
        """
        runtype = re.match("^[A-Z]*", sample_obj.libraryprep)  # Extract first group of capitalised characters
        if runtype.group(0) not in self.runtype_list:
            self.errors["runtypes_err"].append("Runtype not in allowed list ({}, {})".format(sample, key))

    def check_tso(self):
        """ Returns True if TSO sample
        """
        if any(item in self.pannumbers for item in self.tso500panel_list):
            self.tso = True


def main():
    args = arg_parse()
    ss = SamplesheetCheck(args.samplesheet, panel_list, runtype_list, tso500panel_list)
    for key in ss.errors.keys():
        print(', '.join(ss.errors[key]))


if __name__ == '__main__':
    main()