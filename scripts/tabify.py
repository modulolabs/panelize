#!/usr/bin/env python

import sys, re, os

"""
This script processes a gerber outline file produced by gerbmerge.
It adds tabs between boards and a border around the entire panel.

It operates as a chain of filters. Each filter has methods for
certain gerber commands and is responsible for processing those
commands and calling the next filter. The first filter reads
the source gerber file and the last filter writes the results.
"""

class Reader(object) :
    def __init__(self, writer, filename) :
        self.writer = writer
        self.inFile = file(filename, "r")

    def read(self) :
        drawRegExp = re.compile("X(?P<X>[0-9]+)Y(?P<Y>[0-9]+)D(?P<D>[0-9]+).*")
        apertureRegExp = re.compile("%ADD(?P<D>[0-9]+)C,(?P<width>[0-9]*\.[0-9]*)\*%")

        for line in self.inFile :
            match = drawRegExp.match(line)
            if match is not None :
                X,Y,D = [int(x) for x in match.groups()]
                pos = (X*1e-5, Y*1e-5)
                if (D == 2) :
                    self.writer.moveTo(pos)
                elif (D == 1) :
                    self.writer.drawTo(pos)
                else :
                    self.writer.write(line)
                continue

            match = apertureRegExp.match(line)
            if match is not None :
                D,width = match.groups()
                self.writer.write("%%ADD%sC,0.00500*%%\n" % D)
                continue

            if line.strip() != "M02*" :
                self.writer.write(line)

        self.writer.endFile()

class BorderFilter(object) :

    def __init__(self, writer, borderPoints) :
        self.writer = writer
        self.borderPoints = borderPoints

    def moveTo(self, point) :
        self.writer.moveTo(point)

    def drawTo(self, point) :
        self.writer.drawTo(point)

    def write(self, line) :
        self.writer.write(line)

    def endFile(self) :
        # Draw the inner border
        minX = 1e6
        maxX = 1e-6
        minY = 1e6
        maxY = 1e-6

        self.writer.moveTo(self.borderPoints[-1])
        for point in self.borderPoints :
            self.writer.drawTo(point)
            minX = min(minX, point[0])
            maxX = max(maxX, point[0])
            minY = min(minY, point[1])
            maxY = max(maxY, point[1])

        margin=.3
        self.writer.moveTo((minX-margin, minY-margin))
        self.writer.drawTo((maxX+margin, minY-margin))
        self.writer.drawTo((maxX+margin, maxY+margin))
        self.writer.drawTo((minX-margin, maxY+margin))
        self.writer.drawTo((minX-margin, minY-margin))

        self.writer.endFile()

class Tab() :

    def __init__(self, pos) :
        self.pos = pos
        self.intersections = []
        self.bottomY = None
        self.topY = None

    def __getitem__(self, i) :
        return self.pos[i]

    def __setitem__(self, i, v) :
        self.pos[i] = v

class TabsFilter(object) :
    def __init__(self, writer, tabs, drillFile):
        self.tabs = tabs
        self.writer = writer
        self.currentPos = (0,0)
        self.tabBottom = -.05
        self.tabTop = .2
        self.tabWidth = .1
        self.drillFile = drillFile

    def getTabIntersections(self, tab, p0, p1) :
        if abs(p0[1]-p1[1] > .001) : # Not a horizontal line
            return None
        if (p0[1] < tab[1]+self.tabBottom) : # Below the tab bottom
            return None
        if (p0[1] > tab[1]+self.tabTop) : # Above the tab top
            return None
        if (p0[0] < tab[0] and p1[0] < tab[0]) : #Left of the tab
            return None
        if (p0[0] > tab[0]+self.tabWidth and p1[0] > tab[0]+self.tabWidth) : #Right of the tab
            return None

        if (tab.bottomY is None) :
            tab.bottomY = p0[1]
        elif (tab.bottomY < p0[1]) :
            tab.topY = p0[1]
        else :
            tab.topY = tab.bottomY
            tab.bottomY = p0[1]

        if (p0[0] < p1[0]) : # First point is to the left of the second
            return [(tab[0], p0[1]), (tab[0]+self.tabWidth, p0[1])]
        else :
            return [(tab[0]+self.tabWidth, p0[1]), (tab[0], p0[1])]

    def write(self, line) :
        self.writer.write(line)

    def moveTo(self, point) :
        self.writer.moveTo(point)
        self.currentPos = point

    def _drawToCheckTabs(self, point, tabs) :
        for i in range(len(tabs)) :
            tab = tabs[i]
            intersections = self.getTabIntersections(tab, self.currentPos, point)
            if intersections is not None :
                self._drawToCheckTabs(intersections[0], tabs[i+1:])
                self.insertMousebites(self.currentPos, intersections[1])
                self.writer.moveTo(intersections[1])

        self.currentPos = point
        self.writer.drawTo(point)

    def drawTo(self, point) :
        self._drawToCheckTabs(point, self.tabs)

    def endFile(self) :
        for tab in self.tabs :
            if (tab.bottomY is not None and tab.topY is not None) :
                self.writer.moveTo((tab.pos[0], tab.bottomY))
                self.writer.drawTo((tab.pos[0], tab.topY))
                self.writer.moveTo((tab.pos[0]+self.tabWidth, tab.bottomY))
                self.writer.drawTo((tab.pos[0]+self.tabWidth, tab.topY))

        self.writer.endFile()

    def insertMousebites(self, p0, p1) :
        # More generally, we should get the p0->p1 vector and rotate it
        offset = .010
        if p0[0] > p1[0] :
            offset *= -1

        for t in [-.15, 1.15] :
            p = (p0[0]*t + p1[0]*(1-t), p1[1]*t + p1[1]*(1-t))
            self.drillFile.addHit(p)

        for t in [.17, .5, .83] :
            p = (p0[0]*t + p1[0]*(1-t), offset + p1[1]*t + p1[1]*(1-t))
            self.drillFile.addHit(p)


