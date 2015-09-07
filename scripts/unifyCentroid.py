#!/usr/bin/env python

import csv, os

def unifyCentroid(config, outFilename) :
    keys = ['RefDes','Layer','LocationX','LocationY','Rotation']
    boards = config['boards']
    pcbDir = config['pcbDir']


    with open(outFilename,'w') as dstfile :
        writer = csv.DictWriter(dstfile, keys, extrasaction='ignore')
        writer.writeheader()

        globalOffset = config['globalOffset']

        for boardNum,boardInfo in boards.iteritems() :
            boardName,xOffset,yOffset = boardInfo
            filename = os.path.join(pcbDir,"%s/gerber/%s.centroid.csv" % (boardName, boardName))
            with open(filename, 'r') as srcfile :
                reader = csv.DictReader(srcfile)
                for row in reader :
                    row['LocationX'] = float(row['LocationX'])+xOffset+globalOffset[0]
                    row['LocationY'] = float(row['LocationY'])+yOffset+globalOffset[1]
                    row['LocationX'] = "%.3f" % row['LocationX']
                    row['LocationY'] = "%.3f" % row['LocationY']
                    row['RefDes'] = "%d-%s" % (boardNum, row['RefDes'])
                    writer.writerow(row)

def genPlacementFile(config, placementFilename) :
    boards = config['boards']
    globalOffset = config['globalOffset']


    with open(placementFilename,"w") as placeFile :
        for id,board in boards.iteritems() :
            placeFile.write("%s %f %f\n" % (board[0], board[1] + globalOffset[0], board[2]+globalOffset[1]))

if __name__ == '__main_':
    config = eval(file('config/placement.json','r').read())

    unifyCentroid(config, os.path.join(config['rfqDir'],'centroid.csv'))
    genPlacementFile(config, 'tmp/placement.txt')
