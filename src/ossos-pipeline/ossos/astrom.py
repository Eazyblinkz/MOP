"""
Reads and writes .astrom files.
"""
import os
from ossos.downloads.cutouts.source import SourceCutout
from ossos.gui import logger

__author__ = "David Rusk <drusk@uvic.ca>"

import re

from ossos import storage, wcs

DATASET_ROOT = "vos://cadc.nrc.ca~vospace/OSSOS/dbimages"

# Images from CCDs < 18 have their coordinates flipped
MAX_INVERTED_CCD = 17

HEADER_LINE_LENGTH = 80

FAKE_PREFIX = "fk"

OBS_LIST_PATTERN = "#\s+(?P<rawname>(?P<fk>%s)?(?P<expnum>\d{7})(?P<ftype>[ops])(?P<ccdnum>\d+))" % FAKE_PREFIX

## Observation header keys
MOPVERSION = "MOPversion"

# NOTE: MJD_OBS_CENTER is actually MJD-OBS-CENTER in the .astrom files, but
# dashes aren't valid as regex names so I use underscores
MJD_OBS_CENTER = "MJD_OBS_CENTER"
EXPTIME = "EXPTIME"
THRES = "THRES"
FWHM = "FWHM"
MAXCOUNT = "MAXCOUNT"
CRVAL1 = "CRVAL1"
CRVAL2 = "CRVAL2"
EXPNUM = "EXPNUM"
SCALE = "SCALE"
CHIP = "CHIP"
CRPIX1 = "CRPIX1"
CRPIX2 = "CRPIX2"
NAX1 = "NAX1"
NAX2 = "NAX2"
DETECTOR = "DETECTOR"
PHADU = "PHADU"
RDNOIS = "RDNOIS"

# System header keys
RMIN = "RMIN"
RMAX = "RMAX"
ANGLE = "ANGLE"
AWIDTH = "AWIDTH"

def parse(filename):
    return AstromParser().parse(filename)


def parse_sources(filename):
    return parse(filename).get_sources()


class AstromFormatError(Exception):
    """Base class for errors in working with Astrom files."""


