"""
Main entry point for demultiplex module.

Demultiplexes NGS Run Folders. See README and docstrings for further details
"""
from demultiplex import demultiplex
import toolbox.toolbox as toolbox
import ad_logger.ad_logger as ad_logger


gr_obj = demultiplex.GetRunfolders()
toolbox.script_start_logmsg(gr_obj.script_logger, __file__)

gr_obj.setoff_processing()

toolbox.script_end_logmsg(gr_obj.script_logger, __file__)
ad_logger.shutdown_logs(gr_obj.script_logger)
