import csv
from collections import namedtuple
import os
from math import  sin, cos, acos, pi


GPSPoint = namedtuple('GPSPoint', ['lat', 'lon', 'ele', 'activity'])

def GPSPointStr(self):
    return '<GPSPoint(lat=' + str(self.lat) + ', lon=' + str(self.lon) + ', ele=' + str(self.ele) + ', activity=' + str(self.activity) + ')>'
GPSPoint.__repr__ = GPSPointStr

def trackpointToGPSPoint(trkpt, activity):
    lat = float(trkpt['lat'])
    lon = float(trkpt['lon'])
    ele = float(trkpt.ele.text)
    return GPSPoint(lat, lon, ele, int(activity['idx']))
    
def rowToGPSPoint(row):
    return GPSPoint(float(row[0]), float(row[1]), float(row[2]), int(row[3]))


# Saves an array of GPSPoints to disk
def savePoints(workdir, points, fiilename):
    with open(workdir + os.sep + fiilename, 'w') as csvfile:
        writer = csv.writer(csvfile, lineterminator='\n')
        writer.writerows(points)


# Loads an array of GPSPoints from disk
def loadPoints(workdir, filename):
    with open(workdir + os.sep + filename, 'r') as csvfile:
        reader = csv.reader(csvfile, lineterminator='\n')
        pts = map(rowToGPSPoint, reader)
        return [i for i in pts]
    
    
deg2rad = pi/180
earth_radius = 6317.0

def greatCircleDistance(point1, point2):
    # Convert lat/long to spherical coordinates
    phi1 = (90.0 - point1.lat) * deg2rad
    phi2 = (90.0 - point2.lat) * deg2rad    
    theta1 = point1.lon * deg2rad
    theta2 = point2.lon * deg2rad
    
    try:
        arc = acos( sin(phi1)*sin(phi2)*cos(theta1-theta2) + cos(phi1)*cos(phi2) )
    except Exception as e:
        print('ERROR between points: ' + str(point1) + ", " + str(point2))
        return 9999
    
    # Multiply by Earth's radius in meters
    return arc * 6373*1000.0


def removeWithinRange(points, maxdist, sameactivity=False, verbose=False):
    npoints = len(points)
    keep = [True] * npoints
    
    # Do a quick filter
    for ii in range(npoints):
        if verbose and ii%500 == 0:
            print(str(int(100.0*ii/npoints)))
        if keep[ii]:
            for jj in range(ii+1, npoints):
                if sameactivity:
                    if not points[ii].activity == points[jj].activity:
                        break
                if keep[jj]:
                    dist = greatCircleDistance(points[ii], points[jj])
                    if dist < maxdist:
                        #print('Removing ' + str(jj))
                        keep[jj] = False
    
    return [point for i,point in enumerate(points) if keep[i]]
