# coding=utf-8
__author__ = 'Michele Bannister   git:@mtbannister'

import os
import cPickle
from collections import OrderedDict
import math

import ephem
from astropy.table import Table
from uncertainties import ufloat
import numpy

from ossos import mpc
from ossos import orbfit
from ossos import storage
import parameters
from ossos.gui import context
import plot_lightcurve
import plot_efficiency


# from parameters import tno

def ossos_release_parser(table=False):
    '''
    extra fun as this is space-separated so using CSV parsers is not an option
    '''
    names = ['cl', 'p', 'j', 'k', 'sh', 'object', 'mag', 'mag_E', 'F', 'H_sur', 'dist', 'dist_E', 'nobs',
             'time', 'av_xres', 'av_yres', 'max_x', 'max_y', 'a', 'a_E', 'e', 'e_E', 'i', 'i_E', 'node', 'node_E',
             'argperi', 'argperi_E', 'time_peri', 'time_peri_E', 'ra_dis', 'dec_dis', 'jd_dis', 'rate']

    if table:
        # have to specify the names because the header line contains duplicate IDs, which wrecks auto-column creation
        retval = Table.read(parameters.RELEASE_DETECTIONS, format='ascii', guess=False,
                            delimiter=' ', data_start=0, comment='#', names=names, header_start=None)
    else:
        retval = []
        with open(parameters.RELEASE_DETECTIONS, 'r') as detectionsfile:
            for line in detectionsfile.readlines()[1:]:  # first line is column definitions
                obj = tno.from_str(line, version=parameters.RELEASE_VERSION)
                retval.append(obj)

    return retval


class tno(object):
    def __init__(self, observations):
        self.orbit = orbfit.Orbfit(observations.mpc_observations)
        self.discovery = [n for n in observations.mpc_observations if n.discovery.is_discovery][0]
        self.name = observations.provisional_name
        return


def ossos_discoveries(directory=parameters.REAL_KBO_AST_DIR,
                      suffix='ast',
                      no_nt_and_u=True,
                      single_object=None,
                      all=False,
                      release=parameters.RELEASE_VERSION,
                      ):
    """
    Returns a list of objects holding orbfit.Orbfit objects with the observations in the Orbfit.observations field.
    Default is to return only the objects corresponding to the current Data Release.
    """
    retval = []
    working_context = context.get_context(directory)
    files = working_context.get_listing(suffix)

    if single_object is not None:
        files = filter(lambda name: name.startswith(single_object), files)
    if not all:
        # only return the objects corresponding to a particular Data Release
        objects = ossos_release_parser(table=True)['object']
        files = filter(lambda name: name.partition(suffix)[0].rstrip('.') in objects, files)

    for filename in files:
        # keep out the not-tracked and uncharacterised.
        if no_nt_and_u:
            if not (filename.__contains__('nt') or filename.startswith('u')):
                observations = mpc.MPCReader(directory + filename)
                obj = tno(observations)
                retval.append(obj)
        else:  # now we want those uncharacterised ones
            observations = mpc.MPCReader(directory + filename)
            obj = tno(observations)
            retval.append(obj)

    return retval


def ossos_release_with_metadata():
    """
    Wrap the objects from the Version Releases together with the objects instantiated from fitting their mpc lines
    """
    # discoveries = ossos_release_parser()
    discoveries = []
    observations = ossos_discoveries()
    for obj in observations:
        discov = [n for n in obj[0].mpc_observations if n.discovery.is_discovery][0]
        tno = parameters.tno()
        tno.dist = obj[1].distance
        tno.ra_discov = discov.coordinate.ra.degrees
        tno.mag = discov.mag
        tno.name = discov.provisional_name
        discoveries.append(tno)

    # for obj in discoveries:
    # observation = [n for n in observations if n.observations[-1].provisional_name == obj.name][0]
    # for obs in observation.observations:
    # if obs.discovery.is_discovery:
    #             if obj.mag is not None:
    #                 H = obj.mag + 2.5 * math.log10(1. / ((obj.dist ** 2) * ((obj.dist - 1.) ** 2)))
    #             else:
    #                 H = None
    #             obj.H = H
    #             obj.T = observation.T
    #             obj.discovery_date = obs.date
    #             obj.observations = observation

    return discoveries  # list of tno() objects


