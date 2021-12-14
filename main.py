import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import OrdinalEncoder
from sklearn.linear_model import LinearRegression
import seaborn as sns
import numpy as np
from random import seed
from random import randint
from random import gauss
from random import uniform
from random import shuffle
import matplotlib.pyplot as plt
sns.set_style('darkgrid')
get_ipython().run_line_magic('matplotlib', 'inline')
# %matplotlib qt5
from sklearn.model_selection import train_test_split
import hashlib
import random
# random.seed(6)
from IPython.display import Image
from causalml.inference.tree import UpliftTreeClassifier, UpliftRandomForestClassifier
from causalml.inference.tree import uplift_tree_string, uplift_tree_plot
from causalml.metrics import plot_gain
from causalml.metrics import get_qini
from causalml.metrics import plot_qini
from causalml.metrics import qini_score
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold
from itertools import combinations 
import os
import sys
random.seed(7)
from sklift.metrics import (
    uplift_at_k, uplift_auc_score, qini_auc_score, weighted_average_uplift
)
from sklift.models import TwoModels
from sklearn.linear_model import LogisticRegression
from sklift.models import ClassTransformation
from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
import sys
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
import scipy.stats as st
from scipy.linalg import eig, eigh, svd
from scipy.spatial.distance import pdist, squareform
import adapt
from adapt.instance_based import KLIEP
from sklearn.tree import DecisionTreeRegressor
from sklearn.decomposition import PCA
from sklearn.svm import LinearSVC, SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV, \
    RidgeClassifier, RidgeClassifierCV
from sklearn.model_selection import cross_val_predict
from sklearn.calibration import CalibratedClassifierCV
from os.path import basename
from scipy.spatial.distance import cdist
from cvxopt import matrix, solvers
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
import numpy as np
import scipy.stats as st
from scipy.sparse.linalg import eigs
from scipy.spatial.distance import cdist
import sklearn as sk
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV, \
    RidgeClassifier, RidgeClassifierCV
from sklearn.model_selection import cross_val_predict
from os.path import basename
import ot
from sklearn.preprocessing import MinMaxScaler
from causalml.inference.meta.base import BaseLearner
from causalml.inference.meta.utils import (check_treatment_vector,
    get_xgboost_objective_metric, convert_pd_to_np)
from causalml.inference.meta.explainer import Explainer
from causalml.propensity import compute_propensity_score, ElasticNetPropensityModel

from causalml.inference.meta import LRSRegressor
from causalml.inference.meta import XGBTRegressor, MLPTRegressor
from causalml.inference.meta import BaseXRegressor, BaseRRegressor, BaseSRegressor, BaseTRegressor, BaseXLearner, BaseDRLearner
from causalml.match import NearestNeighborMatch, MatchOptimizer, create_table_one
from causalml.propensity import ElasticNetPropensityModel
from causalml.dataset import *
from causalml.metrics import *
from xgboost import XGBRegressor

import ratioOfGaussians


def saveList(filename,my_list):
    with open(filename, 'w') as filehandle:
        for listitem in my_list:
            filehandle.write('%s\n' % listitem)
def readListFromTxt(lst, filepath):
    # open file and read the content in a list
    with open(filepath, 'r') as filehandle:
        for line in filehandle:
            # remove linebreak which is the last character of the string
            currentPlace = line[:-1]

            # add item to the list
            lst.append(currentPlace)
    return lst

def InverseTrtProb(trtData,CtrlData,features,model="LR"):
    frames = [trtData, CtrlData]
    df_LR = pd.concat(frames)
    
    df_LR.drop("visit",inplace=True,axis=1)
    
    if model=="LR":
        clf = LogisticRegression()
    elif model=="xg":
        clf = XGBClassifier(n_estimators=25)
    clf.fit(X=df_LR[features],y=df_LR['segment'])
    trtProbPred=clf.predict_proba(trtData[features])
        
    return (trtProbPred[:,0]/trtProbPred[:,1])
    