class AstromParser(object):
    """
    Parses a .astrom file (our own format) which specifies exposure numbers,
    identified point sources, their x, y location, source readings for
    potential moving objects, etc.
    """

    def __init__(self):
        """Creates the parser"""

        # Set up the regexes need to parse each section of the .astrom file

        self.obs_list_regex = re.compile(OBS_LIST_PATTERN)

        self.obs_header_regex = re.compile(
            "##\s+MOPversion\s+#\s+"
            "(?P<MOPversion>\d+\.[\d\w]+)\s+"
            "##\s+MJD-OBS-CENTER\s+EXPTIME\s+THRES\s+FWHM\s+MAXCOUNT\s+CRVAL1\s+CRVAL2\s+EXPNUM\s+"
            "#\s+(?P<MJD_OBS_CENTER>\d{4} \d{2} \d+\.\d+)\s+"
            "(?P<EXPTIME>\d+\.\d+)\s+"
            "(?P<THRES>\d+\.\d+)\s+"
            "(?P<FWHM>\d+\.\d+)\s+"
            "(?P<MAXCOUNT>\d+\.\d+)\s+"
            "(?P<CRVAL1>-?\d+\.\d+)\s+"
            "(?P<CRVAL2>-?\d+\.\d+)\s+"
            "(?P<EXPNUM>\d+)\s+"
            "##\s+SCALE\s+CHIP\s+CRPIX1\s+CRPIX2\s+NAX1\s+NAX2\s+DETECTOR\s+PHADU\s+RDNOIS\s+#\s+"
            "(?P<SCALE>\d+\.\d+)\s+"
            "(?P<CHIP>\d+)\s+"
            "(?P<CRPIX1>-?\d+\.\d+)\s+"
            "(?P<CRPIX2>-?\d+\.\d+)\s+"
            "(?P<NAX1>\d+)\s+"
            "(?P<NAX2>\d+)\s+"
            "(?P<DETECTOR>\w+)\s+"
            "(?P<PHADU>\d+\.\d+)\s+"
            "(?P<RDNOIS>\d+\.\d+)"
        )

        self.sys_header_regex = re.compile(
            "##\s+RMIN\s+RMAX\s+ANGLE\s+AWIDTH\s+#\s+"
            "(?P<RMIN>\d+\.\d+)\s+"
            "(?P<RMAX>\d+\.\d+)\s+"
            "(?P<ANGLE>-?\d+\.\d+)\s+"
            "(?P<AWIDTH>\d+\.\d+)"
        )

        self.source_list_reg = re.compile(
            "##\s+X\s+Y\s+X_0\s+Y_0\s+R.A.\s+DEC\s+(.*)",
            re.DOTALL
        )

    def _parse_observation_list(self, filestr):
        matches = self.obs_list_regex.findall(filestr) # returns list of tuples
        return [Observation.from_parse_data(*match) for match in matches]

    def _parse_observation_headers(self, filestr, observations):
        obsnum = 0
        for match in self.obs_header_regex.finditer(filestr):
            obs = observations[obsnum]
            for header_key, header_val in match.groupdict().iteritems():
                obs.header[header_key] = header_val
            obsnum += 1

        assert obsnum == len(observations), ("Number of observations headers "
                                             "parsed doesn't match length of "
                                             "observation list")

    def _parse_system_header(self, filestr):
        sys_header_match = self.sys_header_regex.search(filestr)

        assert sys_header_match is not None, "Could not parse system header"

        return sys_header_match.groupdict()

    def _parse_source_data(self, filestr, observations):
        source_list_match = self.source_list_reg.search(filestr)

        assert source_list_match is not None, "Could not find the source list"

        raw_source_list = (source_list_match.group(1)).split("\n\n")

        sources = []
        for raw_source in raw_source_list:
            source = []

            source_obs = raw_source.strip().split("\n")
            assert len(source_obs) == len(
                observations), "Source doesn't have same number of observations (%d) as in observations list (%d)." % (
                len(source_obs), len(observations))

            x_ref = None
            y_ref = None
            for i, source_ob in enumerate(source_obs):
                fields = source_ob.split()

                if i == 0:
                    x_ref = fields[0]
                    y_ref = fields[1]

                fields.append(x_ref)
                fields.append(y_ref)

                # Find the observation corresponding to this reading
                fields.append(observations[i])

                source.append(SourceReading(*fields))

            sources.append(source)

        return sources

    def parse(self, filename):
        """
        Parses a file into an AstromData structure.

        Args:
          filename: str
            The name of the file whose contents will be parsed.

        Returns:
          data: AstromData
            The file contents extracted into a data structure for programmatic
            access.
        """
        filehandle = storage.open_vos_or_local(filename, "rb")
        filestr = filehandle.read()
        filehandle.close()

        assert filestr is not None, "File contents are None"

        observations = self._parse_observation_list(filestr)

        self._parse_observation_headers(filestr, observations)

        sys_header = self._parse_system_header(filestr)

        sources = self._parse_source_data(filestr, observations)

        return AstromData(observations, sys_header, sources)


