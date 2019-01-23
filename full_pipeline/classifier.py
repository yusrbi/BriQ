import os
#os.environ['R_HOME'] = './QCR/qcr_env/lib/R'

import urllib
import rpy2
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr, data
from html_page import HtmlPage
from extractor import FeatureExtractor
import array
import pandas as pd
import numpy as np
from rpy2.robjects import pandas2ri
pandas2ri.activate()

caret = importr('caret')
e1071 = importr('e1071')
randomForest = importr('randomForest')
glmnet = importr('glmnet')
kernlab = importr('kernlab')
base = importr('base')
import_ = importr('import')

robjects.r('''
    get_prediction <-function(data.raw){
        data.raw[,c('scale','prec')] <- scale(data.raw[,c('scale','prec')], center = T, scale = T)
        rf_model <- readRDS("RFmodel2_with_sampling.rds")
        pred.RF = predict(rf_model, newdata=data.raw,  type='prob')
        data.raw$prob <- pred.RF$X1
    }''')

#rf_model = robjects.r.readRDS("./QCR/qcr_env/classifier/parRF.rds") # Random Forest classifier with none sampling
rf_model = robjects.r.readRDS("parRF.rds") 
prediction_fn = robjects.globalenv['get_prediction']




def classify(document):
    print("Run classifier for document %s"%document.doc_id)

    data = document.get_mention_pairs()
    data = process_mention_pairs_for_classifier(data)
    if data.empty:
        document.set_classification_results(data)
        return document

    #data_with_predictions = prediction_fn(data)
    # Now get the final results just by the classifier
    r_true = robjects.BoolVector([True])
    #get predictions first
    predictions =robjects.r.predict(rf_model, newdata = data, type='prob' )
    #print(predictions.dtypes)
    #print(predictions.shape)
    # confert the FactorVector to pandas dataframe
    #predictions = convert_factor(predictions)
    # record the predictions
    #for col in predictions:
        #print(col.rclass[0])
    try:
        data['pr'] = np.asarray(predictions[1])
    except:
        print("NO priors were obtained")

    # filter the probabilities
    #final_predictions = data.ix[data.pr  >  0.3]
    #with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
    #        print(final_predictions)

    #results_text = html_page.get_documents_as_text()
    #mention_pairs = extract_mention_pairs(html_content)
    #mention_pairs_processed= process_mention_pairs_for_classifier(mention_pairs)
    #predictions = predict_fn(mention_pairs_processed)

    # run the graph/ILP solver
    #final_predictioins = graph_solver(predictions,
    # return the results
    #print(results_text)
    document.set_classification_results(data)
    return document

def process_mention_pairs_for_classifier(mention_pairs):
#create a data frame withe the following data
#no_scale_diff+diff_max+dif_sum+scale+prec+unit+modApprox+modBound+modExact+modNone+aggr+ltokn+lnps+gtokn+gnps+surfaceform
    data = []
    col_names =['doc_id', 'mXId','mTid','no_scale_diff','diff_max','dif_sum','scale','prec','unit','mod', 'aggr','ltokn','lnps','gtokn', 'gnps','surfaceform','approx_sim']

    flat_mention_pairs = [m for ls in mention_pairs for m in ls]

    for mention_pair in flat_mention_pairs:
        #print(mention_pair)
        item = mention_pair.get_as_list()
        data.append(item)


    data_frame = pd.DataFrame(data = data, columns = col_names)
    print(data_frame)
    data_frame['modapprox']  = [1 if mod == 'approx'  else 0 for mod  in data_frame['mod']]
    data_frame['modbound']  = [1 if mod == 'bound'  else 0 for mod  in data_frame['mod']]
    data_frame['modexact']  = [1 if mod == 'exact'  else 0 for mod  in data_frame['mod']]
    data_frame['modNone']  = [1 if mod == None or  mod == 'None'  else 0 for mod  in data_frame['mod']]


    #print(data_frame.dtypes)
    #print(data_frame.size)
    #print(data_frame.shape)
    #print(data_frame)
    return data_frame
