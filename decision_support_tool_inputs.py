'''
In order to run some run wide tasks we need to supply the inputs in the form jobid.output_name
This is hard to do if we are running workflows as the job id relates to one app within a workflow.
This script takes an analysis id and returns the job id of the specific stage.
The script will print the output to the command line, in a tool specific format as per the module/arguments provided.
'''

import subprocess
import json
import argparse
import time
# import config file
import automate_demultiplex_config as config
import json
import re

from collections import namedtuple

def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments and help menu
    """
    # Create ArgumentParser object. Description message will be displayed as part of help message if script is run with -h flag
    parser = argparse.ArgumentParser(description='given an analysis-id will obtain the job ids for bam and vcf files for upload to the specified decision support tool')
    # Define the arguments that will be taken.
    parser.add_argument('-a', '--analysis_id', required=True, help='workflow Analysis ID in format Analysis-abc123')
    parser.add_argument('-t', '--tool', choices=['iva', 'sapientia'], required=True, help='decision support tool (iva or sapientia)')
    parser.add_argument('-p', '--project',  required=True, help='The DNAnexus project id in which the analysis is running')
    # Return the arguments
    return parser.parse_args()

# def get_sapientia_job_id(project, analysis_id):
#     cmd = "source /etc/profile.d/dnanexus.environment.sh; dx describe %s:%s --json --auth-token %s " % (project,analysis_id, config.Nexus_API_Key)






# def print_sapientia_input (jobid):
#     """
#     The sapientia import app takes VCFs and BAMs. 
#     Return the app specific input, using the senteion job id and output name.
#     """
#     print(config.sapientia_vcf_inputname + jobid + "." + config.mokawes_senteion_vcf_output_name + config.sapientia_bam_inputname + jobid + "." + config.mokawes_senteion_bam_output_name)

# def print_iva_input (jobid):
#     """
#     The IVA import app takes VCFs, BAMs and BAIs. 
#     Return the app specific input, using the sapientia job id and output names.
#     """
#     print(" %s%s:%s%s%s:%s%s%s:%s" % (config.iva_vcf_inputname, jobid, config.mokawes_senteion_vcf_output_name, config.iva_bam_inputname, jobid, config.mokawes_senteion_bam_output_name,config.iva_bai_inputname, jobid, config.mokawes_senteion_bai_output_name))

def get_panel_settings(analysis_id):
    pass

class DecisionTooler():

    wfo = namedtuple('Workflow', 'name vcf_out bam_out bai_out')

    def __init__(self):
        pass

    def _get_mokawes_jobid(self, analysis_id, project):
        # obtain json for dx describe on the given analysis id
        cmd = "source /etc/profile.d/dnanexus.environment.sh; dx describe %s:%s --json --auth-token %s " % (project,analysis_id, config.Nexus_API_Key)

        # jobid comes from the sention sub-job, which takes a few moments to initiate after calling the sention app.
        # Running this script immeidately after running the sention workflow raises an IndexError.
        #   We retry in the while loop until the jobid becomes available.
        jobid = None
        tries = 0
        while jobid == None:
            try:
                # execute command
                proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                # capture the streams
                (out, err) = proc.communicate()
                json_ob=json.loads(out)
                for stage in json_ob["stages"]:
                    if stage["execution"]["stage"] in config.wes_sention_samplename:
                        # Outputs from the sention job in the workflow/analysis are linked to a sub-job.
                        # The ID for the sub-job can be pulled from the first dependsOn field of the sention job.
                        return stage['execution']['dependsOn'][0]
                else:
                    raise Exception('No stage found in job')
            except IndexError:
                tries += 1
                if tries == 200: # Can take a while for the server to update
                    raise Exception('Maximum Tries Exceeded')

    def get_job_id(self, analysis_id, project, workflow):
        if workflow.name == 'mokawes':
            return self._get_mokawes_jobid(analysis_id, project)

    def get_workflow(self, ps):
        if ps['mokawes']:
            return self.wfo('mokawes', config.mokawes_senteion_vcf_output_name, config.mokawes_senteion_bam_output_name, config.mokawes_senteion_bai_output_name)

    def printer(self, workflow, tool):
        if tool == "iva":
            print(
                " %s%s:%s%s%s:%s%s%s:%s" % (
                config.iva_vcf_inputname, jobid, workflow.vcf_out,
                config.iva_bam_inputname, jobid, workflow.bam_out,
                config.iva_bai_inputname, jobid, workflow.bai_out
                )
            )


if __name__ == "__main__":
    args = get_arguments()
    ajson = json.loads(
        subprocess.check_output(
            [ 'dx', 'describe', args.analysis_id, '--auth', config.Nexus_API_Key, '--json']
        )
    )
    pannumber = re.search('Pan\d+', ajson['name']).group()
    pansettings = config.panel_settings[pannumber]

    tooler = DecisionTooler()
    workflow = tooler.get_workflow(pansettings)
    jobid = tooler.get_job_id(args.analysis_id, args.project, workflow)
    tooler.printer(workflow, args.tool)

    # if args.tool == "iva":
    #     jobid = get_sention_job_id(args.project, args.analysis_id)
    #     print_iva_input(jobid)
    # if args.tool == "sapientia":
    #     jobid = get_sention_job_id(args.project, args.analysis_id)
    #     print_sapientia_input(jobid)
        