def synthetic_model_kbos(at_date=parameters.NEWMOONS[parameters.DISCOVERY_NEW_MOON], maglimit=24.5, kbotype=False,
                         arrays=False):
    # # build a list of Synthetic KBOs
    kbos = []
    print "LOADING SYNTHETIC MODEL KBOS FROM: {}".format(parameters.L7MODEL)
    pastpath = parameters.L7_HOME + str(at_date).split()[0].replace('/', '-') + '_' + str(maglimit) + (
        kbotype or '') + '.dat'
    print(pastpath)
    if os.path.exists(pastpath):
        with open(pastpath) as infile:
            ra, dist, hlat, Hmag = cPickle.load(infile)
        print('{} synthetic model kbos brighter than {} at {} in L7 model'.format(len(ra), maglimit, at_date))
    else:
        if arrays:  # much easier to use for plt.scatter()
            ra = []
            dist = []
            hlat = []
            Hmag = []

        lines = storage.open_vos_or_local(parameters.L7MODEL).read().split('\n')
        counter = 0
        for line in lines:
            if len(line) == 0 or line[0] == '#':  # skip initial column descriptors and the final blank line
                continue
            kbo = ephem.EllipticalBody()
            values = line.split()
            kbo.name = values[8]
            if kbotype and (kbo.name == kbotype) and (values[9] == '3' and values[10] == '2'):  # keeping 3:2 resonators
                kbo._a = float(values[0])
                kbo._e = float(values[1])
                kbo._inc = float(values[2])
                kbo._Om = float(values[3])
                kbo._om = float(values[4])
                kbo._M = float(values[5])
                kbo._H = float(values[6])
                epoch = ephem.date(2453157.50000 - ephem.julian_date(0))
                kbo._epoch_M = epoch
                kbo._epoch = epoch
                date = ephem.date(at_date)
                kbo.compute(date)
                counter += 1

                # ## only keep objects that are brighter than limit
                if (kbo.mag < maglimit):
                    kbos.append(kbo)
                    if arrays:
                        ra.append(float(kbo.ra))
                        dist.append(float(kbo.sun_distance))
                        hlat.append(float(kbo.hlat))
                        Hmag.append(float(kbo._H))

        print '{} synthetic model kbos brighter than {} at {} retained from {} in L7 model'.format(len(kbos), maglimit,
                                                                                                   at_date, counter)
    if not arrays:
        return kbos
    else:
        if not os.path.exists(pastpath):
            with open(pastpath, 'w') as outfile:
                cPickle.dump((ra, dist, hlat, Hmag), outfile)
        return ra, dist, hlat, Hmag


def output_discoveries_for_animation():
    discoveries = ossos_release_with_metadata()
    with open('/Users/michele/Desktop/OSSOSdiscoveries.txt', 'w') as outfile:
        outfile.write('name a e i node peri MA epoch H date_of_discovery\n')
        for obj in discoveries:
            # a e i node peri MA epoch H date_of_discovery
            outfile.write(
                '{:>10s} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:>10s}\n'.format(
                    obj.name, obj.a, obj.e, obj.i, obj.node, obj.argp, obj.M, obj.T, obj.H, obj.discovery_date))


def round_sig_error(num, uncert):
    '''
    Return a string of the number and its uncertainty to the right sig figs via uncertainty's print methods.
    The uncertainty determines the sig fig rounding of the number.
    https://pythonhosted.org/uncertainties/user_guide.html
    '''
    u = ufloat(num, uncert)
    outstr = '{:.1uLS}'.format(u)

    return outstr


def linesep(name, distinguish=None):
    names = {'N': "Objects in resonance with Neptune",
             'U': "Objects in resonance with Uranus",  # don't have one yet but Kat does check
             'i': 'Inner classical belt',
             'm': 'Main classical belt',
             'o': 'Outer classical belt',
             'd': 'Detached classical belt',
             'x': 'Scattering disk',
             'c': 'Centaurs',
    }
    if distinguish:
        if distinguish == 'sca':
            name = 'x'
        elif distinguish == 'det':
            name = 'd'
        elif distinguish == 'cen':
            name = 'c'

    midline = r"\cutinhead{" + \
              "{}".format(names[name]) + \
              "} \n"

    return midline


