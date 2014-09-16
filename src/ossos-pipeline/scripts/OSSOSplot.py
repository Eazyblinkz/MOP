#!python
from Tkinter import *
import logging
import tkFileDialog
import math
import optparse
import re
import sys
import time

import Polygon
import Polygon.IO
from astropy import coordinates
from astropy import units
import ephem

from ossos.ephem_target import EphemTarget
from ossos.gui import context
from ossos import orbfit, cadc
from ossos import storage
from ossos.coord import Coord
from ossos import mpc
from ossos import wcs


color_key = {"yellow": "Fill colour is yellow == tracking termination",
             "blue": "Outline is blue == ColOSSOS target.",
             'red': "Large ephemeris uncertainty object."}

Neptune = {'Halimde': {"RA": ephem.hours("22:32:05.1"), "DEC": ephem.degrees("-10:08:42")},
           'Psamathe': {"RA": ephem.hours("22:32:41.0"), "DEC": ephem.degrees("-09:48:06")},
           'Sao': {"RA": ephem.hours("22:33:48.6"), "DEC": ephem.degrees("-09:50:02")},
           'Laomedeia': {"RA": ephem.hours("22:32:09.0"), "DEC": ephem.degrees("-10:07:53")},
           'Neso': {"RA": ephem.hours("22:31:31.9"), "DEC": ephem.degrees("-10:19:18")},
           'Neptune': {"RA": ephem.hours("22:32:49.39"), "DEC": ephem.degrees("-09:57:02.8")}}

colossos = ['O13BL3R9',
            'O13BL3SK',
            'O13BL3RB',
            'O13BL3SC',
            'O13BL3S3',
            'O13BL3QX',
            'O13BL3TF',
            'O13BL3TA',
            'O13BL3SN',
            'O13BL3RE',
            'O13BL3RV',
            'O13BL3SY',
            'O13BL3RG',
            'O13BL3RN',
            'O13BL3SW',
            'O13BL3T7',
            'O13BL3RT',
            'O13BL3RQ',
            'O13BL3SH',
            'O13BL3R1',
            'O13BL3RH']
tracking_termination = ['o3e01',
                        'o3e10',
                        'o3e15',
                        'o3e16',
                        'o3e18',
                        'o3e20PD',
                        'o3e21',
                        'o3e22',
                        'o3e23PD',
                        'o3e24',
                        'o3e25',
                        'o3e26',
                        'o3e27PD',
                        'o3e28',
                        'o3e29',
                        'o3e30PD',
                        'o3e32',
                        'o3e33',
                        'o3e34PD',
                        'o3e35',
                        'o3e36',
                        'o3e37PD',
                        'o3e38',
                        'o3e40',
                        'o3e51',
                        'o3e54',
                        "o3o01",
                        "o3o22",
                        "o3o23",
                        "o3o26",
                        "o3o28",
                        "o3o31",
                        "o3o35",
                        "uo3o37",
                        "uo3o38",
                        "uo3o50"]


