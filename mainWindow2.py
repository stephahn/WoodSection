# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainWindow2.ui'
#
# Created: Mon May 18 17:44:25 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(795, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame = QtGui.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtGui.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.widget = GraphicsView(self.frame)
        self.widget.setObjectName("widget")
        self.graphicsView = ImageViewSimple(self.widget)
        self.graphicsView.setGeometry(QtCore.QRect(9, 9, 256, 511))
        self.graphicsView.setObjectName("graphicsView")
        self.gridLayout_2.addWidget(self.widget, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.frame)
        self.treeWidget = ParameterTreeSimple(self.centralwidget)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.treeWidget.header().setVisible(False)
        self.horizontalLayout.addWidget(self.treeWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 795, 21))
        self.menubar.setObjectName("menubar")
        self.menuMeasure = QtGui.QMenu(self.menubar)
        self.menuMeasure.setObjectName("menuMeasure")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionSwitch_image_part = QtGui.QAction(MainWindow)
        self.actionSwitch_image_part.setObjectName("actionSwitch_image_part")
        self.actionLaunch = QtGui.QAction(MainWindow)
        self.actionLaunch.setObjectName("actionLaunch")
        self.menuMeasure.addAction(self.actionLaunch)
        self.menubar.addAction(self.menuMeasure.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.menuMeasure.setTitle(QtGui.QApplication.translate("MainWindow", "Tool", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSwitch_image_part.setText(QtGui.QApplication.translate("MainWindow", "Switch zone", None, QtGui.QApplication.UnicodeUTF8))
        self.actionLaunch.setText(QtGui.QApplication.translate("MainWindow", "Launch Measure", None, QtGui.QApplication.UnicodeUTF8))

from pyqtgraph import GraphicsView
from simpleUI import ParameterTreeSimple, ImageViewSimple