def create_table(tnos, outfile):
    # no. columns must match no. c's
    # table has small font and is horizontal.
    header = r"\begin{deluxetable}{ccccccccccccc}" + '\n' + \
             r"\tabletypesize{\scriptsize}" + '\n' + \
             r"\rotate" + '\n' + \
             r"\tablecolumns{13}" + '\n' + \
             r"\tablehead{\colhead{$m_{r}$} \vspace{-0.2cm} & " \
             r"\colhead{$\sigma$ $m_{r}$} & " \
             r"\colhead{Detectability} & " \
             r"\colhead{RA} & " \
             r"\colhead{Dec} & " \
             r"\colhead{a} & " \
             r"\colhead{e} & " \
             r"\colhead{i} & " \
             r"\colhead{r$_{H}$} & " \
             r"\colhead{H$_{r}$} & " \
             r"\colhead{MPC} & " \
             r"\colhead{Object} & " \
             r"\colhead{Status} \\" \
             r"\colhead{discovery} & " \
             r"\colhead{all obs} & " \
             r"\colhead{} & " \
             r"\colhead{discov.} & " \
             r"\colhead{discov.} & " \
             r"\colhead{(AU)} & " \
             r"\colhead{} & " \
             r"\colhead{($^{\circ}$)} & " \
             r"\colhead{(AU)} & " \
             r"\colhead{} & " \
             r"\colhead{design.} & " \
             r"\colhead{} & " \
             r"\colhead{} " \
             + r"}" \
             + "\n" \
             + "\startdata \n" \
             + r"\cutinhead{Centaurs}" + "\n"

    footer = r"\enddata " + "\n" + \
             r"\tablecomments{$p:q$: object is in the $p:q$ resonance; I: the orbit classification is currently " \
             r"insecure; " \
             r"" \
             r"" \
             r"H: the human operator intervened to declare the orbit security status. " \
             r"$a, e, i$ are J2000 ecliptic barycentric coordinates, with uncertainties from the covariant matrix fit " \
             r"of \citet{Bernstein:2000p444}; full barycentric elements are available at \url{http://www.ossos-survey" \
             r".org/}." \
             r"The full heliocentric orbital elements are available in electronic form from the Minor Planet Center.} " "\n" + \
             "\end{deluxetable} \n"

    # Scrape the index file for MPC designations - this would work better if the alternate designations were consistent
    # idx = {}
    # with open(parameters.IDX) as infile:
    # lines = infile.readlines()

    # sort order gives Classical, Detached, Resonant, Scattered
    # Sort by discovery mag within each classification.
    tnos.sort(['cl', 'p', 'j', 'k', 'mag'])

    with open(outfile, 'w') as ofile:
        ofile.write(header)
        for i, r in enumerate(tnos):
            # write line separator between object classification types
            if r['p'] != tnos[i - 1]['p']:
                if r['p'] == 'x':  # 'x' doesn't give enough info to set scattered or detached
                    ofile.write(linesep(r['p'], distinguish=r['cl']))
                else:
                    ofile.write(linesep(r['p']))

            sigma_mag = plot_lightcurve.stddev_phot(r['object'])
            if not numpy.isnan(sigma_mag):
                sigma_mag = '{:2.2f}'.format(sigma_mag)
            else:
                sigma_mag = r'--'
            eff_at_discovery = plot_efficiency.square_fit_discovery_mag(r['object'], r['mag'], r['rate'])

            # mag ± dmag, std dev of all clean photometry, efficiency function at that discovery mag
            # m ± dm sigma_m eff_discov RA Dec a ± da e ± de i ± di r ± dr H ± dH j k MPC obj status
            # put characterisation limits in footnotes.
            out = "{} & {} & {:2.2f} & {:3.3f} & {} & {} & {} & {} & {} & {} & & {} & ".format(
                round_sig_error(r['mag'], r['mag_E']),
                sigma_mag,
                eff_at_discovery,
                math.degrees(ephem.degrees(ephem.hours(str(r['ra_dis'])))),
                r['dec_dis'],
                                                            round_sig_error(r['a'], r['a_E']),
                                                            round_sig_error(r['e'], r['e_E']),
                                                            round_sig_error(r['i'], r['i_E']),
                                                            round_sig_error(r['dist'], r['dist_E']),
                r['H_sur'],
                # MPC designation
                r['object'],
            )
            # make sure these come out with nice formatting
            if r['j'] != -1:
                out += "{}:{} ".format(r['j'], r['k'])  # resonant object: give the resonance
            else:
                out += "    "  # it's a classical or scattered object
            if r['sh'] != 'S':
                out += "{} {} \n".format(r['sh'], r'\\')
            else:
                out += "  {} \n".format(r'\\')
            ofile.write(out)
        ofile.write(footer)