class Plot(Canvas):
    """A plot class derived from the the Tkinter.Canvas class"""

    def __init__(self, root, width=1.5 * 640, height=1.5 * 480, background='white'):

        self.heliocentric = StringVar()
        self.heliocentric.set("00:00:00.00 +00:00:00.0")
        self.equatorial = StringVar()
        self.equatorial.set("00:00:00.00 +00:00:00.0")
        self.elongation = StringVar()
        self.object_info = StringVar()
        self.expnum = StringVar()
        self.objList = None
        self.elongation.set("0.0")
        self.SearchVar = StringVar()
        self.FilterVar = StringVar()
        self.FilterVar.set("")
        self.camera = StringVar()
        self.show_ellipse = IntVar()
        self.show_ellipse.set(1)
        self.pointing_format = StringVar()
        self.pointing_format.set('CFHT PH')
        self.show_labels = IntVar()
        self.show_labels.set(1)
        self.date = StringVar()
        self.date.set(time.strftime('%Y-%m-%d %H:%M:%S'))
        self.plabel = StringVar()
        self.plabel.set("P0")
        sun = ephem.Sun()
        sun.compute(self.date.get())
        self.sun = Coord((sun.ra, sun.dec))
        self.width = width
        self.unit = StringVar()
        self.unit.set('elong')
        self.height = height
        self.kbos = {}

        Canvas.__init__(self, root, width=width, height=height, background=background)
        self.tk_focusFollowsMouse()

    def load_objects(self, directory_name=None):
        """Load the targets from a file

        """

        for name in Neptune:
            self.kbos[name] = Neptune[name]

        if directory_name is not None:

            working_context = context.get_context(directory_name)

            for filename in working_context.get_listing('ast'):
                fhandle = working_context.open(filename)
                observations = []
                lines = fhandle.read().split('\n')
                fhandle.close()
                for line in lines:
                    if len(line) > 0 and not line.startswith('#'):  # skip the comments, don't care about them here
                        observations.append(mpc.Observation.from_string(line))
                name = filename.rstrip('.ast')  # observations[0].provisional_name
                try:
                    this_orbit = orbfit.Orbfit(observations)
                except Exception as e:
                    logging.error(str(e))
                self.kbos[name] = this_orbit

        self.doplot()


    def eps(self):
        """Print the canvas to a postscript file"""

        #filename = tkFileDialog.asksaveasfile()
        filename = tkFileDialog.asksaveasfilename(message="save postscript to file")
        if filename is None:
            return

        self.postscript(file=filename)

    def newPlot(self):

        self.rgutter = 0
        self.lgutter = 0
        self.tgutter = 0
        self.bgutter = 0
        self.cx1 = self.lgutter
        self.cx2 = self.width - self.rgutter
        self.cy1 = self.height - self.bgutter
        self.cy2 = self.tgutter
        self.current = None
        self.limits(2 * math.pi, 0, -0.5 * math.pi, 0.5 * math.pi)
        self.pointings = []

    def p2c(self, p=None):
        """convert from plot to canvas coordinates.

        See also c2p."""
        if p is None:
            p = [0, 0]

        x = (p[0] - self.x1) * self.xscale + self.cx1
        y = (p[1] - self.y1) * self.yscale + self.cy1
        #logging.debug("p2c: ({},{}) -> ({},{})".format(p[0],p[1], x, y))

        return (x, y)

    def p2s(self, p=None):
        """Convert from plot to screen coordinates"""
        if not p: p = [0, 0]

        s = self.p2c(p)
        return self.c2s(s)

    def c2s(self, p=None):
        """Convert from canvas to screen coordinates"""
        if not p:
            p = [0, 0]

        return p[0] - self.canvasx(self.cx1), p[1] - self.canvasy(self.cy2)

    def c2p(self, p=None):
        """Convert from canvas to plot coordinates.

        See also p2s."""
        if not p:
            p = [0, 0]

        x = (p[0] - self.cx1) / self.xscale + self.x1
        y = (p[1] - self.cy1) / self.yscale + self.y1
        return x, y

    def centre(self):
        """Return the RA/DEC of the center of the visible Canvas."""
        return self.p2s(self.canvasx(self.width / 2.0)), self.p2s(self.canvasy(self.height / 2.0))

    def _convert(self, s, factor=15):
        p = s.split(":")
        h = float(p[0])
        m = float(p[1])
        s = float(p[2])
        sign = 1.0
        if h < 0:
            sign = -1.0
        h = h * sign
        return math.radians(sign * (h + m / 60.0 + s / 3600.0) * factor)

    def hours(self, s):

        return self._convert(s, factor=15.0)

    def degrees(self, s):

        return self._convert(s, factor=360.0)


    def coord_grid(self):
        """Draw a grid of RA/DEC on Canvas."""

        ra2 = math.pi * 2
        ra1 = 0
        dec1 = -1 * math.pi / 2.0
        dec2 = math.pi / 2.0

        dra = math.fabs((self.x2 - self.x1) / 4.0)
        ddec = math.fabs((self.y2 - self.y1) / 4.0)
        logging.debug("Drawing the grid.")
        label = True
        ra = ra1
        while ra <= ra2:
            # create a line that goes from dec1 to dec2 at this ra
            (cx1, cy1) = self.p2c((ra, dec1))
            # ly is the y location mid-way between the top and bottom of the plot
            (cx2, cy2) = self.p2c((ra, dec2))
            # create a dashed line for un-labeled lines
            self.create_line(cx1, cy1, cx2, cy2, dash=(20, 20))
            dec = dec1
            while dec <= dec2:
                if label:
                    # lx is the the x screen coordinate location of the ra
                    (lx, ly) = self.p2c((ra, dec + ddec / 2.0))
                    self.create_text(lx + 5, ly, justify=LEFT,
                                     font=('Times', '-20'),
                                     text="\n".join(str(ephem.hours(ra))[:-3]), fill='brown')
                label = not label
                dec += ddec
            ra += dra

        # plot dec grid lines bewtween South (dec1) and North (dec2) limits of plot
        dec = dec1
        # should we label the current grid line?
        label = True
        while dec <= dec2:
            # create a line the goes from ra1 to ra2 at this dec
            (cx1, cy1) = self.p2c((ra1, dec))
            (cx2, cy2) = self.p2c((ra2, dec))
            self.create_line(cx1, cy1, cx2, cy2, dash=(20, 20))
            ra = ra1
            while ra <= ra2:
                if label:
                    # lx/ly are the screen coordinates of the label
                    (lx, ly) = self.p2c((ra + dra / 2.0, dec))
                    self.create_text(lx, ly - 5, font=('Times', '-20'),
                                     text=str(ephem.degrees(dec)), fill='brown')
                ra += dra
            dec += ddec
            label = not label

    def eq2ec(self, ra, dec):
        sb = math.asin(math.sin(dec) * math.cos(math.radians(23.43)) - math.cos(dec) * math.sin(ra) * math.sin(
            math.radians(23.43)))
        sl = math.acos(math.cos(ra) * math.cos(dec) / math.cos(sb))

        return (sb, sl)

    def pos_update(self, event):


        s = self.sun

        (ra, dec) = self.c2p((self.canvasx(event.x), self.canvasy(event.y)))
        p = Coord((ra, dec))
        elong = math.fabs(p.el - s.el)
        if elong > math.pi:
            elong = 2.0 * math.pi - elong

        p.set_system('ecliptic')
        self.heliocentric.set(str(p))
        p.set_system('ICRS')
        self.equatorial.set(str(p))
        self.elongation.set("%6.2f" % (math.degrees(elong)))


    def helio_grid(self, event):


        (ra, dec) = self.c2p((self.canvasx(event.x), self.canvasy(event.y)))
        p = Coord((ra, dec))
        t1 = Coord((0, p.eb), system='ecliptic')
        for i in range(0, 360):
            a = math.radians(i / 1.0)
            t = Coord((a, p.eb), system='ecliptic')
            self.create_line(t1.ra, t1.dec, t.ra, t.dec)
            self.create_point(t.ra, t.dec, size=1, color='magenta')
            t1 = t

        t1 = Coord((p.el, math.radians(-90)), system='ecliptic')
        for i in range(-90, 90):
            b = math.radians(i / 1.0)
            t = Coord((p.el, b), system='ecliptic')
            self.create_line(t1.ra, t1.dec, t.ra, t.dec)
            self.create_point(t.ra, t.dec, size=1, color='magenta')
            t1 = t

    def tickmark(self, x, y, size=10, orientation=90):
        """Draw a line of size and orientation at x,y"""

        (x1, y1) = self.p2c([x, y])
        x2 = x1 + size * math.cos(math.radians(orientation))
        y2 = y1 - size * math.sin(math.radians(orientation))
        self.create_line(x1, y1, x2, y2)

    def label(self, x, y, label, offset=[0, 0]):
        """Write label at plot coordinates (x,y)"""
        (xc, yc) = self.p2c([x, y])
        return self.create_text(xc - offset[0], yc - offset[1], font=('Times', '-15'), text=label)


    def limits(self, x1, x2, y1, y2):
        """Set the coordinate boundaries of plot"""

        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.xscale = (self.cx2 - self.cx1) / (self.x2 - self.x1)
        self.yscale = (self.cy2 - self.cy1) / (self.y2 - self.y1)

        # Determine the limits of the canvas
        (cx1, cy1) = self.p2c((0, -math.pi / 2.0))
        (cx2, cy2) = self.p2c((2 * math.pi, math.pi / 2.0))
        ## set the scroll region to the size of the camvas plus a boundary to allow the canvas edge to be at centre
        self.config(scrollregion=(
            cx2 - self.width / 2.0, cy2 - self.height / 2.0, cx1 + self.width / 2.0, cy1 + self.height / 2.0))

    def reset(self):
        """Expand to the full scale"""

        sun = ephem.Sun()
        sun.compute(self.date.get())
        self.sun = Coord((sun.ra, sun.dec))

        self.doplot()
        self.plot_pointings()

    def updateObj(self, event):
        """Put this object in the search box"""

        name = self.objList.get("active")
        self.SearchVar.set(name)
        self.object_info.set(str(self.kbos.get(name, '')))
        return

    def relocate(self):
        """Move to the position of self.SearchVar"""

        name = self.SearchVar.get()
        if self.kbos.has_key(name):
            kbo = self.kbos[name]
            assert isinstance(kbo, orbfit.Orbfit)
            date = self.date.get()
            date.replace("/", " ")
            try:
                kbo.predict(self.date.get())
                self.recenter(kbo.coordinate.ra.radians, kbo.coordinate.dec.radians)
                self.create_point(kbo.coordinate.ra.radians, kbo.coordinate.dec.radians, color='blue', size=4)
            except:
                logging.error("failed to compute KBO position")

    def recenter(self, ra, dec):

        # Take the given RA/DEC and make that the center of the view frame.
        (cx, cy) = self.p2c((ra, dec))
        (sx, sy) = self.c2s((cx, cy))
        logging.debug("Canvas: {},{} , Screen: {},{}".format(cx, cy, sx, sy))
        self.scan_mark(int(sx), int(sy))
        self.scan_dragto(480, 360, gain=1)

    def center(self, event):
        logging.debug("EVENT: {} {}".format(event.x, event.y))
        self.scan_mark(event.x, event.y)
        self.scan_dragto(480, 360, gain=1)

    def zoom_in(self, event=None):

        self.zoom(event, scale=2.0)

    def zoom_out(self, event=None):

        self.zoom(event, scale=0.5)

    def zoom(self, event=None, scale=2.0):
        """Zoom in"""

        # # compute the x,y of the center of the screen
        sx1 = (self.cx1 + self.cx2) / 2.0
        sy1 = (self.cy1 + self.cy2) / 2.0

        if not event is None:
            logging.debug("EVENT: {},{}".format(event.x, event.y))
            sx1 = event.x
            sy1 = event.y

        (x, y) = self.c2p((self.canvasx(sx1), self.canvasy(sy1)))
        xw = (self.x2 - self.x1) / 2.0 / scale
        yw = (self.y2 - self.y1) / 2.0 / scale


        ## reset the limits to be centered at x,y with
        ## area of xw*2,y2*2
        self.limits(x - xw, x + xw, y - yw, y + yw)

        self.delete(ALL)
        self.doplot()

    def create_ellipse(self, xcen, ycen, a, b, ang, resolution=40.0):
        """Plot ellipse at x,y with size a,b and orientation ang"""

        e1 = []
        e2 = []
        ang = ang - math.radians(90)
        for i in range(0, int(resolution) + 1):
            x = (-1 * a + 2 * a * float(i) / resolution)
            y = 1 - (x / a) ** 2
            if y < 1E-6:
                y = 1E-6
            y = math.sqrt(y) * b
            ptv = self.p2c((x * math.cos(ang) + y * math.sin(ang) + xcen, y * math.cos(ang) - x * math.sin(ang) + ycen))
            y = -1 * y
            ntv = self.p2c((x * math.cos(ang) + y * math.sin(ang) + xcen, y * math.cos(ang) - x * math.sin(ang) + ycen))
            e1.append(ptv)
            e2.append(ntv)
        e2.reverse()
        e1.extend(e2)
        self.create_line(e1, fill='red', width=1)

    def create_point(self, xcen, ycen, size=10, color='red', fill=None):
        """Plot a circle of size at this x,y location"""

        if fill is None:
            fill = color

        (x, y) = self.p2c((xcen, ycen))
        x1 = x - size
        x2 = x + size
        y1 = y - size
        y2 = y + size
        self.create_rectangle(x1, y1, x2, y2, fill=fill, outline=color)

    def current_pointing(self, index):
        """set the color of the currently selected pointing to 'blue'"""
        if self.current is not None:
            for item in self.pointings[self.current]['items']:
                self.itemconfigure(item, outline="black")
        self.current = index
        for item in self.pointings[self.current]['items']:
            self.itemconfigure(item, outline="blue")

    def delete_pointing(self, event):
        """Delete the currently active pointing"""

        if self.current is None:
            return
        for item in self.pointings[self.current]['items']:
            self.delete(item)
        self.delete(self.pointings[self.current]['label']['id'])
        del (self.pointings[self.current])

        self.current = None


    def load_pointings(self, filename=None):
        """Load some pointings"""

        filename = ( filename is None and tkFileDialog.askopenfilename() or filename)

        if filename is None:
            return

        f = storage.open_vos_or_local(filename)
        lines = f.readlines()
        f.close()
        points = []
        if lines[0][0:5] == "<?xml":
            # ## assume astrores format
            # ## with <DATA at start of 'data' segment
            for i in range(len(lines)):
                if lines[i][0:5] == '<DATA':
                    break
            for j in range(i + 5, len(lines)):
                if lines[j][0:2] == "]]":
                    break
                vs = lines[j].split('|')
                points.append(vs)
        elif lines[0][0:5] == 'index':
            # ## Palomar Format
            # ## OK.. ID/NAME/RA /DEC format
            for line in lines:
                if line[0] == '!' or line[0:5] == 'index':
                    # index is a header line for Palomar
                    continue
                d = line.split()
                if len(d) != 9:
                    sys.stderr.write("Don't understand pointing format\n%s\n" % line)
                    continue
                ras = "%s:%s:%s" % ( d[2], d[3], d[4])
                decs = "%s:%s:%s" % ( d[5], d[6], d[7])
                points.append((d[1].strip(), ras, decs))
        elif lines[0][0:5] == "#SSIM":
            # ## Survey Simulator format
            for line in lines[1:]:
                d = line.split()
                points.append((d[8], d[2], d[3]))
        else:
            # ## try name/ ra /dec / epoch
            for line in lines:
                d = line.split()
                if len(d) != 4:
                    if len(d) != 8:
                        sys.stderr.write("Don't understand pointing format\n%s\n" % ( line))
                        continue
                    line = "%s %s:%s:%s %s:%s:%s %s" % (d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7] )
                    d = line.split()

                f = d[1].count(":")
                if ( f > 0 ):
                    points.append((d[0], d[1], d[2]))
                else:
                    points.append(('', math.radians(float(d[1])), math.radians(float(d[2]))))

        self.plot_points_list(points)
        return

    def plot_points_list(self, points):

        for point in points:
            label = {}
            label['text'] = point[0]
            (ra, dec) = (ephem.hours(point[1]), ephem.degrees(point[2]))
            this_camera = Camera(camera=self.camera.get())
            ccds = this_camera.getGeometry(float(ra), float(dec))
            items = []
            for ccd in ccds:
                if len(ccd) == 4:
                    (x1, y1) = self.p2c((ccd[0], ccd[1]))
                    (x2, y2) = self.p2c((ccd[2], ccd[3]))
                    item = self.create_rectangle(x1, y1, x2, y2, stipple='gray25', fill=None)
                else:
                    (x1, y1) = self.p2c((ccd[0] - ccd[2] / math.cos(ccd[1]), ccd[1] - ccd[2]))
                    (x2, y2) = self.p2c((ccd[0] + ccd[2] / math.cos(ccd[1]), ccd[1] + ccd[2]))
                    item = self.create_oval(x1, y1, x2, y2)
                items.append(item)
            self.pointings.append({"label": label,
                                   "items": items,
                                   "camera": this_camera})

        self.plot_pointings()
        return


    def create_pointing(self, event, label_text=None):
        """Plot the sky coverage of pointing at event.x,event.y on the canvas.

        """

        (ra, dec) = self.c2p((self.canvasx(event.x),
                              self.canvasy(event.y)))
        this_camera = Camera(camera=self.camera.get())
        ccds = this_camera.getGeometry(ra, dec)
        items = []
        for ccd in ccds:
            if len(ccd) == 4:
                (x1, y1) = self.p2c((ccd[0], ccd[1]))
                (x2, y2) = self.p2c((ccd[2], ccd[3]))
                item = self.create_rectangle(x1, y1, x2, y2, stipple='gray25', fill=None)
            else:
                (x1, y1) = self.p2c((ccd[0] - ccd[2]), ccd[1] - ccd[2])
                (x2, y2) = self.p2c((ccd[0] + ccd[2]), ccd[1] + ccd[2])
                item = self.create_oval(x1, y1, x2, y2)
            items.append(item)
        label = {}
        if label_text is None:
            label_text = self.plabel.get()
        label['text'] = label_text
        label['id'] = self.label(this_camera.ra, this_camera.dec, label['text'])
        self.pointings.append({
            "label": label,
            "items": items,
            "camera": this_camera})
        self.current = len(self.pointings) - 1
        self.current_pointing(len(self.pointings) - 1)


    def plot_pointings(self, pointings=None):
        """Plot pointings on canavs"""

        if pointings is None:
            pointings = self.pointings

        i = 0
        for pointing in pointings:
            items = []
            i = i + 1
            label = {}
            label['text'] = pointing['label']['text']
            for ccd in pointing["camera"].getGeometry():
                if len(ccd) == 4:
                    (x1, y1) = self.p2c((ccd[0], ccd[1]))
                    (x2, y2) = self.p2c((ccd[2], ccd[3]))
                    item = self.create_rectangle(x1, y1, x2, y2, stipple='gray25', fill=pointing.get('color', ''))
                else:
                    (x1, y1) = self.p2c((ccd[0] - ccd[2]), ccd[1] - ccd[2])
                    (x2, y2) = self.p2c((ccd[0] + ccd[2]), ccd[1] + ccd[2])
                    item = self.create_oval(x1, y1, x2, y2)
                items.append(item)
            if self.show_labels.get() == 1:
                label['id'] = self.label(pointing["camera"].ra, pointing["camera"].dec, label['text'])
            pointing["items"] = items
            pointing["label"] = label


    def set_pointing_label(self):
        """Let the label of the current pointing to the value in the plabel box"""

        current = self.current
        pointing = self.pointings[current]
        self.delete_pointing(None)
        pointing["label"]['text'] = self.plabel.get()
        self.pointings.append(pointing)
        self.plot_pointings([pointing])
        self.current = current

    def move_pointing(self, event):
        """Grab nearest pointing to event.x,event.y and with cursor"""

        (ra, dec) = self.c2p((self.canvasx(event.x),
                              self.canvasy(event.y)))
        closest = None
        this_pointing = None
        this_index = -1
        index = -1
        for pointing in self.pointings:
            index = index + 1
            # Find the camera we clicked closest too
            ds = pointing["camera"].separation(ra, dec)
            if this_pointing is None or ds < closest:
                this_index = index
                closest = ds
                this_pointing = pointing
        if this_pointing is None:
            return
        self.plabel.set(this_pointing['label']['text'])
        ccds = this_pointing["camera"].getGeometry(ra, dec)
        items = this_pointing["items"]
        label = this_pointing["label"]
        (x1, y1) = self.p2c((this_pointing["camera"].ra, this_pointing["camera"].dec))
        self.coords(label["id"], x1, y1)
        for i in range(len(ccds)):
            ccd = ccds[i]
            item = items[i]
            if len(ccd) == 4:
                (x1, y1) = self.p2c((ccd[0], ccd[1]))
                (x2, y2) = self.p2c((ccd[2], ccd[3]))
            else:
                (x1, y1) = self.p2c((ccd[0] - ccd[2]), ccd[1] - ccd[2])
                (x2, y2) = self.p2c((ccd[0] + ccd[2]), ccd[1] + ccd[2])
            self.coords(item, x1, y1, x2, y2)
        self.current_pointing(this_index)

    def clear_pointings(self):
        """clear the pointings from the display"""

        self.pointings = []
        self.doplot()

    def ossos_pointings(self):
        """
        plot an OSSOS observation on the OSSOS plot.
        """
        match = re.match('(\d+)\D(\d+)', self.expnum.get())
        if match is not None:
            expnum = int(match.group(1))
            ccd = int(match.group(2))
            x = 2112/2.0
            y = 4644/2.0
        else:
            expnum = int(str(self.expnum.get()))
            ccd = 22
            x = 1000
            y = 4644 - 15/0.185
        header = None
        try:
            header = storage.get_astheader(expnum, ccd=ccd)
        except:
            if header is None:
                print "Didn't get a header... "
                return

        ossos_wcs = wcs.WCS(header)
        (ra, dec) = ossos_wcs.xy2sky(x, y)
        class MyEvent(object):
            def __init__(self, x, y):
                self.x = x
                self.y = y

        (x, y) = self.p2s((math.radians(ra), math.radians(dec)))
        event = MyEvent(x, y)
        self.create_pointing(event, label_text=header['OBJECT']+' ccd{}'.format(ccd))


    def get_pointings(self):
        """
        Retrieve the MEGACAM pointings that overlap with the current FOV and plot.
        @return: None
        """

        this_camera = Camera(camera="MEGACAM_1")

        ra_cen = math.degrees((self.x1 + self.x2) / 2.0)
        dec_cen = math.degrees((self.y1 + self.y2) / 2.0)
        width = math.degrees(math.fabs(self.x1 - self.x2))
        height = math.degrees(math.fabs(self.y1 - self.y2))

        table = cadc.cfht_megacam_tap_query(ra_cen, dec_cen, width, height)

        for row in table:
            ra = row['RAJ2000']
            dec = row['DEJ2000']

            class MyEvent(object):
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            (x, y) = self.p2s((ra, dec))
            event = MyEvent(x, y)
            self.create_pointing(event)

    def save_pointings(self):
        """Print the currently defined FOVs"""

        i = 0
        if self.pointing_format.get() == 'CFHT ET':
            for pointing in self.pointings:
                name = pointing["label"]["text"]
                camera = pointing["camera"]
                ccds = camera.getGeometry()
                polygons = []
                for ccd in ccds:
                    polygon = Polygon.Polygon(((ccd[0], ccd[1]),
                                               (ccd[0], ccd[3]),
                                               (ccd[2], ccd[3]),
                                               (ccd[2], ccd[1]),
                                               (ccd[0], ccd[1])))
                    polygons.append(polygon)
                et = EphemTarget(name)
                # determine the mean motion of KBOs in this field.
                field_kbos = []
                center_ra = 0
                center_dec = 0
                for kbo_name in self.kbos:
                    kbo = self.kbos[kbo_name]
                    kbo.predict(mpc.Time(self.date.get(), scale='utc'))
                    ra = kbo.coordinate.ra.radians
                    dec = kbo.coordinate.dec.radians
                    for polygon in polygons:
                        if polygon.isInside(ra, dec):
                            field_kbos.append(kbo)
                            center_ra += ra
                            center_dec += dec
                start_date = mpc.Time(self.date.get(), scale='utc').jd
                trail_mid_point = 6
                for days in range(trail_mid_point * 2 + 1):
                    for hours in range(24):
                        today = mpc.Time(start_date - trail_mid_point + days + hours / 24.0,
                                         scale='utc',
                                         format='jd')
                        mean_motion = (0, 0)
                        if len(field_kbos) > 0:
                            current_ra = 0
                            current_dec = 0
                            for kbo in field_kbos:
                                kbo.predict(today)
                                current_ra += kbo.coordinate.ra.radians
                                current_dec += kbo.coordinate.dec.radians
                            mean_motion = ((current_ra - center_ra) / len(field_kbos),
                                           (current_dec - center_dec) / len(field_kbos))
                        ra = pointing['camera'].coordinate.ra.radians + mean_motion[0]
                        dec = pointing['camera'].coordinate.dec.radians + mean_motion[1]
                        cc = coordinates.ICRSCoordinates(ra=ra,
                                                         dec=dec,
                                                         unit=(units.radian, units.radian),
                                                         obstime=today)
                        et.coordinates.append(cc)
                et.save()
            return
        f = tkFileDialog.asksaveasfile()
        if self.pointing_format.get() == 'Subaru':
            for pointing in self.pointings:
                (sra, sdec) = str(pointing["camera"]).split()
                ra = sra.replace(":", "")
                dec = sdec.replace(":", "")
                name = pointing["label"]["text"]
                f.write("""{}=OBJECT="{}" RA={} DEC={} EQUINOX=2000.0 INSROT_PA=90\n""".format(name,
                                                                                               name,
                                                                                               ra,
                                                                                               dec))
            return
        if self.pointing_format.get() == 'CFHT PH':
            f.write("""<?xml version = "1.0"?>
<!DOCTYPE ASTRO SYSTEM "http://vizier.u-strasbg.fr/xml/astrores.dtd">
<ASTRO ID="v0.8" xmlns:ASTRO="http://vizier.u-strasbg.fr/doc/astrores.htx">
<TABLE ID="Table">
<NAME>Fixed Targets</NAME>
<TITLE>Fixed Targets for CFHT QSO</TITLE>
<!-- Definition of each field -->
<FIELD name="NAME" datatype="A" width="20">
   <DESCRIPTION>Name of target</DESCRIPTION>
</FIELD>
<FIELD name="RA" ref="" datatype="A" width="11" unit="&quot;h:m:s&quot;">
   <DESCRIPTION>Right ascension of target</DESCRIPTION>
</FIELD>     
<FIELD name="DEC" ref="" datatype="A" width="11" unit="&quot;d:m:s&quot;">
   <DESCRIPTION>Declination of target</DESCRIPTION>
</FIELD>     
<FIELD name="EPOCH" datatype="F" width="6">
    <DESCRIPTION>Epoch of coordinates</DESCRIPTION>
</FIELD>     
<FIELD name="POINT" datatype="A" width="5">
<DESCRIPTION>Pointing name</DESCRIPTION>
</FIELD>     
<!-- Data table --> 
<DATA><CSV headlines="4" colsep="|"><![CDATA[
NAME                |RA         |DEC        |EPOCH |POINT|
                    |hh:mm:ss.ss|+dd:mm:ss.s|      |     |
12345678901234567890|12345678901|12345678901|123456|12345|
--------------------|-----------|-----------|------|-----|\n""")
        if self.pointing_format.get() == 'Palomar':
            f.write("index\n")
        for pointing in self.pointings:
            i = i + 1
            name = pointing["label"]["text"]
            (sra, sdec) = str(pointing["camera"]).split()
            ra = sra.split(":")
            dec = sdec.split(":")
            dec[0] = str(int(dec[0]))
            if int(dec[0]) >= 0:
                dec[0] = '+' + dec[0]
            if self.pointing_format.get() == 'Palomar':
                f.write("%5d %16s %2s %2s %4s %3s %2s %4s 2000\n" % (i, name,
                                                                     ra[0].zfill(2),
                                                                     ra[1].zfill(2),
                                                                     ra[2].zfill(2),
                                                                     dec[0].zfill(3),
                                                                     dec[1].zfill(2),
                                                                     dec[2].zfill(2)))
            elif self.pointing_format.get() == 'CFHT PH':
                # f.write("%f %f\n" % (pointing["camera"].ra,pointing["camera"].dec))
                f.write("%-20s|%11s|%11s|%6.1f|%-5d|\n" % (name, sra, sdec, 2000.0, 1))
            elif self.pointing_format.get() == 'KPNO/CTIO':
                str1 = sra.replace(":", " ")
                str2 = sdec.replace(":", " ")
                f.write("%16s %16s %16s 2000\n" % ( name, str1, str2))
            elif self.pointing_format.get() == 'SSim':
                ra = []
                dec = []
                for ccd in pointing["camera"].getGeometry():
                    ra.append(ccd[0])
                    ra.append(ccd[2])
                    dec.append(ccd[1])
                    dec.append(ccd[3])

                dra = math.degrees(math.fabs(max(ra) - min(ra)))
                ddec = math.degrees(math.fabs(max(dec) - min(dec)))
                f.write("%f %f %16s %16s DATE 1.00 1.00 500 FILE\n" % (dra, ddec, sra, sdec ))
        if self.pointing_format.get() == 'CFHT PH':
            f.write("""]]</CSV></DATA>
</TABLE>
</ASTRO>
""")
        f.close()

    def doplot(self):
        """
        Clear the plot and then redraw it.

        """
        w = self
        w.delete(ALL)
        w.coord_grid()
        w.objList.delete(0, END)
        self._plot()

    def _plot(self):
        """Draw the actual plot.

        """

        w = self
        kbos = self.kbos
        re_string = w.FilterVar.get()
        vlist = []
        for name in kbos:
            if not re.search(re_string, name):
                continue
            vlist.append(name)
            fill = None
            is_colossos_target = False
            for cname in colossos:
                if cname in name:
                    is_colossos_target = True
                    print "ColOSSOS: ", cname
                    break
            is_terminated = False
            for cname in tracking_termination:
                if cname in name:
                    is_terminated = True
                    print "Terminated", cname
                    break
            if type(kbos[name]) == type(ephem.EllipticalBody()):
                try:
                    kbos[name].compute(w.date.get())
                except Exception as e:
                    logging.error("Failed to compute KBO position. {}".format(name))
                    continue
                ra = kbos[name].ra
                dec = kbos[name].dec
                a = math.radians(10.0 / 3600.0)
                b = a
                ang = 0.0
                point_size = 2
                yoffset = +10
                xoffset = +10
            elif isinstance(kbos[name], orbfit.Orbfit):
                yoffset = -10
                xoffset = -10
                kbo = kbos[name]
                start_date = mpc.Time(w.date.get(), scale='utc').jd
                trail_mid_point = 0
                for days in range(trail_mid_point * 2 + 1):
                    point_size = days == trail_mid_point and 5 or 1
                    today = mpc.Time(start_date - trail_mid_point + days, scale='utc', format='jd')
                    kbo.predict(today, 568)
                    ra = kbo.coordinate.ra.radians
                    dec = kbo.coordinate.dec.radians
                    a = math.radians(kbo.dra / 3600.0)
                    b = math.radians(kbo.ddec / 3600.0)
                    ang = math.radians(kbo.pa)
                    lost = False
                    if a > math.radians(0.3):
                        lost = True

                fill_colour = lost and "red" or "green"
                fill_colour = is_colossos_target and "blue" or fill_colour
                point_colour = is_terminated and "red" or "yellow"
                w.create_point(ra, dec, size=point_size, color=point_colour, fill=fill_colour)
                if w.show_ellipse.get() == 1 and days == trail_mid_point:
                    if a < math.radians(5.0):
                        w.create_ellipse(ra, dec, a, b, ang)
                    if w.show_labels.get() == 1:
                        w.label(ra, dec, name, offset=[xoffset, yoffset])
            else:
                ra = kbos[name]['RA']
                dec = kbos[name]['DEC']
                w.create_point(ra, dec, size=6, color='cyan')
                w.label(ra, dec, name, offset=[-15, +15])

        vlist.sort()
        for v in vlist:
            w.objList.insert(END, v)
        w.plot_pointings()


