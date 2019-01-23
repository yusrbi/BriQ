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
library(fastAdaboost)
library(adabag)
library(plyr)
require(mgcv)
library(gbm)


twoClassSummaryCustom = function (data, lev = NULL, model = NULL) 
{
  lvls <- levels(data$obs)
  if (length(lvls) > 2)
    stop(paste("Your outcome has", length(lvls), "levels. The twoClassSummary() function isn't appropriate."))
  if (!all(levels(data[, "pred"]) == lvls)) 
    stop("levels of observed and predicted data do not match")
  rocAUC <- ModelMetrics::auc(ifelse(data$obs == lev[2], 0, 
                                     1), data[, lvls[1]])
  out <- c(rocAUC,
           sensitivity(data[, "pred"], data[, "obs"], lev[1]),
           specificity(data[, "pred"], data[, "obs"], lev[2]),
           Precision(data[, "pred"], data[, "obs"], lev[2]),
           F1_Score(data[, "pred"], data[, "obs"], lev[1]),
           posPredValue(data[, "pred"], data[, "obs"], lev[1]))
  names(out) <- c("ROC", "Sens", "Spec", "Prec", "F1", "Prec3")
  out
}


print_results = function(relation, confusion_matrix){
  print(paste0(c("Results for Relation:",relation), collapse =' '))
  print("Kappa,Accuracy,Sensitivity,specificity,balanced accuracy, precision, F1")
  print(paste0(c( confusion_matrix$overall['Kappa'], confusion_matrix$overall['Accuracy'],confusion_matrix$byClass['Sensitivity'], confusion_matrix$byClass['Specificity'], confusion_matrix$byClass['Balanced Accuracy'],confusion_matrix$byClass['Pos Pred Value'],  confusion_matrix$byClass['F1']), collapse = ','))
}

multmerge = function(mypath){
  filenames<-list.files(path=mypath, full.names=TRUE, pattern='part', recursive = T)
  filenames<-filenames[grepl("^.*batch.*",filenames)]
  datalist <- lapply(filenames, function(x){
    if(file.size(x) > 0){
      read.csv(file=x,header=F ,sep="\t", stringsAsFactors= F )
    }
  })
  data <- Reduce(function(x,y) {(rbind(x,y, stringsAsFactors= F))}, datalist)
  data
}

load_data = function(file_name){
  
  set.seed(777)
  data.raw <-  multmerge(file_name)
  colnames(data.raw) <- c("doc_id","m_id","mod","precision", "scale", "unit", "aggr_fun","glbl_perc","glbl_sum","glbl_diff", "glbl_rat","lcl_perc", "lcl_sum","lcl_diff", "lcl_rat","glbl_stats","glbl_finance","glbl_unit","glbl_temp","lcl_stats","lcl_finance","lcl_unit","lcl_temp","exact_count", "class")

  #data.raw <- data.raw[!(data.raw$class %in% c('None','avg')), ]
  
  #data.raw$class <- make.names(data.raw$class)
  data.raw$class <- as.factor(data.raw$class)
  data.raw$mod <- as.factor(data.raw$mod)
  data.raw$aggr_fun <- as.factor(data.raw$aggr_fun)
  data.raw$unit <-  as.factor(data.raw$unit)
  
  #summary(data.raw)
  # scale the data
  #data.raw[,c('no_scale_diff','diff_max','dif_sum','scale','prec', 'ltokn','lnps','gtokn', 'gnps','surfaceform')] <- scale(data.raw[,c('no_scale_diff','diff_max','dif_sum','scale','prec', 'ltokn','lnps','gtokn', 'gnps','surfaceform')], center = T, scale = T)
  #data.raw[,c('scale','precision', "glbl_per_kw_cnt", "glbl_sum_kw_cnt", "glbl_diff_kw_cnt","glbl_rat_kw_cnt", "lcl_per_kw_cnt", "lcl_sum_kw_cnt", "lcl_diff_kw_cnt","lcl_rat_kw_cnt")] <- scale(data.raw[,c('scale','precision', "glbl_per_kw_cnt", "glbl_sum_kw_cnt", "glbl_diff_kw_cnt","glbl_rat_kw_cnt", "lcl_per_kw_cnt", "lcl_sum_kw_cnt", "lcl_diff_kw_cnt","lcl_rat_kw_cnt")], center = F, scale = T)
  data.processed <- data.raw[ ,  c("doc_id","m_id","mod","precision", "scale", "unit", "aggr_fun","glbl_perc","glbl_sum","glbl_diff", "glbl_rat","lcl_perc", "lcl_sum","lcl_diff", "lcl_rat","glbl_stats","glbl_finance","glbl_unit","glbl_temp","lcl_stats","lcl_finance","lcl_unit","lcl_temp","exact_count", "class")]

  #mod_data<- with(data.raw, model.matrix(~ mod + 0))
  # convert the categorical variable to multiple binary features 
  #data.processed[,colnames(mod_data)] <- mod_data
  
  
  #aggr_function <- with(data.raw, model.matrix(~ aggr_fun + 0))
  #data.processed[,colnames(aggr_function)] <- aggr_function
  
  #units <- with(data.raw, model.matrix(~ unit + 0))
  #data.processed[,colnames(units)] <- units
  
  
  data.processed 
 
}




