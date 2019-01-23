import urllib
import rpy2
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr, data
from .mention_pairs_extractor.html_page import HtmlPage
from .mention_pairs_extractor.extractor import FeatureExtractor
import array
import pandas as pd
import numpy as np
from rpy2.robjects import pandas2ri
pandas2ri.activate()
from .mention_pairs_extractor.graph_algorithm import solve_document_rwr

caret = importr('caret')
e1071 = importr('e1071')
randomForest = importr('randomForest')
glmnet = importr('glmnet')
kernlab = importr('kernlab')
base = importr('base')

robjects.r('''
    get_prediction <-function(data.raw){
        data.raw[,c('scale','prec')] <- scale(data.raw[,c('scale','prec')], center = T, scale = T)
        rf_model <- readRDS("RFmodel2_with_sampling.rds")
        pred.RF = predict(rf_model, newdata=data.raw,  type='prob')
        data.raw$prob <- pred.RF$X1
    }''')

rf_model = robjects.r.readRDS("parRF_none.rds") # Random Forest classifier with none sampling
prediction_fn = robjects.globalenv['get_prediction']


def process_url(url):
    results ={'url': url}
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read()
            results = process_html(html)

    except:
        results ={"error" :"Could not download the webpage"}

    return results
def convert_factor(obj):
    """
    Taken from jseabold's PR: https://github.com/pydata/pandas/pull/9187
    """
    ordered = robjects.r["is.ordered"](obj)[0]
    categories = list(obj.levels)
    codes = np.asarray(obj) - 1  # zero-based indexing
    values = pd.Categorical.from_codes(codes, categories=categories,ordered=ordered)
    return values

def process_html(html_content):
    global prediction_fn, rf_model
    results = {'html file': html_content}
    # load html content into document

    # extract mention pairs

    # call the classifier

    html_page = HtmlPage(html_content.decode('utf-8'))
    print("page loaded")
    documents = html_page.create_documents()
    feature_extractor = FeatureExtractor(5, 1)
    # pick 5 for k!
    #for eta the approx_sim :         0%        25%        50%        75%       100%
    #                            -0.5985708  2.1250165  2.8879552  3.5073260  6.0000000
    # Thus I picked 1

    documents = list(map(lambda x: feature_extractor.extract_features_for_document(x), documents))
    all_mention_pairs = list(map(lambda x: feature_extractor.extract_mention_pairs_with_features(x), documents))
    all_mention_pairs_flat = [mp for mp_lst in all_mention_pairs for mp in mp_lst]

    data = process_mention_pairs_for_classifier(all_mention_pairs_flat)
    #data_with_predictions = prediction_fn(data)
    # Now get the final results just by the classifier
    r_true = rpy2.robjects.BoolVector([True])
    #get predictions first
    predictions =robjects.r.predict(rf_model, newdata = data, type='prob' )
    #print(predictions.dtypes)
    #print(predictions.shape)
    # confert the FactorVector to pandas dataframe
    #predictions = convert_factor(predictions)
    # record the predictions
    for col in predictions:
        print(col.rclass[0])
    data['pr'] = np.asarray(predictions[1])
    # filter the probabilities
    #final_predictions = data.ix[data.pr  >  0.3]
    #with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
    #        print(final_predictions)
    print("documents processed")
    for document in documents:
        solve(document, data)

    results_text = html_page.get_documents_as_text()
    #mention_pairs = extract_mention_pairs(html_content)
    #mention_pairs_processed= process_mention_pairs_for_classifier(mention_pairs)
    #predictions = predict_fn(mention_pairs_processed)

    # run the graph/ILP solver
    #final_predictioins = graph_solver(predictions,
    # return the results
    results = {'results':results_text}
    #print(results_text)
    return results
def solve(document, data_with_prob):
    print("Solving Document:%s"%document.doc_id)
    edges = document.get_all_edges()
    priors = data_with_prob[data_with_prob.doc_id == document.doc_id]
    solve_document_rwr(priors,edges, document)
    # solve with the graph
    # write the solution to the documents


def process_mention_pairs_for_classifier(mention_pairs):
#create a data frame withe the following data
#no_scale_diff+diff_max+dif_sum+scale+prec+unit+modApprox+modBound+modExact+modNone+aggr+ltokn+lnps+gtokn+gnps+surfaceform
    data = []
    col_names =['doc_id', 'mXId','mTid','no_scale_diff','diff_max','dif_sum','scale','prec','unit','mod', 'aggr','ltokn','lnps','gtokn', 'gnps','surfaceform','approx_sim']
    for mention_pair in mention_pairs:
        item = mention_pair.get_as_list()
        data.append(item)


    data_frame = pd.DataFrame(data = data, columns = col_names)
    data_frame['modApprox']  = [1 if mod == 'approx'  else 0 for mod  in data_frame['mod']]
    data_frame['modBound']  = [1 if mod == 'bound'  else 0 for mod  in data_frame['mod']]
    data_frame['modExact']  = [1 if mod == 'exact'  else 0 for mod  in data_frame['mod']]
    data_frame['modNone']  = [1 if mod == 'None'  else 0 for mod  in data_frame['mod']]


    #print(data_frame.dtypes)
    #print(data_frame.size)
    #print(data_frame.shape)
    #print(data_frame)
    return data_frame
