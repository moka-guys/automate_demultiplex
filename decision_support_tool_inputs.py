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

def set_panel_dictionary():
    """ 
    Populate the dictionary detailing panel specific settings.
    Default settings are set in the config file and then updated as and when required for each panel the defaults in config file.
    Loop through panel specific properties in config file and overwrite any default with panel specific settings
    Return dictionary
    """
    dictionary_to_return = {}
    # for each panel 
    for panel in config.panel_list:          
        # loop through default settings, adding to dictionary and  then loop through panel settings from config, overwriting any defaults
        dictionary_to_return[panel] = {}
        for setting in  config.default_panel_properties:
            dictionary_to_return[panel][setting] = config.default_panel_properties[setting]
        for setting in config.panel_settings[panel]:
            dictionary_to_return[panel][setting] = config.panel_settings[panel][setting]
    return dictionary_to_return

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
                    if stage["execution"]["name"] == "Sentieon DNAseq FASTQ to VCF":
                        if stage['execution']['output'] and 'mappings_realigned_bam' in stage['execution']['output']:
                            return stage['execution']['id']
                        elif stage['execution']['dependsOn'] != []:
                            return stage['execution']['dependsOn'][0]
                else:
                    tries += 1
                    if tries == 1000:
                        raise Exception('No stage found in job')
            except IndexError:
                tries += 1
                if tries == 1000: # Can take a while for the server to update
                    raise Exception('Maximum Tries Exceeded')


    def _get_mokapipe_jobid(self, analysis_id, project):
        cmd = "source /etc/profile.d/dnanexus.environment.sh; dx describe %s:%s --json --auth-token %s " % (project,analysis_id, config.Nexus_API_Key)
        proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        # capture the streams
        (out, err) = proc.communicate()
        json_ob=json.loads(out)
        for stage in json_ob["stages"]:
            if stage["execution"]["stage"] == 'stage-F2gPqFQ025p601qgGq0QVvX2':
                return stage['execution']['id']

    def get_job_id(self, analysis_id, project, workflow):
        if workflow.name == 'mokawes':
            return self._get_mokawes_jobid(analysis_id, project)
        elif workflow.name == 'mokapipe':
            return self._get_mokapipe_jobid(analysis_id, project)

    def get_workflow(self, ps):
        if ps['mokawes']:
            return self.wfo('mokawes', config.mokawes_senteion_vcf_output_name, config.mokawes_senteion_bam_output_name, config.mokawes_senteion_bai_output_name)
        elif ps['mokapipe']:
            return self.wfo('mokapipe', config.mokapipe_vcf_output_name, None, None)

    def printer(self, workflow, tool):
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
            print(
                " %s%s:%s%s%s:%s" % (
                config.sapientia_vcf_inputname, jobid, workflow.vcf_out,
                config.sapientia_bam_inputname, jobid, workflow.bam_out
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
    paneldict = set_panel_dictionary()
    pansettings = paneldict[pannumber]

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
        