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
import time

from credentials import *

cred = {'USERNAME':USERNAME,'PASSWORD':PASSWORD,'HOST':HOST,'PORT':PORT}

def get_image(id,level=0):
    with OmeroClient(cred['USERNAME'],cred['PASSWORD'],cred['HOST'],cred['PORT'],group=103) as client:
        image=client.get_image(id)
        info = image.get_info()
        I=image.get_plane(level=level)[0]
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
    f.close()
    return img
def ellipse(a,b):
    xx,yy=npy.meshgrid(range(a),range(b))
    ellarray=((xx-a/2.0)*2.0/a)**2+((yy-b/2.0)*2.0/b)**2
    return ellarray<1
def get_label(img,radius=20,selem=None,seg=False,max_size_th=1000,min_size_th=0,p0=0.7,sigma=None,iter=2):
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
    if selem==None:
        selem = disk(radius)
    if sigma:
        img=filters.gaussian_filter(img,sigma)
    img = rank.enhance_contrast_percentile(img, disk(3), p0=0.5, p1=1)

    Seg = rank.threshold_percentile(img,selem,p0=p0)
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
def get_mask(img,selem=None,low_res=5):
    '''
    Get the mask of the lumens
    :param img: Input image
    :param selem: A structuring element
    :return: the mask for the image
    '''
    if selem==None:
        selem=npy.ones((50,200))
    tmp = misc.imresize(img,size=low_res)
    mask = rank.median(tmp,selem)
    otsu = threshold_otsu(mask)
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
    return npy.abs(math.degrees(npy.arctan2(pt1[0]-pt2[0],pt1[1]-pt2[1])))
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


    return center[candidat[idx],:],candidat[idx]
#imgo=get_image(5102)
#to_hdf5(imgo,'5102',os.getcwd()+'/tmp')
imgo=get_from_hdf5('5106',os.getcwd()+'/tmp')
if len(imgo.shape)==3:
    img=npy.sum(imgo,axis=2)/3
else:
    img=imgo
#img = img[:,0:5000]
img=img.astype(npy.uint8)
mask = get_mask(img,selem=ellipse(100,20),low_res=50)
#mask=npy.ones_like(img)

#labels,Seg=get_label(img,seg=True,min_size_th=500,max_size_th=4000,mask=mask,radius=70,p0=0.1,iter=4)
labels,Seg=get_label(img,seg=True,min_size_th=400,max_size_th=float('Inf'),radius=70,p0=0.5,iter=10,selem=ellipse(50,70))
#labels2,Seg=get_label(img,seg=True,min_size_th=500,max_size_th=4000,mask=mask,radius=70,p0=0.9,iter=4)

center,tree=get_tree_center(mask*Seg,mask*labels)




checked=npy.zeros(center.shape[0])

print 'debut'
def get_all(cur,checked,alpha=0.8,eps=20,k=9):
    tmpcur = cur
    Test=[True,True]
    plt.plot(cur[1],cur[0],'bo')
    orientation=[170,10]
    for j in range(2):
        cur=tmpcur
        while Test[j]:
            try:
                next,idx=get_next(tree,cur,center,orient=orientation[j],eps=eps,k=k)
                if orientation[j]==None:
                    orientation[j]=cal_angle(cur,next)
                else:
                    orientation[j]=(1-alpha)*orientation[j]+alpha*cal_angle(cur,next)
                    checked[idx]=1
                plt.plot([cur[1],next[1]],[cur[0],next[0]],'g-')
                plt.plot(next[1],next[0],'go')
                cur=next
                print orientation[j]
            except:
                Test[j]=False
def onclick(evt,seg,labels,check,center,fig):
    num = labels[evt.ydata,evt.xdata]
    if num!=0:
        cur = measurements.center_of_mass(seg,labels,num)
        idx = npy.where((center[:,0]==cur[0])&(center[:,1]==cur[1]))
        check[idx]=1
        get_all(cur,checked,alpha=0.2,eps=10,k=10)
        fig.canvas.draw()


#get_all(checked,alpha=0.9,eps=45)

fig = plt.figure()
ax=fig.add_subplot(111)
fig.canvas.mpl_connect('button_press_event', lambda evt,lab=labels,seg=Seg,fig=fig,check=checked,center=center:onclick(evt,seg,labels,check,center,fig))
ax.imshow(imgo)
ax.imshow(labels,alpha=0.3)
plt.plot(center[:,1],center[:,0],'b.')
plt.show()