class Writer(object) :
    def __init__(self, filename) :
        self.outFile = file(filename,"w")

    def _formatNumber(self, x) :
        return ("%2.5f" % x).replace(".", "")

    def _formatPoint(self, point) :
        return "X%sY%s" % (self._formatNumber(point[0]), self._formatNumber(point[1]))

    def write(self, line) :
        self.outFile.write(line)

    def moveTo(self, point) :
        self.currentPos = point
        self.outFile.write("%sD02*\n" % (self._formatPoint(point)))

    def drawTo(self, point) :
        self.outFile.write("%sD01*\n" % (self._formatPoint(point)))
        self.currentPos = point

    def endFile(self) :
        self.outFile.write("M02*\n")
        self.outFile.close()

class DrillFile(object) :

    def __init__(self) :
        self.diameters = {}
        self.drillHits = {}
        self.currentTool = None


    def setTool(self, diameter) :
        nextTool = 1
        for tool,toolDiameter in self.diameters.iteritems() :
            if (diameter == toolDiameter) :
                return tool
            nextTool = max(tool+1,nextTool)
        self.diameters[nextTool] = diameter
        self.drillHits[nextTool] = []
        self.currentTool = nextTool

    def addHit(self, pt) :
        self.drillHits[self.currentTool].append((int(pt[0]*10000),int(pt[1]*10000)))

    def read(self, filename) :

        toolDefRegExp = re.compile("T(?P<tool>[0-9][0-9])C(?P<diameter>[0-9]*\.[0-9]*)")
        toolSelectRegExp = re.compile("T(?P<tool>[0-9][0-9])")
        drillRegExp = re.compile("X(?P<X>[0-9]+)Y(?P<Y>[0-9]+)")

        with open(filename,"r") as f :
            for line in f :
                m = toolDefRegExp.match(line)
                if m :
                    tool = int(m.groupdict()['tool'])
                    diameter = float(m.groupdict()['diameter'])
                    self.drillHits[tool] = []
                    self.diameters[tool] = diameter

                    continue

                m = toolSelectRegExp.match(line)
                if m :
                    self.currentTool = int(m.groupdict()['tool'])
                    continue

                m = drillRegExp.match(line)
                if m :
                    x = int(m.groupdict()['X'])
                    y = int(m.groupdict()['Y'])
                    self.drillHits[self.currentTool].append((x,y))
                    continue
                if line.strip() not in ['%','M30'] :
                    print 'Skipping: ', line

    def write(self, filename) :
        with open(filename,'w') as f :
            f.write("%\n")

            for item in self.diameters.iteritems() :
                f.write("T%02dC%1.6f\n" % item)

            f.write("%\n")

            for tool,hits in self.drillHits.iteritems() :
                f.write("T%02d\n" % tool)
                for hit in hits :
                    s = "X%dY%d\n" % hit
                    f.write(s.replace("",""))

            f.write("M30\n")


def runFilters(config) :

    outputDir = config['outputDir']
    tmpDir = config['tmpDir']
    globalOffset = config['globalOffset']

    drillFile = DrillFile()
    drillFile.read('tmp/Modulo.drills.xln')
    drillFile.setTool(.022)

    # The last object in the chain writes the new gerber file
    writer = Writer(os.path.join(outputDir,"Modulo.boardoutline.ger"))

    # Lower left hand corner of each tab
    tabs = config['tabs']
    tabs = [(tab[0]+globalOffset[0],tab[1]+globalOffset[1]) for tab in tabs]

    # Create a flter that inserts the tabs
    tabsFilter = TabsFilter(writer, [Tab(p) for p in tabs], drillFile)

    # A filter that creates a border around the entire panel
    borderPoints = config['border']
    borderPoints.reverse()
    borderPoints = [(borderPoint[0]+globalOffset[0],borderPoint[1]+globalOffset[1]) for borderPoint in borderPoints]

    borderFilter = BorderFilter(tabsFilter, borderPoints)

    # Read from the source gerber file.
    reader = Reader(borderFilter, os.path.join(tmpDir,"boardoutline.ger"))
    reader.read()

    drillFile.write(os.path.join(outputDir,'Modulo.drills.xln'))

if __name__ == '__main__' :
    config = eval(file('config/placement.json','r').read())
    runFilters(config)
