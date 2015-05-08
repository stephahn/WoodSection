__author__ = 'Stephan'
from tools import *
import logging
import os
import numpy as npy
import pandas as pd
from PySide import QtCore
from config import *
import matplotlib.pyplot as plt
from PIL import Image
import json
from skimage import restoration

logging.basicConfig(filename=os.getcwd()+'/tmp/wood.log', level=logging.INFO,format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',datefmt="%Y-%m-%d %H:%M:%S")
class Wood(QtCore.QObject):
    '''
    retrieve an image from Omero with the id.
    '''
    speak = QtCore.Signal()
    def __init__(self):
        '''
        retrieve the omero image from the id
        :param id: id of an image
        '''
        self.listFile = [os.path.join(dp, f) for dp, dn, filenames in os.walk(os.getcwd()+'/data') for f in filenames if os.path.splitext(f)[1] == '.tif']
        QtCore.QObject.__init__(self)
        self.parameter=DEFAULT
        self.id = self.listFile[0]
        logging.info('Started wood')
        self.Image = get_image(self.id)
        self.index = npy.array([self.parameter['FirstLine'],self.parameter['FirstLine']+self.parameter['VisualWidth'],\
                                self.parameter['FirstColumn'],self.parameter['FirstColumn']+self.parameter['VisualHeight']])

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
        if self.parameter['UseMask']=='yes':
            self.center,self.tree=get_tree_center(self.mask*self.Seg,self.mask*self.labels)
        elif self.parameter['UseMask']=='no':
            self.center,self.tree=get_tree_center(self.Seg,self.labels)
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
        #self.Tile = restoration.denoise_bilateral(self.Tile,win_size=5,sigma_spatial=100,sigma_range=0.5)
        self.Tile = restoration.denoise_tv_chambolle(self.Tile, weight=0.1, multichannel=False,n_iter_max=20)

    def updateIndex(self):
        self.index = npy.array([self.parameter['FirstLine'],self.parameter['FirstLine']+self.parameter['VisualWidth'],\
                                self.parameter['FirstColumn'],self.parameter['FirstColumn']+self.parameter['VisualHeight']])

    def initToShow(self):
        self.toShow = self.Tile.copy()
        self.mask = npy.zeros_like(self.toShow)
        self.labels = npy.zeros_like(self.toShow)
    def compute_Row(self):
        a=0
        maxi=0
        for i in range(self.center.shape[0]):
            if self.selected[i]==0:
                self.cellsRows.append(CellRow(self.center[i,:],self))
                a=a+len(self.cellsRows[-1])
                if len(self.cellsRows[-1])>20:
                    maxi = maxi+1
        print "mean",a*1.0/len(self.cellsRows)
        print "maxi",maxi
        print "total",len(self.cellsRows)
    def set_parameter(self,name,data):
        if name[0]=='Image ID':
            self.setImage(data)
        elif name[0]=='extract' or name[0]=='save Parameter' or name[0]=='load Parameter':
            print name[0]
        elif name[1] == 'selemMask' or name[1] == 'selemSeg':
            if name[2]=='height':
                self.parameter[name[1]][self.parameter[name[1]].keys()[0]][0]=data
            elif name[2]=='width':
                self.parameter[name[1]][self.parameter[name[1]].keys()[0]][1]=data
            elif name[2]=='shape':
                self.parameter[name[1]][data]=self.parameter[name[1]].pop(self.parameter[name[1]].keys()[0])
        elif name[1] in ['VisualWidth','VisualHeight','FirstLine','FirstColumn']:
            self.parameter[name[1]]=data
            self.updateIndex()
            self.updateImg()
            self.initToShow()
            self.speak.emit()
        else:
            self.parameter[name[1]]=data
    def setImage(self,id):
        self.updateIndex()
        self.Image=get_image(id)
        self.id=id
        self.updateImg()
        self.initToShow()
        self.speak.emit()
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
    def launch_all_image(self):
        self.index = npy.array([0,self.Image.shape[0],0,self.Image.shape[1]])
        self.updateImg()
        if self.parameter['UseMask']=='yes':
            self.computeMask()
        self.computeSeg()
        self.computeTrack()
        self.extract_profil()
    def extract_profil(self):
        value = list()
        x_value = list()
        y_value = list()
        rows_number= list()
        connections_number = list()
        f = h5py.File(os.getcwd()+'/tmp/'+os.path.splitext(os.path.basename(self.id))[0]+'.hdf5','w')
        n_row = 0
        n_connection = 0
        for i in range(len(self.cellsRows)):
            if len(self.cellsRows[i])>1:
                prev = self.cellsRows[i][0]
                for j in range(1,len(self.cellsRows[i])):
                    cur = self.cellsRows[i][j]
                    length = int(npy.hypot(cur.line-prev.line, cur.column-prev.column))
                    x, y = npy.linspace(prev.line,cur.line, length), npy.linspace(prev.column,cur.column, length)
                    value.extend(self.Tile[x.astype(npy.int),y.astype(npy.int)])

                    x_value.extend(x.astype(npy.int))
                    y_value.extend(y.astype(npy.int))
                    rows_number.extend([n_row]*length)
                    connections_number.extend([n_connection]*length)

                    prev =  self.cellsRows[i][j]
                    n_connection = n_connection+1
                n_row=n_row+1

        f.create_dataset('value',data=value)
        f.create_dataset('x',data=x_value)
        f.create_dataset('y',data=y_value)
        f.create_dataset('connection_number',data=connections_number)
        f.create_dataset('row_number',data=rows_number)

    def saveParameter(self,name):
        with open(os.getcwd()+'/parameter/'+name+'.json', 'wb') as fp:
            json.dump(self.parameter,fp)
    def loadParameter(self,name):
        with open(name) as fp:
            self.parameter = json.load(fp)
    def getTip(self):
        tip = list()
        for cell in self.cellsRows:
            if len(cell)>1:
                    tip.append(cell.tipAngle[0]*1.0/cell.tipAngle[1])
        return npy.median(tip)
class CellRow(list):
    '''
    List of lumen
    '''
    def __init__(self,(x,y),wood):
        super(CellRow,self).__init__()
        self.append(Lumen(x,y))
        self.wood=wood
        self.tipAngle=[self.wood.get_parameter('orient0'),1]
        self.get_next_item(self.wood.get_parameter('orient0'))
        self.profil = list()

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
                self.tipAngle[0]=self.tipAngle[0]+self[-1].MAngle
                self.tipAngle[1]=self.tipAngle[1]+1
    def get_profil(self):
        if len(self)>1:
            prev = self[0]
            for i in range(1,len(self)):
                cur = self[i]
                length = int(npy.hypot(cur.line-prev.line, cur.column-prev.column))
                x, y = npy.linspace(prev.line,cur.line, length), npy.linspace(prev.column,cur.column, length)
                self.profil.extend(self.wood.Tile[x.astype(npy.int),y.astype(npy.int)])
                prev=self[i]







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
        if angle>270:
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
    A = Wood(1)
    A.computeMask()
    A.computeSeg()
    A.computeTrack()
    A.extract_profil()
