'''
Created on Jun 20, 2013

@author: wkulp
'''
import collections
import csv
import os
from bs4 import BeautifulSoup
import functools
import itertools
import zipfile

GPSPoint = collections.namedtuple('GPSPoint', ['lat', 'lon', 'ele', 'activity'])

def GPSPointStr(self):
    return '<GPSPoint(lat=' + str(self.lat) + ', lon=' + str(self.lon) + ', ele=' + str(self.ele) + ', activity=' + str(self.activity) + ')>'
GPSPoint.__repr__ = GPSPointStr

# Saves an array of GPSPoints to disk
def savePoints(workdir, points, fiilename):
    with open(workdir + os.sep + fiilename, 'w') as csvfile:
        writer = csv.writer(csvfile, lineterminator='\n')
        writer.writerows(points)


# Loads an array of GPSPoints from disk
def loadPoints(workdir, filename):
    with open(workdir + os.sep + filename, 'r') as csvfile:
        reader = csv.reader(csvfile, lineterminator='\n')
        pts = map(_rowToGPSPoint, reader)
        return [i for i in pts]


# Reads an activity index from disk
def parseIndexFile(workdir):
    print('Processing index file')
    with open(workdir + os.sep + 'cardioActivities.csv', 'r') as f:
        fieldnames = next(csv.reader(f)) # The first line contains field names
        activities = [i for i in csv.DictReader(f, fieldnames)]
    
    # Only keep activities with an associated GPX file (empty strings in the lambda expression evaluate to False)
    activities = [i for i in filter(lambda x:x['GPX File'], activities)]
    
    for i in range(0, len(activities)):
        activities[i]['idx'] = i
    return activities


def _trackpointToGPSPoint(trkpt, activity):
    lat = float(trkpt['lat'])
    lon = float(trkpt['lon'])
    ele = float(trkpt.ele.text)
    return GPSPoint(lat, lon, ele, int(activity['idx']))
    
def _rowToGPSPoint(row):
    return GPSPoint(float(row[0]), float(row[1]), float(row[2]), int(row[3]))


def _readPointsFromActivity(activity, workdir):
    print('Processing file: ' + activity['GPX File'])
    with open(workdir + os.sep + activity['GPX File'], 'r') as f:
        soup = BeautifulSoup(f.read())
    
    points = map(functools.partial(_trackpointToGPSPoint, activity=activity), soup.find_all('trkpt'))
    return [i for i in points]


def loadArchive(workdir, filename):
    print('Extracting: ' + filename)
    
    # Extract the archive
    with zipfile.ZipFile(filename) as zf:
        for f in zf.namelist():
            zf.extract(f, workdir)


# Reads the master index file. an array of GPSPoints to disk
def readAllPoints(workdir):
    # Read the master activity index
    activities = parseIndexFile(workdir)
    
    # Parse the points associated with all activities
    points = map(functools.partial(_readPointsFromActivity, workdir=workdir), activities)
    
    # Reduce into a single list
    return [i for i in functools.reduce(itertools.chain, points)]