def performReweighting(DA, x,z,attributes):
    if DA=='rg':
        weights=ratioOfGaussians.iwe_ratio_gaussians(x[features], z[features])
    elif DA=="wt1":
        weights=InverseTrtProb(x,z,attributes)
    elif DA=="wt2":
        weights=InverseTrtProb(x,z,attributes,"xg")
        print("Weights LENGHT")
        print(len(weights))
    else:
        print("IMPORTANCE WEIGHTING ALGORITHM NOT RECOGNIZED")
    weights_control=[1]*z.shape[0]
    
    return weights,weights_control
    
    
def learnUpliftAndPlotAndGetQini(df_b_train,df_b_test,features, algorithm = 'KL',SavePredictions=False, NoBias=False):
    global domain_ada
    global IndividualsWithWeights
    global EnterInIndividualsWeights
    global path
    DA = domain_ada
        
    df_tr = df_b_train.copy()
    df_te = df_b_test.copy()
        
    df_tr['segment']=df_tr['segment'].astype(int)
    df_te['segment']=df_te['segment'].astype(int)
        
    X=df_tr[df_tr['segment']==1]
    Z=df_tr[df_tr['segment']==0]
    
    
    if algorithm == "KL" or algorithm =="CTS" or algorithm =="Chi" or algorithm=="ED":
        uplift_model = UpliftRandomForestClassifier(evaluationFunction = algorithm, control_name='0',max_features=4,n_estimators = 30,max_depth=10)
        uplift_model.fit(df_tr[features].values,treatment=df_tr['segment'].astype(str),y=df_tr['visit'].values)
        pred=uplift_model.predict(df_te[features].values)
    elif algorithm=="SLearner_LR" or algorithm=="SLearner_Xgboost" or algorithm =="TLearner" or algorithm=="RLearner" or algorithm =="XLearner_Xgboost" or algorithm=="XLearner_LR" or algorithm=="DR_LR" or algorithm =="DR_Xgboost"  :
        fitted = False
        if algorithm=="SLearner_LR":
            #To use the Logistic regression function, the python file "slearner" in causalml library should be modified. All functions predict() should become predict_proba()[:0]
            learner = BaseSRegressor(learner=LinearRegression())
            if DA=='rg' or DA=="wt1" or DA=="wt2":
                weights,weights_control=performReweighting(DA,X, Z,features)
                w = np.concatenate([weights, weights_control])
                learner.setWeights(w)
                frames = [X, Z]
                df_tr = pd.concat(frames)
                df_tr.reset_index(inplace=True)
            learner.fit(X=df_tr[features].values, treatment=df_tr['segment'].values, y=df_tr['visit'].values)
            fitted=True
            pred=learner.predict(df_te[features].values)
        elif algorithm=="SLearner_Xgboost":
            learner = BaseSRegressor(learner=XGBRegressor())
            if DA=='rg' or DA=="wt1" or DA=="wt2":
                weights,weights_control=performReweighting(DA,X, Z,features)
                if SavePredictions==True and NoBias==True and EnterInIndividualsWeights==False:
                    ww = list(weights)+list(weights_control)
                    IndividualsWithWeights=df_tr.copy()
                    IndividualsWithWeights['Weights']=pd.Series(ww)
                    EnterInIndividualsWeights=True
                    IndividualsWithWeights.to_csv(path+"IndividualsWithWeights.csv")
                w = np.concatenate([weights, weights_control])
                learner.setWeights(w)
                frames = [X, Z]
                df_tr = pd.concat(frames)
                df_tr.reset_index(inplace=True)
            learner.fit(X=df_tr[features].values, treatment=df_tr['segment'].values, y=df_tr['visit'].values)
            fitted=True
            pred=learner.predict(df_te[features].values)
        elif algorithm == "XLearner_Xgboost":
            learner = BaseXRegressor(learner=XGBRegressor())
            learner.fit(X=df_tr[features].values, treatment=df_tr['segment'].values, y=df_tr['visit'].values)
            fitted=True
            pred=learner.predict(df_te[features].values)
        elif algorithm == "XLearner_LR":
            #To use the Logistic regression function, the python file "slearner" in causalml library should be modified. All functions predict() should become predict_proba()[:0]
            learner = BaseXRegressor(learner=LinearRegression())
            learner.fit(X=df_tr[features].values, treatment=df_tr['segment'].values, y=df_tr['visit'].values)
            fitted=True
            pred=learner.predict(df_te[features].values)
        elif algorithm=="TLearner":
            learner = BaseTRegressor(learner=XGBRegressor())
        elif algorithm=="RLearner":
            learner = BaseRRegressor(learner=XGBRegressor())
        elif algorithm=="DR_Xgboost":
            learner=BaseDRLearner(learner=XGBRegressor())
        elif algorithm=="DR_LR":
            #To use the Logistic regression function, the python file "slearner" in causalml library should be modified. All functions predict() should become predict_proba()[:0]
            learner=BaseDRLearner(learner=LinearRegression())

        if fitted==False:
            learner.fit(X=df_tr[features].values, treatment=df_tr['segment'].values, y=df_tr['visit'].values)
            pred=learner.predict(df_te[features].values)
    elif algorithm == "2MLR" or algorithm == "2M_Xgboost":
        if algorithm == "2MLR":
            es_trmnt = LogisticRegression()
            es_ctrl = LogisticRegression()
        elif algorithm == "2M_Xgboost":
            es_trmnt = XGBClassifier(n_estimators=25)
            es_ctrl = XGBClassifier(n_estimators=25)
        else:
            print("ERROR IN ALGORITHM CHOICE")
            
        tm = TwoModels(
        estimator_trmnt = es_trmnt, 
        estimator_ctrl = es_ctrl, 
        method='vanilla'
        )
        
        if DA=='rg' or DA=="wt1" or DA=="wt2":
            weights,weights_control=performReweighting(DA,X, Z,features)
            
            frames = [X, Z]
            df_tr = pd.concat(frames)
            df_tr.reset_index(inplace=True)
            
            #To Save the predicted weights
            if SavePredictions==True and NoBias==True and EnterInIndividualsWeights==False:
