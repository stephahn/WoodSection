__author__ = 'Stephan'
"""
Class which embedded ImageView from pyqtgraph.
"""
from PySide import QtCore, QtGui
import pyqtgraph as pg
import numpy as npy
import matplotlib.pyplot as plt
class ImageViewSimple(pg.ViewBox):
    def __init__(self,parent):
        super(ImageViewSimple, self).__init__()
        parent.setCentralWidget(self)
        self.setAspectLocked(True)
        self.item=[0,0,0,0]
    def add(self, array,idx):
        if self.item[idx]==0:
            self.item[idx]=pg.ImageItem(array,autoDownsample=True)
            self.addItem(self.item[idx])
        else:
            self.item[idx].setImage(array)
        if (idx!=1) & (idx!=3):
            self.item[idx].setLookupTable(self.getLUT(idx))
        if idx!=0:
            for i in range(1,len(self.item)):
                if self.item[i]!=0:
                    self.item[i].setZValue(-100)
            if self.item[idx]!=0:
                self.item[idx].setZValue(100)
                self.item[idx].setOpacity(0.7)
            self.item[0].setZValue(99)
    def getLUT(self,idx):
        if idx == 0 :
            pos = npy.array([0.0,1.0])
            color=npy.array([[0,0,0,255], [255,255,255,255]], dtype=npy.ubyte)
            map = pg.ColorMap(pos, color)
            lut = map.getLookupTable(0.0, 1.0, 256)
        elif idx >1:
            pos = npy.array([0.0,0.000001,0.5,1.0])
            color=npy.array([[0,0,0,255],[255,0,0,255],[0,255,0,255],[255,255,255,255]], dtype=npy.ubyte)
            map = pg.ColorMap(pos, color)
            lut = map.getLookupTable(0.0, 1.0, 256)
        return lut
    def remove(self,idx):
        if self.item[idx]!=0:
            self.removeItem(self.item[idx])
            self.item[idx]=0

class ParameterTreeSimple(pg.parametertree.ParameterTree):
    def __init__(self,parent):
        super(ParameterTreeSimple,self).__init__(parent)
    def addParameter(self,params,changeParam,computeMask,computeSeg,computeTrack,extract,saveParam,loadParam):
        self.p = pg.parametertree.Parameter.create(name='params', type='group', children=params)
        for par in self.p.childs:
            par.opts['expanded']=False
        self.setParameters(self.p, showTop=False)
        self.p.sigTreeStateChanged.connect(lambda param,changes,par = self.p :changeParam(param,changes,par))

        self.p.param('Global Mask optimization', 'Compute mask').sigActivated.connect(computeMask)
        self.p.param('Segmentation optimization', 'Compute Seg').sigActivated.connect(computeSeg)
        self.p.param('Tracking optimization', 'Compute track').sigActivated.connect(computeTrack)
        self.p.param('extract').sigActivated.connect(extract)
        self.p.param('save Parameter').sigActivated.connect(saveParam)
        self.p.param('load Parameter').sigActivated.connect(loadParam)
    def setTip(self,value):
        self.p.param('Tracking optimization', 'tips').setValue(value)