test_all <- function(){
  file_name<-"mention_features"

  data<- load_data(file_name)
  #data$is_same = data[data$class =='same']
  #remove average
  data <- data[data$class != 'avg', ]
  test_doc_ids <- read.csv(file="test_document_ids.txt",header=F ,sep="\t", stringsAsFactors= F )
  colnames(test_doc_ids) <- c("doc_id")
  train_all <- data[!(data$doc_id %in% test_doc_ids$doc_id), ]
  train <- train_all[train_all$class != 'None', ]
  test_all <- data[(data$doc_id %in% test_doc_ids$doc_id), ]
  test <- test_all[test_all$class != 'None', ]
  #partition data
  #intrain <- createDataPartition(y= data$class, p = 0.85, list = FALSE)
  #train <- data[intrain,]
  #test <- data[-intrain,]
  train_control <- trainControl(method='cv', number = 10, search='grid', savePredictions=T,verboseIter = TRUE, classProbs = TRUE)
  #train_control <- trainControl(method='cv', number = 10, search='grid', savePredictions=T, classProbs = TRUE,verboseIter = TRUE,
  #                              summaryFunction=twoClassSummary)
  #train_without_same <- train[train$class !='same',]
  #test_without_same <- test[test$class !='same', ]
  #set.seed(373737)
  counts <- table(train$class)
  class_weights <- 1/counts
  
  train$class_weight <- class_weights[train$class] * 0.5
  
  set.seed(9977)
  model<- caret::train(class~ mod+precision+ scale+ unit+aggr_fun+ glbl_perc+glbl_sum+glbl_diff+ glbl_rat+lcl_perc+ lcl_sum+lcl_diff+ lcl_rat+glbl_stats+glbl_finance+glbl_unit+glbl_temp+lcl_stats+lcl_finance+lcl_unit+lcl_temp+exact_count
                       , data = train, method ='gbm', trControl=train_control)#, weights=  train$class_weight)
 
  saveRDS(model,  'mention_features/mention_type_classifier_wo_weights.rds')
   #model_wo_same<- caret::train(class~ mod+precision+ scale+ unit+ aggr_fun+glbl_perc+glbl_sum+glbl_diff+ glbl_rat+lcl_perc+ lcl_sum+lcl_diff+ lcl_rat+glbl_stats+glbl_finance+glbl_unit+glbl_temp+lcl_stats+lcl_finance+lcl_unit+lcl_temp
   #                    , data = train_without_same, method ='parRF', metric="kappa", trControl=train_control)
  # on test
  pred = predict(model, newdata=test,  type='prob')
  aggr<-colnames(pred)
  pred.2nd_labels = c()
  for (row in 1:nrow(pred)) {
    sorted_row<-sort(pred[row,])
    sorted_aggr <- colnames(sorted_row)
    n <- length(sorted_aggr)
    if (sorted_aggr[n] == "same"){
      second_label <- sorted_aggr[n-1] #second max
    }else{
      second_label <- sorted_aggr[n] #second max
    }
    
    pred.2nd_labels[row] <- second_label
    
  }
  pred.2nd_labels<- as.factor(pred.2nd_labels)
  confusion_matrix<-confusionMatrix(pred.2nd_labels, test$class)
  #confusion_matrix_wo_same<-confusionMatrix(pred_wo_same.labels, test_without_same$class)
  
  confusion_matrix
  
  pred.labels = predict(model, newdata=test)
  #pred_wo_same.labels = predict(model_wo_same, newdata=test_without_same)
  confusion_matrix<-confusionMatrix(pred.labels, test$class)
  #confusion_matrix_wo_same<-confusionMatrix(pred_wo_same.labels, test_without_same$class)
  
  confusion_matrix
  #confusion_matrix_wo_same
  summary
  imp = varImp(model)
  #imp_wo_same = varImp(model_wo_same)
  imp
  #imp_wo_same
  
  #train_without_same$pred<-model_wo_same$pred$pred
  #test_without_same$pred<-pred_wo_same.labels
  
  #pred_wo_same <- predict(model_wo_same, newdata = test_without_same, type="prob")
  #test_without_same$perc_prob<- pred_wo_same$perc
  #test_without_same$rat_prob<- pred_wo_same$rat
  #test_without_same$sum_prob<- pred_wo_same$sum
  #test_without_same$dif_prob<- pred_wo_same$dif
  pred.labels <- predict(model, newdata=test_all)
  test_all$pred<-pred.labels
  pred<- predict(model, newdata = test_all, type="prob")
  test_all$perc_prob<- pred$perc
  test_all$rat_prob<- pred$rat
  test_all$sum_prob<- pred$sum
  test_all$dif_prob<- pred$dif
  test_all$same_prob<- pred$same
  write.table(test_all, file="mention_classification_test_all", quote=FALSE, sep='\t', col.names = NA)

  pred.labels <- predict(model, newdata=train_all)
  train_all$pred<-pred.labels
  pred<- predict(model, newdata = train_all, type="prob")
  train_all$perc_prob<- pred$perc
  train_all$rat_prob<- pred$rat
  train_all$sum_prob<- pred$sum
  train_all$dif_prob<- pred$dif
  train_all$same_prob<- pred$same
  
  write.table(train_all, file="mention_classification_train_all", quote=FALSE, sep='\t', col.names = NA)
  
  
  rownames(imp$importance) <- c("mod","precision", "scale", "unit", "aggr_fun","glbl_per_kw_cnt", "glbl_sum_kw_cnt", "glbl_diff_kw_cnt","glbl_rat_kw_cnt", "lcl_per_kw_cnt", "lcl_sum_kw_cnt", "lcl_diff_kw_cnt","lcl_rat_kw_cnt")
  print_results('All', confusion_matrix)
  
}


test_all()

