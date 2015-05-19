__author__ = 'Stephan'
from  mainWindow2 import Ui_MainWindow
import os
from PySide import QtGui,QtCore
import sys
from wood_seg import Wood
import pyqtgraph as pg
from simpleUI import *
from ThreadPool2 import Worker
import copy



class Main(Ui_MainWindow):
    def __init__(self,parent,wood):
        super(Main,self).__init__()
        self.setupUi(parent)
        self.wood=wood
        self.copyWood=list()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setAlignment(QtCore.Qt.AlignLeft)
        self.statusbar.addPermanentWidget(self.progressBar)
        self.statusbar.showMessage('Ready')
        self.threadList=list()
        self.graphicsView.add(self.wood.toShow,0)
        self.initParameter()
        self.connectAll()
    def connectAll(self):
        self.wood.speak.connect(self.updateView)
        self.wood.speakProgress.connect(self.updateBar)
        self.actionLaunch.triggered.connect(lambda: self.wood.measure.launch_measure(self.wood.speakProgress))
    def initParameter(self):
        '''
        Initialise parameters
        '''
        params = self.getParams()
        self.treeWidget.addParameter(params,self.change,self.computeMask,self.computeSeg,self.computeTrack,self.extract,self.saveParameter,self.loadParameter)
    def getParams(self):

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
             {'name': 'Compute track', 'type': 'action'},
             {'name':'tips','type':'int','value':self.wood.get_parameter('orient0')}]
            },
            {'name':'options','type':'group','children':
            [{'name':'UseMask','type':'list','values':['yes','no'],'value':self.wood.get_parameter('UseMask')},
             {'name':'VisualWidth','type':'int','value':self.wood.get_parameter('VisualWidth')},
             {'name':'VisualHeight','type':'int','value':self.wood.get_parameter('VisualHeight')},
             {'name':'FirstLine','type':'int','value':self.wood.get_parameter('FirstLine')},
             {'name':'FirstColumn','type':'int','value':self.wood.get_parameter('FirstColumn')}]},
            {'name':'Image ID','type':'list','values':self.wood.listFile,'value':self.wood.listFile[0]},
            {'name':'save Parameter','type':'action'},
            {'name':'load Parameter','type':'action'},
            {'name':'extract','type':'action'}]
        return params
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
        self.treeWidget.setTip(int(self.wood.getTip()))
    def extract(self):
        self.copyWood.append(copy.copy(self.wood))
        self.threadList.append( Worker(func=self.copyWood[-1].launch_all_image))
        self.threadList[-1].end.connect(self.finished)
        self.threadList[-1].start()
    def finished(self):
        import gc
        self.threadList=list()
        self.copyWood=list()
        gc.collect()
        self.wood.speakProgress.emit({"msg":"ready","value":0,"max":100})
    def saveParameter(self):
        name, ok = QtGui.QInputDialog.getText(QtGui.QWidget(), 'Save Parameter', 'Give name to the file:',text=os.path.splitext(os.path.basename(self.wood.id))[0]+"_param")
        self.wood.saveParameter(name)
    def loadParameter(self):
        name, ok = QtGui.QFileDialog.getOpenFileName(QtGui.QWidget(), 'Open file',os.getcwd()+'/parameter')
        self.wood.loadParameter(name)
        params=self.getParams()
        self.treeWidget.clear()
        self.treeWidget.addParameter(params,self.change,self.computeMask,self.computeSeg,self.computeTrack,self.extract,self.saveParameter,self.loadParameter)
    @QtCore.Slot()
    def updateView(self):
        self.graphicsView.add(self.wood.toShow,0)
        self.graphicsView.remove(1)
        self.graphicsView.remove(2)
        self.graphicsView.remove(3)
    @QtCore.Slot()
    def updateBar(self,msg):
        self.statusbar.showMessage(msg['msg'])
        self.progressBar.setValue(msg['value'])
        if 'max' in msg:
            self.progressBar.setMaximum(msg['max'])







pg.setConfigOptions(useWeave=False)
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    B = Wood()

    A= QtGui.QMainWindow()
    #workPool.append_work(Work(Main,[A,B]))
    window = Main(A,B)

    #view = ImageViewSimple(window.graphicsView)

    #A = pg.image(B.Image)

    A.show()
    app.processEvents()
    app.exec_()