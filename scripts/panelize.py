#!/usr/bin/python

from unifyCentroid import unifyCentroid, genPlacementFile
from unifyBOM import unifyBOM
from tabify import runFilters
import sys,os

if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]) :
    print 'ERROR: Please specify the panel directory'
    sys.exit(-1)

configDir = sys.argv[1]
configFile = os.path.join(sys.argv[1],'panelConfig.json')
config = eval(file(configFile,'r').read())

pcbDir = config['pcbDir']

placementFile = 'tmp/placement.txt'
mergeConfigFile = 'merge.cfg'
centroidFile = 'RFQ/centroid.csv'
bomFile = 'RFQ/bom.csv'
tmpDir = 'tmp'
partDetailsFile = os.path.join(pcbDir,"../panelize/config/PartDetails.csv")

os.chdir(configDir)

if not os.path.exists('RFQ') :
    os.makedirs('RFQ')

if not os.path.exists(tmpDir) :
    os.makedirs(tmpDir)

unifyCentroid(config, centroidFile)

genPlacementFile(config, placementFile)

unifyBOM(config, partDetailsFile, bomFile)

os.system("/Users/ekt/integer-labs/gerbmerge/gerbmerge/gerbmerge.py --place-file=%s %s" % (placementFile, mergeConfigFile))

runFilters(config)
