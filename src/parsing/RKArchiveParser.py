'''
Created on Jun 19, 2013

@author: wkulp
'''

import rkIO
import tempfile
import os, shutil
import functools, itertools
from math import  sin, cos, acos, pi
import simplekml


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


def _removeWithinRange(points, maxdist, sameactivity=False):
    npoints = len(points)
    keep = [True] * npoints
    
    # Do a quick filter
    for ii in range(npoints):
        if ii%1000 == 0:
            print('progress: ' + str(int(ii/npoints*100.0)))
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


def processPoints(workdir, points):
    # Get unique activity types
    activities = rkIO.parseIndexFile(workdir)
    types = set([a['Type'] for a in activities])
    
    # Filter points into activity types
    filteredpoints = []
    for t in types:
        filteredpoints.append([point for i,point in enumerate(points) if activities[point.activity]['Type'] == t])
    
    points = []
    for i in range(len(types)):
        # Remove points within a specified distance
        print('Filtering pass ' + str(i) + '.1')
        n0 = len(filteredpoints[i])
        filteredpoints[i] = _removeWithinRange(filteredpoints[i], 15, True)
        
        print('Filtering pass ' + str(i) + '.2')
        n1 = len(filteredpoints[i])
        filteredpoints[i] = _removeWithinRange(filteredpoints[i], 15)
        n2 = len(filteredpoints[i])
        
        print('Pass 1 kept ' + str(n1) + '/' + str(n0))
        print('Pass 2 kept ' + str(n2) + '/' + str(n1))
    
    # Reduce into a single list
    return [i for i in functools.reduce(itertools.chain, filteredpoints)]
    


def writeOutput(workdir, points):
    activities = rkIO.parseIndexFile(workdir)
    gpspoints = rkIO.loadPoints(workdir, 'processedpoints.csv')
    print('Writing KML document...')
    
    kml = simplekml.Kml(name='Runkeeper Heatmap')
    
    icon = 'http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png'
    #icon = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    scale = 0.45
    
    footstyle = simplekml.Style()
    footstyle.iconstyle.icon.href = icon
    footstyle.iconstyle.scale = scale
    footstyle.iconstyle.color = simplekml.Color.lightgreen
    
    bikestyle = simplekml.Style()
    bikestyle.iconstyle.icon.href = icon
    bikestyle.iconstyle.scale = scale
    bikestyle.iconstyle.color = simplekml.Color.aqua
    
    otherstyle = simplekml.Style()
    otherstyle.iconstyle.icon.href = icon
    otherstyle.iconstyle.scale = scale
    otherstyle.iconstyle.color = simplekml.Color.red
    
    for i,gpspoint in enumerate(gpspoints):
        pt = kml.newpoint(coords = [(gpspoint.lon, gpspoint.lat)])
        
        try:
            method = activities[gpspoint.activity]['Type']
        except:
            import pdb;pdb.set_trace()
            pass
        if method == 'Running' or method == 'Hiking' or method == 'Walking':
            pt.style = footstyle
        elif method == 'Cycling':
            pt.style = bikestyle
        else:
            pt.style = otherstyle
    
    kml.save(workdir + os.sep + 'out.kml')
    import pdb;pdb.set_trace()


if __name__ == '__main__':
    
    try:
        #workdir = tempfile.mkdtemp(prefix='RKWorking_')
        workdir = r"C:\Users\wkulp\Documents\GitHub\RunkeeperMapper\data"
        print('Working dir: ' + workdir)
        
        #rkIO.loadArchive(workdir, r"data\runkeeper-data-export-2338982-2013-06-19-1533.zip")
        
        points = rkIO.readAllPoints(workdir)
        rkIO.savePoints(workdir, points, 'rawpoints.csv')
        
        #points = processPoints(workdir, points)    
        #rkIO.savePoints(workdir, points, 'processedpoints.csv')
        
        points = rkIO.loadPoints(workdir, 'processedpoints.csv')
        writeOutput(workdir, points)
        
        import pdb;pdb.set_trace()
    
    finally:
        #shutil.rmtree(workdir)
        pass