#                 testData_upliftPredictions = pd.concat([df_tr,pd.Series(weights)],axis=1)
                ww = list(weights)+list(weights_control)
#                 weights = ww
                IndividualsWithWeights=df_tr.copy()
                IndividualsWithWeights['Weights']=pd.Series(ww)
                EnterInIndividualsWeights=True
                IndividualsWithWeights.to_csv(path+"IndividualsWithWeights.csv")
            
            tm = tm.fit(df_tr[features], df_tr['visit'], df_tr['segment'],estimator_trmnt_fit_params={'sample_weight':weights},estimator_ctrl_fit_params={'sample_weight':weights_control})
            pred = tm.predict(df_te[features])
        else:
            tm = tm.fit(df_tr[features], df_tr['visit'], df_tr['segment'])
            pred = tm.predict(df_te[features])
    elif algorithm == "CT_Xgboost" or algorithm == "ClassTransformation" :
        if algorithm =="CT_Xgboost":
            estimator = XGBClassifier(n_estimators=25)
        elif algorithm == "ClassTransformation":
            estimator = LogisticRegression()
        
        ct = ClassTransformation(estimator=estimator)
        
        if DA=='rg' or DA=="wt1" or DA=="wt2":
            weights,weights_control=performReweighting(DA,X, Z,features)
            
            frames = [X, Z]
            df_tr = pd.concat(frames)
            
             
            w = np.concatenate([weights, weights_control])
#             w =  weights + weights_control
#             weights = list(w)
            weights = w.copy()
            
            df_tr.reset_index(inplace=True)
            
            #To Save the predicted weights
            if SavePredictions==True and NoBias==True and EnterInIndividualsWeights==False:
