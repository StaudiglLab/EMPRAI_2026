from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel


def getMedianBlank(subID,
                   minBlock=0 #starting block (all blocks before would be excluded from median computation)
                    ):
    #load relevant columns from csv file
    df=pd.read_csv("outfiles/triggeringSaccades/Sub_%02d_triggeringSaccades.csv"%subID)#pd.read_csv(directory+"/Sub_%02d_s1_CLP/task_CLP_Sub_%02d_s1_trialSequence.csv"%(subID,subID))
    blockID=df['blockId'].values
    latency=df['latency'].values
    blankDuration=df['blankDurationInFrameCount'].values
    result=df['result'].values
    #select blocks
    selmask=blockID>=minBlock
    latency=latency[selmask]
    blankDuration=1e3*blankDuration[selmask]/240.0 #converting from frame samples to ms
    result=result[selmask]
    
    #get median for each latency condition
    uniqLatency=np.unique(latency)
    medianBlankDuration=np.zeros_like(uniqLatency,dtype='float')
    for i in range(0,len(uniqLatency)):
        trialSelmask=latency==uniqLatency[i]
        medianBlankDuration[i]=np.median(blankDuration[trialSelmask])
    return uniqLatency,medianBlankDuration

#loop over all subjects to get the median blank durations in each condition
    
def getAllMedianBlankDurations(sub_all, #list of all subjects
                               minBlock=0, #starting block (all blocks before would be excluded from median computation)
                               nLatency=5   #number of latency conditions
                               ):

    medianBlankDuration=np.zeros((len(sub_all),nLatency))
    for i in range(len(sub_all)):
        uniqLatency,medianBlankDuration[i]=getMedianBlank(sub_all[i],minBlock=minBlock)
    return uniqLatency,medianBlankDuration

#performing anova (this will _not_ work if you don't have the pingouin library installed!)
def performAnova(sub_all,minBlock=0):
    import pingouin as pg
    #getting the blank durations for each subject and condition before running a repeated measure anova

    uniqLatency,medianBlankDuration=getAllMedianBlankDurations(sub_all,minBlock=minBlock)
    df=pd.DataFrame(columns=['sub','latency','medianBlankDuration'])
    for i in range(0,len(sub_all)):
        for j in range(0,len(uniqLatency)):
            df.loc[len(df)]=[sub_all[i],uniqLatency[j],medianBlankDuration[i,j]]

    anova= pg.rm_anova(
    dv='medianBlankDuration',
    within=['latency'],
    subject='sub',
    data=df,
    detailed=True)
    #print and save anova to file
    print(anova)
    anova.to_csv("outfiles/anova_results.csv")


#plot distribution of blank durations

def plotDistribution(sub_all,minBlock=0):
    #getting the blank durations for each subject and condition

    uniqLatency,medianBlankDuration=getAllMedianBlankDurations(sub_all,minBlock=minBlock)

    #doing a t-test for only first and second conditions
    ttest=ttest_rel(medianBlankDuration[:,0],medianBlankDuration[:,1])

    #geting the mean and s.e.m. on the median blank durations
    mean=np.mean(medianBlankDuration,axis=0)
    sem=np.nanstd(medianBlankDuration,axis=0)/np.sqrt(len(sub_all))

    fig,axs=plt.subplots(1,2,figsize=(12,4))

    #sns.boxplot(df,x='latency',y='blankDuration')
    axs[0].text(0.86,0.9,"N=%d"%len(sub_all),transform=axs[0].transAxes)
    
    if(ttest.pvalue<0.05): #print p-value if significant
        axs[0].plot([0,50],[np.max(mean)*1.1,np.max(mean)*1.1],c='black',lw=2)
        axs[0].text(0,np.max(mean)*1.07,"p=%0.5f"%ttest.pvalue)
    #plot mean and s.e.m
    axs[0].plot(uniqLatency,mean,marker='o')
    axs[0].fill_between(uniqLatency,mean-sem,mean+sem,alpha=0.5)

    axs[0].set_xlabel("time since microsaccade detection (ms)")
    axs[0].set_ylabel("median blank duration (ms)")

    #do boxplot in the other panel
    bplot=axs[1].boxplot(medianBlankDuration,patch_artist=True)
    for patch in bplot['boxes']:
        patch.set_facecolor('C0')
    #plot individual points.

    for i in range(0,len(medianBlankDuration)):
        axs[1].plot(np.arange(len(uniqLatency))+1,medianBlankDuration[i],c='gray',marker='o',lw=1,ms=1.5)
        
    axs[1].set_ylabel("median blank duration (ms)")
    axs[1].set_xlabel("time since microsaccade detection (ms)")
    axs[1].set_xticks(np.arange(len(uniqLatency))+1,uniqLatency)
    
    plt.savefig("figures/blankDuration_allBlocks.png",bbox_inches='tight',dpi=300.)

