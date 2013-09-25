__author__ = 'Michele Bannister'

import matplotlib.pyplot as plt
import brewer2mpl
from matplotlib import rcParams
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import numpy as np
import math
import ephem
from track_done import parse, get_names
from ossos import storage

# nicer defaults
# every colourbrewer scale: http://bl.ocks.org/mbostock/5577023
# hues create primary visual differences between classes; does not imply magnitude differences between classes
set2 = brewer2mpl.get_map('Set2', 'qualitative', 8).mpl_colors
# sequential for ordered data where light is low values, dark is high values
ylorrd = brewer2mpl.get_map('YlOrRd', 'sequential', 9).mpl_colors
# diverging for equal emphasis on mid-range critical values and extremes at both ends of data range
puor = brewer2mpl.get_map('PuOr', 'diverging', 11).mpl_colors
almost_black = '#262626'

# rcParams['figure.figsize'] = (10, 10)
# rcParams['figure.dpi'] = 150
rcParams['axes.color_cycle'] = set2
rcParams['font.size'] = 12   # good for posters/slides
rcParams['patch.facecolor'] = set2[0]


def remove_border(axes=None, keep=('left', 'bottom'), remove=('right', 'top'), labelcol=almost_black):
    """
    Minimize chart junk by stripping out unnecessary plot borders and axis ticks.
    The top/right/left/bottom keywords toggle whether the corresponding plot border is drawn
    """
    ax = axes or plt.gca()
    for spine in remove:
        ax.spines[spine].set_visible(False)
    for spine in keep:
        ax.spines[spine].set_linewidth(0.5)
        ax.spines[spine].set_color('white')
    # match the label colour to that of the axes
    ax.xaxis.label.set_color(labelcol)
    ax.yaxis.label.set_color(labelcol)

    # remove all ticks, then add back the ones in keep
    # Does this also need to specify the ticks' colour, given the axes/labels are changed?
    ax.yaxis.set_ticks_position('none')
    ax.xaxis.set_ticks_position('none')
    for spine in keep:
        if spine == 'top':
            ax.xaxis.tick_top()
        if spine == 'bottom':
            ax.xaxis.tick_bottom()
        if spine == 'left':
            ax.yaxis.tick_left()
        if spine == 'right':
            ax.yaxis.tick_right()

    return

def clean_legend():
    # as per prettyplotlib.
    # Remove the line around the legend box, and instead fill it with a light grey
    # Also only use one point for the scatterplot legend because the user will
    # get the idea after just one, they don't need three.
    light_grey = np.array([float(248)/float(255)]*3)
    legend = ax.legend(frameon=True, scatterpoints=1)
    rect = legend.get_frame()
    rect.set_facecolor(light_grey)
    rect.set_linewidth(0.0)

    # Change the legend label colors to almost black, too
    texts = legend.texts
    for t in texts:
        t.set_color(almost_black)




"""
Plots to make:
- sky map ra/dec global with field locations
- tweaked version of 13A field_locations plot with appropriate styling for poster
- tweaked version of 13B field_locations plot with appropriate styling for poster
- 13AE discoveries:
    - sky location (shrunk version of field_locations, 13AE only)
    - efficiencies plot per JJ's calculations
    - top-down Solar System with clumping vs. Neptune and RA pie overlay
    - orbital parameters per Brett's plots:
        - i vs a
        - q vs a
"""

