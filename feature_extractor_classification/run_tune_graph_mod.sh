

# Fixed K =5, with  sampling 
#svm Linear kernel 
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/output_plus_prob_svmLinear_smote_dev.tsv>  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/tune_graph_svmLinear_smote_dev.out 2>&1 &

#svm linear + tomek Links removal
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/output_plus_prob_svmLinear_none_smote_tomek_dev.tsv>  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/tune_graph_svmLinear_none_smote_tomek_dev.out 2>&1 &


#LR 
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/output_plus_prob_regLogistic_smote_dev.tsv  >  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/tune_graph_regLogistic_smote_dev.out 2>&1 &

#LR smote + tomek links removal
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/output_plus_prob_regLogistic_none_smote_tomek_dev.tsv  >  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/tune_graph_regLogistic_none_smote_tomek_dev.out 2>&1 &


#RF
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/output_plus_prob_parRF_none_dev.tsv >  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg_mod/evaluation_results/tune_graph_parRF_none_dev.out 2>&1 &



########################Original mentions

# Fixed K =5, with  sampling 
#svm Linear kernel 
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/evaluation_results/output_plus_prob_svmLinear_smote_dev.tsv>  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/evaluation_results/tune_graph_svmLinear_smote_dev.out 2>&1 &


#LR 
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/evaluation_results/output_plus_prob_regLogistic_smote_dev.tsv  >  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/evaluation_results/tune_graph_regLogistic_smote_dev.out 2>&1 &

#RF
nohup python /GW/D5data-8/yibrahim/script/FeaturesExtractor/tune_graph_with_input.py /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/ /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/evaluation_results/output_plus_prob_parRF_none_dev.tsv >  /GW/D5data-8/yibrahim/script/FeaturesExtractor/results_5neg/evaluation_results/tune_graph_parRF_none_dev.out 2>&1 &


nohup Rscript new_test_classifiers.R  >results_5neg_mod/evaluation_results/new_test_classifiers_1803_smote_2.out 2 >&1 &




########### Cost sensitive -- Original mentions


output_plus_prob_regLogistic_dev.tsv
output_plus_prob_svmRadialWeights_dev.tsv
output_plus_prob_parRF_dev.tsv 

# Logistic Regerssion cost sensitive
nohup python tune_graph_with_input.py results_5neg/ results_5neg/evaluation_results/output_plus_prob_regLogistic_dev.tsv>  results_5neg/evaluation_results/tune_graph_regLogistic_dev_prec.out 2>&1 &


#SVM Radial cost sensitive
nohup python tune_graph_with_input.py results_5neg/ results_5neg/evaluation_results/output_plus_prob_svmRadialWeights_dev.tsv  >  results_5neg/evaluation_results/tune_graph_svmRadialWeights_dev_prec.out 2>&1 &

#RF
nohup python tune_graph_with_input.py results_5neg/ results_5neg/evaluation_results/output_plus_prob_parRF_dev.tsv  >  results_5neg/evaluation_results/tune_graph_parRF_dev_prec.out 2>&1 &


########### Cost sensitive -- Modified  mentions



# Logistic Regerssion cost sensitive
nohup python tune_graph_with_input.py results_5neg_mod/ results_5neg_mod/evaluation_results/output_plus_prob_regLogistic_dev.tsv>  results_5neg_mod/evaluation_results/tune_graph_regLogistic_dev_prec.out 2>&1 &


#SVM Radial cost sensitive
nohup python tune_graph_with_input.py results_5neg_mod/ results_5neg_mod/evaluation_results/output_plus_prob_svmRadialWeights_dev.tsv  >  results_5neg_mod/evaluation_results/tune_graph_svmRadialWeights_dev_prec.out 2>&1 &

#RF
nohup python tune_graph_with_input.py results_5neg_mod/ results_5neg_mod/evaluation_results/output_plus_prob_parRF_dev.tsv  >  results_5neg_mod/evaluation_results/tune_graph_parRF_dev_prec.out 2>&1 &



########### Cost sensitive -- truncated  mentions



# Logistic Regerssion cost sensitive
nohup python tune_graph_with_input.py results_5neg_trunc/ results_5neg_trunc/evaluation_results/output_plus_prob_regLogistic_dev.tsv>  results_5neg_trunc/evaluation_results/tune_graph_regLogistic_dev_prec.out 2>&1 &


#SVM Radial cost sensitive
nohup python tune_graph_with_input.py results_5neg_trunc/ results_5neg_trunc/evaluation_results/output_plus_prob_svmRadialWeights_dev.tsv  >  results_5neg_trunc/evaluation_results/tune_graph_svmRadialWeights_dev_prec.out 2>&1 &

#RF
nohup python tune_graph_with_input.py results_5neg_trunc/ results_5neg_trunc/evaluation_results/output_plus_prob_parRF_dev.tsv  >  results_5neg_trunc/evaluation_results/tune_graph_parRF_dev_prec.out 2>&1 &





