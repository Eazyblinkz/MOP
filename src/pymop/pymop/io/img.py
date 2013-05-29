__author__ = "David Rusk <drusk@uvic.ca>"

import cStringIO
import tempfile

from astropy.io import fits


class FitsImage(object):
    """
    Provides the MOP's abstraction of a FITS file image.
    """

    def __init__(self, strdata, coord_converter, in_memory=True):
        """
        Constructs a new FitsImage object.

        Args:
          strdata: str
            Raw data read from a FITS file in string format.
          coord_converter: pymop.io.imgaccess.CoordinateConverter
            Converts coordinates from the original FITS file into pixel
            locations.  Takes into account cutouts.
          in_memory: bool
            If True, the FITS file will only be held in memory without
            writing to disk.  If False, the data will be written to a
            temporary file on disk and not held in memory.
            NOTE: calling as_hdulist will load the data into memory if
            it is only on disk.  Likewise, calling as_file on an "in memory"
            image will cause it to be written to disk.  Therefore this
            parameter is mostly for specifying the PREFERRED way of storing
            the data, not the only way in which it may be stored.
        """
        assert strdata is not None, "No data"
        assert coord_converter is not None, "Must have a coordinate converter"

        self._hdulist = None
        self._tempfile = None

        if in_memory:
            self._hdulist = self._create_hdulist(strdata)
        else:
            self._tempfile = self._create_tempfile(strdata)

        self._coord_converter = coord_converter

    def _create_hdulist(self, strdata):
        return fits.open(cStringIO.StringIO(strdata))

    def _create_tempfile(self, strdata=None):
        tf = tempfile.NamedTemporaryFile(mode="r+b", suffix=".fits")

        if strdata is not None:
            tf.write(strdata)
            tf.flush()
            tf.seek(0)

        return tf

    def get_pixel_coordinates(self, point):
        """
        Retrieves the pixel location of a point within the image given the
        location in the original FITS image.  This takes into account that
        the image may be a cutout of a larger original.

        Args:
          point: tuple(float, float)
            (x, y) in original.

        Returns:
          (x, y) pixel in this image.
        """
        return self._coord_converter.convert(point)

    def as_hdulist(self):
        if self._hdulist is None:
            # we are currently storing "in file" only
            assert self._tempfile is not None

            self._tempfile.seek(0)
            self._hdulist = self._create_hdulist(self._tempfile.read())
            self._tempfile.seek(0)

        return self._hdulist

    def as_file(self):
        if self._tempfile is None:
            # we are currently storing "in memory" only
            assert self._hdulist is not None

            self._tempfile = self._create_tempfile()
            self._hdulist.writeto(self._tempfile.name)

        return self._tempfile

    def close(self):
        if self._hdulist is not None:
            self._hdulist.close()
        if self._tempfile is not None:
            self._tempfile.close()
