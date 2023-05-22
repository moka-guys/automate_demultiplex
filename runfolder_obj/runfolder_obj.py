# coding=utf-8
""" runfolder_obj.py

This module creates an object with runfolder specific properties
"""
import os
import re
import config.ad_config as ad_config
import config.panel_config as panel_config


# TODO correct documentation
# TODO make this runnable on the command line
class RunfolderObject(object):
    """
    An object with runfolder-specific properties.

    Args:
        runfolder_name (str):   Runfolder name string
        timestamp (str):        Timetamp in the format
                                str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
    """

    def __init__(self, runfolder_name, timestamp):
        """"""
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token

        self.timestamp = timestamp
        self.runfolder_name = runfolder_name
        self.runfolderpath = os.path.join(ad_config.RUNFOLDERS, self.runfolder_name)
        self.samplesheet_name = ad_config.SAMPLESHEET_NAME % self.runfolder_name
        # Stored within runfolder
        # Sequencing finished file (within runfolder)
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["rtacomplete"]
        )
        # Samplesheet (within runfolder)
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        # Integrity check file (within runfolder)
        self.checksumfile_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["md5checksum"]
        )
        # Bcl2fastq log file (within runfolder)
        self.bcl2fastqlog_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["bcl2fastqlog"]
        )
        # Runfolder fastq folder (within runfolder)
        self.fastq_dir_path = os.path.join(self.runfolderpath, ad_config.DIRS["fastqs"])
        # Upload agent logfile (within runfolder)
        self.upload_agent_logfile = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["upload_started"]
        )
        # Bcl2fastq stats file (within runfolder)
        self.bcl2fastqstats_file = os.path.join(
            self.runfolderpath,
            ad_config.DIRS["bcl2fastq_stats"],
            ad_config.FILENAMES["bcl2fastq_stats"],
        )

        # Stored within samplesheets dir
        # Samplesheet (samplesheets dir)
        self.samplesheet_path = ad_config.SAMPLESHEET_PATH % self.runfolder_name

        # Stored within logfiles dir
        # Workflow dx run commands for runfolder (within logfiles dir)
        self.runfolder_dx_run_script = (
            ad_config.LOGFILES["dx_run_script"] % self.runfolder_name
        )
        # Congenica upload commands for runfolder (within logfiles dir)
        self.congenica_dx_run_script = (
            ad_config.LOGFILES["congenica_upload_script"] % self.runfolder_name
        )
        # Dnanexus project creation bash script (within logfiles dir)
        self.project_creation_logfile = (
            ad_config.LOGFILES["proj_creation_script"] % self.runfolder_name
        )
        # Backup runfolder logfile (within logfiles dir)
        self.backup_runfolder_logfile = (
            ad_config.LOGFILES["backup_runfolder"] % self.runfolder_name
        )
        # Logfiles that contain timestamps - uses get_scriptlog() to search
        # for existing logfile containing runfolder name

        # Logfile to contain runfolder upload log
        self.upload_runfolder_logfile = self.get_runfolder_logs(
            ad_config.LOGDIRS["upload_script"],
            ad_config.LOGFILES["upload_script"]
            % f"{self.timestamp}_{self.runfolder_name}",
        )
        # Logfile to contain runfolder demultiplex log
        self.demultiplex_runfolder_logfile = self.get_runfolder_logs(
            ad_config.LOGDIRS["demultiplex"],
            ad_config.LOGFILES["demultiplex_script_logfile"]
            % f"{self.timestamp}_{self.runfolder_name}",
        )
        self.cluster_density_files = [
            (
                f"{self.runfolderpath}{self.runfolder_name}"
                f"{ad_config.CLUSTER_DENSITY_FILE_SUFFIX}"
            ),
            (
                f"{self.runfolderpath}{self.runfolder_name}"
                f"{ad_config.PHASING_METRICS_FILE_SUFFIX}"
            ),
        ]
        self.logfiles_to_upload = [self.loggers.logfiles_config.values()].append(
            self.runfolder_obj.bcl2fastqlog_path
        )

    def get_runfolder_logs(self, directory, logfile):
        """
        Find the the logfile for the runfolder. Logfile contains an unknown
        timestamp. Search for any demultiplex logfiles matching the runfolder
        name and return the first
        If none exist, get the logfile from before it is renamed with
        processed runfolders
        """
        any_logs = [
            os.path.join(directory, filename)
            for filename in os.listdir(directory)
            if self.runfolder_name in filename
        ]
        logfile = any_logs.pop() if any_logs else logfile
        return logfile

    def get_samples(self):
        """
        Call get_pipeline and get_samples_dict methods to add pipeline string
        and samples_dict attributes to class
        """
        setattr(self, "pipeline", self.get_pipeline())
        setattr(self, "samples_dict", self.get_samples_dict())
        if self.pipeline != "tso500":
            # tso500 run is not demultiplexed locally so there are no fastqs
            # All other runfolders have fastqs in the BaseCalls directory
            # Check fastqs in fastq dir were correctly identified from the
            # samplesheet, and add any missing samples to the samples dict
            self.check_fastqs()
        setattr(self, "fastqs_list", {**self.samples_dict.items()}["fastqs"])
        setattr(self, "batch_numbers_str", self.capture_library_batch_numbers())
        self.get_nexus_paths()

    def get_nexus_paths(self):
        """
        Build nexus paths, using NGS run numbers (and batch numbers in the case of WES)
        """
        if self.pipeline == "tso500":
            fastq_type = "tso_fastqs"
        else:
            fastq_type = "fastqs"

        setattr(
            self,
            "nexus_fastqs_dir",
            (
                f"{self.runfolder_obj.runfolder_name}_"
                f"{self.rf_obj.batch_numbers_str}/{ad_config.DIRS[fastq_type]}"
            ),
        )
        setattr(
            self,
            "nexus_runfolder_name",
            (
                f"{self.runfolder_obj.runfolder_name}_"
                f"{self.rf_obj.batch_numbers_str}"
            ),
        )
        setattr(
            self,
            "nexus_proj_name",
            f"{ad_config.DNANEXUS_PROJECT_PREFIX}{self.nexus_runfolder_name}",
        )
        setattr(self, "nexus_proj_root", f"{self.nexus_proj_name}:/")
        setattr(
            self,
            "nexus_runfolder_subdir",
            f"{self.nexus_proj_root}{self.nexus_proj_name}",
        )
        setattr(self, "dnanexus_logfiles_dir", f"/{self.nexus_proj_name}/Logfiles/")

    def get_upload_cmds(self):
        """
        Cluster density and bcl2fastq stats json files required to be uploaded
        before the rest of the runfolder to ensure they are included in the
        MultiQC report. The 'restart_ua_2' part of the command means the
        command repeats until it exits with exit code 0 (success)
        """
        setattr(
            self,
            "fastq_upload_command",
            (
                f"{ad_config.UPLOAD_ARGS['restart_ua_1']}"
                f"{ad_config.EXECUTABLES['upload_agent']} "
                f"--auth-token {self.dnanexus_apikey} "
                f"--project {self.runfolder_obj.nexus_project_name} "
                f"--folder /{self.runfolder_obj.nexus_fastqs_dir} "
                "--do-not-compress --upload-threads 10 "
                f"{self.fastqs_str}{ad_config.UPLOAD_ARGS['restart_ua_2']}"
            ),
        )
        # TODO this might not be uploading to the correct folder (!!)
        setattr(
            self,
            "rf_samplesheet_upload_command",
            (
                f"{ad_config.UPLOAD_ARGS['restart_ua_1']}"
                f"{ad_config.EXECUTABLES['upload_agent']} "
                f"--auth-token {self.dnanexus_apikey} "
                f"--project {self.runfolder_obj.nexus_project_name} "
                f"--folder /{self.runfolder_obj.nexus_fastqs_dir} "
                "--do-not-compress --upload-threads 10 "
                f"{self.runfolder_samplesheet_path}"
                f"{ad_config.UPLOAD_ARGS['restart_ua_2']}"
            ),
        )
        setattr(
            self,
            "cd_upload_cmd",
            (
                f"{ad_config.UPLOAD_ARGS['restart_ua_1']}"
                f"{ad_config.EXECUTABLES['upload_agent']} "
                f"--auth-token {self.dnanexus_apikey} "
                f"--project {self.runfolder_obj.nexus_project_name} "
                "--folder /QC --do-not-compress --upload-threads 1 "
                f"{' '.join(self.runfolder_obj.cluster_density_files)}"
                f"{ad_config.UPLOAD_ARGS['restart_ua_2']}"
            ),
        )
        setattr(
            self,
            "bcl2fastq_qc_upload_cmd",
            (
                ad_config.UPLOAD_ARGS["restart_ua_1"]
                + ad_config.EXECUTABLES["upload_agent"]
                + " --auth-token "
                + self.dnanexus_apikey
                + " --project "
                + self.runfolder_obj.nexus_project_name
                + f" --folder /{self.runfolder_obj.nexus_fastqs_dir}/Stats"
                + " --do-not-compress --upload-threads 1 "
                + " ".join(self.runfolder_obj.bcl2fastqstats_file)
                + ad_config.UPLOAD_ARGS["restart_ua_2"]
            ),
        )
        setattr(
            self,
            "logfiles_upload_cmd",
            (
                f"{ad_config.EXECUTABLES['upload_agent']} "
                f"--auth-token {self.dnanexus_apikey} "
                f"--project {self.runfolder_obj.nexus_project_name} "
                f"--folder {self.dnanexus_logfiles_dir} "
                f"--do-not-compress {' '.join(self.logfiles_to_upload)}"
            ),
        )

    def capture_library_batch_numbers(self):
        """
        Input = list of samples to be processed
        DNANexus project names are the runfolder suffixed with identifiers
        This function parses samplenames and identifies the library prep
        numbers, identified as the first element in the sample name (before
        the first underscore)
        It also identifies the WES batch numbers from the samplenames

        If no library prep numbers are found, raise error
        Returns = unique library batch numbers (str) or None
        """
        batch_numbers_list = []
        wes_batch_numbers_list = []

        for fastq in self.fastqs_list:
            # Identify library batch numbers
            if "_" in fastq:  # Check there are underscores present
                # Split on underscores to capture library_batch number.
                # eg ONC100 or NGS100
                batch_numbers_list.append(fastq.split("_")[0])
            if "WES" in fastq:
                # Capture WES batch (WES followed by digits)
                # Optional underscore ensures this will capture WES5 or WES_5
                wesbatch = re.search(r"WES_?\d+", fastq).group()
                wes_batch_numbers_list.append(wesbatch.replace("_", ""))

        # There should always be library batch numbers found - raise error
        # if not
        if batch_numbers_list:
            batch_numbers_str = "_".join(set(batch_numbers_list))

            if wes_batch_numbers_list:
                batch_numbers_str = "_".join(
                    batch_numbers_str, set(wes_batch_numbers_list)
                )
            return batch_numbers_str

        else:  # Prompt a slack alert
            self.loggers.usw_rf.exception(
                self.loggers.msgs["rf_obj"]["library_batch_no_err"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
            raise Exception  # Stop script

    def get_pipeline(self):
        """"""
        pipelines_list = set(key["pipeline"] for key in self.sample_dict.items())
        if len(pipelines_list) > 1:
            self.loggers.usw_rf.error(
                self.loggers.msgs["rf_obj"]["multiple_pipeline_names"],
                pipelines_list,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
        # Get pipeline from pipelines_list
        return max(set(pipelines_list), key=pipelines_list.count)

    def get_samples_dict(self):
        """
        Read samplesheet to create a list of samples
        Use this to create a SampleObject for each sample which returns a
        sample dictionary containing the sample_name, pannum, panel_settings
        and fastqs paths for that sample
        Add each SampleObject to a larger samples_dict
        Return samples_dict
        """
        samples_dict = {}
        with open(
            self.runfolder_obj.samplesheet_path, "r", encoding="utf-8"
        ) as samplesheet_stream:
            # Read file into list and loop through list in reverse
            # Allows us to access sample names and stop at column headers,
            # skipping file header
            for line in reversed(samplesheet_stream.readlines()):
                if line.startswith("Sample_ID") or "[Data]" in line:
                    break
                # Skip empty lines (check first element of the line, after
                # splitting on comma)
                elif len(line.split(",")[0]) < 2:
                    pass
                else:  # If it's a line detailing a sample
                    sample_name = line.split(",")[0]
                    samples_dict[sample_name] = SampleObject(
                        sample_name
                    ).return_sample_dict
        if samples_dict.keys():  # If samples identified
            # Create file - takes long time before upload creates file to stop
            # further processing
            open(self.loggers.upload_agent.filepath, "w", encoding="utf-8").close()
        return samples_dict

    def check_fastqs(self):
        """
        Check all fastqs in fastq dir were correctly identified from the
        samplesheet and stored in the sample dict, and add any missing samples
        to the samples dict

        Loops through all the files in the given folder
        Identifies if each file is a fastq
        # Returns = a tuple of list of processed samples and string of fastq
        # filepaths.
        """
        for fastq_dir_file in os.listdir(self.runfolder_obj.fastq_dir_path):
            if fastq_dir_file.endswith("fastq.gz"):
                self.loggers.usw_rf.info(
                    self.loggers.msgs["rf_obj"]["fastq_identified"],
                    fastq_dir_file,
                    extra={"flag": self.loggers.log_flags["usw"]["info"]},
                )
                if not (
                    self.check_undetermined(fastq_dir_file)
                    or self.check_miseq(fastq_dir_file)
                ):
                    # Check if fastq matches a sample in the sample_dict
                    # If not add to sample_dict
                    for key in self.sample_dict.keys():
                        if key in fastq_dir_file:
                            self.loggers.usw_rf.info(
                                self.loggers.msgs["usw"]["sample_match"],
                                key,
                                fastq_dir_file,
                                extra={"flag": self.loggers.log_flags["usw"]["info"]},
                            )
                        else:
                            self.loggers.usw_rf.info(
                                self.loggers.msgs["usw"]["sample_mismatch"],
                                key,
                                extra={"flag": self.loggers.log_flags["usw"]["error"]},
                            )
                            sample_name = re.sub(
                                "R[0-9]_001.fastq.gz", "", fastq_dir_file
                            )
                            # Add the sample to the sample_obj
                            self.samples_dict[sample_name] = SampleObject(
                                sample_name, self.runfolder_obj
                            ).return_sample_dict()
            else:
                self.loggers.usw_rf.info(
                    self.loggers.msgs["rf_obj"]["sample_mismatch"],
                    key,
                    extra={"flag": self.loggers.log_flags["usw"]["error"]},
                )

    def check_undetermined(self, fastq_dir_file):
        """"""
        # Exclude undetermined
        if fastq_dir_file.startswith("Undetermined"):
            self.loggers.usw_rf.info(
                self.loggers.msgs["rf_obj"]["undetermined_identified"],
                fastq_dir_file,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return True

    def check_miseq(self, fastq_dir_file):
        """"""
        # Exclude any fastqs created by miseq (seperated by "-"
        # rather than "_")
        if "-Pan" not in fastq_dir_file:
            self.loggers.usw_rf.info(
                self.loggers.msgs["rf_obj"]["miseq_fastq_identified"],
                fastq_dir_file,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return True


# TODO make this runnable on the command line
# TODO see if this can be used by the other scripts
class SampleObject:
    """"""

    def __init__(self, sample_name, runfolder_obj):
        """"""
        # TODO maybe add all these attrs into return_sample_dict ??
        self.runfolder_obj = runfolder_obj
        # Samplename is used to assign read groups in BWA or as an input to sentieon
        self.sample_name = sample_name
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["sample"],
            self.panel_settings['panel_name'],
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        self.negative_control = self.check_negative_control()
        self.workflow_name = self.get_workflow_name(self.pipeline)
        self.pannum = self.find_pannum(sample_name)
        self.panel_settings = panel_config.PANEL_DICT[self.pannum]
        self.fastqs_dict = self.get_rf_fastqs()
        self.fastqs_str = " ".join([v['path'] for k, v in self.fastqs_dict.items()])
        self.identifiers = self.get_identifiers()
        self.query = self.get_sample_query()

    def check_negative_control(self):
        """
        Determine whether sample is a negative control
        """
        if "NTCcon" in self.sample_name:
            return True
        else:
            return False

    def find_pannum(self, sample_name):
        pannum = re.search(r"Pan\d+", sample_name)
        if pannum:
            self.validate_pannum(pannum)
            return pannum
        else:
            self.loggers.usw_rf.error(
                self.loggers.msgs["rf_obj"]["unrecognised_panno"],
                sample_name,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
            return False

    def validate_pannum(self, pannum):
        """
        Check whether pan number is valid
        """
        if pannum in ad_config.PANELS:
            self.loggers.usw_rf.info(
                self.loggers.msgs["rf_obj"]["recognised_panno"],
                self.sample_name,
                self.pannum,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
        else:
            self.loggers.usw_rf.error(
                self.loggers.msgs["rf_obj"]["unrecognised_panno"],
                self.sample_name,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )

    def get_rf_fastqs(self):
        """
        tso500 run is not demultiplexed locally so there are no fastqs
        All other runfolders have fastqs in the BaseCalls directory
        """
        rf_fastqs_dict = {}

        for read in ["R1", "R2"]:
            nexus_path = os.path.join(
                    f"{self.runfolder_obj.nexus_project_name}:/",
                    self.runfolder_obj.nexus_fastqs_dir,
                    f"{self.sample_name}_{read}.fastq.gz"
                )
            if self.panel_settings["pipeline"] == "tso500":
                rf_fastqs_dict[read] = {
                    "name": None,
                    "path": None,
                    "nexus_path": nexus_path,
                }
            else:
                rf_fastqs_dict[read] = {
                    "name": f"{self.sample_name}_{read}.fastq.gz",
                    "path": os.path.join(
                        self.runfolder_obj.fastq_dir_path, rf_fastqs_dict[read]['name']
                        ),
                    "nexus_path": nexus_path,
                }
        return rf_fastqs_dict

    def return_sample_dict(self):
        """"""
        return {
            "sample_name": self.sample_name,
            "negative_control": self.negative_control,
            "identifiers": self.identifiers,
            "pannum": self.pannum,
            "panel_settings": self.panel_settings,
            "fastqs": self.fastqs,
            "SQL_query": self.sql_query,
            "pipeline_sample_cmd": self.sample_pipeline_cmd,
            "congenica_upload_cmd": self.congenica_upload_cmd,
        }

    def requires_processing(self):
        """
        Input = None
        This method calls other methods in order
        Returns = True if runfolder requires processing
        """
        # Check if already uploaded and demultiplexing finished sucessfully
        if self.already_uploaded() and self.has_demultiplexed():
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["runfolder_prev_proc"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return False
        else:
            return True

    def already_uploaded(self):
        """
        Input = None
        Upload agent stdout is written to a file, indicating that the runfolder
        has been processed.
        This function checks for presense of this file
        Returns = Boolean (True/False)
        """
        if os.path.isfile(self.F.upload_agent_logfile):
            self.loggers.usw_script.info(
                self.loggers.msgs["usw"]["ua_file_present"],
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return True
        else:
            # If file doesn't exist return false to continue, write to log file
            self.loggers.usw_script.info(
                self.loggers.msgs["usw"]["ua_file_absent"],
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return False

    def has_demultiplexed(self):
        """
        Input = None
        Check if demultiplexing has been performed and completed sucessfully.
        The demultiplexing script will raise any alerts if issues are found
        with demultiplexing, but we also need to prevent further processing
        of the run.
        Checks the demultiplex log file exists, and if present, checks the
        expected success string is in the last line of the log file.
        Returns = Boolean (True/False)
        """
        # Check demultiplexing log file exists
        if os.path.isfile(self.runfolder_obj.bcl2fastqlog_path):
            with open(
                self.runfolder_obj.bcl2fastqlog_path, "r", encoding="utf-8"
            ) as logfile:
                # Capture logfile into list (not doing this caused an issue
                # with the if loop below)
                logfile_list = logfile.readlines()
                if re.search(
                    ad_config.DEMULTIPLEXLOG_TSO500MSG, logfile_list[-1]
                ):  # Check if tso500 run
                    self.loggers.usw_rf.info(
                        self.loggers.msgs["usw"]["tso_run"],
                        extra={"flag": self.loggers.log_flags["usw"]["info"]},
                    )
                    return True
                # Check if successful demuliplex statement in last line of log
                elif re.search(ad_config.DEMULTIPLEX_SUCCESS_REGEX, logfile_list[-1]):
                    self.loggers.usw_rf.info(
                        self.loggers.msgs["usw"]["demux_complete"],
                        extra={"flag": self.loggers.log_flags["usw"]["info"]},
                    )
                    return True
                else:
                    # Write to logfile that demultplex was not successful
                    self.loggers.usw_rf.info(
                        self.loggers.msgs["usw"]["demux_failed"],
                        extra={"flag": self.loggers.log_flags["usw"]["info"]},
                    )
                    return False
        else:
            # Write to logfile that not yet demultiplexed
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["not_yet_demultiplexed"],
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return False

    def get_identifiers(self):
        """
        For WES and PIPE samples, extract DNA number from sample name.
        For oncology samples, collect 3rd and 4th identifiers, setting id2 to null if
        the sample is a negative control (these only have one identifier)
        """

        if self.pipeline in ("wes", "pipe"):
            # Extract the dna number from sample name
            id1 = self.sample_name.split("_")[2]
            id2 = False
        elif self.pipeline in ("tso500", "archerdx", "amp"):
            # Collect 3rd and 4th elements (identifiers)
            id1, id2 = self.sample_name.split("_")[2:4]
            # negative controls only have one ID so set id2 to null
            if self.negative_control:
                id2 = "NULL"
        return id1, id2

    def get_sample_query(self):
        """
        Call functions to construct query for the sample
        """
        if self.pipeline in ("pipe", "snp"):
            # TODO refactor below function
            query = self.return_rd_query()
        elif self.pipeline in ("tso500", "archerdx", "amp"):
            # TODO refactor below function
            query = self.return_oncology_query()
        elif self.pipeline in "wes":
            # This query is constructed at the runfolder level, not the sample level
            query = False
        return query

    def return_rd_query(self):
        """
        Create a query per sample using the dna number
        """
        pipeline_version = str(ad_config.SQL_IDS["WORKFLOWS"][self.pipeline])
        query = ad_config.QUERIES["customrun"] % (
            f"'{self.identifiers[0]}','{pipeline_version}',"
            f"'{self.runfolder_obj.runfolder_name}'"
        )
        return query

    def return_oncology_query(self, pannumber):
        """
        Create a query per sample using IDs from the samplename (3rd and 4th)
        elements. These are recorded along with the pipeline version, name of
        the run, and panel ID.
        """
        pipeline_version = str(ad_config.SQL_IDS["WORKFLOWS"][self.pipeline])
        panel_id = self.pannum.replace("Pan", "")

        query = (
            ad_config.QUERIES["oncology"]
            % (
                f"'{self.identifiers[0]}','{self.identifiers[1]}',"
                f"'{self.runfolder_obj.runfolder_name}',"
                f"'{pipeline_version}','{panel_id}'"
            ),
        )
        return query

    def get_workflow_name(self, workflow_name):
        """"""
        if self.pipeline == "tso500":
            out, _ = self.execute_subprocess_command(
                        f"dx describe {ad_config.NEXUS_IDS['APPS'][workflow_name]} "
                        "--json | jq -r '(.name)'"
                    )
        else:
            out, _ = self.execute_subprocess_command(
                "dx describe "
                f"{ad_config.NEXUS_IDS['WORKFLOWS'][workflow_name]} "
                "--json | jq -r '\"\(.folder)/\(.name)\"'"
            )
        return out

    def build_dx_run_cmd(self):
        """
        Build sample-level dx run commands
        """
        if self.pipeline == "wes":
            workflow_cmd = self.create_wes_cmd()
            congenica_cmd = self.self.return_congenica_cmd()
        elif self.pipeline == "pipe":
            workflow_cmd = self.create_pipe_cmd()
            congenica_cmd = self.return_congenica_cmd()
        elif self.pipeline == "amp":
            workflow_cmd = self.create_amp_cmd()
            congenica_cmd = False
        elif self.pipeline == "snp":
            workflow_cmd = self.create_snp_cmd()
            congenica_cmd = False
        elif self.pipeline == "archerdx":
            workflow_cmd = self.create_fastqc_cmd()
            congenica_cmd = False
        elif self.pipeline == "tso500":
            # TSO pipeline command is built at the whole run level
            workflow_cmd = False
            congenica_cmd = False

        setattr(self, 'sample_pipeline_cmd', workflow_cmd)
        setattr(self, 'congenica_upload_cmd', congenica_cmd)

    def return_congenica_cmd(self):
        """
        If sample requires congenica upload, there are 2 methods
        If a project id is specified in the ad_config it means it can be uploaded using
        the upload agent and does not need any patient specific info to be pre-added
        into Congenica by the scientists. Otherwise, if the congenica project is not
        set, it should be uploaded via the SFTP
        """
        # write to logger to create slack alert that there are some
        # congenica files to upload
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["congenica_upload_required"],
            self.runfolder_obj.nexus_project_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Check if reference ids (flanked by underscores) present in fastq
        # name. If so, skip step
        for ref_sample_id in ad_config.REF_SAMPLE_IDS:
            if f"_{ref_sample_id}_" in self.sample_name:
                self.loggers.usw_rf.info(
                    self.loggers.msgs["usw"]["reference_sample"],
                    self.sample_name,
                    extra={"flag": self.loggers.log_flags["usw"]["info"]},
                )
                return None

        # If project is specified then upload via upload agent
        if self.panel_settings["congenica_project"]:
            # Upload via upload agent
            return self.build_congenica_cmd()
        else:  # Upload via SFTP
            return self.build_congenica_sftp_cmd()

    def build_congenica_cmd(self):
        """
        The import congenica app takes inputs in the format jobid.outputname
        which ensures the job doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called
        immediately before this job, and the output is captures into the
        variable $analysisid
        The panel dictionary in the ad_config file is used to determine the
        congenica project, IR template and credentials file
        This command is appended to a file which will be run after the QC is
        passed.
        Returns = dx run command for congenica import app (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "congenica",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        dx_command = (
            ad_config.DX_RUN_CMDS["congenica_app"]
            + f"congenica_{self.sample_name}"
            + " -icongenica_project="
            + str(self.panel_settings["congenica_project"])
            + " -icredentials="
            + self.panel_settings["congenica_credentials"]
            + " -iIR_template="
            + self.panel_settings["congenica_IR_template"]
            + ad_config.APP_INPUTS["congenica_upload"]["samplename"]
            + self.sample_name
            + self.dest_str
            + self.runfolder_obj.nexus_proj_root
            + (ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey).replace(
                ")", "' >> " f"{self.runfolder_obj.congenica_dx_run_script}"
            )
        )
        return dx_command

    def build_congenica_sftp_cmd(self):
        """
        Input = R1 fastq file name
        The import congenica SFTP app takes inputs in the format
        jobid.outputname which ensures job doesn't run until the vcfs have been
        created.
        These inputs are created by a python script, which is called
        immediately before this job, and the output is captures into the
        variable $analysisid
        Upload via SFTP only required the bam and vcf inputs, and does not need
        projectids, IR templates or names
        This command is appended to a file which will be run after the QC is
        passed.
        Returns = dx run command for congenica import app (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "congenica sftp",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        dx_command = (
            ad_config.DX_RUN_CMDS["congenica_sftp"]
            + f"congenica_SFTP_upload_{self.sample_name}"
            + self.dest_str
            + self.runfolder_obj.nexus_proj_root
            + (ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey).replace(
                ")", "' >> " f"{self.runfolder_obj.congenica_dx_run_script}"
            )
        )
        return dx_command

    def create_wes_cmd(self):
        """
        Returns = dx run command for MokaWES workflow (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "WES",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        # Create the MokaWES dx command
        dx_command_list = [
            ad_config.DX_RUN_CMDS["mokawes"],
            self.sample_name,
            ad_config.STAGE_INPUTS["mokawes"]["fastqc1_reads"],
            self.fastqs_dict["R1"],
            ad_config.STAGE_INPUTS["mokawes"]["fastqc2_reads"],
            self.fastqs_dict["R2"],
            ad_config.STAGE_INPUTS["mokawes"]["sentieon_samplename"],
            self.sample_name,
            ad_config.STAGE_INPUTS["mokawes"]["picard_bed"],
            self.panel_settings["hsmetrics_bedfile"],
            ad_config.STAGE_INPUTS["mokawes"]["sambamba_bed"],
            self.panel_settings['sambamba_bedfile'],
            self.dest_str,
            self.runfolder_obj.nexus_proj_root,
            self.token,
        ]

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_pipe_cmd(self):
        """
        Returns =  dx run command for pipe workflow (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "PIPE",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        # Congenica requires variant calling to be restricted in the pipeline,
        # in some cases to prevent incidental findings
        # The variant caller pads bed files by 100bp by default so this may
        # need to be overruled.
        # The panel dictionary default is to give a value of 0, which turns off
        # this padding.
        # An example of the use of this is for STG BrCa who require padding of
        # +/- 11bp (bed files are padded +/-10bp) so 1bp padding is applied.
        pipe_padding_cmd = ad_config.STAGE_INPUTS["pipe"]["gatk_padding"] + str(
            panel_config.PIPE_HAPLOTYPE_CALLER_PADDING
        )

        # if sample is not NA12878 we want to skip the vcfeval stage (the app
        # default is skip=false)
        # assume it's not a NA12878 sample, and set skip = true
        vcf_eval_skip_string = f'{ad_config.STAGE_INPUTS["pipe"]["happy_skip"]}true'
        # set the prefix as the samplename
        vcf_eval_prefix_string = (
            f'{ad_config.STAGE_INPUTS["pipe"]["happy_prefix"]}{self.sample_name}'
        )
        # identify NA12878 samples by checking if any reference ids (flanked by
        # underscores) are present in the fastq name
        # if so, set skip = false
        for ref_sample_id in ad_config.REF_SAMPLE_IDS:
            if f"_{ref_sample_id}_" in self.sample_name:
                vcf_eval_skip_string = (
                    f'{ad_config.STAGE_INPUTS["pipe"]["happy_skip"]}false'
                )

        # Set parameters specific to FH_PRS app

        # TODO think I can get rid of this and access through the sample dict
        if self.panel_settings["FH"]:
            # If sample is R134 we want app to run - set skip to false
            # Specify instance type for human exome app and specify output as
            # both vcf and gvcf
            fh_prs_cmd_string = (
                f"{ad_config.STAGE_INPUTS['pipe']['fhprs_skip']} "
                f"--instance-type "
                f"{ad_config.NEXUS_IDS['STAGES']['pipe']['gatk']}="
                f"{ad_config.STAGE_INPUTS['pipe']['fhprs_instance']}"
                f"{ad_config.STAGE_INPUTS['pipe']['gatk_vcf_format']}"
                f"{ad_config.PIPE_FH_GATK_TIMEOUT_ARGS}"
            )
        else:
            fh_prs_cmd_string = ""

        # Set parameters specific to polyedge app
        polyedge_cmd_string = ""

        # If test contains polyedge, we want app to run
        if self.panel_settings["polyedge"]:
            polyedge_cmd_string += (
                ad_config.STAGE_INPUTS["pipe"]["polyedge_gene"]
                + self.panel_settings["polyedge"]["gene"]
                + ad_config.STAGE_INPUTS["pipe"]["polyedge_chrom"]
                + str(self.panel_settings["polyedge"]["chrom"])
                + ad_config.STAGE_INPUTS["pipe"]["polyedge_poly_start"]
                + str(self.panel_settings["polyedge"]["poly_start"])
                + ad_config.STAGE_INPUTS["pipe"]["polyedge_poly_end"]
                + str(self.panel_settings["polyedge"]["poly_end"])
                + ad_config.STAGE_INPUTS["pipe"]["polyedge_skip"]
            )

        masked_reference_command = ""
        if self.panel_settings["masked_reference"]:
            masked_reference_command += (
                f"{ad_config.STAGE_INPUTS['pipe']['bwa_ref']}"
                f"{self.panel_settings['masked_reference']}"
            )
        # Create the dx command
        dx_command = (
            ad_config.DX_RUN_CMDS["pipe"]
            + self.sample_name,
            + ad_config.STAGE_INPUTS["pipe"]["fastqc_reads"]
            + self.fastqs_dict["R1"],
            + ad_config.STAGE_INPUTS["pipe"]["fastqc_reads"]
            + self.fastqs_dict["R2"]
            + ad_config.STAGE_INPUTS["pipe"]["bwa_reads1"]
            + self.fastqs_dict["R1"]
            + ad_config.STAGE_INPUTS["pipe"]["bwa_reads2"]
            + self.fastqs_dict["R2"]
            + ad_config.STAGE_INPUTS["pipe"]["bwa_rg_sample"]
            + self.sample_name
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_bed"]
            + self.panel_settings['sambamba_bedfile']
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_min_base_qual"]
            + str(self.panel_settings["coverage_min_basecall_qual"])
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_min_mapping_qual"]
            + str(self.panel_settings["coverage_min_mapping_qual"])
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_cov_level"]
            + str(self.panel_settings["clinical_coverage_depth"])
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_filter_cmds"]
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_excl_dups"]
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_excl_failed_qual"]
            + ad_config.STAGE_INPUTS["pipe"]["sambamba_count_overl_mates"]
            + vcf_eval_skip_string
            + vcf_eval_prefix_string
            + fh_prs_cmd_string
            # TODO change this from "FH" to fhs_bed or similar
            + f'{ad_config.STAGE_INPUTS["pipe"]["fhprs_bed"]}'
            + f'{self.panel_settings["FH"]}'
            + polyedge_cmd_string
            + masked_reference_command
            + ad_config.STAGE_INPUTS["pipe"]["picard_bed"]
            + self.panel_settings["hsmetrics_bedfile"]
            + ad_config.STAGE_INPUTS["pipe"]["picard_capturetype"]
            + self.panel_settings["capture_type"]
            + pipe_padding_cmd
            + ad_config.STAGE_INPUTS["pipe"]["filter_vcf_bed"]
            + self.panel_settings["variant_calling_bedfile"]
            + self.dest_str
            + self.runfolder_obj.nexus_proj_root
            + ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        )
        return dx_command

    def create_amp_cmd(self):
        """
        Input = R1 fastq file name and pan number for a single sample
        Returns = dx run command for AMP (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "AMP",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        # Paired end BED file used by primer clipping tool
        amp_bed_PE_input = f"{ad_config.BEDFILE_FOLDER}{self.pannum}_PE.bed"
        # AMP variant callers need the flat file
        amp_variant_calling_bed = f"{ad_config.BEDFILE_FOLDER}{self.pannum}_flat.bed"

        # create the AMP dx command
        dx_command_list = [
            ad_config.DX_RUN_CMDS["amp"],
            self.sample_name,
            ad_config.STAGE_INPUTS["amp"]["fastqc1_reads"],
            self.fastqs_dict["R1"],
            ad_config.STAGE_INPUTS["amp"]["fastqc2_reads"],
            self.fastqs_dict["R2"],
            ad_config.STAGE_INPUTS["amp"]["bwa_rg_sample"],
            self.sample_name,
            ad_config.STAGE_INPUTS["amp"]["picard_bed"],
            self.panel_settings["hsmetrics_bedfile"],
            ad_config.STAGE_INPUTS["amp"]["picard_capturetype"],
            panel_config.CAPTURE_PANEL_DICT["amp"]["capture_type"],
            ad_config.STAGE_INPUTS["amp"]["ampliconfilt_bed"],
            amp_bed_PE_input,
            ad_config.STAGE_INPUTS["amp"]["sambamba_cov_level"],
            str(panel_config.CAPTURE_PANEL_DICT["amp"]["clinical_coverage_depth"]),
            ad_config.STAGE_INPUTS["amp"]["mpileup_covlevel"],
            str(panel_config.CAPTURE_PANEL_DICT["amp"]["clinical_coverage_depth"]),
            ad_config.STAGE_INPUTS["amp"]["sambamba_bed"],
            self.panel_settings['sambamba_bedfile'],
            ad_config.STAGE_INPUTS["amp"]["vardict_bed"],
            amp_variant_calling_bed,
            ad_config.STAGE_INPUTS["amp"]["varscan_bed"],
            amp_variant_calling_bed,
            ad_config.STAGE_INPUTS["amp"]["bwa_ref"],
            ad_config.STAGE_INPUTS["amp"]["vardict_samplename"],
            self.sample_name,
            ad_config.STAGE_INPUTS["amp"]["varscan_samplename"],
            self.sample_name,
            ad_config.STAGE_INPUTS["amp"]["picard_ref"],
            ad_config.STAGE_INPUTS["amp"]["vardict_ref"],
            ad_config.STAGE_INPUTS["amp"]["varscan_ref"],
            self.dest_str,
            self.runfolder_obj.nexus_proj_root,
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ]

        # Variables from dx_command_list are read from ad_config file as
        # various atomic types. Convert to string and join to creat
        # dx_command
        dx_command = "".join(map(str, dx_command_list))

        # remove the bit that adds the job to the depends on list for the
        # negative control as varscan fails on nearempty/-empty BAM files
        # and this will stop multiqc etc running
        if self.negative_control:
            dx_command = dx_command.replace("jobid=$(", "").replace(
                self.dnanexus_apikey + ")", self.dnanexus_apikey
            )
        return dx_command

    def create_snp_cmd(self, fastq):
        """
        Input = R1 fastq filename and Pan number for a single sample
        Returns = dx run command for SNP workflow (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "SNP",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Create the SNP dx command
        dx_command_list = [
            ad_config.DX_RUN_CMDS["snp"],
            self.sample_name,
            ad_config.STAGE_INPUTS["snp"]["fastqc1_reads"],
            self.fastqs_dict["R1"],
            ad_config.STAGE_INPUTS["snp"]["fastqc2_reads"],
            self.fastqs_dict["R2"],
            ad_config.STAGE_INPUTS["snp"]["sentieon_samplename"],
            self.sample_name,
            self.dest_str,
            self.runfolder_obj.nexus_proj_root,
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ]

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_fastqc_cmd(self, fastqs):
        """
        Build dx run command, in this case to run fastqc on a single fastq file
        Inputs:
            R1 fastq filename
            Pan number
            read (R1 or R2)
        Returns:
            dx run command for fastqc (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "fastqc",
            self.sample_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        dx_command_list = [
            ad_config.DX_RUN_CMDS["fastqc"],
            self.sample_name,
            " -ireads=",
            self.fastqs_dict["R1"],
            " -ireads=",
            self.fastqs_dict["R2"],
            self.dest_str,
            self.runfolder_obj.nexus_proj_root,
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ]
        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_tso500_cmd(self):
        """
        Build dx run command for tso500 docker app.
        Will assess if it's a novaseq or not from the runfoldername and if
        it's a highthroughput
        TSO run (needing a larger instance type)
        Inputs:
            List of samplenames to be processed
        Returns:
            dx run command for tso500 app (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "TSO500",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Is it a novaseq run?
        if ad_config.NOVASEQ_ID in self.runfolder_obj.runfolder_name:
            tso500_analysis_options = "--isNovaSeq "
        else:
            tso500_analysis_options = ""

        # get a list of unique pan numbers from samplenames
        pannumber_list = set(
            [re.search(r"Pan\d+", sample).group() for sample in self.samples_to_process]
        )
        # capture any pan numbers that are a highthroughput assay
        high_throughput_list = [
            pannumber
            for pannumber in pannumber_list
            if self.panel_settings["panel_name"]
            == "tso500_high_throughput"
        ]
        # if this list is not empty apply high throughput instance type,
        # otherwise use low throughput instance type
        if high_throughput_list:
            instance_type = (
                f" --instance-type " f"{ad_config.APP_INPUTS['tso500']['ht_instance']} "
            )
        else:
            instance_type = (
                f" --instance-type " f"{ad_config.APP_INPUTS['tso500']['lt_instance']} "
            )
        # build dx run command - inputs are:
        # docker image (from ad_config)
        # runfolder_tar and samplesheet paths (from runfolder_obj class)
        # analysis options eg --isNovaSeq flag
        dx_command_list = [
            # ends with --name so supply the runfoldername to name the job
            ad_config.DX_RUN_CMDS["tso500"],
            self.runfolder_obj.runfolder_name,
            ad_config.APP_INPUTS["tso500"]["docker"],
            ad_config.NEXUS_IDS["FILES"]["tso500_docker"],
            ad_config.APP_INPUTS["tso500"]["samplesheet"],
            f"{self.nexus_project_id}:{self.runfolder_obj.samplesheet_name}",
            ad_config.APP_INPUTS["tso500"]["project_name"],
            self.runfolder_obj.nexus_project_name,
            ad_config.APP_INPUTS["tso500"]["analysis_options"],
            tso500_analysis_options,
            instance_type,
            "--wait ",
            self.dest_str,
            self.runfolder_obj.nexus_proj_root,
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ]
        dx_command = "".join(map(str, dx_command_list))
        return dx_command
