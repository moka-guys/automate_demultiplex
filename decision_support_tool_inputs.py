'''
In order to run some run wide tasks we need to supply the inputs in the form jobid.output_name
This is hard to do if we are running workflows as the job id relates to one app within a workflow.
This script takes an analysis id and returns the job id of the specific stage.
The script will print the output to the command line, in a tool specific format as per the module/arguments provided.
'''

import subprocess
import json
import re
import datetime
from collections import namedtuple
import argparse
# import config file
import automate_demultiplex_config as config
from upload_and_setoff_workflows import process_runfolder


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments and help menu
    """
    # Create ArgumentParser object. Description message will be displayed as part of help message if script is run with -h flag
    parser = argparse.ArgumentParser(description='given an analysis-id will obtain the job ids for bam and vcf files for upload to the specified decision support tool')
    # Define the arguments that will be taken.
    parser.add_argument('-a', '--analysis_id', required=True, help='workflow Analysis ID in format Analysis-abc123')
    parser.add_argument('-t', '--tool', choices=['iva', 'sapientia'], required=True, help='decision support tool (iva or sapientia)')
    parser.add_argument('-p', '--project', required=True, help='The DNAnexus project id in which the analysis is running')
    # Return the arguments
    return parser.parse_args()


class DecisionTooler():
    """
    This class takes an analysis ID and the required information to build the input to the decision support tools
    """
    # named tuple to hold all the output names - This tuple name is "workflow" and has four attributes which can be accessed using Workflow.attribute
    wfo = namedtuple('Workflow', 'name vcf_out bam_out bai_out')

    def __init__(self):
        pass

    def _parse_mokawes_json(self, json_ob):
        """
        Take the JSON from dx describe on MokaWES.
        MokaWES Senteion app is itself a workflow, this means there are two valid approaches to obtaining the job id depending on
        how quickly the dx run command is processed and the senteion workflow is established
        Parse to get the job id using two approaches.
        If not found return null
        """
        #for each stage
        for stage in json_ob["stages"]:
            # check for app name
            if stage["id"] == config.senteion_stage_id:
                return stage["execution"]["id"]
                #if stage['execution']['output'] and 'mappings_realigned_bam' in stage['execution']['output']:
                    # return job id
                    #return stage['execution']['id']
                # the workflow depends on the job set off within the workflow so alternativly can access the jobid here too.
                # elif stage['execution']['dependsOn'] != []:
                #     return stage['execution']['dependsOn'][0]
        # if not found return null - this function is called multiple times
        return None

    def _parse_mokapipe_json(self, json_ob):
        """
        Parse the dx describe output from the mokapipe analysis id
        use the stage id to identify the job id of the required stage (see config file)
        return the job id for the variant annotator app for vcf and the gatk human exome pipeline for BAM
        """
        jobid = None
        bamjobid = None
        for stage in json_ob["stages"]:
            if stage["execution"]["stage"] == config.mokapipe_variant_annotator_stage:
                jobid = stage['execution']['id']
            elif stage["execution"]["stage"] == config.mokapipe_gatk_human_exome_stage:
                bamjobid = stage['execution']['id']
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
        cmd = "source /etc/profile.d/dnanexus.environment.sh; dx describe %s:%s --json --auth-token %s " % (project, analysis_id, config.Nexus_API_Key)
        # jobid comes from the sention sub-job, which takes a few moments to initiate after calling the sention app.
        # Running this script immeidately after running the sention workflow raises an IndexError.
        #   We retry in the while loop until the jobid becomes available.
        jobid = None
        bamjobid = None
        tries = 0
        while not jobid:
            try:
                # execute command
                proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                # capture the streams
                (out, err) = proc.communicate()
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
                if tries == 1000: # Can take a while for the server to update
                    raise Exception('Maximum Tries Exceeded')
        return jobid, bamjobid


    def get_workflow(self, ps):
        """
        input is the panel settings dictionary created outside of this class
        create a namedtuple named as the workflow name and with the output names from the app which produces the decision support tool inputs
        returns the namedtuple
        """
        if ps['mokawes']:
            return self.wfo('mokawes', config.mokawes_senteion_vcf_output_name, config.mokawes_senteion_bam_output_name, config.mokawes_senteion_bai_output_name)
        elif ps['mokapipe']:
            return self.wfo('mokapipe', config.mokapipe_vcf_output_name, config.mokapipe_bam_output_name, None)

    def printer(self, jobid, workflow, tool, pipe_bam_jobid):
        """
        recieves the jobids that created vcf and bam and the decision support tool to be used
        also recieves the named tuple containing the workflow details (output names for each relevant decision support tool input)
        Each tool and each workflow requires a slightly different input.
        prints to stdout the required input for the decision support tool app in form
        decision_suport_tool_input=jobid.outputname
        """
        if tool == "iva":
            if workflow.name == 'mokawes':
                print(
                    " %s%s:%s%s%s:%s%s%s:%s" % (
                    config.iva_vcf_inputname, jobid, workflow.vcf_out,
                    config.iva_bam_inputname, jobid, workflow.bam_out,
                    config.iva_bai_inputname, jobid, workflow.bai_out
                    )
                )
            elif workflow.name == 'mokapipe':
                print(
                    " %s%s:%s" % (
                    config.iva_vcf_inputname, jobid, workflow.vcf_out
                    )
                )
        if tool == "sapientia":
            if workflow.name == 'mokawes':
                print(
                    " %s%s:%s%s%s:%s" % (
                    config.sapientia_vcf_inputname, jobid, workflow.vcf_out,
                    config.sapientia_bam_inputname, jobid, workflow.bam_out
                    )
                )
            elif workflow.name == 'mokapipe':
                print(
                    " %s%s:%s%s%s:%s" % (
                    config.sapientia_vcf_inputname, jobid, workflow.vcf_out,
                    config.sapientia_bam_inputname, pipe_bam_jobid, workflow.bam_out
                    )
                )


if __name__ == "__main__":
    args = get_arguments()
    ajson = json.loads(
        subprocess.check_output(
            ['dx', 'describe', args.analysis_id, '--auth', config.Nexus_API_Key, '--json']
        )
    )

    # Get settings for analysis panel (used to determine which workflow is running)
    pannumber = re.search('Pan\d+', ajson['name']).group()
    # using function imported from upload_and_setoff_workflow.py build the panel dict to be used to determine the workflow etc
    paneldict = process_runfolder("test", str('{:%Y%m%d_%H}'.format(datetime.datetime.now())), True).set_panel_dictionary()
    pansettings = paneldict[pannumber]

    # # Print decision support tool inputs
    tooler = DecisionTooler()
    workflow = tooler.get_workflow(pansettings)
    jobid, bamjobid = tooler.get_job_id(args.analysis_id, args.project, workflow)
    tooler.printer(jobid, workflow, args.tool, pipe_bam_jobid=bamjobid)