#                 testData_upliftPredictions = pd.concat([df_tr,pd.Series(weights)],axis=1)
                IndividualsWithWeights=df_tr.copy()
                IndividualsWithWeights['Weights']=pd.Series(weights)
                EnterInIndividualsWeights=True
                IndividualsWithWeights.to_csv(path+"IndividualsWithWeights.csv")

            ct = ct.fit(df_tr[features], df_tr['visit'], df_tr['segment'],estimator_fit_params={'sample_weight':weights})
            pred = ct.predict(df_te[features])
        else:
            ct = ct.fit(df_tr[features], df_tr['visit'], df_tr['segment'])
            pred = ct.predict(df_te[features])
    else: 
        print("ERROOR IN MODEL CHOICE")
    result = pd.DataFrame(pred,columns=["1"])
    
    df_te.reset_index(inplace=True)
    trt=df_te["segment"]
    trt=trt.astype(int)
    df_te['visit']=df_te['visit'].astype(int)
    sortedResultByPercentage = pd.concat([result['1'],df_te['visit'],trt],axis=1)
    sortedResultByPercentage = sortedResultByPercentage.sort_values(by='1',ascending=False)

    tm_uplift_auc = qini_auc_score(y_true=sortedResultByPercentage['visit'], uplift=sortedResultByPercentage['1'], treatment=sortedResultByPercentage['segment'])
    tm_upliftAt10 = uplift_at_k(y_true=sortedResultByPercentage['visit'], uplift=sortedResultByPercentage['1'], treatment=sortedResultByPercentage['segment'], strategy="overall", k=0.1)
    tm_auuc = uplift_auc_score(y_true=sortedResultByPercentage['visit'], uplift=sortedResultByPercentage['1'], treatment=sortedResultByPercentage['segment'])
    
    return tm_uplift_auc,tm_upliftAt10,tm_auuc
'''
They will be put in the order of (according to the percentage of Group 1):
T1:50 T2:50 Index:0
T1:55 T2:50 Index:1
T1:60 T2:50 Index:2
T1:65 T2:50 Index:3
T1:70 T2:50 Index:4
'''
def createBiasedDfsHillstromWthNRBias(df_train):
    df_tr=df_train.copy()
    df_t1_unbalanced=df_tr[df_tr['segment']=='1']
    df_t0_unbalanced=df_tr[df_tr['segment']=='0']

    listOfBiasedDFs = []
    Group1Proba = 0.5

    constantSizeT1 = df_t1_unbalanced['Group'].value_counts()[1]/1.05
    constantSizeT0 = df_t0_unbalanced['Group'].value_counts()[1] #the least frequent item
    
    varProbs = {'1': 0.5, '2': 0.5}
    df_t0=pd.concat([df_t0_unbalanced[df_t0_unbalanced["Group"] == k].sample(int(v * constantSizeT0), replace=False) for k, v in varProbs.items()])
    
    for i in range(50,105,5):
        proba = i/100
        df_t1_unbalanced=df_tr[df_tr['segment']=='1'].copy()
       
        varProbs = {'1': proba, '2': 1-proba}
        df_t1=pd.concat([df_t1_unbalanced[df_t1_unbalanced["Group"] == k].sample(int(v * constantSizeT1), replace=False) for k, v in varProbs.items()])
        
        frames = [df_t0.copy(),df_t1.copy()]
        df_b=pd.concat(frames)
        df_b = df_b.sample(frac=1).reset_index(drop=True)

        listOfBiasedDFs.append(df_b.copy())
    
    return listOfBiasedDFs

