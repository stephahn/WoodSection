__author__ = 'Stephan'

from omero_lib import OmeroClient
import mahotas as mh
from skimage.filter import rank,threshold_otsu
from skimage.morphology import disk
import numpy as npy
import matplotlib.pyplot as plt
import os
from pprint import pprint
import scipy.ndimage.filters as filters
import scipy.ndimage.measurements as measurements
import scipy.ndimage.morphology as morphology
import scipy.spatial as ssp
import scipy.misc as misc
import math
import h5py
from time import gmtime, strftime
import logging
from credentials import *

cred = {'USERNAME':USERNAME,'PASSWORD':PASSWORD,'HOST':HOST,'PORT':PORT}

def get_image(id,level=0):
    try:
        I = get_from_hdf5(str(id),os.getcwd()+'/tmp/')
    except:
        with OmeroClient(cred['USERNAME'],cred['PASSWORD'],cred['HOST'],cred['PORT'],group=103) as client:
            image=client.get_image(id)
            info = image.get_info()
            I=image.get_plane(level=level)[0]
            to_hdf5(I,str(id),os.getcwd()+'/tmp')
    return I
def to_hdf5(array,name,file):
    '''
    save data in a hdf5 file
    '''
    f=h5py.File(file+'/'+name+'.hdf5','w')
    f.create_dataset('img',data=npy.array(array))
    f.close()
def get_from_hdf5(name,file,idx=None):
    '''
    Read hdf5 file from a serie
    '''
    f=h5py.File(file+'/'+name+'.hdf5','r')
    if idx==None:
        img=f['img'].value
    else:
        img=f['img'][idx[0]:idx[2],idx[1]:idx[3],::]
    f.close()
    return img
def ellipse(dim):
    b,a = dim[0],dim[1]
    xx,yy=npy.meshgrid(range(a),range(b))
    ellarray=((xx-a/2.0)*2.0/a)**2+((yy-b/2.0)*2.0/b)**2
    return ellarray<1
def get_label(img,radius=20,selemSeg=None,seg=False,max_size_th=1000,min_size_th=0,p0=0.7,sigma=None,iter=2):
    '''
    Return the labeled image calculated from a radius disk
    :param img: input image
    :param radius: radius of the object to label
    :param seg: True if the segmented image is return
    :param max_size_th: Threshold on the maximum size
    :param p0: percentile for the segmentation
    :return: Labeled image
    '''
    #radius of the object to segment
    if selemSeg==None:
        selemSeg = disk(radius)
    if sigma:
        img=filters.gaussian_filter(img,sigma)
    img = rank.enhance_contrast_percentile(img, disk(3), p0=0.5, p1=1)

    Seg = rank.threshold_percentile(img,selemSeg,p0=p0)
    Seg = morphology.binary_fill_holes(Seg)
    Seg = morphology.binary_erosion(Seg,iterations=iter)
    Seg = morphology.binary_dilation(Seg,iterations=iter)
    Seg = morphology.binary_fill_holes(Seg)


    labels, nr_objects  = mh.label(Seg)
    #too big
    sizes = mh.labeled.labeled_size(labels)
    too_big = npy.where(sizes > max_size_th)
    labels = mh.labeled.remove_regions(labels, too_big)

    #too small
    sizes = mh.labeled.labeled_size(labels)
    too_small = npy.where(sizes < min_size_th)
    labels = mh.labeled.remove_regions(labels, too_small)

    if seg:
        return labels,Seg
    return labels
def get_mask(img,selemMask=None,low_res=0.5):
    '''
    Get the mask of the lumens
    :param img: Input image
    :param selem: A structuring element
    :return: the mask for the image
    '''
    if selemMask==None:
        selemMask=npy.ones((50,200))
    if low_res!=0:
        tmp = misc.imresize(img,size=low_res)
    else:
        tmp=img

    mask = rank.median(tmp,selemMask)
    otsu = threshold_otsu(mask)
    thre=mask<otsu
    if npy.sum(thre)<(thre.shape[0]*thre.shape[1])/2:
        thre=mask>otsu
    if thre.shape!=img.shape:
        thre= misc.imresize(thre,img.shape,interp='nearest')
    return thre
def get_tree_center(seg,labels,mask=None):
    if mask==None:
        mask=npy.ones_like(labels)
    center = mh.center_of_mass(mask*seg,labels=mask*labels)
    center = center[~npy.isnan(center).any(axis=1)]#delete line with nan value.

    center=center[center[:,1].argsort()]

    kd = ssp.KDTree(center)
    return center, kd
def rgb2hsv(rgb):
        # -- V channel
        out = npy.empty_like(rgb)
        out_v = npy.max(rgb,axis=2)
        mini=npy.min(rgb,axis=2)
        # -- S channel

        # Ignore warning for zero divided by zero
        old_settings = npy.seterr(invalid='ignore')
        out_s = 1-(mini*1.0 /out_v)
        out_s[out_v==0] = 0.
        # red is max
        idx = (rgb[:, :, 0] == out_v)
        out[idx, 0] = (360+((rgb[idx, 1] - rgb[idx, 2])*1.0 / (out_v[idx]-mini[idx])))%360

        # green is max
        idx = (rgb[:, :, 1] == out_v)
        out[idx, 0] = 120 + (rgb[idx, 2] - rgb[idx, 0])*60.0 /(out_v[idx]-mini[idx])

        # blue is max
        idx = (rgb[:, :, 2] == out_v)
        out[idx, 0] = 240 + (rgb[idx, 0] - rgb[idx, 1]) *60.0/(out_v[idx]-mini[idx])
        out[(out_v-mini) == 0.,0] = 0.

        npy.seterr(**old_settings)

        # -- output
        #out[:, :, 0] = out_h
        out[:, :, 1] = out_s
        out[:, :, 2] = out_v

        # remove NaN
        out[npy.isnan(out)] = 0
        return out

