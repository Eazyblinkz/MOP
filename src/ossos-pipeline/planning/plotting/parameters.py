__author__ = 'Michele Bannister   git:@mtbannister'

import os

from collections import OrderedDict

MPCORB_FILE = os.path.join(os.getenv('HOME', '/Users/michele/'), 'MPCORB-Distant.dat')
L7MODEL = '/Users/michele/Dropbox/OSSOS/Release_summaries/L7model-3.0-9.0'  # 'vos:OSSOS/CFEPS/L7SyntheticModel-v09.txt'
L7_HOME = '/Users/michele/Dropbox/OSSOS/Release_summaries/'
REAL_KBO_AST_DIR = '/Users/michele/Dropbox/OSSOS/measure3/ossin/'  # 'vos:OSSOS/dbaseclone/ast/'
RELEASE_VERSION = 4
RELEASE_SUMMARY = '/Users/michele/Dropbox/OSSOS/Release_summaries/OSSOSv4/OSSOSv4summary.dat'
RELEASE_CLASSIFICATION = '/Users/michele/Dropbox/OSSOS/Release_summaries/OSSOSv4/OSSOSv4class.dat'
PLOT_FIELD_EPOCH = 'Jun14.00'  # Jun14.00 ==> '0' days since the New Moon on Jun14

PLOT_USNO_STARS = True
PLOT_MEGACAM_ARCHIVE_FIELDS = False  # # TODO Make this work when True
PLOT_SYNTHETIC_KBOS = False
PLOT_SYNTHETIC_KBO_TRAILS = False
PLOT_REAL_KBOS = True and os.access(REAL_KBO_AST_DIR, os.F_OK)
PLOT_FIELD_LAYOUT = True

PLOT_MPCORB = True and os.access(MPCORB_FILE, os.F_OK)

NEWMOONS = {'Feb13': "2013/02/10 10:00:00",
            'Mar13': "2013/03/11 10:00:00",
            'Apr13': "2013/04/10 10:00:00",
            'May13': "2013/05/09 10:00:00",
            'Jun13': "2013/06/08 10:00:00",
            'Jul13': "2013/07/08 10:00:00",
            'Aug13': "2013/08/06 10:00:00",
            'Sep13': '2013/09/05 10:00:00',
            'Oct13': '2013/10/04 10:00:00',
            'Nov13': '2013/11/03 10:00:00',
            'Dec13': '2013/12/02 10:00:00',
            'Jan14': '2014/01/01 10:00:00',
            'Feb14': '2014/01/31 10:00:00',
            'Mar14': '2014/03/28 10:00:00',
            'Apr14': '2014/04/01 10:00:00',
            'May14': '2014/05/28 10:00:00',
            'Jun14': '2014/06/26 10:00:00',
            'Jul14': '2014/07/26 10:00:00',
            'Aug14': "2014/08/25 10:00:00",
            'Sep14': '2014/09/24 10:00:00',
            'Oct14': '2014/10/23 10:00:00',
            'Nov14': '2014/11/22 10:00:00',
            'Dec14': '2014/12/22 10:00:00',
            'Jan15': '2015/01/20 10:00:00',
            'Feb15': '2015/02/18 10:00:00',
            'Mar15': '2015/03/19 10:00:00',
            'Apr15': '2015/04/18 10:00:00',
            'May15': '2015/05/17 10:00:00',
            'Jun15': '2015/06/16 10:00:00',
            'Jul15': '2015/07/15 10:00:00',
            'Aug15': '2015/08/14 10:00:00',
            'Sep15': '2015/09/12 10:00:00',
            'Oct15': '2015/10/12 10:00:00',
            'Nov15': '2015/11/11 10:00:00',
            'Dec15': '2015/12/11 10:00:00',
            'Jan16': '2016/01/09 10:00:00',
            'Feb16': '2016/03/08 10:00:00',
            'Mar16': '2016/03/09 10:00:00',
            'Apr16': '2016/04/08 10:00:00',
            'May16': '2016/05/07 10:00:00',
            'Jun16': '2016/06/05 10:00:00',
            'Jul16': '2016/07/05 10:00:00',
            'Aug16': '2016/08/03 10:00:00',
            'Sep16': '2016/09/01 10:00:00',
            'Oct16': '2016/10/01 10:00:00',
            'Nov16': '2016/11/01 10:00:00',
            'Dec16': '2016/12/01 10:00:00',
            'Jan17': '2017/01/01 10:00:00',
            'Feb17': '2017/02/01 10:00:00',
}

# ORIGINAL: DON't USE, does not match the location of the data as pointed & taken!
# Ablocks={'13AE': {"RA": "14:32:30.29","DEC":"-13:54:01.4"},
# '13AO': {"RA": "16:17:04.41","DEC":"-13:14:45.8"}}
BLOCKS = OrderedDict([
    # E+0+0: image 1616681, ccd21 on April 9. E block discovery triplets are April 4,9,few 19
    ('13AE', {"RA": "14:15:28.89", "DEC": "-12:32:28.4"}),
    ('13AO', {"RA": "15:58:01.35", "DEC": "-12:19:54.2"}),  # O+0+0: image 1625346, ccd21 on May 8. O block are May 7,8.
    ('13BL', {'RA': "00:54:00.00", "DEC": "+03:50:00.00"}),  # 13B blocks are at their opposition locations
    ('14BH', {'RA': "01:30:00.00", "DEC": "+13:00:00.00"}),  # due to bad weather, discovery wasn't until 2014, so 14

    ('15AP', {'RA': "13:30:00.00", "DEC": "-7:45:00.00"}),  # on-plane
    ('15AM', {'RA': "15:30:00.00", "DEC": "-12:20:00.0"}),  # at its 2014 initial observation.
    ('15B?', {'RA': "00:45:00.00", "DEC": "+00:05:00.00"}),  # FIXME: NOT CHECKED against lunations etc yet. Indicative.
    ('15BD', {'RA': "03:15:00.00", "DEC": "+16:30:00.00"})
])

