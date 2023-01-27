""" Print inputs required by decision support tool upload applications on DNANexus

In order to run some run wide tasks we need to supply the inputs in the form jobid.output_name
This is hard to do if we are running workflows as the job id relates to one app within a workflow.
This script takes an analysis id and returns the job id of the specific stage.
The script prints the output to the command line formatted for the tool given in as an argument.
"""

import subprocess
import json
import re
from collections import namedtuple
import argparse
import ad_config as config  # Import config file
from upload_and_setoff_workflows import RunfolderProcessor


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments and help menu
    """
    # Create ArgumentParser object. Description message will be displayed as part of help message if
    # script is run with -h flag
    parser = argparse.ArgumentParser(
        description=(
            "given an analysis-id will obtain the job ids for bam and vcf files for upload to the "
            "specified decision support tool"
        )
    )
    # Define the arguments that will be taken.
    parser.add_argument(
        "-a",
        "--analysis_id",
        required=True,
        help="workflow Analysis ID in format Analysis-abc123",
    )
    parser.add_argument(
        "-t",
        "--tool",
        choices=["congenica"],
        required=True,
        help="decision support tool (currently only supports congenica)",
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="The DNAnexus project id in which the analysis is running",
    )
    # Return the arguments
    return parser.parse_args()


class DecisionTooler(object):
    """
    Builds decision support tool command line inputs
    """

    # named tuple to hold all the output names - This tuple name is "workflow" and has four
    # attributes which can be accessed using Workflow.attribute
    workflow_object = namedtuple("Workflow", "name vcf_out bam_out bai_out")

    def __init__(self):
        pass

    def _parse_mokawes_json(self, json_ob):
        """
        Take the JSON from dx describe on MokaWES.
        MokaWES Senteion app is itself a workflow, this means there are two valid approaches to
        obtaining the job id depending on how quickly the dx run command is processed and the
        sentieon workflow is established. Parse to get the job id using two approaches.
        If not found return null
        """
        # for each stage
        for stage in json_ob["stages"]:
            # check for app name
            if stage["id"] == config.sentieon_stage_id:
                return stage["execution"]["id"]
        return None

    def _parse_mokapipe_json(self, json_ob):
        """
        Parse the dx describe output from the mokapipe analysis id
        use the stage id to identify the job id of the required stage (see config file)
        return the job id for the bed filtering app for vcf and return the gatk human exome
        pipeline for BAM
        """
        jobid = None
        bamjobid = None
        for stage in json_ob["stages"]:
            if stage["id"] == config.mokapipe_filter_vcf_with_bedfile_stage:
                jobid = stage["execution"]["id"]
            elif stage["id"] == config.mokapipe_gatk_human_exome_stage:
                bamjobid = stage["execution"]["id"]
        return jobid, bamjobid

    def get_job_id(self, analysis_id, project, workflow):
        """
        perform dx describe on the workflow (analysis id)
        Loop through up to 1000 times incase the dx run commands have not yet been executed
        Depending on the workflow pass the dx describe json to a workflow specific function.
        recieves the bam and vcf stage ids
        returns tuple of job ids that created vcf and bam
        """
        # obtain json for dx describe on the given analysis id
        cmd = ("source {}; dx describe" " {}:{} --json --auth-token {}").format(
            config.sdk_source_cmd, project, analysis_id, config.nexus_apikey
        )
        # jobid comes from the sentieon sub-job, which takes a few moments to initiate after
        # calling the sentieon app. Running this script immediately after running the sentieon
        # workflow raises an IndexError. We retry in the while loop until the jobid is available.
        jobid = None
        bamjobid = None
        tries = 0
        while not jobid:
            try:
                # execute command
                proc = subprocess.Popen(
                    [cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
                )
                # capture the streams
                (out, _) = proc.communicate()
                json_ob = json.loads(out)
                if workflow.name == "mokawes":
                    # same stage is used for BAM and VCF
                    jobid = self._parse_mokawes_json(json_ob)
                    bamjobid = jobid
                elif workflow.name == "mokapipe":
                    # seperate stages are returned by mokapipe parse function
                    jobid, bamjobid = self._parse_mokapipe_json(json_ob)
            except IndexError:
                tries += 1
                if tries == 1000:  # Can take a while for the server to update
                    raise Exception("Maximum Tries Exceeded")
        return jobid, bamjobid

    def get_workflow(self, ps):
        """
        input is the panel settings dictionary created outside of this class
        create a namedtuple named as the workflow name and with the output names from the app which
        produces the decision support tool inputs. returns the namedtuple
        """
        if ps["pipeline"] == "mokawes":
            return self.workflow_object(
                "mokawes",
                config.mokawes_sentieon_vcf_output_name,
                config.mokawes_sentieon_bam_output_name,
                config.mokawes_sentieon_bai_output_name,
            )
        elif ps["pipeline"] == "mokapipe":
            return self.workflow_object(
                "mokapipe",
                config.mokapipe_vcf_output_name,
                config.mokapipe_bam_output_name,
                None,
            )

    def printer(self, jobid, workflow, tool, pipe_bam_jobid):
        """
        recieves the jobids that created vcf and bam and the decision support tool to be used
        also recieves the named tuple containing the workflow details (output names for each
        relevant decision support tool input).
        Each tool and each workflow requires a slightly different input.
        prints to stdout the required input for the decision support tool app in form
        decision_suport_tool_input=jobid.outputname
        """
        if tool == "congenica":
            if workflow.name == "mokawes":
                print(
                    " %s%s:%s%s%s:%s"
                    % (
                        config.congenica_vcf_inputname,
                        jobid,
                        workflow.vcf_out,
                        config.congenica_bam_inputname,
                        jobid,
                        workflow.bam_out,
                    )
                )
            elif workflow.name == "mokapipe":
                print(
                    " %s%s:%s%s%s:%s"
                    % (
                        config.congenica_vcf_inputname,
                        jobid,
                        workflow.vcf_out,
                        config.congenica_bam_inputname,
                        pipe_bam_jobid,
                        workflow.bam_out,
                    )
                )


if __name__ == "__main__":
    args = get_arguments()
    ajson = json.loads(
        subprocess.check_output(
            [
                "dx",
                "describe",
                args.analysis_id,
                "--auth",
                config.nexus_apikey,
                "--json",
            ]
        )
    )

    # Get settings for analysis panel (used to determine which workflow is running)
    pannumber = re.search(r"Pan\d+", ajson["name"]).group()
    # Using function imported from upload_and_setoff_workflow.py build the panel dict to be used to
    # determine the workflow etc
    paneldict = RunfolderProcessor.set_panel_dictionary()
    pansettings = paneldict[pannumber]

    # Print decision support tool inputs
    tooler = DecisionTooler()
    workflow = tooler.get_workflow(pansettings)
    jobid, bamjobid = tooler.get_job_id(args.analysis_id, args.project, workflow)
    tooler.printer(jobid, workflow, args.tool, pipe_bam_jobid=bamjobid)