def cal_angle(pt1,pt2):
    angle = math.degrees(npy.arctan2(pt1[0]-pt2[0],pt1[1]-pt2[1]))+90
    if angle>0:
        angle=360-angle
    return npy.abs(angle)
def get_next(kd,cur,center,orient=None,eps=45,k=9):
    distance,candidat = kd.query(cur,k=k,p=1)
    distance = distance[1::]
    candidat = candidat[1::]
    selecte=list()

    for i in range(candidat.shape[0]):
        if candidat[i]==center.shape[0]:
            return None
        #elif center[candidat[i]][1]>cur[1]:
        elif center[candidat[i]][1]!=cur[1]:
            if orient!=None:
                next=center[candidat[i]]
                min=npy.abs(orient-cal_angle(cur,next))
                if min<eps:
                    selecte.append(i,)
            else:
                selecte.append(i,)

    if len(selecte)>1:
        min=distance[selecte[0]]
        idx=selecte[0]
        for i in range(1,len(selecte)):
            if min>distance[selecte[i]]:
                min=distance[selecte[i]]
                idx=selecte[i]

    elif len(selecte)!=0:
        idx=selecte[0]
    else:
        return None


    return (center[candidat[idx],:],candidat[idx])
def get_all(cur,checked,alpha=0.8,eps=20,k=9,ori_list=None):
    tmpcur = cur
    Test=[True,True]
    plt.plot(cur[1],cur[0],'bo')
    orientation=[90,270]
    chain = list()
    chain.append(cur)
    for j in range(2):
        cur=tmpcur
        while Test[j]:
            try:
                next,idx=get_next(tree,cur,center,orient=orientation[j],eps=eps,k=k)
                if checked[idx]==0:
                    curAngle = cal_angle(cur,next)
                    if orientation[j]==None:
                        orientation[j]=curAngle
                    else:
                        orientation[j]=(1-alpha)*orientation[j]+alpha*curAngle
                        checked[idx]=1
                    plt.plot([cur[1],next[1]],[cur[0],next[0]],'g-')
                    plt.plot(next[1],next[0],'go')
                    chain.append(next)
                    cur=next
                    if ori_list!=None:
                        ori_list.append(curAngle)

                else:
                    Test[j]=False
                #print orientation[j]
            except:
                Test[j]=False
    return  chain
def onclick(evt,seg,labels,check,center,fig):
    num = labels[evt.ydata,evt.xdata]
    if num!=0:
        cur = measurements.center_of_mass(seg,labels,num)
        idx = npy.where((center[:,0]==cur[0])&(center[:,1]==cur[1]))
        check[idx]=1
        get_all(cur,check,alpha=0.2,eps=10,k=10)
        fig.canvas.draw()


if __name__ == '__main__':
    import scipy.signal as ss

    #get_all(checked,alpha=0.9,eps=45)
    #imgo=get_image(5222)
    #to_hdf5(imgo,'5222',os.getcwd()+'/tmp')
    imgo=get_from_hdf5('5222',os.getcwd()+'/tmp',idx=(0,10000,2000,20000))
    if len(imgo.shape)==3:
        img=npy.sum(imgo,axis=2)/3
    else:
        img=imgo
    #img = img[:,0:5000]
    img=img.astype(npy.uint8)
    mask = get_mask(img,selemMask=ellipse((100,20)),low_res=50)

    #mask=npy.ones_like(img)

    #labels,Seg=get_label(img,seg=True,min_size_th=500,max_size_th=4000,mask=mask,radius=70,p0=0.1,iter=4)
    labels,Seg=get_label(img,seg=True,min_size_th=400,max_size_th=float('Inf'),radius=70,p0=0.5,iter=10,selemSeg=ellipse((50,70)))
    #labels2,Seg=get_label(img,seg=True,min_size_th=500,max_size_th=4000,mask=mask,radius=70,p0=0.9,iter=4)

    center,tree=get_tree_center(mask*Seg,mask*labels)
    checked=npy.zeros(center.shape[0])



    fig = plt.figure()
    ax=fig.add_subplot(111)
    fig.canvas.mpl_connect('button_press_event', lambda evt,lab=labels,seg=Seg,fig=fig,check=checked,center=center:onclick(evt,seg,labels,check,center,fig))
    ax.imshow(imgo)
    ax.imshow(labels,alpha=0.3)
    plt.plot(center[:,1],center[:,0],'b.')
    plt.show()

    '''

    fig = plt.figure()
    ax=fig.add_subplot(111)
    ax.imshow(imgo)
    ax.imshow(labels,alpha=0.3)
    orientation = list()
    matrix = npy.zeros((center.shape[0],imgo.shape[1]))
    all_chain = list()
    for k in range(center.shape[0]):
        i=-k
        if checked[i]==0:
            checked[i]=1
            all_chain.append(get_all(center[i,:],checked,alpha=0.2,eps=10,k=10,ori_list=orientation))
            plt.plot(center[i,1],center[i,0],'b.')
    print all_chain
    h, n =npy.histogram(npy.array(orientation).flatten(),bins=range(360))
    orientation = ss.medfilt(npy.array(orientation),kernel_size=3)
    m = npy.median(npy.array(orientation))

    x = npy.arange(0,imgo.shape[0])

    y = x*math.tan(math.radians(m))+imgo.shape[0]/4
    plt.xlim((0,imgo.shape[1]))

    plt.plot(y,x,'r')
    plt.show()
    '''

