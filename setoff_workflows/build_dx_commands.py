#!/usr/bin/python3
"""build_dx_commands.py

Builds dx commands for a runfolder
"""
import logging
from typing import Optional, Union, Tuple
from toolbox.toolbox import get_credential, RunfolderObject, SampleObject
from config.ad_config import SWConfig

class BuildRunfolderDxCommands(SWConfig):
    """
    Build dx run commands that are run at the runfolder level

        create_tso500_cmd(tso_ss)
            Build dx run command for tso500 docker app
        get_tso_analysis_options()
            Determine whether its a novaseq run from the runfoldername, and return the
            relevant tso500 app input string
        return_multiqc_cmds()
            Create list of multiqc commands (for running multiqc and upload multiqc
            apps) by calling the relevant methods
        create_multiqc_cmd()
            Build dx run command to run MultiQC for the run. MultiQC is run after all
            QC tools have been run
        create_upload_multiqc_cmd()
            Build dx run command to run upload_multiqc app for the run. This uploads the
            MultiQC data to the genomics server. The input to the upload_multiqc app is
            the html_report output of the multiqc app in the format jobid:output_name
        create_peddy_cmd()
            Build dx run command to run peddy for the project. Run once at the end of a
            WES run and downloads required files from the project
        create_rpkm_cmd(core_panel_name)
            Build dx run command to run RPKM for a core panel
        create_ed_readcount_cmd(core_panel_name)
            Build dx run command for exomedepth readcount app
        create_ed_cnvcalling_cmd(panno)
            Build dx run command for exomedepth cnv calling app
        create_duty_csv_cmd()
            Build dx run command to run create_duty_csv app for the run
    """
    def __init__(self, rf_obj: object, logger: logging.Logger):
        self.rf_obj = rf_obj
        self.logger = logger

    def create_tso500_cmd(self, tso_ss: str) -> str:
        """
        Build dx run command for tso500 docker app
            :param tso_ss (str):    TSO SampleSheet
            :return (str):          Dx run command for tso500 app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            self.rf_obj.runfolder_name,
            tso_ss,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["tso500"]}{SWConfig.RUNFOLDER_NAME}',
                SWConfig.APP_INPUTS["tso500"]["docker"],
                f'{SWConfig.APP_INPUTS["tso500"]["samplesheet"]}{tso_ss}',
                SWConfig.APP_INPUTS["tso500"]["project_name"],
                SWConfig.APP_INPUTS["tso500"]["runfolder_name"],
                self.get_tso_analysis_options(),
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def get_tso_analysis_options(self) -> str:
        """
        Determine whether its a novaseq run from the runfoldername, and return the
        relevant tso500 app input string
            :return (str):  Analysis options for the tso500 app
        """
        if SWConfig.NOVASEQ_ID in self.rf_obj.runfolder_name:
            tso500_analysis_options = "--isNovaSeq "
        else:
            tso500_analysis_options = ""
        return f'{SWConfig.APP_INPUTS["tso500"]["analysis_options"]}{tso500_analysis_options}'

    def return_multiqc_cmds(self, pipeline: str) -> list:
        """
        Create list of multiqc commands (for running multiqc and upload multiqc apps) by
        calling the relevant methods
            :return cmd_list (str): List of multiqc commands
        """
        cmd_list = []
        cmd_list.append(self.create_multiqc_cmd(pipeline))
        cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list"])
        cmd_list.append(self.create_upload_multiqc_cmd())
        cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list"])
        return cmd_list

    def create_multiqc_cmd(self, pipeline: str) -> str:
        """
        Build dx run command to run MultiQC for the run. MultiQC is run after all QC tools have been
        run. Requires a project to download data from, and a coverage level. Coverage level differs
        between panels. The lowest value for the panels on the run is used
            :return (str): Dx run command for MultiQC app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "multiqc",
            self.rf_obj.runfolder_name,
        )
        coverage_level = list(
            set(
                [
                    v["multiqc_coverage_level"]
                    for k, v in SWConfig.CAPTURE_PANEL_DICT.items()
                    if v["pipeline"] == pipeline
                ]
            )
        )[0]
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["multiqc"]}MultiQC',
                SWConfig.APP_INPUTS["multiqc"]["project_name"],
                f'{SWConfig.APP_INPUTS["multiqc"]["coverage_level"]}{str(coverage_level)}',
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ],
        )

    def create_upload_multiqc_cmd(self) -> str:
        """
        Build dx run command to run upload_multiqc app for the run. This uploads the
        MultiQC data to the genomics server. The input to the upload_multiqc app is the
        html_report output of the multiqc app in the format jobid:output_name
            :return (str): Dx run command for upload_multiqc app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "upload multiqc",
            self.rf_obj.runfolder_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["upload_multiqc"]}Upload_MultiQC',
                SWConfig.APP_INPUTS["upload_multiqc"]["multiqc_html"],
                SWConfig.APP_INPUTS["upload_multiqc"]["lane_metrics"],
                SWConfig.APP_INPUTS["upload_multiqc"]["multiqc_output"],
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_peddy_cmd(self) -> str:
        """
        Build dx run command to run peddy for the project. Run once at the
        end of a WES run and downloads required files from the project
            :return (str):  Dx run command for peddy app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "peddy",
            self.rf_obj.runfolder_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["peddy"]}Peddy',
                SWConfig.APP_INPUTS["peddy"]["project_name"],
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_rpkm_cmd(self, core_panel_name: str) -> str:
        """
        Build dx run command to run RPKM for a core panel. RPKM app requires project id,
        bedfile and string containing the pannumber(s) of all files that should be included
        in this analysis (input list is pulled from PanelConfig.VCP_PANELS using the core_panel_name).
        App takes pan numbers as string, and will separate on commas when passed multiple pan numbers
            :param core_panel_name (str):   Name of synnovis core panel
            :return (str):                  Dx run command for RPKM app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "RPKM",
            core_panel_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["rpkm"]}RPKM_using_conifer-{core_panel_name}',
                f'{SWConfig.APP_INPUTS["rpkm"]["bed"]}{SWConfig.CAPTURE_PANEL_DICT[core_panel_name]["rpkm_bedfile"]}',
                SWConfig.APP_INPUTS["rpkm"]["proj"],
                f'{SWConfig.APP_INPUTS["rpkm"]["pannos"]}{",".join(SWConfig.VCP_PANELS[core_panel_name])}',
                SWConfig.UPLOAD_ARGS["depends_gatk"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_ed_readcount_cmd(self, core_panel_name: str) -> str:
        """
        Build dx run command for exomedepth readcount app. Exome depth is run in 2 stages,
        firstly readcounts are calculated for each capture panel. Job ID is saved to $ED_READCOUNT_JOB_ID
        which allows the output of this stage to be used to filter CNVs with a panel-specific BEDfile
            :param core_panel_name (str):   Name of synnovis core panel
            :return (str):                  Dx run command for ED readcount app

        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "ED_readcount",
            core_panel_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["ed_readcount"]}ED_Readcount-{core_panel_name}',
                f'{SWConfig.APP_INPUTS["ed_readcount"]["ref_genome"]}'
                f'{SWConfig.NEXUS_IDS["FILES"]["hs37d5_ref_no_index"]}',
                f'{SWConfig.APP_INPUTS["ed_readcount"]["bed"]}'
                f'{SWConfig.CAPTURE_PANEL_DICT[core_panel_name]["ed_readcount_bedfile"]}',
                f'{SWConfig.APP_INPUTS["ed_readcount"]["normals_rdata"]}'
                f'{SWConfig.NEXUS_IDS["FILES"][f"ed_{core_panel_name}_readcount_normals"]}',
                SWConfig.APP_INPUTS["ed_readcount"]["proj"],
                f'{SWConfig.APP_INPUTS["ed_readcount"]["pannos"]}{",".join(SWConfig.ED_PANNOS[core_panel_name])}',
                SWConfig.UPLOAD_ARGS[
                    "depends_gatk"
                ],  # Use list of gatk related jobs to delay start
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_ed_cnvcalling_cmd(self, panno: str) -> str:
        """
        Build dx run command for exomedepth cnv calling app
            :param panno (str):     Pannumber to filter CNV calls
            :return (str):          Dx run command for ED cnv calling app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "ED_cnvcalling",
            panno,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["ed_cnvcalling"]}ED_CNVcalling-{panno}',
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["readcount"]}',
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["bed"]}'
                f'{SWConfig.BEDFILE_FOLDER}{SWConfig.PANEL_DICT[panno]["ed_cnvcalling_bedfile"]}_CNV.bed',
                SWConfig.APP_INPUTS["ed_cnvcalling"]["proj"],
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["pannos"]}{panno}',
                SWConfig.UPLOAD_ARGS[
                    "depends_gatk"
                ],  # Use list of gatk related jobs to delay start
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_duty_csv_cmd(self) -> str:
        """
        Build dx run command to run create_duty_csv app for the run. This creates a CSV
        file for use in downloading files to the trust network with the process_duty_csv
        script. It also sends an email denoting the run is ready for processing. The
        input to the duty_csv app is the DNAnexus project name, and the pan numbers for
        tso samples, stg samples, and the custom panel whole capture for each core panel
            :return (str):  Dx run command for duty_csv app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "create_duty_csv",
            self.rf_obj.runfolder_name,
        )
        return " ".join(
            [
                f"{SWConfig.DX_CMDS['duty_csv']}Duty_CSV",
                SWConfig.APP_INPUTS["duty_csv"]["project_name"],
                f'{SWConfig.APP_INPUTS["duty_csv"]["tso_pannumbers"]}{",".join(SWConfig.TSO_SYNNOVIS_PANNUMBERS)}',
                f'{SWConfig.APP_INPUTS["duty_csv"]["stg_pannumbers"]}{",".join(SWConfig.STG_PANNUMBERS)}',
                f'{SWConfig.APP_INPUTS["duty_csv"]["cp_capture_pannos"]}{",".join(SWConfig.CP_CAPTURE_PANNOS)}',
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def return_wes_query(self) -> str:
        """
        Return WES SQL query. This is a single update query per-run
            :return query (str):    Single update query for the WES run
        """
        wes_dnanumbers = [
            self.rf_samples.samples_dict[k]["identifiers"]["primary"]
            for k in self.rf_samples.samples_dict.keys()
        ]
        return [
            SWConfig.QUERIES["wes"]
            % (
                str(SWConfig.SQL_IDS["WORKFLOWS"]["wes"]),
                str(SWConfig.SQL_IDS["WES_TEST_STATUS"]["data_processing"]),
                ("','").join(wes_dnanumbers),
                str(SWConfig.SQL_IDS["WES_TEST_STATUS"]["nextseq_sequencing"]),
            )
        ]

    def write_dx_run_cmds(self, workflow_cmds: list, dx_postprocessing_cmds: list, decision_support_upload_cmds: list) -> None:
        """
        Write dx run commands to the dx run script, post dx run script, and decision support upload
        script for the runfolder. Remove any None values
        from the command list
            :return None:
        """

        if workflow_cmds:  # Write dx run commands
            cmds_to_write = base_variables.extend(workflow_cmds)
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["writing_cmds"],
                self.rf_obj.runfolder_dx_run_script,
            )
            write_lines(  # Write commands to dx run script
                self.rf_obj.runfolder_dx_run_script,
                "w",
                list(filter(None, cmds_to_write)),
            )
        if self.dx_postprocessing_cmds:  # Write postprocessing commands
            cmds_to_write = base_variables.extend(self.dx_postprocessing_cmds)
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["writing_cmds"],
                self.rf_obj.post_run_dx_run_script,
            )
            write_lines(
                self.rf_obj.post_run_dx_run_script,
                "w",
                list(filter(None, cmds_to_write)),
            )
        if self.decision_support_upload_cmds:
            cmds_to_write = base_variables.extend(self.decision_support_upload_cmds)
            write_lines(
                self.rf_obj.decision_support_upload_script,
                "w",
                list(filter(None, cmds_to_write)),
            )


