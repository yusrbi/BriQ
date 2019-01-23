#install.packages('caret')
library('caret')
#install.packages('e1071')
library('e1071')
#install.packages('glmnet')
library(glmnet)
library(randomForest)
library(foreach)
library(import)
# install.packages('ROSE')
# install.packages('abind')
# install.packages('zoo')
# install.packages('xts')
# install.packages('quantmod')
# install.packages('ROCR')
# install.packages("DMwR")
# install.packages('DMwR')
library(ROSE)
library(DMwR)
#library(fastAdaboost)
#library(adabag)
library(plyr)
require(mgcv)
library(kernlab)
library(gbm)

print_results = function(relation, confusion_matrix){
  print(paste0(c("Results for Relation:",relation), collapse =' '))
  print("Kappa,Accuracy,Sensitivity,specificity,balanced accuracy, precision, F1")
  print(paste0(c( confusion_matrix$overall['Kappa'], confusion_matrix$overall['Accuracy'],confusion_matrix$byClass['Sensitivity'], confusion_matrix$byClass['Specificity'], confusion_matrix$byClass['Balanced Accuracy'],confusion_matrix$byClass['Pos Pred Value'],  confusion_matrix$byClass['F1']), collapse = ','))
}

multmerge = function(mypath){
  filenames<-list.files(path=mypath, full.names=TRUE, pattern='part', recursive = T)
  filenames<-filenames[grepl("^.*output.*",filenames)]
  datalist <- lapply(filenames, function(x){
    if(file.size(x) > 0){
      read.csv(file=x,header=F ,sep="\t", stringsAsFactors= F )
    }
  })
  data <- Reduce(function(x,y) {(rbind(x,y, stringsAsFactors= F))}, datalist)
  data
}


load_data = function(file_name, test_doc_ids_file_name){
  
  set.seed(777)
  data.raw <-  multmerge(file_name)
  colnames(data.raw) <- c('doc_id', 'mXId','mTid','no_scale_diff','diff_max','dif_sum','scale','prec','unit','mod', 'aggr','ltokn','lnps','gtokn', 'gnps','surfaceform','approx_sim','mx','mt','scalex','scalet','GT','aggrFunction')
  
  data.raw$GT <- make.names(data.raw$GT)
  data.raw$GT <- as.factor(data.raw$GT)
  data.raw$mod <- as.factor(data.raw$mod)
  data.raw$aggrFunction <- as.factor(data.raw$aggrFunction)
  data.processed <-data.raw[,c('doc_id', 'mXId','mTid','no_scale_diff','diff_max','dif_sum','scale','prec', 'unit','mod','aggr','ltokn','lnps','gtokn','gnps', 'surfaceform','approx_sim','mx','mt','scalex','scalet', 'GT')]
  
 
  
  test_doc_ids <- read.csv(file=test_doc_ids_file_name,header=F ,sep="\t", stringsAsFactors= F )
  colnames(test_doc_ids) <- c("doc_id")
  train <- data.processed[!(data.processed$doc_id %in% test_doc_ids$doc_id), ]
  test <- data.processed[(data.processed$doc_id %in% test_doc_ids$doc_id), ]
  
  train_doc_ids <- unique(train$doc_id)
  folds = createFolds(train_doc_ids,k=10, list=T, returnTrain = FALSE)
  print(paste0("test set size:",nrow(test)))
  print(paste0("train set size", nrow(train)))
  print(paste0("Number of +ve instances in train:",nrow(train[train$GT =='X1',])))
  print(paste0("Number of -ve instances in train:",nrow(train[train$GT =='X0',])))
  print(paste0("Number of +ve instances in test:",nrow(test[test$GT =='X1',])))
  print(paste0("Number of -ve instances in test:",nrow(test[test$GT =='X0',])))

  print(paste0("Unique mentions: ", length(unique(data.raw$mXId))))
  print(paste0("Unique mentions with +ve class: ", length(unique(data.raw[data.raw$GT =='X1',]$mXId))))
  print(paste0("Unique mentions with -ve class: ", length(unique(data.raw[data.raw$GT =='X0',]$mXId))))
  
  
  train_indexes = c()
  for (i in 1:10){
    test_ids <- train_doc_ids[folds[[i]]]
    train_ids <- train_doc_ids[-folds[[i]]]
    name <- paste(c("MyFold", i), collapse = "")
    train_indx = which(train$doc_id %in% train_ids)
    train_indexes[[name]] <- train_indx
  }
  mydata <- list("train_indexes" = train_indexes, "test" = test, "train" = train)
  mydata
}
svm_linear_grid<- function(len){
  
  tuneGrid <- expand.grid(cost = c(0.25,4,8,16,32,128),#2 ^((1:len) - 3)
                          weight = 9) # weight is defined as cwts <- c(1, param$weight), thus this value is for the postive class X1
  tuneGrid
}

svm_radial_grid <-function(len, srng){
  tuneGrid <- expand.grid(sigma = mean(as.vector(srng[-2])) , # get the mean of the first and last value except for the median (-1)
                          C = c(16,8,128),#2 ^((1:len) - 3)
                          Weight = 1/9) # the weight is defined as wts <- c(param$Weight, 1), thus this value is for the negative class X0
  tuneGrid
}


regLogistic_grid <- function(len){
  
  tune_grid<- expand.grid(cost = c(32,4),#2 ^((1:len)- ceiling(len*0.5))
                          loss = c("L1"), #, "L2_dual", "L2_primal"
                          epsilon = c(10^-4, 10^-6)) #signif(0.01 * (10^((1:len) - ceiling(len*0.5))), 2) 
  tune_grid
}