def choosingBias(df_to_Bias,Variables,E2_values=None):
    global prime
    dfBiasChosen=df_to_Bias.copy()
    
    dfBiasChosen['VarBias']=""
    for var in Variables:
        dfBiasChosen['VarBias']=dfBiasChosen['VarBias']+var+dfBiasChosen[var].astype(str)
    dfBiasChosen['VarBias']=dfBiasChosen['VarBias'].str.encode("utf-8")
    
    if E2_values==None:
        s = dfBiasChosen[Variables[0]].value_counts().index.to_list()
        if prime=="prime":
            random.seed(99)
        s = random.sample(s,len(s))
        s = s[:len(s)//2]
    else:
        s=E2_values
    dfBiasChosen['Group']=np.where(dfBiasChosen[Variables[0]].isin(s),'2','1')
    #remove unnecessary columns
    dfBiasChosen.drop(['VarBias'],axis=1,inplace = True)
    dfBiasChosen['stratified']="visit"+dfBiasChosen['visit'].astype(str)+"treatment"+dfBiasChosen['segment'].astype(str)
    
    DetailedOutputExcelDataframe.loc["UpliftMoyenE1","".join(Variables)]=dfBiasChosen[(dfBiasChosen['Group']=='1')&(dfBiasChosen['segment']=='1')]['visit'].mean()-dfBiasChosen[(dfBiasChosen['Group']=='1')&(dfBiasChosen['segment']=='0')]['visit'].mean()
    DetailedOutputExcelDataframe.loc["UpliftMoyenE2","".join(Variables)]=dfBiasChosen[(dfBiasChosen['Group']=='2')&(dfBiasChosen['segment']=='1')]['visit'].mean()-dfBiasChosen[(dfBiasChosen['Group']=='2')&(dfBiasChosen['segment']=='0')]['visit'].mean()
    
    return dfBiasChosen

def stratifiedCVAndQiniEval(df_Biased,X,VariablesToBias,algorithm="KL",nfolds = 10,Bias="X"):
    dfBiasChosen = df_Biased.copy()
    features = X.copy()
    skf = StratifiedKFold(n_splits=nfolds)

    s = skf.split(dfBiasChosen,dfBiasChosen['stratified'])
    ListOfListsOfBiasedDfs=[]
    ListOfQinisCTS = []
    ListOfUpliftsAt10=[]
    ListOfAuuc=[]
    k=0
    print("Spitting for stratified kfold cross validation ",nfolds)
    BIAS=0
    for train_index, test_index in s:
        print("--------------------------------")
        print("\nAnother Fold")
        df_train, df_test = dfBiasChosen.iloc[train_index], dfBiasChosen.iloc[test_index]
        if BIAS==0:
            df_train.to_csv("df_trainBias0.csv")
            BIAS=BIAS+1
        l=[]
        if Bias=="X":
            l = createBiasedDfsHillstromWthNRBias(df_train)
        else :
            print("ERROR IN BIAS CHOICE")
        ListOfListsOfBiasedDfs.append(l)
        qinisCTS=[]
        uplifstAt10=[]
        auucList=[]
        
        DetailedOutputExcelDataframe.loc["test"+str(k)+"Size","".join(VariablesToBias)]=df_test.shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"E1Size","".join(VariablesToBias)]=df_test[df_test['Group']=="1"].shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"CRSize","".join(VariablesToBias)]=df_test[(df_test['segment']=="0")&(df_test['visit']==1)].shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"CNRSize","".join(VariablesToBias)]=df_test[(df_test['segment']=="0")&(df_test['visit']==0)].shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"TRSize","".join(VariablesToBias)]=df_test[(df_test['segment']=="1")&(df_test['visit']==1)].shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"TNRSize","".join(VariablesToBias)]=df_test[(df_test['segment']=="1")&(df_test['visit']==0)].shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"Y1Size","".join(VariablesToBias)]=df_test[df_test['visit']==1].shape[0]
        DetailedOutputExcelDataframe.loc["test"+str(k)+"T1Size","".join(VariablesToBias)]=df_test[df_test['segment']=="1"].shape[0]
        
        for i in range(len(l)):
            SavePredictions=False
            NoBias=False
            if i==5:
                SavePredictions=True
                NoBias = True
            elif i==(len(l)-1):
                SavePredictions=True
            qiniCTS,upAt10,auuc=learnUpliftAndPlotAndGetQini(l[i].drop(['Group','stratified'],axis = 1,inplace=False),df_test.drop(['Group','stratified'],axis = 1),features,algorithm = algorithm,SavePredictions=SavePredictions, NoBias=NoBias)
            qinisCTS.append(qiniCTS)
            uplifstAt10.append(upAt10)
            auucList.append(auuc)
            
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"Size","".join(VariablesToBias)]=l[i].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"Y1Size","".join(VariablesToBias)]=l[i][l[i]['visit']==1].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"T1Size","".join(VariablesToBias)]=l[i][l[i]['segment']=="1"].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"E1Size","".join(VariablesToBias)]=l[i][l[i]['Group']=="1"].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"T1E1Size","".join(VariablesToBias)]=l[i][(l[i]['Group']=="1")&(l[i]['segment']=="1")].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"T0E1Size","".join(VariablesToBias)]=l[i][(l[i]['Group']=="1")&(l[i]['segment']=="0")].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"CRSize","".join(VariablesToBias)]=l[i][(l[i]['segment']=="0")&(l[i]['visit']==1)].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"CNRSize","".join(VariablesToBias)]=l[i][(l[i]['segment']=="0")&(l[i]['visit']==0)].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"TRSize","".join(VariablesToBias)]=l[i][(l[i]['segment']=="1")&(l[i]['visit']==1)].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"TRSize in E1","".join(VariablesToBias)]=l[i][(l[i]['segment']=="1")&(l[i]['visit']==1)&(l[i]['Group']=="1")].shape[0]
            DetailedOutputExcelDataframe.loc["train"+str(k)+"Bias"+str(i)+"TNRSize","".join(VariablesToBias)]=l[i][(l[i]['segment']=="1")&(l[i]['visit']==0)].shape[0]
            #===========================================================================
            DetailedOutputExcelDataframe.loc["test"+str(k)+"Model"+str(i)+"QINI","".join(VariablesToBias)]=qiniCTS
            
        ListOfQinisCTS.append(qinisCTS)
        ListOfUpliftsAt10.append(uplifstAt10)
        ListOfAuuc.append(auucList)
        k+=1
    return ListOfQinisCTS,ListOfUpliftsAt10,ListOfAuuc

