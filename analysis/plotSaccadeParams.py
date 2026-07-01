import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


#get distribution of microsaccade onset times for each latency condition
def eventLockedMicroSaccadeCount(saccadefname,      #saccade dataframe
                                binTrialInMs=1,     #size of bins
                                tLimInMs=[-500,150] #timerange to cover                
                                ):
    #load relevant parameters from the csv file
    df=pd.read_csv(saccadefname)
    latency=df['latency'].values
    targetOnsetTime=df['targetOnsetTime'].values*1e3 #in milliseconds
    saccadeOnset=df['startTime'].values*1e3 #in milliseconds


    uniqLatency=np.unique(latency)      #get an array containing all latency conditions
    
    #time axis of bin
    taxis=np.arange(tLimInMs[0],tLimInMs[-1],binTrialInMs)
    taxisTrialCentral=(taxis[1:]+taxis[:-1])/2.
    
    #array to store the distribution for each latency condition
    saccadeCounts=np.zeros((len(uniqLatency),len(taxisTrialCentral)))

    for i in range(0,len(uniqLatency)):
        selmask=latency==uniqLatency[i] #select trials of given latency condition
        saccadeCounts[i],t=np.histogram(saccadeOnset[selmask]-targetOnsetTime[selmask],     #get distribution of time differences
                                      bins=taxis)
    return uniqLatency,taxisTrialCentral,saccadeCounts


#loop over all subjects and plot the distribution of saccade onset times.
def plotLatencyDistribution(sub_all,ax):
    for iSub in range(len(sub_all)):    
        saccadefname="outfiles/triggeringSaccades/Sub_%02d_triggeringSaccades.csv"%sub_all[iSub]
        uniqLatency,taxisTrialCentral,saccadeCountsThis=eventLockedMicroSaccadeCount(saccadefname)

        if(iSub==0):    #creating relevant arrays if first subject            
            saccadeCounts=saccadeCountsThis
        else:   #just adding to the array to get the cumulative counts
            saccadeCounts=saccadeCounts+saccadeCountsThis 
    for i in range(0,len(uniqLatency)):        
        ax.bar(taxisTrialCentral,saccadeCounts[i],width=2.0,label='%d ms'%uniqLatency[i],fc='C%d'%(i+1))
        #ax.axvline(-uniqLatency[i],ls='--',c='C%d'%(i+1),zorder=-999)
        #plt.fill_between(taxisTrialCentral,mean-sem,mean+sem,alpha=0.5)
    ax.axvline(0,ls='--',c='gray',zorder=-999)
    ax.legend(ncols=3,framealpha=1.0)
    ax.set_xlabel("Microssacade onset time (relative target onset, in ms)")
    ax.set_ylabel("Number of microsaccades")
    ax.set_xlim((-500,50))
    ax.set_ylim((0,190))
    ax.minorticks_on()
    #ax.grid()

#plotting both the combined figure
def plotCombined(sub_all):
    fig,axs = plt.subplots(1,2,figsize=(10,4))
    
    plotLatencyDistribution(sub_all,axs[0])

    #get all saccade params
    dfSaccadesAll=[]
    for subID in sub_all:
        saccadefname="outfiles/triggeringSaccades/Sub_%02d_triggeringSaccades.csv"%subID
        dfSaccadesAll.append(pd.read_csv(saccadefname))
    dfSaccadesAll=pd.concat(dfSaccadesAll)

    #simple amp vs. peak velocity plot
    axs[1].scatter(dfSaccadesAll['amplitude'],dfSaccadesAll['peakVelocity'],s=1.8)
    axs[1].set_ylim((0,175))
    axs[1].set_xlabel("Saccade Amplitude (deg)")
    axs[1].set_ylabel("Saccade Velocity (deg/s)")
    axs[1].minorticks_on()
    plt.savefig("figures/saccadeParams.png",bbox_inches='tight',dpi=300.0)

#sub_all=[1,2,3,4,5,6,8,9,12,13,14,15,16,17,18,20,22,23,24]
