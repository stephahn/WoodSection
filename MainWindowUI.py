__author__ = 'Stephan'
from  mainWindow2 import Ui_MainWindow
from PySide import QtGui,QtCore
import sys
from wood_seg import Wood
import pyqtgraph as pg
from simpleUI import *

class Main(Ui_MainWindow):
    def __init__(self,parent,wood):
        super(Main,self).__init__()
        self.setupUi(parent)
        self.wood=wood
        self.graphicsView.add(self.wood.toShow,0)
        self.initParameter()
        self.machine = QtCore.QStateMachine()
    def initParameter(self):
        '''
        Initialise parameters
        '''
        params = [{
            'name':'Global Mask optimization','type':'group','children':
            [{'name': 'low_res', 'type': 'float', 'value': self.wood.get_parameter('low_res'), 'limits': (0,1), 'step': 0.1},
             {'name': 'selemMask','type':'group','children':[
                 {'name':'shape','type':'list','values':['ellipse','rectangle'],'value':self.wood.get_parameter('selemMask',meta=True)[0]},
                 {'name':'height','type':'int','value':self.wood.get_parameter('selemMask',meta=True)[1][0],'limits': (0,10000)},
                 {'name':'width','type':'int','value':self.wood.get_parameter('selemMask',meta=True)[1][1],'limits': (0,10000)}
                                                          ]},
                {'name': 'Compute mask', 'type': 'action'}
            ]},
            {
            'name':'Segmentation optimization','type':'group','children':
            [{'name':'min_size_th','type':'int','value':self.wood.get_parameter('min_size_th'),'limits': (0,10**16)},
             {'name':'max_size_th','type':'int','value':self.wood.get_parameter('max_size_th'),'limits': (0,10**16)},
             {'name':'radius','type':'int','value':self.wood.get_parameter('radius'),'limits':(0,10**16)},
             {'name':'p0','type':'float','step':0.1,'value':self.wood.get_parameter('p0'),'limits':(0,1)},
             {'name':'iter','type':'int','value':self.wood.get_parameter('iter'),'limits':(1,15)},
             {'name': 'selemSeg','type':'group','children':[
                 {'name':'shape','type':'list','values':['ellipse','rectangle'],'value':self.wood.get_parameter('selemSeg',meta=True)[0]},
                 {'name':'height','type':'int','value':self.wood.get_parameter('selemSeg',meta=True)[1][0],'limits': (0,10000)},
                 {'name':'width','type':'int','value':self.wood.get_parameter('selemSeg',meta=True)[1][1],'limits': (0,10000)}
                                                            ]},
             {'name': 'Compute Seg', 'type': 'action'}

            ]},
            {'name':'Tracking optimization','type':'group','children':
            [{'name':'eps','type':'int','value':self.wood.get_parameter('eps'),'limits':(10,45)},
             {'name':'k','type':'int','value':self.wood.get_parameter('k'),'limits':(1,20)},
             {'name':'orient0','type':'int','value':self.wood.get_parameter('orient0'),'limits':(0,360)},
             {'name':'alpha','type':'float','value':self.wood.get_parameter('alpha'),'limits':(0,1),'step':0.1},
             {'name': 'Compute track', 'type': 'action'}]
            },
            {'name':'Image ID','type':'int','value':self.wood.id}]
        self.treeWidget.addParameter(params,self.change,self.computeMask,self.computeSeg,self.computeTrack)
    def change(self,param, changes,p):
        for param, change, data in changes:
            path = p.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        childName=childName.split('.')
        self.wood.set_parameter(childName,data)
        self.graphicsView.add(self.wood.toShow,0)
    def computeMask(self):
        self.wood.computeMask()
        self.graphicsView.add(self.wood.mask,1)
    def computeSeg(self):
        self.wood.computeSeg()
        self.graphicsView.add(self.wood.labels,2)
    def computeTrack(self):
        self.wood.computeTrack()
        self.graphicsView.add(self.wood.track,3)







pg.setConfigOptions(useWeave=False)
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    B = Wood(5106)

    A= QtGui.QMainWindow()
    window = Main(A,B)
    #view = ImageViewSimple(window.graphicsView)

    #A = pg.image(B.Image)

    A.show()
    app.exec_()