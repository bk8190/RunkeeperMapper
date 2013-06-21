'''
Created on Jun 19, 2013

@author: wkulp
'''

import parsing.rkIO as rkIO
import parsing.GPSPoint as GPSPoint
import tempfile
import os, shutil
import functools, itertools
import simplekml
from multiprocessing import cpu_count



def processPoints(workdir, points):
    # Get unique activity types
    activities = rkIO.parseIndexFile(workdir)
    types = set([a['Type'] for a in activities])
    types = [i for i in types]
    
    # Filter points into activity types
    filteredpoints = []
    for t in types:
        filteredpoints.append([point for i,point in enumerate(points) if activities[point.activity]['Type'] == t])
    
    points = []
    for i in range(len(types)):
        # Remove points within a specified distance
        print("Filtering type '" + types[i] + "'")
        n0 = len(filteredpoints[i])
        filteredpoints[i] = GPSPoint.removeWithinRange(filteredpoints[i], 20, verbose=True)
        n1 = len(filteredpoints[i])
        
        print('Pass 1 kept ' + str(n1) + '/' + str(n0))
        points.extend(filteredpoints[i])
    
    return points


def writeOutput(workdir, gpspoints):
    activities = rkIO.parseIndexFile(workdir)
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


if __name__ == '__main__':
    
    try:
        import timeit
        #workdir = tempfile.mkdtemp(prefix='RKWorking_')
        workdir = r"C:\Users\wkulp\Documents\GitHub\RunkeeperMapper\data"
        print('Working dir: ' + workdir)
        
        rkIO.loadArchive(workdir, r"data\runkeeper-data-export-2338982-2013-06-19-1533.zip")
        
        # Read the master activity list
        activities = rkIO.parseIndexFile(workdir)
        
        # Parse each GPX file into points
        print('Processing GPS track files')
        nprocs = cpu_count()
        print('Using ' + str(nprocs) + " CPU cores...")
        #points = rkIO.sp_readAllPoints(activities, workdir, spatialFilterDistance = 20)
        points = rkIO.mp_readAllPoints(nprocs, activities, workdir, spatialFilterDistance = 20)
        GPSPoint.savePoints(workdir, points, 'rawpoints.csv')
        
        
        points = processPoints(workdir, points)    
        GPSPoint.savePoints(workdir, points, 'processedpoints.csv')
        
        points = GPSPoint.loadPoints(workdir, 'processedpoints.csv')
        writeOutput(workdir, points)
        
        print('Done!')
    
    finally:
        #shutil.rmtree(workdir)
        pass