def PlotVariationsOfQini(ListOfQinisCTS,plotFig=False,saveFig=False,evaluationMetric = "qini",path=None,saveVariance=False):
    qinisPlotCTS = []
    NiveauLists = []
    variances = []
    
    for i in range(0,len(ListOfQinisCTS[0])):
        q = 0
        NiveauList = []
        for j in range(0,len(ListOfQinisCTS)):
            NiveauList.append(ListOfQinisCTS[j][i])
            q+=ListOfQinisCTS[j][i]
        qinisPlotCTS.append(q/len(ListOfQinisCTS))
        variances.append(np.std(NiveauList))
        NiveauLists.append(NiveauList)
    
    if plotFig == True:
        labels=[]
        Group1Proba = 50
        Group1Proba_t2 = 50
        for i in range(0,len(qinisPlotCTS)):
            labels.append("T1 "+str(Group1Proba)+"%")
            Group1Proba+=5

        plt.xticks(rotation = 'vertical')
        plt.errorbar(labels,qinisPlotCTS,yerr=variances)
        fig1 = plt.gcf()
        
        global BiasGenre
        global AlgorithmName
        global dataPath
        
        saveList(path+evaluationMetric+dataPath+AlgorithmName+"Bias"+BiasGenre+".txt",qinisPlotCTS)
        
        plt.show() 
        
        if saveFig == True:
            fig1.savefig(path+"Final"+evaluationMetric+"vsBiasErrorBars"+AlgorithmName+"_DA"+domain_ada+".png",bbox_inches = 'tight')
    if saveVariance==True:
        saveList(path+evaluationMetric+"variance"+dataPath+AlgorithmName+"Bias"+BiasGenre+".txt",variances)
    return qinisPlotCTS

