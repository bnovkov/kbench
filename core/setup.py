import os
import shutil
import subprocess

import logging as log

from abc import ABC, abstractmethod


class SetupHandler(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass


class FetchSetupHandler(SetupHandler):
    def __init__(self, filePath, url):
        self.path = filePath
        self.url = url

    def run(self):
        # Do not download if file is already present
        if os.path.isfile(self.path):
            log.info(f"Skipping setup for {self.path} - source files already present")
            return
        log.info(f"Downloading '{self.url}'")
        subprocess.run(["fetch", "-o", self.path, self.url], check=True)

        log.info(f"Unpacking file '{self.path}'")
        shutil.unpack_archive(self.path)

    def cleanup(self):
        os.remove(self.path)