DISCOVERY_DATES = {"13AE": "2013/04/09 08:50:00",
                   "13AO": "2013/05/08 08:50:00",
                   "15AP": NEWMOONS['Apr15'],  # FIXME: set when observations taken
                   "15AM": NEWMOONS['May15'],  # Backup triplet: split on 2014/05/29, 2014/06/01
                   "13BL": "2013/09/29 08:50:00",  # HOWEVER: discovery date is split between months (earliest)
                   "14BH": "2014/10/22 09:30:00",  # Note: Col3N triplet is instead 2014/01/03.
                   "15BD": NEWMOONS['Nov15'],  # FIXME: set when observations taken
                   "15B?": NEWMOONS['Oct15']  # FIXME: set when observations taken
}

DISCOVERY_NEW_MOON = 'Apr13'  # applies to the 13A blocks

OPPOSITION_DATES = {"13AE": NEWMOONS['Apr13'],
                    "13AO": NEWMOONS['May13'],
                    "15AP": NEWMOONS['Apr15'],
                    "15AM": NEWMOONS['May15'],
                    "13BL": NEWMOONS['Oct13'],
                    "14BH": NEWMOONS['Oct13'],
                    "15B?": NEWMOONS['Oct15'],
                    "15BD": NEWMOONS['Nov15'],

}


class VersionError(Exception):
    'An error with the TNO summary-file version'


class tno(object):
    ''' This takes two types of input lines, which populate almost the same but subtly different amounts of information.
        Standard orbital elements are always populated.
        Combining both class methods is the most reliable way of instantiating these objects from a data release.
    '''

    def __init__(self, name, dist, dist_e, nobs, arclen, av_xres, av_yres, max_x, max_y,
                 a, a_e, e, e_e, i, i_e, node, node_e, argperi, argperi_e, time_peri, time_peri_e):
        # self.classification = str(classification)
        self.name = str(name)
        self.dist = float(dist)
        self.dist_e = float(dist_e)
        self.nobs = int(nobs)
        self.arclen = float(arclen)
        self.av_xres = float(av_xres)
        self.av_yres = float(av_yres)
        self.max_x = float(max_x)
        self.max_y = float(max_y)
        self.a = float(a)
        self.a_e = float(a_e)
        self.e = float(e)
        self.e_e = float(e_e)
        self.i = float(i)
        self.i_e = float(i_e)
        self.node = float(node)
        self.node_e = float(node_e)
        self.argperi = float(argperi)
        self.argperi_e = float(argperi_e)
        self.time_peri = float(time_peri)
        self.time_peri_e = float(time_peri_e)
        self.peri = self.a * (1. - self.e)

    @classmethod
    def from_summary_line(cls, summaryLine, version=4, existing_object=None):
        ''' Summary format:
        object  mag  stdev   dist  ..E nobs time av_xres av_yres max_x max_y
        a ..E  e  ..E  i ..E    node     ..E    argperi     ..E           M        ..E   ra_dis  dec_dis
        '''
        if not summaryLine:
            raise ValueError('No summary line given')
        if version == 4:
            params = summaryLine.split()
            if len(params) != 25:
                print params
                raise TypeError('Expected 25 columns, {0} given'.format(len(params)))
            input_params = params[0:1] + params[3:23]
            if not existing_object:
                retval = cls(*input_params)
            else:
                assert isinstance(existing_object, tno)
                assert existing_object.name == params[0]
                retval = existing_object
            retval.mean_mag = float(params[1])
            retval.mean_mag_stdev = float(params[2])
            retval.ra_discov = float(params[23])
            retval.dec_discov = float(params[24])
        else:
            raise VersionError('Unknown version "{0}"'.format(version))
        assert retval
        return retval

    @classmethod
    def from_class_line(cls, classLine, version=4, existing_object=None):
        '''
        Class format:
        class wrt n m security object  mag  stdev F H_sur  dist     ..E    nobs   time  av_xres av_yres max_x  max_y
        a ..E        e  ..E      i      ..E      node     ..E   argperi      ..E   time_peri      ..E    rate
        '''
        if not classLine:
            raise ValueError('No class file line given.')
        if version == 4:
            params = classLine.split()
            if len(params) != 31:
                print params
                raise TypeError('Expected 31 columns, {0} given'.format(len(params)))
            input_params = [params[5]] + params[10:30]  # the elements that are in common
            if not existing_object:
                # can later add more tests that the values match those in the existing object
                retval = cls(*input_params)
            else:
                assert isinstance(existing_object, tno)
                assert existing_object.name == params[5]
                retval = existing_object
            retval.classification = params[0]
            retval.wrt = params[1]
            retval.n = int(params[2])
            retval.m = int(params[3])
            retval.security = params[4]
            retval.mag_discov = float(params[6])
            retval.mag_discov_e = float(params[7])
            retval.filter = params[8]
            retval.H = float(
                params[9])  # H_r magnitude, using the average m_r and the discovery geometry (same error as m_r)
            retval.rate = float(params[30])
        else:
            raise VersionError('Unknown version "{0}"'.format(version))
        assert retval
        return retval
