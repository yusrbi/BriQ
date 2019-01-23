#!/bin/bash

#Fixed k = 5,


#max precision
nohup python test_graph_with_input.py results_100000neg/ results_100000neg/evaluation_results/output_plus_prob_parRF_test_filtered.tsv results_100000neg/evaluation_results/graph_rf.tsv 0.1 0.9 0.5 0.9 0.1 >  results_100000neg/evaluation_results/test_graph_parRF_test_3007_maxp.out 2>&1 &

####################### Original mentions
# LR Model 
nohup python test_graph_with_input.py results_100000neg/ results_100000neg/evaluation_results/output_plus_prob_regLogistic_test_filtered.tsv results_100000neg/evaluation_results/graph_lr.tsv 0.6     0.4     0.4     0.2     0.8>  results_100000neg/evaluation_results/test_graph_regLogistic_test_2507.out 2>&1 &


# svm 
nohup python test_graph_with_input.py results_100000neg/ results_100000neg/evaluation_results/output_plus_prob_svmRadialWeights_test_filtered.tsv   results_100000neg/evaluation_results/graph_svm.tsv 0.5     0.5     0.3     0.2     0.8>  results_100000neg/evaluation_results/test_graph_svmRadialWeights_test_2507.out 2>&1 &

# RF 
nohup python test_graph_with_input.py results_100000neg/ results_100000neg/evaluation_results/output_plus_prob_parRF_test_filtered.tsv results_100000neg/evaluation_results/graph_rf.tsv 0.4     0.6     0.4     0.2     0.8>  results_100000neg/evaluation_results/test_graph_parRF_test_2507.out 2>&1 &


nohup python test_graph_with_input.py results_500000neg/ results_500000neg/evaluation_results/output_plus_prob_parRF_test_filtered.tsv results_500000neg/evaluation_results/graph_rf.tsv 0.4     0.6     0.4     0.2     0.8>  results_500000neg/evaluation_results/test_graph_parRF_test.out 2>&1 &

##############################modified mentions
output_plus_prob_regLogistic_test.tsv
output_plus_prob_svmRadialWeights_test.tsv
output_plus_prob_parRF_test.tsv

# LR Model 
nohup python test_graph_with_input.py results_100000neg_mod/ results_100000neg_mod/evaluation_results/output_plus_prob_regLogistic_test_filtered.tsv results_100000neg_mod/evaluation_results/graph_lr.tsv  0.7    0.3     0.3     0.1     0.9>results_100000neg_mod/evaluation_results/test_graph_regLogistic_test_2507.out 2>&1 &


# svm 
nohup python test_graph_with_input.py results_100000neg_mod/ results_100000neg_mod/evaluation_results/output_plus_prob_svmRadialWeights_test_filtered.tsv  results_100000neg_mod/evaluation_results/graph_svm.tsv 0.8     0.2     0.3     0.1     0.9>results_100000neg_mod/evaluation_results/test_graph_svmRadialWeights_test_2507.out 2>&1 &

# RF 
nohup python test_graph_with_input.py results_100000neg_mod/ results_100000neg_mod/evaluation_results/output_plus_prob_parRF_test_filtered.tsv  results_100000neg_mod/evaluation_results/graph_rf.tsv 0.7     0.3     0.3     0.1     0.9>results_100000neg_mod/evaluation_results/test_graph_parRF_test_2507.out 2>&1 &


############################# Truncated mentions

# LR Model 
nohup python test_graph_with_input.py results_100000neg_trunc/ results_100000neg_trunc/evaluation_results/output_plus_prob_regLogistic_test_filtered.tsv results_100000neg_trunc/evaluation_results/graph_lr.tsv 0.6     0.4     0.4     0.1     0.9>results_100000neg_trunc/evaluation_results/test_graph_regLogistic_test_2507.out 2>&1 &


# svm 
nohup python test_graph_with_input.py results_100000neg_trunc/ results_100000neg_trunc/evaluation_results/output_plus_prob_svmRadialWeights_test_filtered.tsv results_100000neg_trunc/evaluation_results/graph_svm.tsv 0.6     0.4     0.3     0.1     0.9>results_100000neg_trunc/evaluation_results/test_graph_svmRadialWeights_test_2507.out 2>&1 &

# RF 
nohup python test_graph_with_input.py results_100000neg_trunc/ results_100000neg_trunc/evaluation_results/output_plus_prob_parRF_test_filtered.tsv  results_100000neg_trunc/evaluation_results/graph_rf.tsv  0.7     0.3     0.3     0.1     0.9 >results_100000neg_trunc/evaluation_results/test_graph_parRF_test_2507.out 2>&1 &








########### Cost sensitive -- Original mentions

results_100000neg/evaluation_results/output_plus_prob_regLogistic_9_cost_sensitive_dev.tsv

results_100000neg/evaluation_results/output_plus_prob_svmRadialWeights_cost_sensitive_dev_9.tsv


# Logistic Regerssion cost sensitive
nohup python tune_graph_with_input.py results_100000neg/ results_100000neg/evaluation_results/output_plus_prob_regLogistic_9_cost_sensitive_dev.tsv>  results_100000neg/evaluation_results/tune_graph_regLogistic_9_cost_sensitive_dev.out 2>&1 &


#SVM Radial cost sensitive
nohup python tune_graph_with_input.py results_100000neg/ results_100000neg/evaluation_results/output_plus_prob_svmRadialWeights_cost_sensitive_dev_9.tsv  >  results_100000neg/evaluation_results/tune_graph_svmRadialWeights_9_cost_sensitive_dev.out 2>&1 &



########### Cost sensitive -- Modified  mentions

results_100000neg_mod/evaluation_results/output_plus_prob_regLogistic_9_cost_sensitive_dev.tsv

results_100000neg_mod/evaluation_results/output_plus_prob_svmRadialWeights_cost_sensitive_dev_9.tsv

# Logistic Regerssion cost sensitive
nohup python tune_graph_with_input.py results_100000neg_mod/ results_100000neg_mod/evaluation_results/output_plus_prob_regLogistic_9_cost_sensitive_dev.tsv>  results_100000neg_mod/evaluation_results/tune_graph_regLogistic_9_cost_sensitive_dev.out 2>&1 &


#SVM Radial cost sensitive
nohup python tune_graph_with_input.py results_100000neg_mod/ results_100000neg_mod/evaluation_results/output_plus_prob_svmRadialWeights_cost_sensitive_dev_9.tsv  >  results_100000neg_mod/evaluation_results/tune_graph_svmRadialWeights_9_cost_sensitive_dev.out 2>&1 &
