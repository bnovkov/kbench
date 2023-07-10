import os
import subprocess
import logging as log


def make(*args, envvar=None, rootdir=None, silent=False):
    log.debug("env: %s, rootdir: %s", str(envvar), str(rootdir))
    stdout = None

    if rootdir:
        os.chdir(rootdir)

    if silent:
        stdout = subprocess.DEVNULL

    subprocess.run(["make", *args], env=envvar, stdout=stdout)
