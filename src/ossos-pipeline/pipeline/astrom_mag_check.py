#!python
"""
Compare the measured fluxes of planted sources against those returned for by digiphot.
"""

__author__ = 'jjk'

import math
import os

from ossos import astrom
from ossos.daophot import TaskError
from ossos.mpc import Time
from ossos.downloads.cutouts import ImageCutoutDownloader
from ossos import storage
import argparse
import logging

logger = logging.getLogger('vos')
logger.setLevel(logging.CRITICAL)
logger.addHandler(logging.StreamHandler())


class PlantedObject(object):
    """
    A class to hold Object.planted files created as part of the OSSOS pipeline.

    """

    def __init__(self, line):
        vals = line.strip().split()
        self.id = int(vals.pop())
        self.rate_arcsec = float(vals.pop())
        self.angle = float(vals.pop())
        self.rate_pixels = float(vals.pop())
        self.mag = float(vals.pop())
        self.y = float(vals.pop())
        self.x = float(vals.pop())
        self.line = line

    def __str__(self):
        return self.line


def match_planted(astrom_filename, match_fname):
    """
    Using the astrom_filename as input get the Object.planted file from VOSpace and match
    planted sources with found sources.

    The Object.planted list is pulled from VOSpace based on the standard file-layout and name of the
    first exposure as read from the .astrom file.

    :param astrom_filename: name of the fk*reals.astrom file to check against Object.planted
    :param match_fname: a file that will contain a list of all planted sources and the matched found source

    """
    image_slice_downloader = ImageCutoutDownloader(slice_rows=100, slice_cols=100)

    fk_candidate_observations = astrom.parse(astrom_filename)
    matches_fptr = storage.open_vos_or_local(match_fname, 'w')

    objects_planted_uri = fk_candidate_observations.observations[0].get_object_planted_uri()
    objects_planted = image_slice_downloader.download_raw(objects_planted_uri, view='data').split('\n')

    planted_objects = []
    for line in objects_planted[1:]:
        if len(line) == 0 or line[0] == '#':
            continue
        planted_objects.append(PlantedObject(line))

    matches_fptr.write("#{}\n".format(fk_candidate_observations.observations[0].rawname))
    matches_fptr.write("{:1s}{} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>8s} \n".format(
        "", objects_planted[0], "x_dao", "y_dao", "mag_dao", "merr_dao", "rate_mes", "ang_mes", "dr_pixels", "mag2_dao", "merr2_dao", "mag3_dao", "merr3_dao"))

    found_idxs = []
    for source in fk_candidate_observations.get_sources():
        reading = source.get_reading(0)
        third = source.get_reading(2)

        cutout = image_slice_downloader.download_cutout(reading, needs_apcor=True)

        try:
            (x, y, mag, merr) = cutout.get_observed_magnitude()
        except Exception as e:
            logger.warning(str(e))
            mag = 0.0
            merr = -1.0

        matched = None
        for idx in range(len(planted_objects)):
            planted_object = planted_objects[idx]
            dist = math.sqrt((reading.x-planted_object.x)**2 + (reading.y - planted_object.y)**2)
            if matched is None or dist < matched:
                matched = dist
                matched_object_idx = idx

        start_jd = Time(reading.obs.header['MJD_OBS_CENTER'], format='mpc', scale='utc').jd
        end_jd = Time(third.obs.header['MJD_OBS_CENTER'], format='mpc', scale='utc').jd

        rate = math.sqrt((third.x - reading.x)**2 + (third.y - reading.y)**2)/(
            24*(end_jd - start_jd))
        angle = math.degrees(math.atan2(third.y - reading.y, third.x - reading.x))

        repeat = ' '
        if matched_object_idx in found_idxs:
            repeat = '#'
        else:
            found_idxs.append(matched_object_idx)

        mags = []
        merrs = []
        for this_reading in source.get_readings()[1:]:
            cutout = image_slice_downloader.download_cutout(this_reading, needs_apcor=True)

            try:
                (this_x, this_y, this_mag, this_merr) = cutout.get_observed_magnitude()
            except Exception as e:
                logger.warning(str(e))
                this_mag = 0.0
                this_merr = -1.0

            mags.append(this_mag)
            merrs.append(this_merr)

        matches_fptr.write("{:1s}{} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} ".format(
            repeat,
            str(planted_objects[matched_object_idx]), reading.x, reading.y, mag, merr, rate, angle, matched))
        for idx in range(len(mags)):
            matches_fptr.write("{:8.2f} {:8.2f}".format(mags[idx], merrs[idx]))
        matches_fptr.write("\n")

    # record the unmatched Object.planted entries, for use in efficiency computing
    for idx in range(len(planted_objects)):
        if idx not in found_idxs:
            planted_object = planted_objects[idx]
            matches_fptr.write("{:1s}{} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f}\n"
                               .format("", str(planted_object), 0, 0, 0, 0, 0, 0, 0))
    matches_fptr.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('astrom_filename',
                        help=".astrom containing objects to match with Object.planted list.")
    parser.add_argument('--dbimages', default='vos:OSSOS/dbimages')
    args = parser.parse_args()

    astrom.DATASET_ROOT = args.dbimages
    storage.DBIMAGES = args.dbimages

    match_filename = os.path.splitext(args.astrom_filename)[0]+'.match'
    false_positive_filename = os.path.splitext(args.astrom_filename)[0]+'.false'

    match_planted(args.astrom_filename, match_filename)