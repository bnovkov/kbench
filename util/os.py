import ctypes
import threading
import logging as log
from ctypes.util import find_library

libc = ctypes.CDLL(find_library("c"))


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
