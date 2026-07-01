import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from numba import njit



#a fast numba accerated function to get the start and stop index of clusters of true values in a boolean array
@njit
def getClustersFromMask(mask):
	mask=mask.astype("int")
	if(np.mean(mask)==1.0):
		return np.array([0]),np.array([len(mask)])
	elif(np.mean(mask)==0.0):
		return np.array([0]),np.array([0])
	ediff=(mask[1:]-mask[:-1])#np.ediff1d(mask.astype("int"))
	startIndx=np.arange(len(ediff))[ediff>0]
	stopIndx=np.arange(len(ediff))[ediff<0]
	if(len(startIndx)<len(stopIndx) or (len(stopIndx)>0 and startIndx[0]>stopIndx[0])):
		startIndx=np.append([-1],startIndx)
	if(len(startIndx)>len(stopIndx)):
		stopIndx=np.append(stopIndx,len(ediff))
	return startIndx+1,stopIndx-startIndx



#get start and stop indices from the mask, after applying the minimum duration criteria

def getDetectionsSingleMask(maskDet,minDurationInSamples):
    startIndx,widthIndx=getClustersFromMask(maskDet)    
  
    #exclude detections at the edges of the recording
    noEdgeMask=np.logical_and(startIndx>minDurationInSamples,startIndx+widthIndx<len(maskDet)-minDurationInSamples)
    selmaskWidth=widthIndx>minDurationInSamples
    
    selmaskInit=np.logical_and(selmaskWidth,noEdgeMask)
    startIndx,widthIndx=startIndx[selmaskInit],widthIndx[selmaskInit]
    return startIndx,startIndx+widthIndx

def getIterativeRobustStd(velocity,cutOff=10):
    velocityTrimmed=velocity.copy()
    std=np.sqrt(np.nanmedian(velocity**2,axis=0,keepdims=True)-np.nanmedian(velocity,axis=0,keepdims=True)**2)
    print(std)
    while(np.sum(np.abs(velocityTrimmed)>cutOff*std)>0):
        velocityTrimmed[np.abs(velocityTrimmed)>cutOff*std]=np.nan
        std=np.sqrt(np.nanmedian(velocityTrimmed**2,axis=0,keepdims=True)-np.nanmedian(velocityTrimmed,axis=0,keepdims=True)**2)
    return std
#get mask of timesamples when the velocity exceeds the threshold*std
def getMasks(velocity,threshold):
    #robust estimate of standard deviation
   
    #std=np.sqrt(np.nanmedian(velocity**2,axis=0,keepdims=True)-np.nanmedian(velocity,axis=0,keepdims=True)**2)
    std=getIterativeRobustStd(velocity=velocity)
    print(std)
    #plt.plot(velocity/std)
    #plt.show()
    maskDetPos=velocity>threshold*std
    maskDetNeg=velocity<-threshold*std
    return maskDetPos,maskDetNeg

#velocity thresholding routine.
def detectSaccadesOnVelocity(velocities,minDurationInSamples,thresholdVel):
    #get the mask for when the velocity exceeds the threshold (both postive and negative velocities, e.g. left and right)

    maskDetPos,maskDetNeg=getMasks(velocities,thresholdVel)
    
    #seperately look for saccades on each of the x and y trackes and on each of the positive and negative directions
    startIndxPos_x,stopIndxPos_x=getDetectionsSingleMask(maskDetPos[:,0],minDurationInSamples)
    startIndxPos_y,stopIndxPos_y=getDetectionsSingleMask(maskDetPos[:,1],minDurationInSamples)

    startIndxNeg_x,stopIndxNeg_x=getDetectionsSingleMask(maskDetNeg[:,0],minDurationInSamples)
    startIndxNeg_y,stopIndxNeg_y=getDetectionsSingleMask(maskDetNeg[:,1],minDurationInSamples)

    #combine all the start and stop indices 
    startIndx=np.hstack([startIndxPos_x,startIndxPos_y,startIndxNeg_x,startIndxNeg_y])
    stopIndx=np.hstack([stopIndxPos_x,stopIndxPos_y,stopIndxNeg_x,stopIndxNeg_y])
    
    return startIndx,stopIndx

#merge saccades if overlap (removes duplicates)
#selects the saccade with highest mergeMetric (could be amplitude, for example)
def getMergeMask(startTime,stopTime,mergeMetric):
    mergeMask=np.zeros(len(startTime),dtype=bool)
    for i in range(0,len(startTime)):
        overlapMask=np.logical_or.reduce((np.logical_and(startTime[i]<=startTime,startTime<=stopTime[i]),
                    np.logical_and(startTime[i]<=stopTime,stopTime<=stopTime[i]),
                    np.logical_and(startTime<=startTime[i],stopTime[i]<=stopTime)))
        if(mergeMetric[i]==np.max(mergeMetric[overlapMask])):
            mergeMask[i]=True
    return mergeMask

