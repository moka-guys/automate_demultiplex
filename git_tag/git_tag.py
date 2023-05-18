"""
This script contains the function used to obtain the git tag of the current
version of the repository
"""

import subprocess
import os


def git_tag():
    """Obtain the git tag of the current commit"""
    filepath = os.path.dirname(os.path.realpath(__file__))
    cmd = f"git -C {filepath} describe --tags"

    proc = subprocess.Popen(
        [cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
    )
    out, _ = proc.communicate()
    #  Return standard out, removing any new line characters
    return out.rstrip().decode("utf-8")


if __name__ == "__main__":
    print(git_tag())