class BaseAstromWriter(object):
    """
    Provides base functionality for AstromWriters.  Use the subclass for your
    use case.
    """

    def __init__(self, filehandle):
        self.output_file = filehandle

        self._header_written = False

    def get_filename(self):
        return self.output_file.name

    def _write_line(self, line, ljust=True):
        if ljust:
            line = line.ljust(HEADER_LINE_LENGTH)

        self.output_file.write(line + "\n")

    def _write_blank_line(self):
        self._write_line("", ljust=False)

    def _write_observation_list(self, observations):
        for observation in observations:
            self._write_line("# %s" % observation.rawname)

    def _write_observation_headers(self, observations):
        """
        See src/pipematt/step1matt-c
        """
        for observation in observations:
            header = observation.header

            def get_header_vals(header_list):
                header_vals = []
                for key in header_list:
                    val = header[key]

                    if key == MJD_OBS_CENTER:
                        header_vals.append(val)
                    elif key == DETECTOR:
                        header_vals.append(val.ljust(20))
                    else:
                        header_vals.append(float(val))

                return tuple(header_vals)

            self._write_line("## MOPversion")
            self._write_line("#  %s" % header[MOPVERSION])
            self._write_line("## MJD-OBS-CENTER  EXPTIME THRES FWHM  MAXCOUNT CRVAL1     CRVAL2     EXPNUM")
            self._write_line("# %s%8.2f%6.2f%6.2f%9.1f%11.5f%11.5f%9d" % get_header_vals(
                [MJD_OBS_CENTER, EXPTIME, THRES, FWHM, MAXCOUNT, CRVAL1, CRVAL2, EXPNUM]))
            self._write_line("## SCALE CHIP CRPIX1    CRPIX2    NAX1  NAX2   DETECTOR           PHADU RDNOIS")
            self._write_line("# %6.3f%4d%10.2f%10.2f%6d%6d %s%5.2f %5.2f" % get_header_vals(
                [SCALE, CHIP, CRPIX1, CRPIX2, NAX1, NAX2, DETECTOR, PHADU, RDNOIS]))

    def _write_sys_header(self, sys_header):
        """
        See src/pipematt/step3matt-c
        """
        header_vals = [sys_header[RMIN], sys_header[RMAX], sys_header[ANGLE],
                       sys_header[AWIDTH]]
        self._write_line("##     RMIN    RMAX   ANGLE   AWIDTH")
        self._write_line("# %8.1f%8.1f%8.1f%8.1f" % tuple(map(float, header_vals)))

    def _write_source_data(self, sources):
        """
        See src/jjk/measure3
        """
        for i, source in enumerate(sources):
            self._write_source(source)

    def _write_source(self, source):
        self._write_blank_line()

        for reading in source.get_readings():
            self._write_line(" %8.2f %8.2f %8.2f %8.2f %12.7f %12.7f" % (
                reading.x, reading.y, reading.x0, reading.y0, reading.ra,
                reading.dec), ljust=False)

    def _write_source_header(self):
        self._write_line("##   X        Y        X_0     Y_0          R.A.          DEC")

    def write_headers(self, observations, sys_header):
        """
        Writes the header part of the astrom file so that only the source
        data has to be filled in.
        """
        if self._header_written:
            raise AstromFormatError("Astrom file already has headers.")

        self._write_observation_list(observations)
        self._write_observation_headers(observations)
        self._write_sys_header(sys_header)
        self._write_source_header()

        self._header_written = True

    def flush(self):
        self.output_file.flush()

    def close(self):
        self.output_file.close()


class StreamingAstromWriter(BaseAstromWriter):
    """
    Use if you want to write out sources one-by-one as they are validated.
    See also BulkAstromWriter.
    """

    def __init__(self, filehandle, sys_header):
        super(StreamingAstromWriter, self).__init__(filehandle)
        self.sys_header = sys_header

        # Allow that the headers might have been written out in a previous
        # session by a different writer object.  In this case we just want
        # to be able to add more sources.
        self.output_file.seek(0)
        if re.match(OBS_LIST_PATTERN, self.output_file.read()):
            self._header_written = True

    def write_source(self, source):
        """
        Writes out data for a single source.
        """
        if not self._header_written:
            observations = [reading.get_observation() for reading in source.get_readings()]
            self.write_headers(observations, self.sys_header)

        self._write_source(source)