def top_down_SolarSystem(date="2013/04/09 08:50:00"):
    """
    Plot the OSSOS discoveries on a top-down Solar System showing the position of Neptune and model TNOs.
    Coordinates should be polar to account for RA hours, but axes are to be labelled in AU...
    :return: a saved plot
    """
    fig = plt.figure(figsize=(6,6))
    rect = [0.1, 0.1, 0.8, .8]  # setting the axis limits in [left, bottom, width, height]
    #
    # ax2 = fig.add_axes(rect)
    # remove_border(axes=ax2)
    # ax2.set_xlim(-60,60)
    # ax2.set_ylim(-60,60)
    # plt.xlabel('AU')

    ax1 = fig.add_axes(rect, polar=True, frameon=False) # theta (RA) is zero at E, increases anticlockwise
    ax1.set_aspect('equal')
    # ax1.set_theta_zero_location('E')

    # plot exclusion zones due to Galactic plane: RAs indicate where bar starts, rather than its centre angle
    width = math.radians(3*15)
    plt.bar(math.radians(16.5*15), 60, width=width, color=almost_black, alpha=0.2)
    plt.bar(math.radians(4.5*15), 60, width=width, color=almost_black, alpha=0.2)

    # plot OSSOS blocks - again RAs indicate where bar starts, so subtract half the block width from these centrepoints
    for block in ["14:15:28.89", "15:58:01.35", "00:54:00.00", "01:30:00.00"]:
        # truncate these at 15 AU to show that we don't have sensitivity in close
        plt.bar(ephem.hours(block)-math.radians(3.5), 60, width=math.radians(7), bottom=15, color='b', alpha=0.2)

    ax1.set_rlim(0,60)
    ax1.set_rgrids([20,40,60], labels=['','20 AU','40 AU','60 AU'], angle=150, alpha=0.45)
    ax1.yaxis.set_major_locator(MultipleLocator(20))
    ax1.xaxis.set_major_locator(MultipleLocator(math.radians(15)))
    ax1.grid(axis='x', color='k', linestyle='--', alpha=0.2)
    ax1.set_xticklabels(['0h','','2h','','4h','','6h',"","8h","","","","","","","","","","","","20h","","22h"],
                        color='b', alpha=0.6)  # otherwise they get in the way of the AU labels

    plot_planets_plus_Pluto(ax1, date)
    plot_ossos_discoveries(ax1, blockID='O13AE', date=date)
    plot_synthetic_model_kbos(ax1, date, kbotype='resonant')

    plt.draw()
    outfile = 'ra_vs_au_20130409'
    plt.savefig(outfile+'.pdf', transparent=True)

    return

def plot_planets_plus_Pluto(ax, date):
    for planet in [ephem.Neptune(), ephem.Pluto()]:
        planet.compute(ephem.date(date))
        ax.scatter(planet.ra, planet.sun_distance,
                     marker='o',
                     s=30,
                     facecolor='#E47833',
                     edgecolor='#E47833')
        ax.annotate(planet.name, (planet.ra+(math.radians(1)), planet.sun_distance+2), size=10)
        # plot Neptune's orbit: e is 0.01 so can get away with a circle
        if planet.name == 'Neptune':
            orb = np.arange(0,2*np.pi,(2*np.pi)/360)
            ax.plot(orb, np.repeat(planet.sun_distance, len(orb)), color='b', linestyle=':', linewidth=0.4, alpha=0.7)

    return

def plot_ossos_discoveries(ax, blockID='O13AE', date="2013/04/09 08:50:00"):
    path = 'vos:OSSOS/measure3/2013A-E/track/submitted/'  # rather than discoveries, for longer arcs
    discoveries = storage.listdir(path)
    names = get_names(path, blockID)
    print 'Discoveries:', len(names)
    for kbo in names:
        arclen, orbit = parse(kbo, discoveries, path=path)
        orbit.predict(date.replace('/', '-'))
        ra = math.radians(orbit.coordinate.ra.degrees)
        fc = 'b'
        alph = 0.8
        mags = [n.mag for n in orbit.observations if (n.mag != -1 and n.mag != None)]  # temporary workaround until zeropoints fixed
        mean_mag = sum(mags)/len(mags)
        if mean_mag > 24.15:  # we can't track these ones
            fc = 'w'
            alph = 1.
            print kbo, mean_mag
        ax.scatter(ra, orbit.distance, marker='o', s=4.5, facecolor=fc, edgecolor=almost_black, linewidth=0.15, alpha=alph)

    return

def plot_synthetic_model_kbos(ax, date, maglimit=24.5, kbotype='resonant'):
    ra = []
    dist = []
    for line in open('L7SyntheticModel-v09.txt'):
        if line[0]=='#':
            continue
        kbo = ephem.EllipticalBody()
        values = line.split()
        kbo._a = float(values[0])
        kbo._e = float(values[1])
        kbo._inc = float(values[2])
        kbo._Om = float(values[3])
        kbo._om = float(values[4])
        kbo._M = float(values[5])
        kbo._H = float(values[6])
        kbo._epoch_M = ephem.date(2453157.50000 - ephem.julian_date(0))
        kbo._epoch = kbo._epoch_M
        kbo.name = values[8]  # values[9] and [10] encode the type of resonance eg. 2:1 - add that if wanted

        kbo.compute(ephem.date(date))
        if (kbo.mag < maglimit):# and (kbo.name == kbotype):
            ra.append(kbo.ra)
            dist.append(kbo.sun_distance)

    ax.scatter(ra, dist, marker='o', s=2, facecolor=almost_black, edgecolor=almost_black, linewidth=0.1, alpha=0.1)

    return

def sky_map_global():

    return



def main():
    top_down_SolarSystem()


if __name__ == "__main__":
    main()