def release_to_latex(outfile):
    tnos = ossos_release_parser(table=True)
    uncharacterised = tnos[numpy.array([name.startswith("u") for name in tnos['object']])]
    # characterised = tnos[numpy.array([name.startswith("o") for name in tnos['object']])]
    # create_table(characterised, outfile)
    create_table(uncharacterised, 'u_' + outfile)

    return

def parse_subaru_radec(line):
    d = line.split()
    pointing_name = line.split('=')[0]
    ra = d[1].split('=')[1]
    dec = d[2].split('=')[1]
    if len(ra.split('.')[0]) == 5:  # LACK OF SEPARATORS ARGH
        ra = '0' + ra
    if len(dec.split('.')[0]) == 5:
        dec = '0' + dec
    ra = "{}:{}:{}".format(ra[0:2], ra[2:4], ra[4:])
    dec = "{}:{}:{}".format(dec[0:2], dec[2:4], dec[4:])
    return pointing_name, ra, dec


def parse_subaru_mags():
    tnos = ossos_discoveries(parameters.REAL_KBO_AST_DIR, suffix='ast')
    index = OrderedDict()
    with open('/Users/michele/Desktop/Col3N.txt', 'r') as infile:
        lines = infile.readlines()
        for line in lines:
            pointing, ra, dec = parse_subaru_radec(line)
            objs = [t for t in pointing.split('_') if t not in ['only', 'alternate', 'bonus']]
            mags = []
            regular = []
            for obj in objs:
                mag = [t.discovery.mag for t in tnos if t.name.endswith(obj)][0]
                mags.append(mag)
                if len([t for t in parameters.COLOSSOS if t.endswith(obj)]) == 0:
                    regular.append(obj)
            index[pointing] = (ra, dec, mags, regular)
            print pointing, index[pointing]

    with open('/Users/michele/Desktop/Col3N_201509121000.txt', 'w') as outfile:
        outfile.write('{: <25} {: <15} {: <15} {: <30} {: <10}\n'.format('Pointing',
                                                                         'RA (hh:mm:ss)',
                                                                         'Dec (dd:mm:ss)',
                                                                         'magnitudes at discovery (m_r)',
                                                                         'regular OSSOS'))
        for key, val in index.items():
            outfile.write('{: <25} {: <15} {: <15} {: <30} {: <10}\n'.format(key,
                                                                             val[0],
                                                                             val[1],
                                                                             ', '.join([str(f) for f in val[2]]),
                                                                             ', '.join([f for f in val[3]])
            ))


def block_table_pprint():
    with open('block_table.tex', 'w') as outfile:
        for name, coords in parameters.BLOCKS.items():
            print name, coords
            ra = ephem.hours(coords['RA'])
            dec = ephem.degrees(coords['DEC'])
            eq = ephem.Equatorial(ra, dec)
            ec = ephem.Ecliptic(eq)
            outfile.write("{} & {:2.1f} & {:2.1f} & {:2.1f} & {:2.1f} {} \n".format(
                name[2:],
                math.degrees(ephem.degrees(ra)),
                math.degrees(dec),
                math.degrees(ec.lat),
                math.degrees(ec.lon),
                r"\\"))
    return


if __name__ == '__main__':
    # ossos_release_parser(table=True)
    release_to_latex('v{}'.format(parameters.RELEASE_VERSION) + '_table.tex')
    # parse_subaru_mags()
    # block_table_pprint()