class BulkAstromWriter(BaseAstromWriter):
    """
    Use if you want to write out an entire AstromData structure at once.
    See also StreamingAstromWriter.
    """

    def __init__(self, filehandle):
        super(BulkAstromWriter, self).__init__(filehandle)

    def write_astrom_data(self, astrom_data):
        """
        Writes a full AstromData structure at once.
        """
        self.write_headers(astrom_data.observations, astrom_data.sys_header)
        self._write_source_data(astrom_data.sources)


class AstromData(object):
    """
    Encapsulates data extracted from an .astrom file.
    """

    def __init__(self, observations, sys_header, sources):
        """
        Constructs a new astronomy data set object.

        Args:
          observations: list(Observations)
            The observations that are part of the data set.
          sys_header: dict
            Key-value pairs of system settings applicable to the data set.
            Ex: RMIN, RMAX, ANGLE, AWIDTH
          sources: list(list(SourceReading))
            A list of point sources found in the data set.  These are
            potential moving objects.  Each point source is itself a list
            of source readings, one for each observation in
            <code>observations</code>.  By convention the ordering of
            source readings must match the ordering of the observations.
        """
        self.observations = observations
        self.sys_header = sys_header
        self.sources = [Source(reading_list) for reading_list in sources]

    def get_reading_count(self):
        count = 0
        for source in self.sources:
            count += source.num_readings()

        return count

    def get_sources(self):
        return self.sources

    def get_source_count(self):
        return len(self.get_sources())


class Source(object):
    """
    A collection of source readings.
    """

    def __init__(self, readings, provisional_name=None):
        self.readings = readings
        self.provisional_name = provisional_name

    def get_reading(self, index):
        return self.readings[index]

    def get_readings(self):
        return self.readings

    def num_readings(self):
        return len(self.readings)

    def has_provisional_name(self):
        return self.provisional_name is not None

    def get_provisional_name(self):
        return self.provisional_name

    def set_provisional_name(self, provisional_name):
        self.provisional_name = provisional_name