def startProcess(data,B,Algorithm,ListOfCombinationOfVars,datasetName,X):
    global var
    global prime
    path = "./"+dataPath+"/"+dataPath+"_"+var+"_"+prime+"_"+AlgorithmName+"_Bias"+BiasGenre+"_DA"+domain_ada+"/"
    if not os.path.exists(path):
        os.mkdir(path)
        print("Directory " , path ,  " Created ")
    else:    
        print("Directory " , path ,  " already exists")
    old_stdout = sys.stdout
    log_file = open(path+"Logs_"+datasetName+"Algo"+Algorithm+"_Bias"+B+"_DA"+domain_ada+"_.log","w")
    sys.stdout = log_file
    features = X
    print("ListOfCombinationOfVars is ",ListOfCombinationOfVars)
    ListsOfListsQinis = []
    ListOfListsUpliftAt10=[]
    ListOfListsAuuc=[]
    for VariablesToBias in ListOfCombinationOfVars:
        saveVariance=True
        if len(ListOfCombinationOfVars)>1:
            print(ListOfCombinationOfVars)
            print("Length of list of combinations of vars is bigger than 1")
            saveVariance=False
        else:
            print("length of list of combinations of vars is NOT bigger than 1")
        df_iteration = data.copy()
                
        E2_group=None
                
        df_iteration=choosingBias(df_iteration,VariablesToBias,E2_values=E2_group)
       
        q,up10,au = stratifiedCVAndQiniEval(df_iteration, features,VariablesToBias,Algorithm,Bias=B)
        
        qinis = PlotVariationsOfQini(q,path=path,saveVariance=saveVariance)
        uplifts =PlotVariationsOfQini(up10,evaluationMetric ="upliftAt10",path=path,saveVariance=saveVariance)
        auuc =PlotVariationsOfQini(au,evaluationMetric ="AUUC",path=path,saveVariance=saveVariance)

        permVars = "".join(VariablesToBias)
        rowToAppendToExcelOutput = [permVars]+qinis#+uplifts
        
        global ExcelOutputDataFrame
        global DetailedOutputExcelDataframe
        qSeries = pd.Series(rowToAppendToExcelOutput, index = ExcelOutputDataFrame.columns)
        ExcelOutputDataFrame=ExcelOutputDataFrame.append(qSeries, ignore_index=True)

        ExcelOutputDataFrame.to_csv(path+"ExcelOutputDataFrame"+datasetName+"Algo"+Algorithm+"_Bias"+B+".csv")
        DetailedOutputExcelDataframe.to_csv(path+"DetailedOutputExcelDataframe"+datasetName+"Algo"+Algorithm+"_Bias"+B+".csv")

        ListsOfListsQinis.append(qinis)
        ListOfListsUpliftAt10.append(uplifts)
        ListOfListsAuuc.append(auuc)
    
    
    saveVariance=False
    if len(ListOfCombinationOfVars)>1:
        saveVariance=True
    PlotVariationsOfQini(ListsOfListsQinis,plotFig=True,saveFig=True,path=path,saveVariance=saveVariance)
    PlotVariationsOfQini(ListOfListsUpliftAt10,plotFig=True,saveFig=True,evaluationMetric ="UpliftAt10",path=path,saveVariance=saveVariance)
    PlotVariationsOfQini(ListOfListsAuuc,plotFig=True,saveFig=True,evaluationMetric ="AUUC",path=path,saveVariance=saveVariance)

dataPath = sys.argv[1]#dataset name + will be used in naming the directory
AlgorithmName = sys.argv[2]
BiasGenre = sys.argv[3]
domain_ada = str(sys.argv[4])
var = str(sys.argv[5])
prime = ''
if (len(sys.argv)) == 7 : 
    prime = str(sys.argv[6])

EnterInIndividualsWeights = False

df=pd.read_csv("~/../../data/userstorage/mrafla/Datasets/"+dataPath+".csv")
try:
    df.drop("Unnamed: 0",axis=1,inplace=True)
except:
    print("NO UNnamed column")

df['segment']=df['segment'].astype(str)
column_means = df.mean()
df = df.fillna(column_means)


X = list(df.columns)
X.remove("segment")
X.remove("visit")
res1 = list(combinations(X, 1))
res2 = list(combinations(X, 2)) 
res3 = list(combinations(X, 3))
res4 = list(combinations(X, 4))
res5 = list(combinations(X, 5))
res1=[(x,) for x in X]

if var=="Comb2":
    res = list(combinations(X, 1))
    print(res)
else:
    res = [(var,)]

DATAFRAME_NOBIAS=pd.DataFrame()
DATAFRAME_ALLBIAS=pd.DataFrame()

IndividualsWithWeights = pd.DataFrame()


ExcelOutputCols = ["PermutationOfVariables"]
ExcelOutputCols = ExcelOutputCols + ["QiniBias"+str(i) for i in range(0,110,10)]
ExcelOutputDataFrame = pd.DataFrame(columns = ExcelOutputCols)

DetailedOutputExcelDataframe = pd.DataFrame()
DetailedOutputExcelDataframe = DetailedOutputExcelDataframe.sort_index() #For performance issues when indexing

path = "./"+dataPath+"/"+dataPath+"_"+var+"_"+prime+"_"+AlgorithmName+"_Bias"+BiasGenre+"_DA"+domain_ada+"/"
startProcess(df,BiasGenre,AlgorithmName,res,dataPath,X)