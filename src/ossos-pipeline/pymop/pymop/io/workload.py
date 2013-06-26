__author__ = "David Rusk <drusk@uvic.ca>"

import os


class NoAvailableWorkException(Exception):
    """"No more work is available."""


class WorkUnit(object):
    def __init__(self, filename, data):
        self.filename = filename
        self.data = data

    def get_filename(self):
        return self.filename


class WorkUnitFactory(object):
    def __init__(self, directory_manager, progress_manager, parser):
        self.directory_manager = directory_manager
        self.progress_manager = progress_manager
        self.parser = parser

    def create_workunit(self):
        potential_files = self.directory_manager.get_listing()

        while len(potential_files) > 0:
            potential_file = potential_files.pop()

            if not self.progress_manager.is_done(potential_file):
                return WorkUnit(
                    potential_file,
                    self.parser.parse(
                        self.directory_manager.get_full_path(potential_file)))

        raise NoAvailableWorkException()


class DirectoryManager(object):
    def __init__(self, directory):
        self.directory = directory

    def get_listing(self, suffix):
        return listdir_for_suffix(self.directory, suffix)

    def get_full_path(self, filename):
        return os.path.join(self.directory, filename)


def listdir_for_suffix(directory, suffix):
    """Note this returns file names, not full paths."""
    return filter(lambda name: name.endswith(suffix), os.listdir(directory))
