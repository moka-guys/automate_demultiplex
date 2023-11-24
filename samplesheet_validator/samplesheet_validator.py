# coding=utf-8
"""
Script for checking sample sheet naming and contents.

Uses the seglh-naming library. And adds further lab-specific checks e.g. whether sequencer IDs and runtypes match
those in lists of allowed IDs. Collects all errors in an errors list (SamplesheetCheck.errors_list)
"""
import os
import re
from collections import defaultdict
from typing import Union
from seglh_naming.sample import Sample
from seglh_naming.samplesheet import Samplesheet
from config import ad_config, panel_config


class SamplesheetCheck(object):
    """
    Runs the checks. Called by webapp for uploaded samplesheets (uses name of file being uploaded), and
    called for runs not yet demultiplexed (uses path of expected samplesheet from demultiplex script)

    Attributes:
        samplesheet_path (str):         Path to samplesheet
        runfolder_name (str):           Name of runfolder (used for naming logfile)
        logger (obj):                   Logger object
        ss_obj (False | obj):           seglh-naming samplesheet object
        development_run (bool):         True if run is a development run, else False
        pannumbers (list):              List of panel numbers in the sample sheet
        tso (bool):                     True if samplesheet contains any TSO samples
        samples (dict):                 Dictionary of sample IDs and sample names from the samplesheet
        errors (bool):                  True if samplesheet errors encountered, False if not
        errors_list (bool):             Stores identifiers for any types of errors encountered
        data_headers (list):            Populated with headers from data section
        missing_headers (list):         Populated with missing data headers
        expected_data_headers (list):   Headers expected to be present in samplesheet
        sequencerid_list (list):        List of valid sequencer IDs
        panel_list (list):              List of all valid pan numbers from config
        runtype_list (list):            List of all valid runtypes from config
        tso_panel_list (list):          List of all valid TSO pannumbers from config

    Methods:
        ss_checks()
            Run checks at samplesheet and sample level
        check_ss_present()
            Checks for upload error (i.e. samplesheet for run not present)
        check_ss_name()
            Validate samplesheet names using seglh-naming Samplesheet module
        check_sequencer_id()
            Check element 2 of samplesheet (sequencer name matches list of allowed names
            in self.sequencerid_list)
        check_ss_contents()
            Check samplesheet not empty (<10 bytes)
        get_data_section()
            Parse data section of samplesheet from file
        development_run()
            Check if the run is a development run, by determining if the run contains
            any development pan numbers from the config file
        check_expected_headers()
            Check [Data] section has expected headers, against self.expected_data_headers list
        comp_samplenameid()
            Check whether names match between Sample_ID and Sample_Name in data section
            of samplesheet
        check_illegal_chars(sample, column)
            Returns true if illegal characters present
        check_sample(sample, column)
            Validate sample names using seglh-naming Sample module.
        check_pannos(sample, column, sample_obj)
            Check sample names contain allowed pan numbers from self.panel_list number list
        check_runtypes(sample, column, sample_obj)
            Check sample names contain allowed runtypes from self.runtype_list
        check_tso()
            Returns True if TSO sample
        log_summary()
            Write summary of validator outcome to log
    """

    def __init__(self, samplesheet_path: str, runfolder_name: str, logger: object):
        """
        Constructor for the SamplesheetCheck class
            :param samplesheet_path (str):  Path to samplesheet
            :param runfolder_name (str):    Name of runfolder (used for naming logfile)
        """
        self.samplesheet_path = samplesheet_path
        self.runfolder_name = runfolder_name
        self.logger = logger
        self.ss_obj = False
        self.pannumbers = []
        self.tso = False
        # Store sample IDs and sample names from samplesheet
        self.samples = defaultdict(str)
        self.errors = False  # Switches to True if samplesheet errors encountered
        self.errors_list = []
        self.data_headers = []  # Populate with headers from data section
        self.missing_headers = []  # Populate with missing headers
        self.expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        self.sequencerid_list = ad_config.SEQUENCER_IDS
        self.panel_list = panel_config.PANELS
        self.runtype_list = ad_config.RUNTYPE_LIST
        self.tso_panel_list = panel_config.TSO500_PANELS

    def ss_checks(self) -> None:
        """
        Run checks at samplesheet and sample level. Performs required extra checks for
        checks not included in seglh-naming
        """
        if self.check_ss_present():
            setattr(self, "ss_obj", self.check_ss_name())
            if self.ss_obj:
                self.check_sequencer_id()
                if self.check_ss_contents():
                    self.get_data_section()
                    if not self.development_run():
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

    def check_ss_present(self) -> Union[bool, None]:
        """
        Checks for upload error (i.e. samplesheet for run not present).
        Appends info to dict. If samplesheet present returns true, else returns
        false.
            :return True | None:    True if samplesheet exists, else None
        """
        if os.path.isfile(self.samplesheet_path):
            self.logger.info(self.logger.log_msgs["ss_present"], self.samplesheet_path)
            return True
        else:
            self.logger.warning(
                self.logger.log_msgs["ss_absent"], self.samplesheet_path
            )
            self.errors = True
            self.errors_list.append("sspresent_err")

    def check_ss_name(self) -> object:
        """
        Validate samplesheet names using seglh-naming Samplesheet module.
            :return ss_obj (obj):   seglh-naming samplesheet object
        """
        try:
            self.ss_obj = Samplesheet.from_string(self.samplesheet_path)
            self.logger.info(
                self.logger.log_msgs["ssname_valid"], self.samplesheet_path
            )
        except Exception as exception:
            self.errors = True
            self.errors_list.append("ssname_err")
            self.logger.warning(
                self.logger.log_msgs["ssname_invalid"], self.samplesheet_path, exception
            )
        return self.ss_obj

    def development_run(self) -> Union[bool, None]:
        """
        Check if the run is a development run, by de    termining if the samplesheet contains
        any development pan numbers from the config file
            :param sscheck_obj (object):    Object created by
                                            samplesheet_validator.SampleheetCheck
            :return True | None:            True if contains dev pan numbers, false if does not
        """
        strings_to_check = self.samples["Sample_ID"] + self.samples["Sample_Name"]
        for panno in panel_config.DEVELOPMENT_PANELS:
            if any(panno in sample_name for sample_name in strings_to_check):
                self.logger.warning(
                    self.logger.log_msgs["dev_run"],
                    self.samplesheet_path,
                )
                setattr(self, "development_run", True)
                return True
        else:
            self.logger.info(
                self.logger.log_msgs["not_dev_run"],
                self.samplesheet_path,
            )
            setattr(self, "development_run", False)

    def check_sequencer_id(self) -> None:
        """
        Check element 2 of samplesheet (sequencer name matches list of
        allowed names in self.sequencerid_list)
            :return None:
        """
        if self.ss_obj.sequencerid not in self.sequencerid_list:
            self.errors = True
            self.errors_list.append("sequencerid_err")
            self.logger.warning(
                self.logger.log_msgs["sequencer_id_invalid"],
                self.ss_obj,
                self.ss_obj.sequencerid,
            )
        else:
            self.logger.info(self.logger.log_msgs["sequencer_id_valid"])

    def check_ss_contents(self) -> Union[bool, None]:
        """
        Check samplesheet not empty (<10 bytes)
            :return (True | None): True if samplesheet not empty, else None
        """
        if os.stat(self.samplesheet_path).st_size < 10:
            self.logger.warning(self.logger.log_msgs["ss_empty"])
            self.errors = True
            self.errors_list.append("ssempty_err")
        else:
            self.logger.info(self.logger.log_msgs["ss_not_empty"])
            return True

    def get_data_section(self) -> None:
        """
        Parse data section of samplesheet from file. Read samplesheet in reverse order,
        collect sample ID and sample name
            :return None:
        """
        sample_ids = []
        sample_names = []
        with open(self.samplesheet_path, "r") as samplesheet_stream:
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
                        sample_id, sample_name = (
                            sample_details[0],
                            sample_details[1],
                        )

                        # Append sample id and sample name to sampleStrings
                        # for testing
                        sample_ids.append(sample_id)
                        sample_names.append(sample_name)
                    except Exception as exception:
                        self.errors = True
                        self.logger.warning(
                            self.logger.log_msgs["get_data_err"], exception
                        )
        self.samples["Sample_ID"] = sample_ids
        self.samples["Sample_Name"] = sample_names

    def check_expected_headers(self) -> None:
        """
        Check [Data] section has expected headers, against self.expected_data_headers
        list
            :return None:
        """
        if not all(
            header in self.data_headers for header in self.expected_data_headers
        ):
            self.errors = True
            self.errors_list.append("headers_err")
            self.missing_headers = list(
                set(self.expected_data_headers).difference(self.data_headers)
            )
            self.logger.warning(
                self.logger.log_msgs["headers_err"], self.missing_headers
            )
        else:
            self.logger.info(self.logger.log_msgs["headers_as_expected"])

    def comp_samplenameid(self) -> None:
        """
        Check whether names match between Sample_ID and Sample_Name in data section of
        samplesheet
            :return None:
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
        self.logger.info(self.logger.log_msgs["samplenames_match"])
        if differences:
            self.errors = True
            self.errors_list.append("samplenamematch_err")
            self.logger.warning(
                self.logger.log_msgs["nonmatching_samplenames"], differences
            )

    def check_illegal_chars(self, sample: str, column: str) -> None:
        """
        Returns true if illegal characters present
            :param sample (str): Sample name
            :param column (str): Column header
            :return None:
        """
        valid_chars = "^[A-Za-z0-9_-]+$"
        if not re.match(valid_chars, sample):
            self.errors = True
            self.errors_list.append("validchars_err")
            self.logger.warning(self.logger.log_msgs["illegal_chars"], column, sample)
        else:
            self.logger.info(self.logger.log_msgs["no_illegal_chars"], sample, column)

    def check_sample(self, sample: str, column: str) -> Union[object, None]:
        """
        Validate sample names using seglh-naming Sample module. Checks run on
        Sample_Name and Sample_ID; Sample_Name is used by bcl2fastq2 and Sample_ID is
        used if Sample_Name is not present
            :param sample (str):               Sample name
            :param column (str):               Column header
            :return sample_obj (obj):   seglh-naming sample object
        """
        try:
            sample_obj = Sample.from_string(sample)
            self.logger.info(self.logger.log_msgs["sample_name_valid"], sample, column)
            return sample_obj
        except Exception as exception:
            self.errors = True
            self.errors_list.append("samplename_err")
            self.logger.warning(
                self.logger.log_msgs["sample_name_invalid"],
                column,
                exception,
            )

    def check_pannos(self, sample: str, column: str, sample_obj: object) -> None:
        """
        Check sample names contain allowed pan numbers from self.panel_list number list
            :param sample (str):            Sample name
            :param column (str):            Column header
            :param sample_obj (object):     seglh-naming sample object
            :return None:
        """
        self.pannumbers.append(sample_obj.panelnumber)
        if sample_obj.panelnumber not in self.panel_list:
            self.errors = True
            self.errors_list.append("panno_err")
            self.logger.warning(
                self.logger.log_msgs["invalid_panno"],
                sample_obj.panelnumber,
                column,
                sample,
            )
        else:
            self.logger.info(
                self.logger.log_msgs["valid_panno"], sample_obj.panelnumber
            )

    def check_runtypes(self, sample: str, column: str, sample_obj: object) -> None:
        """
        Check sample names contain allowed runtypes from self.runtype_list
            :param sample (str):            Sample name
            :param column (str):            Column header
            :param sample_obj (object):     seglh-naming sample oject
            :return None:
        """
        # Extract first group of capitalised characters
        runtype = re.match("^[A-Z]*", sample_obj.libraryprep)
        if runtype.group(0) not in self.runtype_list:
            self.errors = True
            self.errors_list.append("runtype_err")
            self.logger.warning(self.logger.log_msgs["runtypes_err"], sample, column)
        else:
            self.logger.info(self.logger.log_msgs["valid_runtype"], runtype.group(0))

    def check_tso(self) -> None:
        """
        Returns True if TSO sample
            :return None:
        """
        if any(item in self.pannumbers for item in self.tso_panel_list):
            self.tso = True

    def log_summary(self) -> None:
        """
        Write summary of validator outcome to log
            :return None:
        """
        if self.errors:
            self.logger.warning(
                self.logger.log_msgs["sschecks_not_passed"], self.samplesheet_path
            )
        else:
            self.logger.info(
                self.logger.log_msgs["sschecks_passed"], self.samplesheet_path
            )
