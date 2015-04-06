__author__ = 'Stephan'
from tools import *
import logging
import os
import numpy as npy
from PySide import QtCore
from config import *
import matplotlib.pyplot as plt
from PIL import Image


logging.basicConfig(filename=os.getcwd()+'/tmp/wood.log', level=logging.INFO,format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',datefmt="%Y-%m-%d %H:%M:%S")
class Wood():
    '''
    retrieve an image from Omero with the id.
    '''
    def __init__(self,id):
        '''
        retrieve the omero image from the id
        :param id: id of an image
        '''
        self.parameter=DEFAULT
        self.id = id
        logging.info('Started wood')
        self.Image = get_image(id)
        self.index = npy.array([0,2000,0,2000])

        self.updateImg()
        self.initToShow()

        '''
        if len(self.Image.shape)==3:
            self.Image=npy.sum(self.Image,axis=2)/3
        self.Image = (self.Image-npy.min(self.Image))*255.0/(npy.max(self.Image)-npy.min(self.Image))
        self.Image=self.Image.astype(npy.uint8)
        self.Image = self.Image[0:2000,0:10000]
        self.set_parameter('DEFAULT')
        self.mask = get_mask(self.Image,selemMask =self.get_parameter('selemMask'),low_res=self.get_parameter('low_res'))
        self.labels,self.Seg=get_label(self.Image,seg=True,min_size_th=self.get_parameter('min_size_th')\
                                       ,max_size_th=self.get_parameter('max_size_th')\
                                       ,radius=self.get_parameter('radius')\
                                       ,p0=self.get_parameter('p0')\
                                       ,iter=self.get_parameter('iter')\
                                       ,selemSeg=self.get_parameter('selemSeg'))
        self.center,self.tree=get_tree_center(self.mask*self.Seg,self.mask*self.labels)
        self.cellsRows = list()
        self.selected = npy.zeros((self.center.shape[0],1))
        self.compute_Row()
        '''
        logging.info('Finished')
    def computeMask(self):
        self.mask = get_mask(self.Tile,selemMask =self.get_parameter('selemMask'),low_res=self.get_parameter('low_res'))
    def computeSeg(self):
        self.labels,self.Seg=get_label(self.Tile,seg=True,min_size_th=self.get_parameter('min_size_th')\
                                       ,max_size_th=self.get_parameter('max_size_th')\
                                       ,radius=self.get_parameter('radius')\
                                       ,p0=self.get_parameter('p0')\
                                       ,iter=self.get_parameter('iter')\
                                       ,selemSeg=self.get_parameter('selemSeg'))
    def computeTrack(self):
        self.center,self.tree=get_tree_center(self.mask*self.Seg,self.mask*self.labels)
        self.cellsRows = list()
        self.selected = npy.zeros((self.center.shape[0],1))
        self.compute_Row()
        self.track = npy.zeros_like(self.Tile)
        for i, cr in enumerate(self.cellsRows):
            if len(cr)>1:
                for j in range(1,len(cr)):
                    num = max(abs(int(cr[j-1].line)-int(cr[j].line)),abs(int(cr[j-1].column)-int(cr[j].column)))
                    x=npy.linspace(int(cr[j-1].line),int(cr[j].line),num=num).astype(int)
                    y=npy.linspace(npy.int(cr[j-1].column),npy.int(cr[j].column),num=num).astype(int)
                    for k in range(3):
                        self.track[x-k+1,y-k+1]=1

    def updateImg(self):
        self.Tile = self.Image[self.index[0]:self.index[1],self.index[2]:self.index[3]]
        if len(self.Tile.shape)==3:
            self.Tile=npy.sum(self.Tile,axis=2)/3
        self.Tile = (self.Tile-npy.min(self.Tile))*255.0/(npy.max(self.Tile)-npy.min(self.Tile))
        self.Tile = self.Tile.astype(npy.uint8)
        self.Tile = npy.transpose(self.Tile,axes=[1,0])

    def initToShow(self):
        self.toShow = self.Tile.copy()
        self.mask = npy.zeros_like(self.toShow)
        self.labels=npy.zeros_like(self.toShow)
    def compute_Row(self):
        for i in range(self.center.shape[0]):
            if self.selected[i]==0:
                self.cellsRows.append(CellRow(self.center[i,:],self))
    def set_parameter(self,name,data):
        if name[0]=='Image ID':
            self.setImage(data)
        elif name[1] == 'selemMask' or name[1] == 'selemSeg':
            if name[2]=='height':
                self.parameter[name[1]][self.parameter[name[1]].keys()[0]][0]=data
            elif name[2]=='width':
                self.parameter[name[1]][self.parameter[name[1]].keys()[0]][1]=data
            elif name[2]=='shape':
                self.parameter[name[1]][data]=self.parameter[name[1]].pop(self.parameter[name[1]].keys()[0])

        else:
            self.parameter[name[1]]=data
    def setImage(self,id):
        self.Image=get_image(id)
        self.id=id
        self.updateImg()
        self.initToShow()
    def get_parameter(self,name,meta = False):
        '''
        return the value of a parameter translated.
        '''
        logging.info('Try to retrieve parameter %s',name)
        if name == 'selemMask' or name == 'selemSeg':
            param = self.parameter[name]
            if meta == False:
                if param.keys()[0] == 'rectangle':
                    return npy.ones(param[param.keys()[0]])
                elif param.keys()[0] == 'ellipse':

                    return ellipse(param[param.keys()[0]])
            elif meta==True:

                return [param.keys()[0],param[param.keys()[0]]]
        else:
            return self.parameter[name]

    def uptade_param(self,name):
        '''
        Update parameter with a new set of parameter
        '''
        self.parameter.update(eval(name))
        logging.info('Update parameter. New parameter values: %s',self.parameter)
        self.updateImg()
        self.initToShow()


class CellRow(list):
    '''
    List of lumen
    '''
    def __init__(self,(x,y),wood):
        super(CellRow,self).__init__()
        self.append(Lumen(x,y))
        self.wood=wood
        self.get_next_item(self.wood.get_parameter('orient0'))
    def get_next_item(self,orient):
        nextItem = get_next(self.wood.tree,(self[-1].line,self[-1].column),self.wood.center,orient=orient,eps=self.wood.get_parameter('eps'),k=self.wood.get_parameter('k'))
        if nextItem!=None:
            next,idx = Lumen(nextItem[0][0],nextItem[0][1]), nextItem[1]
            if self.wood.selected[idx]==0:
                self.wood.selected[idx] = 1
                angle = self[-1].compute_orientation(next)
                self.append(next)
                orient = (1-self.wood.get_parameter('alpha'))*orient + self.wood.get_parameter('alpha')*angle
                self.get_next_item(orient)




class Lumen():
    '''
    Define an lumen with a position.
    '''
    def __init__(self,x,y):
        self.line   = x
        self.column = y
        self.LAngle = 0
        self.RAngle = 0
        self.MAngle = 0
    def __lt__(self, other):
        return self.column<other.column
    def compute_orientation(self,other):
        pt1 = (self.line,self.column)
        pt2 = (other.line,other.column)
        angle = cal_angle(pt1,pt2)
        if angle>180:
            self.LAngle  = angle
            other.RAngle = angle
        else:
            self.RAngle = angle
            other.LAngle = angle
        self.set_MAngle()
        other.set_MAngle()
        return angle
    def set_MAngle(self):
        if (self.LAngle!=0) & (self.RAngle!=0):
            self.MAngle = (self.RAngle+self.LAngle)*1.0/2
        else:
            self.MAngle = self.RAngle+self.LAngle




if __name__ == '__main__':
    A = Wood(5222)