regLogistic_weights <-function(w=9){
  wi <- c(1,w)
  names(wi) <- c("X0","X1")
  wi
}

test <- function(mydata, classifier, input_dir){
  
  print(paste(c('Staring exp. for', classifier, 'classifier', '- Cost Sensitive'), collapse = " "))
  
  train_indexes <- mydata$train_indexes
  data.train <- mydata$train
  data.test <-mydata$test
 
  set.seed(7733)
  model_file <- paste(c(input_dir,"/evaluation_results/",classifier, ".rds"), collapse = "")
  print(paste(c('load model', model_file)))
  model<- readRDS(model_file)
  
  
  # on Dev
  set.seed(3377)
  sample_size = floor((1/9) * nrow(data.train))
  dev_ids <- sample( seq_len(nrow(data.train)), size = sample_size)
  
  data.dev = data.train[dev_ids, ]
  
  pred = predict(model, newdata=data.dev,  type='prob')
  pred.labels = predict(model, newdata=data.dev)
  confusion_matrix<-confusionMatrix(data =pred.labels, positive='X1', reference=data.dev$GT)
  data.dev$prob <- pred$X1
  write.table(data.dev, file=paste(c(input_dir,"/evaluation_results/output_plus_prob_",classifier, '_dev.tsv'), collapse = ""), quote=FALSE, sep='\t', col.names = NA)
  
  
  
  print_results('All', confusion_matrix)
  
  
  print("######## Sum Results #########")
  confusion_matrix_sum = confusionMatrix(data =pred.labels[grep('sum',data.dev$mTid)], positive='X1',reference=data.dev[grep('sum',data.dev$mTid),]$GT)
  print(confusion_matrix_sum)
  print_results('Sum', confusion_matrix_sum)
  print("######## difference Results #########")
  confusion_matrix_diff =  confusionMatrix(data =pred.labels[grep('dif',data.dev$mTid)], positive='X1',reference=data.dev[grep('dif',data.dev$mTid),]$GT)
  print(confusion_matrix_diff)
  print_results('Difference', confusion_matrix_diff)
  print("######## Percent Results #########")
  confusion_matrix_perc = confusionMatrix(data =pred.labels[grep('perc',data.dev$mTid)], positive='X1',reference=data.dev[grep('perc',data.dev$mTid),]$GT)
  print(confusion_matrix_perc)
  print_results('percentage', confusion_matrix_perc )
  print("######## Ratio Results #########")
  confusion_matrix_rat = confusionMatrix(data =pred.labels[grep('rat',data.dev$mTid)], positive='X1',reference=data.dev[grep('rat',data.dev$mTid),]$GT)
  print(confusion_matrix_rat)
  print_results('Ratio', confusion_matrix_rat)
  print("######## Avg Results #########")
  confusion_matrix_avg =  confusionMatrix(data =pred.labels[grep('avg',data.dev$mTid)], positive='X1',reference=data.dev[grep('avg',data.dev$mTid),]$GT)
  print(confusion_matrix_avg)
  print_results('Average', confusion_matrix_avg)
  print("######## Same Results #########")
  confusion_matrix_same = confusionMatrix(data =pred.labels[grep('^\\d+\\.\\d+$',perl=T, data.dev$mTid)],
                                          positive='X1',reference=data.dev[grep('^\\d+\\.\\d+$', perl = T,data.dev$mTid),]$GT)
  print(confusion_matrix_same)
  print_results('Same', confusion_matrix_same)
  
  
  print("######## virtual cells Results #########")
  confusion_matrix_virtual = confusionMatrix(data =pred.labels[grep('^\\d+\\.\\d+\\,.*$',perl=T, data.dev$mTid)],
                                             positive='X1',reference=data.dev[grep('^\\d+\\.\\d+\\,.*$', perl = T,data.dev$mTid),]$GT)
  print(confusion_matrix_virtual)
  print_results('virtual cells', confusion_matrix_virtual)
  
  results<- c(confusion_matrix$overall['Kappa'],confusion_matrix$overall['Accuracy'],confusion_matrix$byClass['Sensitivity'], confusion_matrix$byClass['Specificity'], confusion_matrix$byClass['Balanced Accuracy'],confusion_matrix$byClass['Pos Pred Value'],  confusion_matrix$byClass['F1'])
  results
  
}

startTrain <- function(input_dir, test_doc_ids_file_name){
 
  data<- load_data(input_dir, test_doc_ids_file_name)
  
  all_results <- c()#c("Classifier","Sampling", "Accuracy","Sensitivity","specificity","balanced accuracy", "precision", "F1") 
  classifiers =c('parRF', 
                 'gbm')
  
  for (classifier in classifiers){
    
      results<- test(data, classifier, input_dir)
      all_results<- rbind(all_results, c(classifier,results))

  }
  print(all_results)
  output_file = paste0(c(input_dir, "/evaluation_results/classifiers_dev_results.tsv"), collapse = "")
  write.table(all_results, file=output_file, quote=FALSE, sep='\t', col.names = c("Classifier", "Kappa" ,"Accuracy","Sensitivity","specificity","balanced accuracy", "precision", "F1") )
  
}


args = commandArgs(trailingOnly=TRUE)
if (length(args)<2) {
  stop("Please specify the input directory and the file containing the test document ids", call.=FALSE)
} 
input_dir = args[1]
test_doc_ids_file_name = args[2]

startTrain(input_dir,test_doc_ids_file_name )

