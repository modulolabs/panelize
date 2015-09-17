#!/usr/bin/python

import csv, os

def rowForPartNum(partNum, data) :
    for row in data :
        if row['Part Number'] == partNum :
            return row

    return None

def calculateCosts(config, partDetailsFilename) :
    data = []
    boards = config['boards']
    pcbDir = config['pcbDir']

    with open(partDetailsFilename,"r") as detailsFile :
        reader = csv.DictReader(detailsFile)
        for row in reader :
            row['Qty'] = 0
            data.append(row)

    for boardNum,boardInfo in boards.iteritems() :
        boardName = boardInfo[0]
        filename = os.path.join(pcbDir,"%s/gerber/%s.bom.csv" % (boardName, boardName))
        with open(filename, 'r') as srcfile :
            reader = csv.DictReader(srcfile)
            print boardName
            total = 0.0
            for boardRow in reader :
                partNum = boardRow['PARTNUM']

                row = rowForPartNum(partNum, data)
                qty = int(boardRow['Qty'])
                description = boardRow['Description']
                cost = "Unknown"
                extCost = "Unknown"
                if row is not None :
                    cost = row['Cost']
                    if cost.strip() != '' :
                        extCost = float(cost)*qty
                        total += extCost
                print "    ",qty,cost,extCost,partNum,description
            print 'Total',total



if __name__ == '__main__' :
    config = eval(file('SmallPanel/panelConfig.json','r').read())
    pcbDir = config['pcbDir']

    calculateCosts(config, "config/PartDetails.csv")