#high level wrapper that makes use of "getMergeMask"
def mergeSaccades(dfSaccades):    
    #using amplitude as mergemetric
    mergeMask=getMergeMask(dfSaccades['startTime'].values,dfSaccades['stopTime'].values,dfSaccades['amplitude'].values)
    print("Number of unique saccades:%d/%d"%(np.sum(mergeMask),len(mergeMask)))
    dfSaccades=dfSaccades[mergeMask]
    dfSaccades=dfSaccades.sort_values(by='startTime')
    return dfSaccades

#core saccade detector
#basically uses a thresholding alogirthm.
#key parameters are the velocity threshold and the duration of saccades
#Note: saccades are detected independently on both eyes at this point. 
#check for binocular saccades happens later
def detectSaccadesCore(ts,coordinates_left,
                       coordinates_right,
                       velocities_left,
                       velocities_right,
                       whichEye='L',
                       thresholdVel=5,
                       minDurationInSamples=5):
    
    #compute the speeds on both eyes
    speed_left=np.sqrt(velocities_left[:,0]**2+velocities_left[:,1]**2)
    speed_right=np.sqrt(velocities_right[:,0]**2+velocities_right[:,1]**2)
    #select the appropriate speed that is thresholded
    if(whichEye=='L'):
        speed=speed_left
    else:
        speed=speed_right
    
    #apply NaN masks from velocity onto coordinates, just to ensure its all consistent.
    coordinates_left[np.isnan(velocities_left)]=np.nan
    coordinates_right[np.isnan(velocities_right)]=np.nan

    #call the velocity thresholding routine with the appropriate parameters.
    #startIndx, stopIndx defines and onset and offset of the saccades.
    if(whichEye=='L'):
        startIndx,stopIndx=detectSaccadesOnVelocity(velocities_left,minDurationInSamples,thresholdVel)
    else:
        startIndx,stopIndx=detectSaccadesOnVelocity(velocities_right,minDurationInSamples,thresholdVel)

    #get the saccade vectors (del x, del y) for both the left and right eye seperately.
    saccade_vec_left=coordinates_left[stopIndx+1,:]-coordinates_left[startIndx-1,:]
    saccade_vec_right=coordinates_right[stopIndx+1,:]-coordinates_right[startIndx-1,:]

    if(whichEye=='L'):
        amplitude=np.sqrt(saccade_vec_left[:,0]**2+saccade_vec_left[:,1]**2)
    elif(whichEye=='R'):
        amplitude=np.sqrt(saccade_vec_right[:,0]**2+saccade_vec_right[:,1]**2)
        
    peakSpeedIndx=np.zeros_like(startIndx)

    #find the time index where the speed peaks
    for j in range(0,len(startIndx)):
        peakSpeedIndx[j]=startIndx[j]+np.argmax(speed[startIndx[j]:stopIndx[j]])

    #put everything into a dataframe
    dfSaccades=pd.DataFrame()
    dfSaccades['startTime']=ts[startIndx]
    dfSaccades['peakVelocityTime']=ts[peakSpeedIndx]
    dfSaccades['stopTime']=ts[stopIndx]
    dfSaccades['amplitude']=amplitude

    dfSaccades['peakVelocity']=speed[peakSpeedIndx]

    labels=['x','y']
    for i in range(0,len(labels)):
        dfSaccades['saccade_vec_left_%s'%labels[i]]=saccade_vec_left[:,i]
        dfSaccades['peak_velocity_vec_left_%s'%labels[i]]=velocities_left[peakSpeedIndx,i]

        dfSaccades['saccade_vec_right_%s'%labels[i]]=saccade_vec_right[:,i]
        dfSaccades['peak_velocity_vec_right_%s'%labels[i]]=velocities_right[peakSpeedIndx,i]
    
    print("Number of saccades:%d"%len(dfSaccades))

    #merge duplicate saccades
    dfSaccades=mergeSaccades(dfSaccades)
    return dfSaccades

#returns start and stop timesamples for all NaN masks.
def getNaNIntervals(ts,series):
    isNaN=np.sum(np.isnan(series),axis=1)>0
    startIndx,widthIndx=getClustersFromMask(isNaN)
    dfNaNs=pd.DataFrame()
    dfNaNs['startTime']=ts[startIndx]
    dfNaNs['stopTime']=ts[startIndx+widthIndx-1]
    return dfNaNs


