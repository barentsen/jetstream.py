"""
jetstream.py makes beautiful maps of the atmospheric jet stream.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__version__ = "0.1"
__author__ = "Geert Barentsen (geert@barentsen.be)"
__copyright__ = "Copyright 2014 Geert Barentsen"

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits import basemap
from pydap import client
import netCDF4
import numpy as np

A = {'r': 52/255., 'g': 152/255., 'b': 219/255.}  # blue
B = {'r': 231/255., 'g': 76/255., 'b': 60/255.}   # red
C = {'r': 241/255., 'g': 196/255., 'b': 15/255.}  # orange

COLORMAP = colors.LinearSegmentedColormap('jetstream',
                                          {'red':   [(0.0, 1.0, 1.0),
                                                     (0.25, A['r'], A['r']),
                                                     (0.75, B['r'], B['r']),
                                                     (1.0, C['r'], C['r'])],
                                           'green': [(0.0, 1.0, 1.0),
                                                     (0.25, A['g'], A['g']),
                                                     (0.75, B['g'], B['g']),
                                                     (1.0, C['g'], C['g'])],
                                           'blue':  [(0.0, 1.0, 1.0),
                                                     (0.25, A['b'], A['b']),
                                                     (0.75, B['b'], B['b']),
                                                     (1.0, C['b'], C['b'])],
                                           'alpha': [(0.0, 0.0, 0.0),
                                                     (0.15, 1.0, 1.0),
                                                     (1.0, 1.0, 1.0)]})


class JetStreamMap():

    def __init__(self, lon1=-140, lon2=40, lat1=20, lat2=70):
        self.lon1, self.lon2 = lon1, lon2
        self.lat1, self.lat2 = lat1, lat2

    def render(self, data, vmin=80, vmax=220, title=None):
        self.fig = plt.figure(figsize=(9, 9*(9/16.)))
        self.fig.subplots_adjust(0.05, 0.15, 0.95, 0.88,
                                 hspace=0.0, wspace=0.1)
        self.map = basemap.Basemap(projection='cyl',
                                   llcrnrlon=self.lon1, llcrnrlat=self.lat1,
                                   urcrnrlon=self.lon2, urcrnrlat=self.lat2,
                                   resolution="c", fix_aspect=False)
        self.map.pcolormesh(data.lon, data.lat, data.windspeed,
                            cmap=COLORMAP, vmin=vmin, vmax=vmax, alpha=None)
        self.colorbar = self.map.colorbar(location='bottom',
                                          pad=0.1, size=0.25,
                                          ticks=[100, 150, 200, 250])
        self.colorbar.ax.set_xlabel('Average wind speed at 250 mb (km/h)', fontsize=16)
        self.map.drawcoastlines(color='#7f8c8d', linewidth=0.5)
        self.map.fillcontinents('#bdc3c7', zorder=0)
        self.fig.text(.05, .91, title, fontsize=24, ha='left')
        return self.fig


class JetStreamData():
    """Abstract base class"""

    def __init__(self):
        self.load()

    def create_map(self, title=None):
        mymap = JetStreamMap(lon1=-180, lon2=180, lat1=-70, lat2=+74)
        mymap.render(self, title=title)
        return mymap


class GFSJetStreamData(JetStreamData):
    """
    Parameters
    ----------
    url : str
        e.g. http://nomads.ncep.noaa.gov:9090/dods/gfs/gfs20140210/gfs_00z_anl
    """
    def __init__(self, url):
        self.url = url
        self.load()

    def load(self):
        c = client.open_url(self.url)
        lon = c.ugrdtrop.lon[:]
        #lon[lon > 180] -= 360  # Basemap runs from -180 to +180
        lat = c.ugrdtrop.lat[:]
        u_component = c.ugrdtrop.ugrdtrop[0][0]  # units m/s
        v_component = c.vgrdtrop.vgrdtrop[0][0]  # units m/s
        windspeed = 3.6 * np.sqrt(u_component**2, v_component**2)  # units km/h
        # Shift grid from 0 to 360 => -180 to 180
        windspeed, lon = basemap.shiftgrid(180, windspeed, lon, start=False)
        self.lon, self.lat, self.windspeed = lon, lat, windspeed


class ERAJetStreamData(JetStreamData):

    def __init__(self, year):
        self.year = year
        self.load()

    def load(self):
        data = netCDF4.Dataset('era-december-averages.nc')
        #times = netCDF4.num2date(data.variables['time'],
        #data.variables['time'].units)
        #print(times[self.year - 1979])
        lon = data.variables['longitude'][:]
        lat = data.variables['latitude'][:]
        windspeed = 3.6 * np.sqrt(data.variables['u'][:]**2
                                  + data.variables['v'][:]**2)
        windspeed = windspeed[self.year - 1979]
        # Shift grid from 0 to 360 => -180 to 180
        windspeed, lon = basemap.shiftgrid(180, windspeed, lon, start=False)
        self.lon, self.lat, self.windspeed = lon, lat, windspeed


def plot_gfs_average():
    days = range(1, 17)
    streamdata = []
    for day in days:
        print(day)
        streamdata.append(GFSJetStreamData("http://nomads.ncep.noaa.gov:9090"
                        "/dods/gfs/gfs201402{0:02d}/gfs_00z_anl".format(day)))
    for data in streamdata[1:]:
        streamdata[0].windspeed += data.windspeed
    streamdata[0].windspeed = streamdata[0].windspeed / float(len(days))
    mymap = streamdata[0].create_map("Jet stream in February 2014"
                                     "(GFS averaged)")
    mymap.fig.savefig('output/gfs.png')


def plot_era_average():
    for year in range(1979, 2014):
        data = ERAJetStreamData(year)
        mymap = data.create_map("December {0}".format(year))
        mymap.fig.savefig('output/{}.png'.format(year), dpi=220)
        plt.close()


if __name__ == '__main__':
    plot_era_average()