class BuildSampleDxCommands(SWConfig):
    """
    Build dx run commands commands that are run at the sample level

    Attributes:
        rf_obj (obj):                           RunfolderObject object (contains runfolder-specific attributes)
        nexus_project_id (str):                 Project ID, generated when the DNAnexus project is created
        workflow_cmds (list):                   Dx run commands for the project
        dx_postprocessing_cmds (list):          Dx run commands to run after the TSO app. TSO runs only
        decision_support_upload_cmds (list):    Dx run commands for decision support uploads

    Methods:
        return_decision_support_cmd()
            Construct decision support tool command for decision support tool upload where required by
            calling build_congenica_sftp_cmd, build_congenica_cmd or build_qiagen_upload_cmd
        create_sompy_cmd(sample)
            Build dx run command to run sompy on a single VCF file
        create_sambamba_cmd(sample, pannumber)
            Build dx run command to run sambamba on a single BAM file
        create_wes_cmd()
            Construct dx run command for WES workflow
        build_congenica_sftp_cmd()
            Build the command to write the Congenica upload dx run command for the SFTP
            app to the decision support tool upload bash script
        build_congenica_cmd()
            Build the command to write the Congenica upload dx run command to the decision
            support tool upload bash script
        build_qiagen_upload_cmd()
            Build the command to write the qiagen upload command to the decisions support
            tool upload bash script
        create_pipe_cmd()
            Construct dx run command for PIPE workflow
        get_vcfeval_cmd_string()
            Get command string for input to vcfeval stage of PIPE workflow
        get_fhprs_cmd_string()
            Get command string for input FH_PRS stage of PIPE workflow
        get_polyedge_cmd_string()
            Get command string for polyedge stage of PIPE workflow
        get_masked_reference_cmd_string()
            Get input string for masked reference input for BWA stage of PIPE workflow,
            if specified for the pan number in the config
        create_snp_cmd()
            Construct dx run command for SNP workflow
        create_fastqc_cmd()
            Build dx run command to run fastqc
        build_oncodeep_upload_cmd()
            Build the command to write the OncoDEEP upload dx run command to the
            decision support tool upload bash script
        return_rd_query()
            Create a query per sample using the DNA number
        return_oncology_query()
            Create a query per sample using IDs from the samplename (3rd and 4th) elements
    """

    def __init__(
        self,
        runfolder_name: str,
        sample_dict: dict,
        logger: logging.Logger,
    ):
        """
        Constructor for the BuildSampleDxCommands class. Calls the class methods
            :param rf_obj (obj):            RunfolderObject object (contains runfolder-specific attributes)
        """
        self.sample_dict = sample_dict
        self.runfolder_name = runfolder_name
        self.logger = logger
        self.sql_queries = []
        self.workflow_cmds = []
        self.dx_postprocessing_cmds = []
        self.decision_support_upload_cmds = []
        self.logger.info(
            self.logger.log_msgs["building_cmds"]
        )

    def return_congenica_cmd(self) -> Union[str, None]:
        """
        Construct decision support tool command for non-reference samples by calling build_congenica_sftp_cmd,
        build_congenica_cmd, or build_qiagen_upload_cmd(). If a sample requires Congenica upload, there are 2
        methods. If Congenica project ID is specified as 'SFTP' within the config it means the sample requires
        upload via SFTP, else if congenica_project ID is specified it means it can be uploaded using the upload
        agent. Both Congenica apps app take inputs in the format jobid.outputname which ensures the job doesn't
        run until the vcfs have been created. App inputs are created by a python script, which is called immediately
        before the app is set off, and the script output (app inputs) is captured by the variable $DSS_INPUTS
            :return (str | None):   Dx run commands (Congenica input command, Congenica upload command, Qiagen upload
                                    command), or None if sample is a reference sample
        """
        if any([self.sample_dict["neg_control"], self.sample_dict["pos_control"]]):
            decision_support_cmd = None
            self.logger.info(
                self.logger.log_msgs[
                    "decision_support_upload_notrequired"
                ],
                self.sample_dict["sample_name"],
            )
        else:
            self.logger.info(
                self.logger.log_msgs[
                    "decision_support_upload_required"
                ],
                self.sample_dict["sample_name"],
            )
            # If project is specified then upload via upload agent
            if self.sample_dict["panel_settings"]["congenica_project"] == "SFTP":  # SFTP upload cmd
                decision_support_cmd = self.build_congenica_sftp_cmd()
            elif isinstance(self.sample_dict["panel_settings"]["congenica_project"], int):
                decision_support_cmd = self.build_congenica_cmd()
            return decision_support_cmd

    def create_sompy_cmd(self, sample: str) -> str:
        """
        Build dx run command to run sompy on a single VCF file
            :param sample (str):    Sample name
            :return (str):          Dx run command for sompy app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"], "sompy", sample
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["sompy"]}Sompy-{sample}',
                SWConfig.APP_INPUTS["sompy"]["truth_vcf"],
                f'{SWConfig.APP_INPUTS["sompy"]["query_vcf"]}{sample}/{sample}_MergedSmallVariants.genome.vcf',
                SWConfig.APP_INPUTS["sompy"]["tso"],
                SWConfig.APP_INPUTS["sompy"]["skip"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_sambamba_cmd(self, sample: str, pannumber: str) -> str:
        """
        Build dx run command to run sambamba on a single BAM file
            :param sample (str):    Sample name
            :param pannumber (str): Config-defined pan number for sample
            :return (str):          Dx run command for sambamba app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "sambamba",
            sample,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["sambamba"]}Sambamba_Chanjo-{sample}',
                f'{SWConfig.APP_INPUTS["sambamba"]["bam"]}{sample}/{sample}.bam',
                f'{SWConfig.APP_INPUTS["sambamba"]["bai"]}{sample}/{sample}.bam.bai',
                f'{SWConfig.APP_INPUTS["sambamba"]["coverage_level"]}'
                f'{str(SWConfig.PANEL_DICT[pannumber]["clinical_coverage_depth"])}',
                f'{SWConfig.APP_INPUTS["sambamba"]["sambamba_bed"]}'
                f'{SWConfig.PANEL_DICT[pannumber]["sambamba_bedfile"]}',
                SWConfig.APP_INPUTS["sambamba"]["cov_cmds"]
                % (
                    str(SWConfig.PANEL_DICT[pannumber]["coverage_min_basecall_qual"]),
                    str(SWConfig.PANEL_DICT[pannumber]["coverage_min_mapping_qual"]),
                ),
                f'{SWConfig.UPLOAD_ARGS["dest"]}:/coverage/{pannumber}',
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_wes_cmd(self) -> str:
        """
        Construct dx run command for WES workflow
            :return (str):  Dx run command string
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            self.sample_dict["panel_settings"]["pipeline"],
            self.sample_dict["sample_name"],
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["wes"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["fastqc1_reads"]}{self.sample_dict["fastqs"]["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["fastqc2_reads"]}{self.sample_dict["fastqs"]["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["sentieon_samplename"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["picard_bed"]}{self.sample_dict["panel_settings"]["hsmetrics_bedfile"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["sambamba_bed"]}{self.sample_dict["panel_settings"]["sambamba_bedfile"]}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def build_congenica_sftp_cmd(self) -> str:
        """
        Build the command to write the Congenica upload dx run command for the SFTP app to the decision
        support tool upload bash script. This command is used to upload the sample to Congenica using
        the SFTP Congenica upload app. Samples requiring upload by SFTP require patient-specific info
        to be pre-added into Congenica by the scientists. Takes BAM and VCF inputs, and does not require
        project IDs, IR templates or name
            :return (str):  Dx run command for the Congenica upload (SFTP app)
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "congenica sftp",
            self.sample_dict["sample_name"],
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["congenica_sftp"]}Congenica_SFTP_Upload-{self.sample_dict["sample_name"]}',
                SWConfig.UPLOAD_ARGS["dest"],
                f'{SWConfig.APP_INPUTS["congenica_upload"]["vcf"]}{self.sample_dict["sample_name"]}*_markdup_Haplotyper.vcf.gz',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["bam"]}{self.sample_dict["sample_name"]}*_markdup.bam',
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def build_congenica_cmd(self) -> str:
        """
        Build the command to write the Congenica upload dx run command to the decision support tool
        upload bash script. This command is used to upload the sample to Congenica using the standard
        Congenica upload app. Takes BAM and VCF inputs, along with config-specified inputs congenica
        project ID, credentials, IR template and sample name
            :param pipeline (str):  
            :return (str):          Dx run command for the Congenica upload (standard Congenica upload app)
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "congenica",
            self.sample_dict["sample_name"],
        )
        if self.sample_dict["panel_settings"]["pipeline"] == "pipe":
            vcf_input = f'{self.sample_dict["sample_name"]}*.bedfiltered.vcf.gz'
            bam_input = f'{self.sample_dict["sample_name"]}*.refined.bam'

        if self.sample_dict["panel_settings"]["pipeline"] == "wes":
            vcf_input = f'{self.sample_dict["sample_name"]}*_markdup_Haplotyper.vcf.gz'
            bam_input = f'{self.sample_dict["sample_name"]}*_markdup.bam'

        return " ".join(
            [
                f'{SWConfig.DX_CMDS["congenica_upload"]}Congenica_Upload-{self.sample_dict["sample_name"]}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["congenica_project"]}'
                f'{str(self.sample_dict["panel_settings"]["congenica_project"])}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["credentials"]}'
                f'{self.sample_dict["panel_settings"]["congenica_credentials"]}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["ir_template"]}'
                f'{self.sample_dict["panel_settings"]["congenica_IR_template"]}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["samplename"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["vcf"]}{vcf_input}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["bam"]}{bam_input}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def build_qiagen_upload_cmd(self) -> str:
        """
        Build the command to write the qiagen upload dx run command to the decision
        support tool upload bash script. This command is used to upload the sample
        to QCII. The command takes sample_name and sample_zip_folder as inputs
            :return (str):  Dx run command for the qiagen_upload app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "qiagen",
            self.sample_dict["sample_name"],
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["qiagen_upload"]}Qiagen_Upload-{self.sample_dict["sample_name"]}',
                f'{SWConfig.APP_INPUTS["qiagen_upload"]["sample_name"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.APP_INPUTS["qiagen_upload"]["sample_zip_folder"]}{self.sample_dict["pannum"]}/{self.sample_dict["sample_name"]}.zip',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_pipe_cmd(self) -> str:
        """
        Construct dx run command for PIPE workflow. Congenica requires variant calling
        to be restricted in the pipeline, in some cases to prevent incidental findings.
        The variant caller pads bed files by 100bp by default so this may need to be
        overruled. The panel dictionary default is to give a value of 0, which turns off
        this padding. An example of the use of this is for STG BrCa who require padding
        of +/- 11bp (bed files are padded +/-10bp) so 1bp padding is applied.
            :return (str):  Dx run command string
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            self.sample_dict["panel_settings"]["pipeline"],
            self.sample_dict["sample_name"],
        )
        # Specify instance type for human exome app
        if self.sample_dict["panel_settings"]["FH"]:  # Larger instance required for FH samples
            GATK_INSTANCE = "mem3_ssd1_v2_x16"
        else:
            GATK_INSTANCE = "mem1_ssd1_v2_x8"

        return " ".join(
            [
                f'{SWConfig.DX_CMDS["pipe"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["fastqc_reads"]}{self.sample_dict["fastqs"]["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["fastqc_reads"]}{self.sample_dict["fastqs"]["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["bwa_reads1"]}{self.sample_dict["fastqs"]["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["bwa_reads2"]}{self.sample_dict["fastqs"]["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["bwa_rg_sample"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_bed"]}{self.sample_dict["panel_settings"]["sambamba_bedfile"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_min_base_qual"]}'
                f'{str(self.sample_dict["panel_settings"]["coverage_min_basecall_qual"])}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_min_mapping_qual"]}'
                f'{str(self.sample_dict["panel_settings"]["coverage_min_mapping_qual"])}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_cov_level"]}'
                f'{str(self.sample_dict["panel_settings"]["clinical_coverage_depth"])}',
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_filter_cmds"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_excl_dups"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_excl_failed_qual"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_count_overl_mates"],
                self.get_vcfeval_cmd_string(),
                self.get_fhprs_cmd_string(),
                f'{SWConfig.STAGE_INPUTS["pipe"]["fhprs_bed"]}{SWConfig.FH_PRS_BEDFILE}',
                self.get_polyedge_cmd_string(),
                self.get_masked_reference_cmd_string(),
                f'{SWConfig.STAGE_INPUTS["pipe"]["picard_bed"]}{self.sample_dict["panel_settings"]["hsmetrics_bedfile"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["picard_capturetype"]}{self.sample_dict["panel_settings"]["capture_type"]}',
                SWConfig.STAGE_INPUTS["pipe"]["gatk_padding"],
                f'{SWConfig.STAGE_INPUTS["pipe"]["filter_vcf_bed"]}{self.sample_dict["panel_settings"]["variant_calling_bedfile"]}',
                SWConfig.STAGE_INPUTS["pipe"]["bwa_instance"],
                f'{SWConfig.STAGE_INPUTS["pipe"]["gatk_instance"]}{GATK_INSTANCE}',
                SWConfig.STAGE_INPUTS["pipe"]["filter_vcf_instance"],
                SWConfig.STAGE_INPUTS["pipe"]["picard_instance"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_instance"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def get_vcfeval_cmd_string(self) -> str:
        """
        Get command string for input to vcfeval stage of PIPE workflow. If sample is not
        NA12878 we want to skip the vcfeval stage (the app default is skip=False)
            :return (str):  App input string
        """
        prefix_str = (  # Set prefix as samplename
            f'{SWConfig.STAGE_INPUTS["pipe"]["happy_prefix"]}{self.sample_dict["sample_name"]}'
        )
        if self.pos_control:
            skip_str = f'{SWConfig.STAGE_INPUTS["pipe"]["happy_skip"]}false'
        else:
            skip_str = f'{SWConfig.STAGE_INPUTS["pipe"]["happy_skip"]}true'

        return " ".join([prefix_str, skip_str])

    def get_fhprs_cmd_string(self) -> str:
        """
        Get command string for input FH_PRS stage of PIPE workflow. If sample is specified as
        requiring FH analysis in the config, set skip to False (the app default is skip=True),
        and specify outptut as both VCF and GVCF
            :return fh_prs_cmd_string: App input string
        """
        if self.sample_dict["panel_settings"]["FH"]:
            return " ".join(
                [
                    SWConfig.STAGE_INPUTS["pipe"]["fhprs_skip"],
                    SWConfig.STAGE_INPUTS["pipe"]["gatk_vcf_format"],
                    SWConfig.PIPE_FH_GATK_TIMEOUT_ARGS,
                ]
            )
        else:
            return ""

    def get_polyedge_cmd_string(self) -> str:
        """
        Get command string for polyedge stage of PIPE workflow. If sample is specified
        as requiring polyedge analysis in the config, set skip to False (the app default
        is skip=True) and specify gene chrom and start / end inputs
            :return polyedge_cmd_string (str):  App input string
        """
        if self.sample_dict["panel_settings"]["polyedge"]:
            return " ".join(
                [
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_gene"]}{self.sample_dict["panel_settings"]["polyedge"]["gene"]}',
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_chrom"]}{str(self.sample_dict["panel_settings"]["polyedge"]["chrom"])}',
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_poly_start"]}'
                    f'{str(self.sample_dict["panel_settings"]["polyedge"]["poly_start"])}',
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_poly_end"]}'
                    f'{str(self.sample_dict["panel_settings"]["polyedge"]["poly_end"])}',
                    SWConfig.STAGE_INPUTS["pipe"]["polyedge_skip"],
                ]
            )
        else:
            return ""

    def get_masked_reference_cmd_string(self) -> str:
        """
        Get input string for masked reference input for BWA stage of PIPE workflow, if
        specified for the pan number in the config
            :return masked_reference_cmd_string (str):  Masked reference input string
        """
        if self.sample_dict["panel_settings"]["masked_reference"]:
            return f"{SWConfig.STAGE_INPUTS['pipe']['bwa_ref']}{self.sample_dict['panel_settings']['masked_reference']}"
        else:
            return ""

    def create_snp_cmd(self) -> str:  # TODO eventually remove this
        """
        Construct dx run command for SNP workflow
            :return (str):  Dx run command string
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            self.sample_dict["panel_settings"]["pipeline"],
            self.sample_dict["sample_name"],
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["snp"]}{self.sample_dict["sample_name"]}',
                f'{SWConfig.STAGE_INPUTS["snp"]["fastqc1_reads"]}{self.sample_dict["fastqs"]["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["snp"]["fastqc2_reads"]}{self.sample_dict["fastqs"]["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["snp"]["sentieon_samplename"]}{self.sample_dict["sample_name"]}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def create_fastqc_cmd(self) -> str:
        """
        Build dx run command to run fastqc
            :return (str): Dx run command for fastqc app
        """
        self.logger.info(
            self.logger.log_msgs["building_cmd"],
            "fastqc",
            self.sample_dict["sample_name"],
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["fastqc"]}FastQC-{self.sample_dict["sample_name"]}',
                f'{SWConfig.APP_INPUTS["fastqc"]["reads"]}{self.sample_dict["fastqs"]["R1"]["nexus_path"]}',
                f'{SWConfig.APP_INPUTS["fastqc"]["reads"]}{self.sample_dict["fastqs"]["R2"]["nexus_path"]}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def build_oncodeep_upload_cmd(file_name: str, run_identifier: str, file: str) -> str:
        """
        Build the command to write the OncoDEEP upload dx run command to the decision
        support tool upload bash script. This command is used to upload the sample to
        OncoDEEP. The command takes sample_sample and sample_zip_folder as inputs
            :param file_name (str):         Name of file being uploaded
            :param run_identifier (str):    Run identifier, e.g. OKD1234
            :param file (str):              Path to file in DNAnexus
            :return (str):                  Dx run command for the oncodeep_upload app
        """
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["oncodeep_upload"]}OncoDEEP_Upload-{file_name}',
                f'{SWConfig.APP_INPUTS["oncodeep_upload"]["run_identifier"]}{run_identifier}',
                f'{SWConfig.APP_INPUTS["oncodeep_upload"]["file_to_upload"]}{file}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"],
            ]
        )

    def return_rd_query(self) -> str:
        """
        Create a query per sample using the DNA number
            :return query (str):    Sample SQL rare disease query
        """
        pipeline_version = str(SWConfig.SQL_IDS["WORKFLOWS"][self.sample_dict["panel_settings"]["pipeline"]])
        rd_query = SWConfig.QUERIES["customrun"] % (
            f"'{self.sample_dict['identifiers']['primary']}','{pipeline_version}',"
            f"'{self.runfolder_name}'"
        )
        return rd_query

    def return_oncology_query(self) -> str:
        """
        Create a query per sample using IDs from the samplename (3rd and 4th) elements.
        These are recorded along with the pipeline version, run name, and panel ID.
            :return query (str):    Sample SQL oncology query
        """
        pipeline_version = str(SWConfig.SQL_IDS["WORKFLOWS"][self.sample_dict["panel_settings"]["pipeline"]])
        panel_id = self.sample_dict["pannum"].replace("Pan", "")

        onc_query = SWConfig.QUERIES["oncology"] % (
            f"'{self.sample_dict['identifiers']['primary']}','{self.sample_dict['identifiers']['secondary']}',"
            f"'{self.runfolder_name}','{pipeline_version}','{panel_id}'"
        )
        return onc_query