class Camera:
    """The Field of View of a direct imager"""

    geometry = {"MP_CCD": [
        {"ra": 0., "dec": 0., "dra": 0.1052, "ddec": 0.2344}],
                "HSC": [{"ra": 0.0, "dec": 0.0, "rad": 0.75}],
                "MEGACAM_00": [{"ra": 0, "dec": 0, "dra": 2112*0.185/3600.0, "ddec": 4640*0.185/3600.0}],
                "MEGACAM_36": [{ "ra": 0.435, "dec": 0.394, "dra": 0.111, "ddec": 0.238},
{ "ra": 0.327, "dec": 0.394, "dra": 0.112, "ddec": 0.238},
{ "ra": 0.218, "dec": 0.394, "dra": 0.112, "ddec": 0.239},
{ "ra": 0.108, "dec": 0.393, "dra": 0.112, "ddec": 0.239},
{ "ra": -0.001, "dec": 0.392, "dra": 0.111, "ddec": 0.240},
{ "ra": -0.111, "dec": 0.391, "dra": 0.111, "ddec": 0.240},
{ "ra": -0.221, "dec": 0.390, "dra": 0.110, "ddec": 0.240},
{ "ra": -0.330, "dec": 0.389, "dra": 0.109, "ddec": 0.240},
{ "ra": -0.438, "dec": 0.387, "dra": 0.108, "ddec": 0.239},
{ "ra": 0.439, "dec": 0.134, "dra": 0.110, "ddec": 0.240},
{ "ra": 0.330, "dec": 0.134, "dra": 0.111, "ddec": 0.241},
{ "ra": 0.220, "dec": 0.133, "dra": 0.111, "ddec": 0.241},
{ "ra": 0.110, "dec": 0.133, "dra": 0.111, "ddec": 0.242},
{ "ra": 0.000, "dec": 0.132, "dra": 0.112, "ddec": 0.242},
{ "ra": -0.110, "dec": 0.131, "dra": 0.111, "ddec": 0.242},
{ "ra": -0.219, "dec": 0.130, "dra": 0.111, "ddec": 0.242},
{ "ra": -0.329, "dec": 0.129, "dra": 0.110, "ddec": 0.242},
{ "ra": -0.438, "dec": 0.128, "dra": 0.109, "ddec": 0.241},
{ "ra": 0.440, "dec": -0.105, "dra": 0.109, "ddec": 0.241},
{ "ra": 0.331, "dec": -0.106, "dra": 0.110, "ddec": 0.241},
{ "ra": 0.222, "dec": -0.107, "dra": 0.111, "ddec": 0.242},
{ "ra": 0.112, "dec": -0.108, "dra": 0.111, "ddec": 0.242},
{ "ra": 0.002, "dec": -0.109, "dra": 0.112, "ddec": 0.242},
{ "ra": -0.108, "dec": -0.109, "dra": 0.112, "ddec": 0.242},
{ "ra": -0.218, "dec": -0.110, "dra": 0.112, "ddec": 0.241},
{ "ra": -0.327, "dec": -0.111, "dra": 0.111, "ddec": 0.241},
{ "ra": -0.436, "dec": -0.111, "dra": 0.111, "ddec": 0.240},
{ "ra": 0.441, "dec": -0.364, "dra": 0.108, "ddec": 0.239},
{ "ra": 0.332, "dec": -0.365, "dra": 0.109, "ddec": 0.240},
{ "ra": 0.223, "dec": -0.367, "dra": 0.110, "ddec": 0.240},
{ "ra": 0.114, "dec": -0.368, "dra": 0.111, "ddec": 0.240},
{ "ra": 0.004, "dec": -0.369, "dra": 0.111, "ddec": 0.240},
{ "ra": -0.105, "dec": -0.370, "dra": 0.112, "ddec": 0.239},
{ "ra": -0.215, "dec": -0.370, "dra": 0.112, "ddec": 0.239},
{ "ra": -0.324, "dec": -0.370, "dra": 0.112, "ddec": 0.238},
{ "ra": -0.433, "dec": -0.370, "dra": 0.112, "ddec": 0.238}],
                "LFCNS": [
                    {"ra": -0.0512, "dec": 0.1045, "dra": .1023, "ddec": 0.2047},
                    {"ra": 0.0512, "dec": 0.1045, "dra": .1023, "ddec": 0.2047},
                    {"ra": -0.0512, "dec": -0.1045, "dra": .1023, "ddec": 0.2047},
                    {"ra": 0.0512, "dec": -0.1045, "dra": .1023, "ddec": 0.2047},
                    {"ra": 0.1536, "dec": 0., "dra": .1023, "ddec": 0.2047},
                    {"ra": -0.1536, "dec": 0., "dra": .1023, "ddec": 0.2047}],
                "LFCEW": [
                    {"dec": -0.0532, "ra": 0.1045, "ddec": .1023, "dra": 0.2047},
                    {"dec": 0.0532, "ra": 0.1045, "ddec": .1023, "dra": 0.2047},
                    {"dec": -0.0532, "ra": -0.1045, "ddec": .1023, "dra": 0.2047},
                    {"dec": 0.0532, "ra": -0.1045, "ddec": .1023, "dra": 0.2047},
                    {"dec": 0.1598, "ra": 0., "ddec": .1023, "dra": 0.2047},
                    {"dec": -0.1598, "ra": 0., "ddec": .1023, "dra": 0.2047}],
                "MEGACAM_1": [
                    {"ra": 0, "dec": 0, "dra": 0.98, "ddec": 0.98}],
                "MMCAM": [
                    {'ra': -0.162500, 'dec': -0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': -0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': -0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': -0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': 0.000000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': 0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': 0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': 0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.162500, 'dec': 0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': -0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': -0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': -0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': -0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': 0.000000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': 0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': 0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': 0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': -0.051389, 'dec': 0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': -0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': -0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': -0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': -0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': 0.000000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': 0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': 0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': 0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.051389, 'dec': 0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': -0.189444, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': -0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': -0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': -0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': 0.000000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': 0.047500, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': 0.095000, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': 0.141944, 'dra': 0.102222, 'ddec': 0.045333},
                    {'ra': 0.162500, 'dec': 0.189444, 'dra': 0.102222, 'ddec': 0.045333}
                ],
                "MEGACAM_2": [
                    {"ra": 0, "dec": -0.252, "dra": 0.98, "ddec": 0.478},
                    {"ra": 0, "dec": +0.235, "dra": 0.98, "ddec": 0.478}],
                "EW-MOSAIC": [
                    {"dec": 1.5 * 0.1479 + 0.0036, "ra": -0.1479 - 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": 0.5 * 0.1479 + 0.0011, "ra": -0.1479 - 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": -0.5 * 0.1479 - 0.0011, "ra": -0.1479 - 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": -1.5 * 0.1479 - 0.0036, "ra": -0.1479 - 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": 1.5 * 0.1479 + 0.0036, "ra": 0.1479 + 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": 0.5 * 0.1479 + 0.0011, "ra": 0.1479 + 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": -0.5 * 0.1479 - 0.0011, "ra": 0.1479 + 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                    {"dec": -1.5 * 0.1479 - 0.0036, "ra": 0.1479 + 0.0019, "dra": 2.0 * 0.1479, "ddec": 0.1479, },
                ],
                "NS-MOSAIC": [
                    {"ra": 1.5 * 0.1479 + 0.0036, "dec": -0.1479 - 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": 0.5 * 0.1479 + 0.0011, "dec": -0.1479 - 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": -0.5 * 0.1479 - 0.0011, "dec": -0.1479 - 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": -1.5 * 0.1479 - 0.0036, "dec": -0.1479 - 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": 1.5 * 0.1479 + 0.0036, "dec": 0.1479 + 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": 0.5 * 0.1479 + 0.0011, "dec": 0.1479 + 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": -0.5 * 0.1479 - 0.0011, "dec": 0.1479 + 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                    {"ra": -1.5 * 0.1479 - 0.0036, "dec": 0.1479 + 0.0019, "ddec": 2.0 * 0.1479, "dra": 0.1479, },
                ],
                "L2": [{"ra": 0, "dec": +0.98 * 0.5, "ddec": 1.0 * 0.98, "dra": 8.0 * 0.98},
                       {"ra": 0, "dec": -0.98 * 0.5, "ddec": 1.0 * 0.98, "dra": 8.0 * 0.98}],
                "SSC": [
                    {"ra": -2 * (0.20 * 2048 + 15.0) / 3600.0, "dec": 0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": -1 * (0.20 * 2048 + 15.0) / 3600.0, "dec": 0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": -0 * (0.20 * 2048 + 15.0) / 3600.0, "dec": 0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": 1 * (0.20 * 2048 + 15.0) / 3600.0, "dec": 0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": 2 * (0.20 * 2048 + 15.0) / 3600.0, "dec": 0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": -2 * (0.20 * 2048 + 15.0) / 3600.0, "dec": -0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": -1 * (0.20 * 2048 + 15.0) / 3600.0, "dec": -0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": -0 * (0.20 * 2048 + 15.0) / 3600.0, "dec": -0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": 1 * (0.20 * 2048 + 15.0) / 3600.0, "dec": -0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0},
                    {"ra": 2 * (0.20 * 2048 + 15.0) / 3600.0, "dec": -0.5 * (4096 * 0.20 + 15.0) / 3600.0,
                     "ddec": 0.20 * 4096 / 3600.0, "dra": 0.20 * 2048 / 3600.0}],
                "SSC1": [{"ra": 0.0, "dec": 0.0, "dra": 5 * (0.20 * 2048 / 3600.0 + 15.0 / 3600.0) - 15.0 / 3600.0,
                          "ddec": 2 * 0.20 * 4096 / 3600 + 15.0 / 3600.0}]
    }

    @property
    def coordinate(self):
        return coordinates.ICRSCoordinates(
            ra=math.degrees(self.ra),
            dec=math.degrees(self.dec),
            unit=(units.degree, units.degree))

    def __init__(self, camera="MEGACAM_36"):
        if camera == '':
            camera = "MEGACAM_36"
        self.camera = camera

    def __str__(self):

        return "%s %s" % ( self.ra, self.dec )

    def getGeometry(self, ra=None, dec=None):
        """Return an array of rectangles that represent the 'ra,dec' corners of the FOV"""

        ccds = []

        if ra is None:
            ra = self.ra
        if dec is None:
            dec = self.dec
        self.ra = ephem.hours(ra)
        self.dec = ephem.degrees(dec)
        for geo in self.geometry[self.camera]:
            ycen = math.radians(geo["dec"]) + dec
            xcen = math.radians(geo["ra"]) / math.cos(ycen) + ra
            try:
                dy = math.radians(geo["ddec"])
                dx = math.radians(geo["dra"] / math.cos(ycen))
                ccds.append([xcen - dx / 2.0, ycen - dy / 2.0, xcen + dx / 2.0, ycen + dy / 2.0])
            except:
                rad = math.radians(geo["rad"])
                ccds.append([xcen, ycen, rad])
        return ccds


    def separation(self, ra, dec):
        """Compute the separation between self and (ra,dec)"""

        return ephem.separation((self.ra, self.dec), (ra, dec))


def start(dirname=None, pointings=None):
    root = Tk()
    # ## Make the root window resizeable
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # ## The PLOT frame
    pframe = Frame()
    pframe.grid(sticky=N + S + E + W)
    pframe.rowconfigure(0, weight=1)
    pframe.columnconfigure(0, weight=1)

    ### Make a plot (w) in the plotFrame
    ## with scroll bars
    w = Plot(pframe)
    sx = Scrollbar(pframe, orient=HORIZONTAL, command=w.xview)
    sy = Scrollbar(pframe, orient=VERTICAL, command=w.yview)
    w.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    sx.grid(row=1, column=0, sticky=E + W)
    sy.grid(row=0, column=1, sticky=N + S)

    ### Get the mouse to do intersting stuff
    w.bind('<Key-g>', w.helio_grid)
    w.bind('<Motion>', w.pos_update)
    w.bind('<Double-Button-1>', w.create_pointing)
    w.bind('<Key-Delete>', w.delete_pointing)
    w.bind('<Key-BackSpace>', w.delete_pointing)
    w.bind('<B1-Motion>', w.move_pointing)
    w.bind('<Control-equal>', w.zoom_in)
    w.bind('<Control-minus>', w.zoom_out)
    w.bind('<Control-Button-1>', w.center)
    w.grid(row=0, column=0, sticky=N + S + E + W)

    ### The infomration Panel
    infoPanel = Frame(root)
    ### Coordinates box
    coordsBox = Frame(infoPanel)
    Label(coordsBox, text="Heliocentric:").grid(row=0, column=0, sticky=E)
    Label(coordsBox, textvariable=w.heliocentric).grid(row=0, column=1, sticky=W)
    Label(coordsBox, text="Equatorial:").grid(row=1, column=0, sticky=E)
    Label(coordsBox, textvariable=w.equatorial).grid(row=1, column=1, sticky=W)
    Label(coordsBox, text="Solar Elong.:").grid(row=3, column=0, sticky=E)
    Label(coordsBox, textvariable=w.elongation).grid(row=3, column=1, sticky=W)

    Entry(coordsBox, textvariable=w.date).grid(row=6, column=1, sticky=W)
    Label(coordsBox, text="Date: ").grid(row=6, column=0, sticky=E)
    Button(coordsBox, text="Update ", command=w.reset).grid(row=6, column=2, sticky=W)

    Entry(coordsBox, textvariable=w.expnum).grid(row=7, column=1, sticky=W)
    Label(coordsBox, text="Expnum: ").grid(row=7, column=0, sticky=E)
    Button(coordsBox, text="Plot ", command=w.ossos_pointings).grid(row=7, column=2, sticky=W)

    Label(coordsBox, text="Pointing:").grid(row=8, column=0, sticky=W)
    Entry(coordsBox, textvariable=w.plabel).grid(row=9, column=1, sticky=W)
    Label(coordsBox, text="Label:").grid(row=9, column=0, sticky=E)
    Button(coordsBox, text="Update Label", command=w.set_pointing_label).grid(row=9, column=2, sticky=W)

    Label(coordsBox, text="Objects").grid(row=12, column=0, sticky=W)
    Entry(coordsBox, textvariable=w.SearchVar).grid(row=13, column=1, sticky=W)
    Label(coordsBox, text="Search:").grid(row=13, column=0, sticky=E)
    Button(coordsBox, text="GoTo: ", command=w.relocate).grid(row=13, column=2, sticky=W)

    Entry(coordsBox, textvariable=w.FilterVar).grid(row=14, column=1, sticky=W)
    Button(coordsBox, text="Filter", command=w.reset).grid(row=14, column=2, sticky=W)


    ### put a list of the currently visible sources
    list_box = Frame(infoPanel)
    list_box.grid(row=1, column=0)
    w.objList = Listbox(list_box,
                        height=15)
    w.objList.grid(row=1, column=0)
    w.objList.bind('<Button-1>', w.updateObj)

    Label(Frame(infoPanel).grid(row=2, column=0),
          justify=LEFT,
          font=("Helvetica", -20),
          textvariable=w.object_info).grid(row=1, column=0)

    coordsBox.grid(row=0, column=0, sticky=NE)

    ### Pack the major frame bits
    pframe.grid(row=0, column=0)
    infoPanel.grid(row=0, column=1, sticky=NE)

    ### ROOT menu bar
    menubar = Menu(root)

    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Save as .eps", command=w.eps)
    menubar.add_cascade(label="File", menu=file_menu)

    ### MENU To add sources
    source_menu = Menu(menubar, tearoff=0)
    source_menu.add_command(label="Select mpc Directory", command=w.load_objects)
    # source_menu.add_command(label="Load ephem.db File", command=load_edbfile)
    source_menu.add_checkbutton(label='Show Labels', variable=w.show_labels, onvalue=1, command=w.reset)
    source_menu.add_checkbutton(label='Show Ellipses', variable=w.show_ellipse, onvalue=1, command=w.reset)
    menubar.add_cascade(label="Objects", menu=source_menu)

    pointing_menu = Menu(menubar, tearoff=0)
    pointing_menu.add_command(label="Load pointings", command=w.load_pointings)

    pointFormat = Menu(pointing_menu, tearoff=0)
    pointFormat.add_checkbutton(label='CFHT PH', variable=w.pointing_format, onvalue='CFHT PH')
    pointFormat.add_checkbutton(label="CFHT ET", variable=w.pointing_format, onvalue='CFHT ET')
    pointFormat.add_checkbutton(label='Palomar', variable=w.pointing_format, onvalue='Palomar')
    pointFormat.add_checkbutton(label='KPNO/CTIO', variable=w.pointing_format, onvalue='KPNO/CTIO')
    pointFormat.add_checkbutton(label='SSim', variable=w.pointing_format, onvalue='SSim')
    pointFormat.add_checkbutton(label='Subaru', variable=w.pointing_format, onvalue='Subaru')
    pointing_menu.add_cascade(label='Save Format', menu=pointFormat)

    pointing_menu.add_command(label="Save pointings", command=w.save_pointings)
    pointing_menu.add_command(label="Clear pointings", command=w.clear_pointings)
    pointing_menu.add_command(label="Query CFHT Archive", command=w.get_pointings)

    cameramenu = Menu(pointing_menu, tearoff=0)
    for name in Camera.geometry:
        cameramenu.add_checkbutton(label=name, variable=w.camera, onvalue=name)

    pointing_menu.add_cascade(label="Geometry", menu=cameramenu)
    menubar.add_cascade(label="Pointings", menu=pointing_menu)

    ### Zoom Menu
    viewmenu = Menu(root)
    viewmenu.add_command(label="Zoom 2", command=lambda: w.zoom(scale=2))
    viewmenu.add_command(label="Zoom 4", command=lambda: w.zoom(scale=4))
    viewmenu.add_command(label="Zoom 8", command=lambda: w.zoom(scale=8))
    viewmenu.add_command(label="Zoom 16", command=lambda: w.zoom(scale=16))
    viewmenu.add_command(label="Zoom 32", command=lambda: w.zoom(scale=32))
    viewmenu.add_command(label="Zoom 64", command=lambda: w.zoom(scale=64))
    viewmenu.add_command(label="Zoom 1/2", command=lambda: w.zoom(scale=0.5))
    viewmenu.add_command(label="Zoom 1/4", command=lambda: w.zoom(scale=0.25))
    viewmenu.add_command(label="Zoom 1/8", command=lambda: w.zoom(scale=0.125))
    viewmenu.add_command(label="Zoom 1/16", command=lambda: w.zoom(scale=0.125 / 2.0))
    viewmenu.add_command(label="Reset Plot", command=w.reset)
    menubar.add_cascade(label="View", menu=viewmenu)


    ### Stick on the root menubar
    root.config(menu=menubar)
    w.newPlot()
    w.load_objects(directory_name=dirname)
    w.recenter(math.pi, 0)

    root.mainloop()


# ## read in pointings, from a command line file...
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-p", "--pointings", help="A file containing some pointings")
    parser.add_option("-d", "--dirname", help="Directory with mpc/ast files of Kuiper belt objects")
    parser.add_option('--debug', action="store_true")

    for key in color_key:
        print "{} ==> {}\n".format(key, color_key[key])

    (opt, files) = parser.parse_args()

    if opt.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    start(opt.dirname, opt.pointings)
