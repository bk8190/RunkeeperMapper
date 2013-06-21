'''
Created on Jun 20, 2013

@author: wkulp
'''
import collections
import csv
import os
import functools
import itertools
import zipfile
import multiprocessing
import queue
import time
from bs4 import BeautifulSoup
import parsing.GPSPoint as GPSPoint
import os


# Reads an activity index from disk
def parseIndexFile(workdir):
    print('Processing index file')
    with open(workdir + os.sep + 'cardioActivities.csv', 'r') as f:
        fieldnames = next(csv.reader(f)) # The first line contains field names
        activities = [i for i in csv.DictReader(f, fieldnames)]
    
    # Only keep activities with an associated GPX file (empty strings in the lambda expression evaluate to False)
    activities = list(filter(lambda x:x['GPX File'], activities))
    
    for i in range(0, len(activities)):
        activities[i]['idx'] = i
    return activities



def loadArchive(workdir, filename):
    print('Extracting: ' + filename)
    
    # Extract the archive
    with zipfile.ZipFile(filename) as zf:
        for f in zf.namelist():
            zf.extract(f, workdir)

def _readPointsFromActivity(activity, workdir, kwargs):   
    try:
        spatialFilterDistance = kwargs['spatialFilterDistance']
    except:
        spatialFilterDistance = None
    
    # Parse the XML document
    with open(workdir + os.sep + activity['GPX File'], 'r') as f:
        soup = BeautifulSoup(f.read())
    
    # Read all GPS trackpoints
    trkpts = soup.find_all('trkpt')
    
    # Convert to GPSPoint structures
    points = [GPSPoint.trackpointToGPSPoint(trkpt, activity) for trkpt in trkpts] 
    
    if spatialFilterDistance is not None:
        points = GPSPoint.removeWithinRange(points, spatialFilterDistance)
    return points


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print ('%r %2.2f sec' %  (method.__name__, te-ts))
        return result
    return timed

@timeit
def sp_readAllPoints(activities, workdir, **kwargs):
    points = []
    for activity in activities:
        print('Processing file: ' + activity['GPX File'])
        points.extend(_readPointsFromActivity(activity, workdir, kwargs))
    return points


def worker(job_q, result_q, workdir, kwargs):
    print('Worker')
    while True:
        activity = job_q.get()
        if activity is Ellipsis:
            return
        print('Processing file: ' + activity['GPX File'])
        outlist = _readPointsFromActivity(activity, workdir, kwargs)
        result_q.put(outlist)

@timeit
def mp_readAllPoints(nprocs, activities, workdir, **kwargs):
    nactivities = len(activities);
    result_q = multiprocessing.Queue()
    job_q = multiprocessing.Queue()
    
    # Add all activities to the queue.  Also add a signal for each process to stop.
    for a in activities:
        job_q.put(a)
    for i in range(nprocs):
        job_q.put(Ellipsis)

    procs = []
    for i in range(nprocs):
        p = multiprocessing.Process(
            target=worker,
            args=(job_q, result_q, workdir, kwargs))
        procs.append(p)
        print('Starting ' + str(p))
        p.start()
    
    # Collect the results
    points = []
    for i in range(nactivities):
        out = result_q.get()
        points.extend(out)
    
    # Make sure all processes are done
    for p in procs:
        print('Joining ' + str(p))
        p.join()
    
    return points