class SourceReading(object):
    """
    Data for a detected point source (which is a potential moving objects).
    """

    def __init__(self, x, y, x0, y0, ra, dec, xref, yref, obs, ssos=False,
                 from_input_file=False,
                 null_observation=False,
                 discovery=False):
        """
        Args:
          x, y: the coordinates of the source in this reading.
          x0, y0: the coordinates of the source in this reading, but in
            the coordinate frame of the reference image.
          ra: right ascension
          dec: declination
          xref, yref: coordinates of the source in the reference image, in
            the reference image's coordinate frame.
          obs: the observation in which this reading was taken.
        """
        self.x = float(x)
        self.y = float(y)
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.ra = float(ra)
        self.dec = float(dec)
        self.xref = float(xref)
        self.yref = float(yref)

        self.x_ref_offset = self.x - self.x0
        self.y_ref_offset = self.y - self.y0

        self.obs = obs
        self.ssos = ssos
        self.from_input_file = from_input_file
        self.null_observation = null_observation
        self.discovery = discovery

    @property
    def from_input_file(self):
        return self._from_input_file
    @from_input_file.setter
    def from_input_file(self,from_input_file):
        self._from_input_file = from_input_file

    def __repr__(self):
        return "<SourceReading x=%s, y=%s, x0=%s, y0=%s, ra=%s, dec=%s, obs=%s" % (
            self.x, self.y, self.x0, self.y0, self.ra, self.dec, self.obs)

    @property
    def source_point(self):
        return self.x, self.y

    @property
    def reference_source_point(self):
        """
        The location of the source in the reference image, in terms of the
        current image coordinates.
        """
        return self.xref + self.x_ref_offset, self.yref + self.y_ref_offset

    def get_observation_header(self):
        return self.obs.header

    def get_original_image_size(self):
        header = self.get_observation_header()
        return (int(header[Observation.HEADER_IMG_SIZE_X]),
                int(header[Observation.HEADER_IMG_SIZE_Y]))

    def get_exposure_number(self):
        return self.obs.expnum

    def get_observation(self):
        return self.obs

    def get_coordinate_offset(self, other_reading):
        """
        Calculates the offsets between readings' coordinate systems.

        Args:
          other_reading: ossos.astrom.SourceReading
            The reading to compare coordinate systems with.

        Returns:
          (offset_x, offset_y):
            The x and y offsets between this reading and the other reading's
            coordinate systems.
        """
        my_x, my_y = self.reference_source_point
        other_x, other_y = other_reading.reference_source_point
        return my_x - other_x, my_y - other_y

    def get_image_uri(self):
        return self.obs.get_image_uri()

    def get_apcor_uri(self):
        return self.obs.get_apcor_uri()

    def get_ccd_num(self):
        """
        Returns:
          ccdnum: int
            The number of the CCD that the image is on.
        """
        return int(self.obs.ccdnum)

    def get_extension(self):
        """
        Returns:
          extension: str
            The FITS file extension.
        """
        if self.obs.is_fake():
            # We get the image from the CCD directory and it is not
            # multi-extension.
            return 0

        # NOTE: ccd number is the extension, BUT Fits file extensions start at 1
        # Therefore ccd n = extension n + 1
        return str(self.get_ccd_num() + 1)

    def is_inverted(self):
        """
        Returns:
          inverted: bool
            True if the stored image is inverted.
        """
        logger.debug("Checking invert on {} {}".format(self.obs.expnum, self.obs.ccdnum))
        if self.ssos or self.obs.is_fake():
            # We get the image from the CCD directory and it has already
            # been corrected for inversion.
            logger.debug("Logic override")
            return False
        logger.debug("No override")

        return True if self.get_ccd_num() <= MAX_INVERTED_CCD else False

    def should_invert(self):
        """
        Returns:
          inverted: bool
            True if the stored image should be inverted for display
        """
        if self.ssos or self.obs.is_fake():
            # We get the image from the MEF so flip on display
            return True if self.get_ccd_num() <= MAX_INVERTED_CCD else False

        return False


class ComparisonSource(SourceReading):
    """
    A comparison image for a previous image.
    """

    def __init__(self, reference_source, refs=None):

        if not refs: refs = []
        assert isinstance(reference_source, SourceCutout)
        ref_wcs = wcs.WCS(reference_source.fits_header)
        (ref_ra, ref_dec) = ref_wcs.xy2sky(reference_source.fits_header['NAXIS1']/2.0,
                                           reference_source.fits_header['NAXIS2']/2.0)

        dra = reference_source.fits_header['NAXIS1']*0.1875/3600.0
        ddec= reference_source.fits_header['NAXIS2']*0.1875/3600.0

        logger.debug("BOX({} {} {} {})".format(ref_ra, ref_dec,dra, ddec))
        query_result = storage.cone_search(ref_ra, ref_dec, dra, ddec)
        logger.debug("Ignoring the following exposure numbers: "+str(refs))
        found = False
        comparison = ""
        x = y = -1
        ccd = -1
        astheader = None
        pvwcs = None
        for comparison in query_result['collectionID']:
            logger.debug("Trying comparison image {}".format(comparison))
            if int(comparison) in refs:
                continue
            for ccd in range(36):
                astheader = storage.get_astheader(comparison, ccd)
                pvwcs = wcs.WCS(astheader)
                (x,y) = pvwcs.sky2xy(ref_ra, ref_dec)
                logger.debug("RA/DEC {}/{} of source at X/Y {}/{} compared to {} {}".format(
                    ref_ra, ref_dec, x,y,
                    2112, 4644))
                if 0 <= x <= 2112 and 0 <= y <= 4644:
                    found = True
                    break
            if found:
                break

        if not found:
            logger.critical("No comparison image found for {} {} -> {},{}".format(reference_source.pixel_x,
                                                                                  reference_source.pixel_y,
                                                                                  ref_ra,ref_dec))
            return
        x0 = x
        y0 = y
        xref = x
        yref = y
        observation = Observation.from_source_reference(comparison, ccd, x, y)

        super(ComparisonSource,self).__init__(x=x, y=y,
                                              x0=x0, y0=y0,
                                              xref=xref,
                                              yref=yref,
                                              ra=ref_ra,
                                              dec=ref_dec,
                                              obs=observation,
                                              ssos=True)
        self.astrom_header = astheader
        self.reference_source = reference_source
        del(pvwcs)




