from astropy import units

__author__ = "David Rusk <drusk@uvic.ca>"
from baseviewer import WxMPLFitsViewer
from displayable import DisplayableImageSinglet
from interaction import Signal
from ..gui import logger
from ..downloads.cutouts.source import SourceCutout


class SingletViewer(WxMPLFitsViewer):
    """
    Displays a single FITS image at a time.
    """

    def __init__(self, parent, display):
        super(SingletViewer, self).__init__(parent, display)
        self.xy_changed = Signal()

    def _refresh_markers(self, cutout):
        self._displayables_by_cutout[cutout].clear_markers(self.ds9)
        self.mark_apertures(self.current_cutout)

    def mark_apertures(self, cutout, pixel=False):
        """

        :param cutout: A SourceCutout that is displayed
        :type cutout: SourceCutout
        :param pixel: Mark based on pixel locations or based on RA/DEC ?
        :type pixel: bool
        """

        if not self.mark_source:
            return

        x, y = cutout.pixel_x, cutout.pixel_y
        try:
            radii = (cutout.apcor.aperture, cutout.apcor.sky, cutout.apcor.swidth+cutout.apcor.sky)
        except Exception as ex:
            logger.info("Exception: {0}".format(ex))
            logger.warning("Failed trying to get apcor radius values, using defaults for marking.")
            radii = (4, 15, 30)

        if pixel:
            self._displayables_by_cutout[cutout].place_annulus(x, y, radii, colour='r')
        else:
            cutout.update_pixel_location((x, y), extno=cutout.original_observed_ext)
            radii = [radius * 0.185 * units.arcsec for radius in radii]
            self._displayables_by_cutout[cutout].place_annulus(cutout.ra, cutout.dec, radii, colour='r')

    def place_marker(self, cutout, x, y, radius, colour):
        self._displayables_by_cutout[cutout].place_marker(x, y, radius, colour=colour)

    def register_xy_changed_event_handler(self, handler):
        self.xy_changed.connect(handler)

    def _create_displayable(self, cutout):
        return DisplayableImageSinglet(cutout.hdulist, self.ds9)

    def _attach_handlers(self, displayable):
        displayable.xy_changed.connect(self.xy_changed.fire)
        displayable.focus_released.connect(self.release_focus)

    def _detach_handlers(self, displayable):
        if displayable is not None:
            displayable.xy_changed.disconnect(self.xy_changed.fire)
            displayable.focus_released.disconnect(self.release_focus)