#find binocular saccades, i.e. those on both L and R eye
#Selected saccades are either (i) detected on both eyes, (ii) detected on one eye when the other eye data is missing in the eyetracker
#Condition ii sometimes happens for eyelink data when the tracker looses one of the two eyes.
def getBinocular(dfSaccades, #saccade timestamps
                 dfNaNs,      #NaN timestamps
                 NaNBuffer=20/1e3,  #reject saccades that are within NanBuffer interval (in sec)
                 ):
    #read parameters from the dataframe
    startTime,stopTime,whichEye,amplitude,peakVelocity=np.split(dfSaccades[['startTime','stopTime','whichEye','amplitude','peakVelocity']].to_numpy(),5,1)
    startTimeNaN,stopTimeNaN,whichEyeNaN=np.split(dfNaNs[['startTime','stopTime','whichEye']].to_numpy(),3,1)
    
    #essentially expand around the NaNs
    startTimeNaN-=NaNBuffer
    stopTimeNaN+=NaNBuffer

    #masks for various saccades

    isSelected=np.zeros(len(startTime),dtype=bool)
    isBinocular=np.zeros(len(startTime),dtype=bool)
    isMissing=np.zeros(len(startTime),dtype=bool)

    #iterate over all saccades
    for i in range(0,len(startTime)):
        #find overlapping saccades on the L and R eye.
        overlapMaskSaccade=np.logical_and.reduce((np.logical_or.reduce((np.logical_and(startTime[i]<=startTime,startTime<=stopTime[i]),
                    np.logical_and(startTime[i]<=stopTime,stopTime<=stopTime[i]),
                    np.logical_and(startTime<=startTime[i],stopTime[i]<=stopTime))),                   
                    np.sign(peakVelocity)==np.sign(peakVelocity[i]),
                    whichEye!=whichEye[i]))
        #find if the saccade overlaps with a NaNmask on the other eye.
        overlapMaskNaN=np.logical_and.reduce((np.logical_or.reduce((np.logical_and(startTime[i]<=startTimeNaN,startTimeNaN<=stopTime[i]),
                    np.logical_and(startTime[i]<=stopTimeNaN,stopTimeNaN<=stopTime[i]),
                    np.logical_and(startTimeNaN<=startTime[i],stopTime[i]<=stopTimeNaN))),
                                   whichEyeNaN!=whichEye[i]))
        
        #if both eyes have the saccade. "whichEye[i]=='L'" ensures that the saccade is not double counted (i.e. for overlaps, 
        #only left eye saccades are selected)
        if(np.sum(overlapMaskSaccade)>0 and whichEye[i]=='L'):
            isSelected[i]=True
            isBinocular[i]=True
            isMissing[i]=False
        #if there is saccade detected on one eye but the other eye is invalid data (NaNs)   
        elif(np.sum(overlapMaskNaN)>0 and np.sum(overlapMaskSaccade)==0):
            isSelected[i]=True
            isMissing[i]=True   
        
    dfSaccades['otherEyeMissingData']=isMissing
    dfSaccades['isBinocular']=isBinocular
    print("Number of binocular saccades: %d/%d"%(np.sum(isBinocular),len(whichEye)))
    print("Number of final saccades: %d/%d"%(np.sum(isSelected),len(whichEye)))
    #return only the selected saccades
    return dfSaccades[isSelected]



#high-level wrapper function: main function to call to get saccade timestamps
def detectSaccades(rawfname,
                   thresholdVel=6,
                   minDurationInSamples=5):
    dfSaccades=[]
    #getting coordinates and velocities from the preprocessed eyetracked file
    raw=mne.io.read_raw(rawfname).load_data()     
    coordinates_left=raw.get_data(['xpos_left','ypos_left']).T
    coordinates_right=raw.get_data(['xpos_right','ypos_right']).T
    velocities_left=raw.get_data(['xvel_left','yvel_left']).T
    velocities_right=raw.get_data(['xvel_right','yvel_right']).T
    dfSaccades=[]
    dfNaNs=[]
    #running independent saccade detection on each eye
    for whichEye in ['L','R']:
        
        dfSaccades_=detectSaccadesCore(raw.times,
                                    coordinates_left,coordinates_right,
                                    velocities_left,velocities_right,
                                    thresholdVel=thresholdVel,
                                    minDurationInSamples=minDurationInSamples,
                                    whichEye=whichEye)
        #finding NaN intervals
        if(whichEye=='L'):
            dfNaNs_=getNaNIntervals(raw.times,velocities_left)
        else:
            dfNaNs_=getNaNIntervals(raw.times,velocities_right)

    
        dfSaccades_['whichEye']=whichEye
        dfNaNs_['whichEye']=whichEye

        dfSaccades.append(dfSaccades_)
        dfNaNs.append(dfNaNs_)

   
    #sort dataframes by time and return them
    dfSaccades=pd.concat(dfSaccades).sort_values("startTime")
    dfNaNs=pd.concat(dfNaNs).sort_values("startTime")   

     #get only binocular saccades, i.e. those detected on both eyes
    dfSaccades=getBinocular(dfSaccades,dfNaNs)


    return dfSaccades,dfNaNs


def detectAndSaveSaccades(infodict,subID,thresholdVel=6,minDurationInSamples=5):
    outdirname=infodict['rootdir']+f"/data/{infodict['outdirname']}/{infodict['subjectNamePrefix']}%02d"%subID
    rawfname=f"{outdirname}/{infodict['subjectNamePrefix']}%02d_eye_raw.fif"%subID
    dfSaccades,dfNaNs=detectSaccades(rawfname=rawfname,thresholdVel=thresholdVel,minDurationInSamples=minDurationInSamples)
    dfSaccades.to_csv(f"{outdirname}/{infodict['subjectNamePrefix']}%02d_saccades.csv"%subID)
    dfNaNs.to_csv(f"{outdirname}/{infodict['subjectNamePrefix']}%02d_NaNs.csv"%subID)