import os
import shutil
import pathlib
import subprocess

import logging as log

from abc import ABC, abstractmethod


class SrcHandler(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass


class FetchSrcHandler(SrcHandler):
    def __init__(self, url, cwd):
        self.url = url
        self.filename = pathlib.Path(url).name

        if not self.filename:
            raise ValueError(
                f"Invalid source url provided - unable to parse archive name from '{self.url}'"
            )

    def run(self):
        # Do not download if file is already present
        if not os.path.isfile(self.filename):
            log.info(f"Downloading '{self.url}'")
            subprocess.run(["fetch", "-o", self.filename, self.url], check=True)

        log.info(f"Unpacking file '{self.filename}'")
        shutil.unpack_archive(self.filename, "./src")

    def cleanup(self):
        os.remove(self.filename)