class Observation(object):
    """
    Stores data for a single observation (which may be associated with many
    point sources/readings).
    """

    # Aliases for useful header keys
    HEADER_IMG_SIZE_X = NAX1
    HEADER_IMG_SIZE_Y = NAX2

    @staticmethod
    def from_parse_data(rawname, fk, expnum, ftype, ccdnum):
        assert rawname == fk + expnum + ftype + ccdnum
        return Observation(expnum, ftype, ccdnum, fk)

    @staticmethod
    def from_source_reference(expnum, ccd, X, Y):
        """
        Given the location of a source in the image, create a source reading.
        """

        image_uri = storage.dbimages_uri(expnum=expnum,
                                         ccd=None,
                                         version='p',
                                         ext='.fits',
                                         subdir=None)
        logger.debug('Trying to access {}'.format(image_uri))

        if not storage.exists(image_uri, force=False):
            logger.warning('Image not in dbimages? Trying subdir.')
            image_uri = storage.dbimages_uri(expnum=expnum,
                                             ccd=ccd,
                                             version='p')

        if not storage.exists(image_uri, force=False):
            logger.warning("Image doesn't exist in ccd subdir. %s" % image_uri)
            return None

        if X == -9999 or Y == -9999 :
            logger.warning("Skipping {} as x/y not resolved.".format(image_uri))
            return None


        mopheader_uri = storage.dbimages_uri(expnum=expnum,
                                             ccd=ccd,
                                             version='p',
                                             ext='.mopheader')
        if not storage.exists(mopheader_uri, force=False):
            # ELEVATE! we need to know to go off and reprocess/include this image.
            logger.critical('Image exists but processing incomplete. Mopheader missing. {}'.format(image_uri))
            return None


        mopheader = storage.get_mopheader(expnum, ccd)

        # Build astrom.Observation
        observation = Observation(expnum=str(expnum),
                                         ftype='p',
                                         ccdnum=str(ccd),
                                         fk="")

        observation.rawname = os.path.splitext(os.path.basename(image_uri))[0]+str(ccd).zfill(2)

        observation.header = mopheader

        return observation


    def __init__(self, expnum, ftype, ccdnum, fk=""):
        self.expnum = expnum
        self.ftype = ftype
        self.ccdnum = ccdnum
        self.fk = fk

        self.rawname = fk + expnum + ftype + ccdnum

        self.header = {}

    def __repr__(self):
        return "<Observation rawname=%s>" % self.rawname

    def is_fake(self):
        return self.fk == FAKE_PREFIX

    def get_image_uri(self):
        # TODO: make more general - have logic for trying alternative locations
        uri = "%s/%s/" % (DATASET_ROOT, self.expnum)

        if self.is_fake():
            uri += "ccd%s/%s.fits" % (self.ccdnum, self.rawname)
        else:
            uri += "%s%s.fits" % (self.expnum, self.ftype)

        return uri

    def get_object_planted_uri(self):
        return "%s/%s/ccd%s/Object.planted" % (DATASET_ROOT, self.expnum,
                                               self.ccdnum)

    def get_apcor_uri(self):
        ccd = "ccd{:02d}".format(int(self.ccdnum))
        return "%s/%s/%s/%s.apcor" % (DATASET_ROOT, self.expnum,
                                         ccd, self.rawname)
