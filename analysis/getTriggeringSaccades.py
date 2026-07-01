import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

#assumed standard naming conventions used in my experiments
def getRawFilePrefix(infodict,subID,session=1):
    rootdir=infodict['rootdir']
    experiment=infodict['experiment']
    subjectNamePrefix=infodict['subjectNamePrefix']
    rawfileprefix=rootdir+f"/data/raw/{subjectNamePrefix}%02d_s{session}_{experiment}/task_{experiment}_{subjectNamePrefix}%02d_s{session}"%(subID,subID)
    return rawfileprefix

#get saccades that have onsets within -20 to 0 ms of online saccade detection
def getTriggeringSaccades(saccadefname, #file containing all detected saccades
                          rawfname,     #file containing eyetracker data
                          trialSeqLog,  #log file         
                          maxAmp=2,     #maximum amplitude of saccades
                          maxWindowInMs=20 #maximum window of acceptance                            
                        ):
    #load log file and select valid trials

    df=pd.read_csv(trialSeqLog)
    latency=df['latency'].values
    blankDuration=df['blankDurationInFrameCount'].values
    result=df['result'].values
    trialID=df['trialIndex']
    selmask=np.logical_and.reduce((np.logical_not(np.isnan(blankDuration)),
                                   np.logical_or(result=='incorrect',result=='correct')))
    latency=latency[selmask]
    blankDuration=blankDuration[selmask]
    result=result[selmask]
    trialID=trialID[selmask].values
    df=df[selmask]

    #load eyetracker file to get the event time stamps
    raw=mne.io.read_raw(rawfname,preload=False,verbose=False)
    events,event_dict=mne.events_from_annotations(raw,verbose=False)
    
    endPracticeEvent=events[event_dict[np.str_('EndPractice')]==events[:,-1]][0,0]  #get end of practise time
    events=events[event_dict[np.str_('blankDurationStart')]==events[:,-1]]  #select start of blank duration
    events=events[events[:,0]>endPracticeEvent]                             #select trials after end of practise
    onlineDetectionTimeStamp=events[:,0]/1e3-2/240.0-latency/1e3            #get time (in seconds) when the microsaccade was detected in real time.

    #load dataframe containing all saccades
    dfSaccades=pd.read_csv(saccadefname)
    dfSaccades=dfSaccades[dfSaccades['amplitude']<=maxAmp]
    dfSaccades=dfSaccades.sort_values(by='startTime')  
    saccadePeak=dfSaccades['peakVelocityTime'].values    

    saccadeIndx=np.zeros(len(trialID),dtype=int)-1

    #get onset of true microsaccades
    for i in range(0,len(onlineDetectionTimeStamp)):
        t0=onlineDetectionTimeStamp[i]        
        selmask=np.logical_and(t0-saccadePeak>0,t0-saccadePeak<maxWindowInMs/1e3)
        if(np.sum(selmask)>0):
            saccadeIndx[i]=np.where(selmask)[0][0]
    
    #select only trials where a corresponding saccade was also detected in offline analysis
    validTrialMask=saccadeIndx>0

    #merge dataframes and add relevant info
    dfSaccades_selected=dfSaccades.iloc[saccadeIndx[validTrialMask]]
    dfSaccades_selected.insert(loc=0, column='trialIndex',value=trialID[validTrialMask])

    dfSaccades_selected=dfSaccades_selected.merge(df[validTrialMask],on='trialIndex')
    dfSaccades_selected.insert(loc=1, column='targetOnsetTime',value=events[validTrialMask,0]/1e3-2/240.0)   
    return dfSaccades_selected

infodict={
    'rootdir':'./',
    'experiment':'CLP',
    'subjectNamePrefix':'Sub_',
    'outdirname':'derived',
    'figuredirectory':'./figures/',
    'subjects':[1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,22,23,24]
}


#loop over all subjects and save dataframe to csv
for iSub in range(len(infodict['subjects'])):
    subID=infodict['subjects'][iSub]
    saccadefname=f"{infodict['rootdir']}/data/{infodict['outdirname']}/{infodict['subjectNamePrefix']}%02d/{infodict['subjectNamePrefix']}%02d_saccades.csv"%(subID,subID)
    rawfname=f"{infodict['rootdir']}/data/{infodict['outdirname']}/{infodict['subjectNamePrefix']}%02d/{infodict['subjectNamePrefix']}%02d_eye_raw.fif"%(subID,subID)
    trialSeqLog=getRawFilePrefix(infodict=infodict,subID=subID)+"_trialSequence.csv"
    
    dfSaccades=getTriggeringSaccades(saccadefname,rawfname,trialSeqLog)
    dfSaccades.to_csv(f"outfiles/triggeringSaccades/{infodict['subjectNamePrefix']}%02d_triggeringSaccades.csv"%(subID))