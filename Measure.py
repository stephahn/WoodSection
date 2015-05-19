__author__ = 'Olivier Debeir'
import pandas as pd
import h5py
import numpy as np
from PySide import QtGui
from scipy.ndimage.filters import gaussian_filter1d
import os
import sys

class Measure():

    def run_length(self,bits):
        """
        returns high length, low length, high center, low center
        """

        # make sure all runs of ones are well-bounded
        bounded = np.hstack(([0], bits, [0]))
        # get 1 at run starts and -1 at run ends
        difs = np.diff(bounded)
        run_starts, = np.where(difs > 0)
        run_ends, = np.where(difs < 0)

        highs = run_ends - run_starts
        lows = run_starts[1:] - run_ends[:-1]

        #cycle = 1 high + 1 low
        pos_high = .5*(run_ends - run_starts -1) + run_starts
        pos_low = .5*(run_starts[1:] - run_ends[:-1]-1) + run_ends[:-1]

        h = highs[1:-1]
        l = lows[1:]
        ph = pos_high[1:-1]
        pl = pos_low[1:]

        start_stop_high = ( run_starts[1:-1],run_ends[1:-1])
        start_stop_low = ( run_ends[1:-1],run_starts[2:])

        return (h,l,ph,pl,start_stop_high,start_stop_low)
    def features(self,values,start_stop_high,start_stop_low):

        std_high = np.zeros_like(start_stop_high[0],dtype=np.float)
        std_low = np.zeros_like(start_stop_high[0],dtype=np.float)
        for k in range(len(start_stop_high[0])):
            std_high[k] = values[start_stop_high[0][k]:start_stop_high[1][k]].std()
            std_low[k] = values[start_stop_low[0][k]:start_stop_low[1][k]].std()
        return std_high,std_low

    def launch_measure(self,progress):
        progress.emit({"msg":"measuring","value":0,"max":100})
        fname, _ = QtGui.QFileDialog.getOpenFileName(QtGui.QWidget(),'Open file',os.getcwd()+'/tmp')
        if fname!="":
            with h5py.File(fname, "r") as fid:
                 df = pd.DataFrame()
                 print fid
                 for name in fid:
                    print 'import ',name
                    df[name] = np.asarray(fid[name])
            segments = df.groupby(['row_number'])
            X = []
            Y = []
            R = []
            NH = []
            NL = []
            ID = []
            progress.emit({"msg":"measuring","value":0,"max":100})
            count=0
            for s_no,seg in segments:
                progress.emit({"msg":"measuring","value":count*100/(len(segments)),"max":100})
                value = seg['value']
                smoothed_value = gaussian_filter1d(value,20)
                thresh = (value-smoothed_value)>0

                n_high,n_low,pos_high,pos_low,start_stop_high,start_stop_low = self.run_length(thresh)

                feat = self.features(value,start_stop_high,start_stop_low)

                ratio = 1.*n_high/(n_high + n_low)

                x = np.asarray(seg['x'])
                y = np.asarray(seg['y'])
                row = np.asarray(seg['row_number'])
                xs = x[start_stop_high[0]]
                ys = y[start_stop_high[0]]
                nrow = row[start_stop_high[0]]

                X.extend(xs)
                Y.extend(ys)
                R.extend(ratio)
                NH.extend(n_high)
                NL.extend(n_low)
                ID.extend(nrow)
                count+=1
            progress.emit({"msg":"measuring:saving","value":99,"max":100})
            if not os.path.isdir(os.getcwd()+'/measure'):
                os.mkdir(os.getcwd()+'/measure')
            with h5py.File(os.getcwd()+'/measure/'+os.path.basename(fname), "w") as f:
                f.create_dataset('x',data=X)
                f.create_dataset('y',data=Y)
                f.create_dataset('ratio',data=R)
                f.create_dataset('h_len',data=NH)
                f.create_dataset('l_len',data=NL)
                f.create_dataset('row',data=ID)
        progress.emit({"msg":"measuring:finish","value":100,"max":100})





if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.quitOnLastWindowClosed()
    M =Measure()
    M.launch_measure()
