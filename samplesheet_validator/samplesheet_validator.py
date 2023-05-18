# coding=utf-8
""" Script for checking sample sheet naming and contents.

Uses the seglh-naming library. And adds further lab-specific checks e.g.
whether sequencer IDs and runtypes match those in lists of allowed IDs.
Collects all errors in an errors list (ValidSamplesheet.errors)
"""

import os
import re
from collections import defaultdict
from seglh_naming.sample import Sample
from seglh_naming.samplesheet import Samplesheet
import config.ad_config as ad_config

# TODO add logging - logger as class argument


class SamplesheetCheck(object):
    """
    Runs the checks. Called by webapp for uploaded samplesheets (uses name of
    file being uploaded), and called for runs not yet demultiplexed (uses path
    of expected samplesheet from demultiplex script)

    Methods:
        ss_checks()
            Run checks at samplesheet and sample level
        check_ss_present()
            Checks for upload error (i.e. samplesheet for run not present)
        check_ss_name()
            Validate samplesheet names using seglh-naming Samplesheet module
        check_sequencer_id()
            Check element 2 of samplesheet (sequencer name matches list of
            allowed names in self.sequencerid_list)
        check_ss_contents()
            Check if samplesheet is empty (<10kbytes)
        get_data_section()
            Parse data section of samplesheet from file
        check_expected_headers()
            Check [Data] section has expected headers, against
            self.expected_data_headers list
        comp_samplenameid()
            Check whether names match between Sample_ID and Sample_Name i
            data section of samplesheet
        check_illegal_chars()
            Returns true if illegal characters present
        check_sample()
            Validate sample names using seglh-naming Sample module.
        check_pannos()
            Check sample names contain allowed pan numbers from self.panel_list
            number list
        check_runtypes()
            Check sample names contain allowed runtypes from self.runtype_list
        check_tso()
            Returns True if TSO sample
    """

    def __init__(
        self,
        ss_path,
        sequencerid_list,
        panel_list,
        runtype_list,
        tso_panel_list,
    ):
        self.ss_path = ss_path
        self.ss_obj = ""
        self.pannumbers = []
        self.tso = False
        self.samples = defaultdict(
            str
        )  # Store sample IDs and sample names from samplesheet
        self.errors = defaultdict(list)  # Store errors
        self.data_headers = []  # Populate with headers from data section
        self.missing_headers = []  # Populate with missing headers
        self.expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        self.sequencerid_list = sequencerid_list
        self.panel_list = panel_list
        self.runtype_list = runtype_list
        self.tso_panel_list = tso_panel_list

        self.ss_checks()

    def ss_checks(self):
        """Run checks at samplesheet and sample level.
        Performs required extra checks for checks not included in seglh-naming
        """
        if self.check_ss_present():
            self.ss_obj = self.check_ss_name()
            if self.ss_obj:
                self.check_sequencer_id()
            if self.check_ss_contents():
                self.get_data_section()
                self.check_expected_headers()
                # Check sample id or sample name columns are not missing before
                # doing sample validation
                self.comp_samplenameid()
                for (
                    column,
                    samples,
                ) in self.samples.items():  # Run checks at the sample level
                    for sample in samples:
                        self.check_illegal_chars(sample, column)
                        sample_obj = self.check_sample(sample, column)
                        if sample_obj:
                            self.check_pannos(sample, column, sample_obj)
                            self.check_runtypes(sample, column, sample_obj)
                self.check_tso()

    def check_ss_present(self):
        """
        Checks for upload error (i.e. samplesheet for run not present).
        Appends info to dict. If samplesheet present returns true, else returns
        false.
        """
        if os.path.isfile(self.ss_path):
            return True
        else:
            self.errors["sspresent_err"].append(
                f"Samplesheet with supplied name "
                f"not present ({self.ss_path})"
            )

    def check_ss_name(self):
        """
        Validate samplesheet names using seglh-naming Samplesheet module.
        """
        try:
            self.ss_obj = Samplesheet.from_string(self.ss_path)
        except Exception as exception:
            self.errors["ssname_err"].append(str(exception))
        return self.ss_obj

    def check_sequencer_id(self):
        """
        Check element 2 of samplesheet (sequencer name matches list of
        allowed names in self.sequencerid_list)
        """
        if self.ss_obj.sequencerid not in self.sequencerid_list:
            self.errors["sequencerid_err"].append(
                f"Sequencer id not in allowed list "
                f"({self.ss_obj}, {self.ss_obj.sequencerid})"
            )

    def check_ss_contents(self):
        """
        Check if samplesheet is empty (<10 bytes)
        """
        if os.stat(self.ss_path).st_size > 10:
            return True
        else:
            self.errors["ssempty_err"].append("Samplesheet empty (<10 bytes)")

    def get_data_section(self):
        """
        Parse data section of samplesheet from file
        Read samplesheet in reverse order, collect sample ID and sample name
        """
        sample_ids = []
        sample_names = []
        with open(self.ss_path, "r", encoding="utf-8") as samplesheet_stream:
            for line in reversed(samplesheet_stream.readlines()):
                # If line contains table headers, stop looping through the file
                if any(
                    header in line for header in self.expected_data_headers
                ):
                    self.data_headers = line.split(",")
                    break
                elif len(line.split(",")[0]) < 2:  # skip empty lines
                    pass
                else:  # Contains sample
                    try:
                        sample_details = line.split(",")
                        sample_id, sample_name = (
                            sample_details[0],
                            sample_details[1],
                        )

                        # Append sample id and sample name to sampleStrings
                        # for testing
                        sample_ids.append(sample_id)
                        sample_names.append(sample_name)
                    except Exception as exception:
                        self.errors["get_data_err"].append(
                            f"Exception raised while parsing "
                            f"data section: {exception}"
                        )
        self.samples["Sample_ID"] = sample_ids
        self.samples["Sample_Name"] = sample_names

    def check_expected_headers(self):
        """
        Check [Data] section has expected headers, against
        self.expected_data_headers list.
        """
        if not all(
            header in self.data_headers
            for header in self.expected_data_headers
        ):
            self.missing_headers = list(
                set(self.expected_data_headers).difference(self.data_headers)
            )
            self.errors["headers_err"].append(
                f"Header(/s) missing from [Data] "
                f"section: '{self.missing_headers}'"
            )

    def comp_samplenameid(self):
        """
        Check whether names match between Sample_ID and Sample_Name in
        data section of samplesheet
        """
        differences = ", ".join(
            map(
                str,
                (
                    list(
                        set(self.samples["Sample_ID"])
                        - set(self.samples["Sample_Name"])
                    )
                ),
            )
        )
        if differences:
            self.errors["samplenameid_err"].append(
                f"The following Sample IDs do not match the "
                f"corresponding Sample Name: ({differences})"
            )

    def check_illegal_chars(self, sample, column):
        """Returns true if illegal characters present"""
        valid_chars = "^[A-Za-z0-9_-]+$"
        if not re.match(valid_chars, sample):
            self.errors["validchars_err"].append(
                f"Sample name contains invalid characters "
                f"({column}: {sample})"
            )

    def check_sample(self, sample, column):
        """
        Validate sample names using seglh-naming Sample module.
        Checks run on Sample_Name and Sample_ID; Sample_Name is used by
        bcl2fastq and Sample_ID is used if Sample_Name is not present.
        """
        try:
            sample_obj = Sample.from_string(sample)
            return sample_obj
        except Exception as exception:
            self.errors["sample_err"].append(f"{column}: {str(exception)}")

    def check_pannos(self, sample, column, sample_obj):
        """
        Check sample names contain allowed pan numbers from
        self.panel_list number list.
        """
        self.pannumbers.append(sample_obj.panelnumber)
        if sample_obj.panelnumber not in self.panel_list:
            self.errors["panno_err"].append(
                f"Pan number not in allowed list: "
                f"{sample_obj.panelnumber} ({column}: {sample})"
            )

    def check_runtypes(self, sample, column, sample_obj):
        """
        Check sample names contain allowed runtypes from self.runtype_list
        """
        # Extract first group of capitalised characters
        runtype = re.match("^[A-Z]*", sample_obj.libraryprep)
        if runtype.group(0) not in self.runtype_list:
            self.errors["runtypes_err"].append(
                f"Runtype not in allowed list ({sample}, {column})"
            )

    def check_tso(self):
        """
        Returns True if TSO sample
        """
        if any(item in self.pannumbers for item in self.tso_panel_list):
            self.tso = True


if __name__ == "__main__":
    for samplesheet in os.listdir("/home/rachel/samplesheets/samplesheets"):
        path = os.path.join(
            "/home/rachel/samplesheets/samplesheets/", samplesheet
        )
        ss_obj = SamplesheetCheck(
            path,
            ad_config.SEQUENCER_IDS,
            ad_config.PANEL_LIST,
            ad_config.RUNTYPE_LIST,
            ad_config.TSO_PANEL_LIST,
        )
        for err_type, items in ss_obj.errors.items():
            for item in items:
                print(item)
