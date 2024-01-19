import json
import ctypes
import subprocess
import logging as log
import contextlib
import os

from ctypes.util import find_library

libc = ctypes.CDLL(find_library("c"))
libutil = ctypes.CDLL(find_library("util"))


def sysctl(name: str, isString=False) -> str | int:
    size = ctypes.c_size_t(0)
    bstr = name.encode("ascii")

    # Find out how big our buffer will be
    libc.sysctlbyname(bstr, None, ctypes.byref(size), None, 0)
    # Make the buffer
    buf = ctypes.create_string_buffer(size.value)
    # Re-run, but provide the buffer
    libc.sysctlbyname(bstr, buf, ctypes.byref(size), None, 0)

    if isString:
        return buf.raw.decode()
    else:
        return ctypes.cast(buf, ctypes.POINTER(ctypes.c_long)).contents.value


def procInfo(name: str):
    psDict = None
    result = subprocess.run(
        ["ps", "x", "--libxo", "json", "-o", "cputime,pid,command"],
        stdout=subprocess.PIPE,
    )

    try:
        psDict = json.loads(result.stdout)
        for procInfo in psDict["process-information"]["process"]:
            if procInfo["command"] == name:
                return procInfo
    except Exception as e:
        log.exception(e, exc_info=True)
        return None

@contextlib.contextmanager
def pushd(dir):
    curdir = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(curdir)
