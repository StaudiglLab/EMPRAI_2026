import pandas as pd
import numpy as np

#counts the number of valid trials (i.e. those with a valid saccade and response) in each latency condition
def getTrialCounts(subID):
    dfSaccades=pd.read_csv("outfiles/triggeringSaccades/Sub_%02d_triggeringSaccades.csv"%subID)
    uniqLatency=np.unique(dfSaccades['latency'])
    counts=np.zeros(len(uniqLatency),dtype=int)
    for i in range(0,len(uniqLatency)):
        counts[i]=np.sum(dfSaccades['latency']==uniqLatency[i])
    return uniqLatency,counts

#loop over all subjects and get a csv file that summarizes the trial counts
def getSummaryTable(minTrials=25    #minimum number of trials per condition
                    ):
    sub_all=[1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,22,23,24]
    counts_all=np.zeros((len(sub_all),5),dtype=int)
    for i in range(len(sub_all)):
        uniqLatency,counts_all[i]=getTrialCounts(subID=sub_all[i])

    includeSubject=np.mean(counts_all>=minTrials,axis=1)==1.0
    dfCounts=pd.DataFrame(columns=['subID','nTrials_0','nTrials_50','nTrials_100','nTrials_200','nTrials_400','includeSubject'],data=np.column_stack((sub_all,counts_all,includeSubject)))
    dfCounts.to_csv("outfiles/trialCountSummary.csv",index=False)

getSummaryTable()