# coding=utf-8
"""
Script for checking sample sheet naming and contents.

Uses the seglh-naming library. And adds further lab-specific checks e.g. whether
sequencer IDs and runtypes match those in lists of allowed IDs. Collects all errors in
an errors list (ValidSamplesheet.errors)
"""
import os
import re
from collections import defaultdict
from seglh_naming.sample import Sample
from seglh_naming.samplesheet import Samplesheet
from shared_functions.shared_functions import git_tag
import config.ad_config as ad_config
import config.panel_config as panel_config
from typing import Union


class SamplesheetCheck(object):
    """
    Runs the checks. Called by webapp for uploaded samplesheets (uses name of file being
    uploaded), and called for runs not yet demultiplexed (uses path of expected
    samplesheet from demultiplex script)

    Attributes:
        samplesheet_path (str):         Path to samplesheet
        logger (obj):                   Logger object
        ss_obj (False | obj):           seglh-naming samplesheet object
        pannumbers (list):              List of panel numbers in the sample sheet
        tso (bool):                     True if samplesheet contains any TSO samples
        samples (dict):                 Dictionary of sample IDs and sample names from
                                        the samplesheet
        errors (bool):                  True if samplesheet errors encountered, False if
                                        not
        errors_list (bool):             Stores identifiers for any types of errors
                                        encountered
        data_headers (list):            Populated with headers from data section
        missing_headers (list):         Populated with missing data headers
        expected_data_headers (list):   Headers expected to be present in samplesheet
        sequencerid_list (list):        List of valid sequencer IDs
        panel_list (list):
        runtype_list (list):
        tso_panel_list (list):

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
        check_expected_headers()
            Check [Data] section has expected headers, against
            self.expected_data_headers list
        comp_samplenameid()
            Check whether names match between Sample_ID and Sample_Name in data section
            of samplesheet
        check_illegal_chars()
            Returns true if illegal characters present
        check_sample()
            Validate sample names using seglh-naming Sample module.
        check_pannos()
            Check sample names contain allowed pan numbers from self.panel_list number
            list
        check_runtypes()
            Check sample names contain allowed runtypes from self.runtype_list
        check_tso()
            Returns True if TSO sample
    """

    def __init__(self, samplesheet_path: str, logger: object):
        """
        Constructor for the SamplesheetCheck class
            :param samplesheet_path (str):  Path to samplesheet
            :param logger (obj):            Logger object
        """
        self.samplesheet_path = samplesheet_path
        self.logger = logger
        self.ss_obj = False
        self.pannumbers = []
        self.tso = False
        self.samples = defaultdict(
            str
        )  # Store sample IDs and sample names from samplesheet
        self.errors = False  # Switches to True if samplesheet errors encountered
        self.errors_list = []
        self.data_headers = []  # Populate with headers from data section
        self.missing_headers = []  # Populate with missing headers
        self.expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        self.sequencerid_list = ad_config.SEQUENCER_IDS
        self.panel_list = panel_config.PANELS
        self.runtype_list = ad_config.RUNTYPE_LIST
        self.tso_panel_list = panel_config.TSO500_PANELS
        self.ss_checks()

    def ss_checks(self) -> None:
        """
        Run checks at samplesheet and sample level. Performs required extra checks for
        checks not included in seglh-naming
        """
        self.logger.info(
            self.logger.log_msgs["script_start"],
            git_tag(),
            "samplesheet_validator.py",
            extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
        )
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
        self.logger.info(
            self.logger.log_msgs["script_end"],
            git_tag(),
            "samplesheet_validator.py",
            extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
        )

    def check_ss_present(self) -> Union[bool, None]:
        """
        Checks for upload error (i.e. samplesheet for run not present).
        Appends info to dict. If samplesheet present returns true, else returns
        false.
            :return True | None:    True if samplesheet exists, else None
        """
        if os.path.isfile(self.samplesheet_path):
            self.logger.info(
                self.logger.log_msgs["ss_present"],
                self.samplesheet_path,
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )
            return True
        else:
            self.logger.error(
                self.logger.log_msgs["ss_absent"],
                self.samplesheet_path,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
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
                self.logger.log_msgs["ssname_valid"],
                self.samplesheet_path,
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )
        except Exception as exception:
            self.errors = True
            self.errors_list.append("ssname_err")
            self.logger.error(
                self.logger.log_msgs["ssname_invalid"],
                self.samplesheet_path,
                exception,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
        return self.ss_obj

    def check_sequencer_id(self) -> None:
        """
        Check element 2 of samplesheet (sequencer name matches list of
        allowed names in self.sequencerid_list)
            :return None:
        """
        if self.ss_obj.sequencerid not in self.sequencerid_list:
            self.errors = True
            self.errors_list.append("sequencerid_err")
            self.logger.error(
                self.logger.log_msgs["sequencer_id_invalid"],
                self.ss_obj, self.ss_obj.sequencerid,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
        else:
            self.logger.info(
                self.logger.log_msgs["sequencer_id_valid"],
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )

    def check_ss_contents(self) -> Union[bool, None]:
        """
        Check samplesheet not empty (<10 bytes)
            :return (True | None): True if samplesheet not empty, else None
        """
        if os.stat(self.samplesheet_path).st_size > 10:
            self.logger.info(
                self.logger.log_msgs["ss_not_empty"],
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )
            return True
        else:
            self.logger.error(
                self.logger.log_msgs["ss_empty"],
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
            self.errors = True
            self.errors_list.append("ssempty_err")

    def get_data_section(self) -> None:
        """
        Parse data section of samplesheet from file. Read samplesheet in reverse order,
        collect sample ID and sample name
            :return None:
        """
        sample_ids = []
        sample_names = []
        with open(self.samplesheet_path, "r", encoding="utf-8") as samplesheet_stream:
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
                        self.logger.error(
                            self.logger.log_msgs["get_data_err"],
                            exception,
                            extra={
                                "flag": self.logger.log_flags["ss_warning"] % "ssvalidator"
                                },
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
            self.logger.error(
                self.logger.log_msgs["headers_err"],
                self.missing_headers,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
        else:
            self.logger.info(
                self.logger.log_msgs["headers_as_expected"],
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )

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
        self.logger.info(
            self.logger.log_msgs["samplenames_match"],
            extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
        )
        if differences:
            self.errors = True
            self.errors_list.append("samplenamematch_err")
            self.logger.error(
                self.logger.log_msgs["nonmatching_samplenames"],
                differences,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
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
            self.logger.error(
                self.logger.log_msgs["illegal_chars"],
                column, sample,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
        else:
            self.logger.info(
                self.logger.log_msgs["no_illegal_chars"],
                sample, column,
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )

    def check_sample(self, sample: str, column: str) -> Union[object, None]:
        """
        Validate sample names using seglh-naming Sample module. Checks run on
        Sample_Name and Sample_ID; Sample_Name is used by bcl2fastq and Sample_ID is
        used if Sample_Name is not present
            :param sample (str):               Sample name
            :param column (str):               Column header
            :return sample_obj (obj) | None:   seglh-naming sample object
        """
        try:
            sample_obj = Sample.from_string(sample)
            self.logger.info(
                self.logger.log_msgs["sample_name_valid"],
                sample, column,
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )
            return sample_obj
        except Exception as exception:
            self.errors = True
            self.errors_list.append("samplename_err")
            self.logger.error(
                self.logger.log_msgs["sample_name_invalid"],
                column,
                exception,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
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
            self.logger.error(
                self.logger.log_msgs["invalid_panno"],
                sample_obj.panelnumber,
                column,
                sample,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
        else:
            self.logger.info(
                self.logger.log_msgs["valid_panno"],
                sample_obj.panelnumber,
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
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
            self.logger.error(
                self.logger.log_msgs["runtypes_err"],
                sample,
                column,
                extra={"flag": self.logger.log_flags["ss_warning"] % "ssvalidator"},
            )
        else:
            self.logger.info(
                self.logger.log_msgs["valid_runtype"],
                runtype.group(0),
                extra={"flag": self.logger.log_flags["info"] % "ssvalidator"},
            )

    def check_tso(self) -> None:
        """
        Returns True if TSO sample
            :return None:
        """
        if any(item in self.pannumbers for item in self.tso_panel_list):
            self.tso = True
