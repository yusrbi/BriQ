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
  data.train <- data.processed[!(data.processed$doc_id %in% test_doc_ids$doc_id), ]
  data.test <- data.processed[(data.processed$doc_id %in% test_doc_ids$doc_id), ]
  
  train_doc_ids <- unique(data.train$doc_id)
  
  folds = createFolds(train_doc_ids,k=10, list=T, returnTrain = FALSE)
  
  set.seed(3377)
  sample_size = floor((1/9) * nrow(data.train))
  dev_ids <- sample( seq_len(nrow(data.train)), size = sample_size)
  
  data.dev = data.train[dev_ids, ]
  data.train = data.train[-dev_ids, ]
  

  #some counts on the splits to make sure there is no bias 
  
  print(paste0("dev set size:",nrow(data.dev)))
  print(paste0("test set size:",nrow(data.test)))
  print(paste0("train set size", nrow(data.train)))
  print(paste0("Number of +ve instances in train:",nrow(data.train[data.train$GT =='X1',])))
  print(paste0("Number of -ve instances in train:",nrow(data.train[data.train$GT =='X0',])))
  print(paste0("Number of +ve instances in test:",nrow(data.test[data.test$GT =='X1',])))
  print(paste0("Number of -ve instances in test:",nrow(data.test[data.test$GT =='X0',])))
  print(paste0("Number of +ve instances in dev:",nrow(data.dev[data.dev$GT =='X1',])))
  print(paste0("Number of -ve instances in dev:",nrow(data.dev[data.dev$GT =='X0',])))
  
  print(paste0("Unique mentions: ", length(unique(data.raw$mXId))))
  print(paste0("Unique mentions with +ve class: ", length(unique(data.raw[data.raw$GT =='X1',]$mXId))))
  print(paste0("Unique mentions with -ve class: ", length(unique(data.raw[data.raw$GT =='X0',]$mXId))))
  
  
  train_indexes = c()
  # Fold number 11 is used for params tuning!
  for (i in 1:10){
    test_ids <- train_doc_ids[folds[[i]]]
    train_ids <- train_doc_ids[-folds[[i]]]
    name <- paste(c("MyFold", i), collapse = "")
    train_indx = which(data.train$doc_id %in% train_ids)
    train_indexes[[name]] <- train_indx
  }
  mydata <- list("train_indexes" = train_indexes, "test" = data.test, "train" = data.train, "dev" = data.dev, "all" = data.processed)
  mydata
}

print_data_stats<-function(data.all){
  
  sum <- nrow(data.all[grep('sum',data.all$mTid),])
  print(paste0(c("sum", sum)))
  avg<-nrow(data.all[grep('avg',data.all$mTid),])
  print(paste0(c("avg",avg)))
  perc<-nrow(data.all[grep('perc',data.all$mTid),])
  print(paste0(c("perc",perc)))
  dif<- nrow(data.all[grep('dif',data.all$mTid),])
  print(paste0(c("dif",dif)))
  rat<-nrow(data.all[grep('rat',data.all$mTid),])
  print(paste0(c("rat",rat)))
  all<- nrow(data.all)
  same<- all -(sum+avg+perc+rat+dif)
  print(paste0(c("same",same)))
  print(paste0(c("all",all)))
  
  data.gt = data.all[data.all$GT=='X1', ]
  quantile(data.gt$approx_sim) # to get the cut off value of the sim for mention-pairs generation
  
  
  psum <- nrow(data.gt[grep('sum',data.gt$mTid),])
  print(paste0(c("+sum", psum)))
  pavg<-nrow(data.gt[grep('avg',data.gt$mTid),])
  print(paste0(c("+avg",pavg)))
  pperc<-nrow(data.gt[grep('perc',data.gt$mTid),])
  print(paste0(c("+perc",pperc)))
  pdif<- nrow(data.gt[grep('dif',data.gt$mTid),])
  print(paste0(c("+dif",pdif)))
  prat<-nrow(data.gt[grep('rat',data.gt$mTid),])
  print(paste0(c("+rat",prat)))
  pall<- nrow(data.gt)
  psame<- pall -(psum+pavg+pperc+prat+pdif)
  print(paste0(c("+same",psame)))
  print(paste0(c("+all",pall)))
  
  #-ves 
  nsum <- sum-psum
  navg<- avg-pavg
  nperc <- perc - pperc
  ndif<- dif - pdif
  nrat<- rat - prat
  nall<- all - pall
  nsame <- same - psame
  print(paste0(c("-sum",nsum)))
  print(paste0(c("-avg",navg)))
  print(paste0(c("-perc",nperc)))
  print(paste0(c("-dif",ndif)))
  print(paste0(c("-rat",nrat)))
  print(paste0(c("-same",nsame)))
  print(paste0(c("-all",nall)))
  
  all = c(sum,avg,perc,dif,rat,same,all)
  pos= c(psum,pavg,pperc,pdif,prat,psame,pall)
  neg = c(nsum,navg,nperc,ndif,nrat,nsame,nall)
  result <- list("all" = all, "pos" = pos, "neg"= neg)
  
}


get_stats <- function(input_dir, test_doc_ids_file_name){
  print(input_dir)
  data<- load_data(input_dir, test_doc_ids_file_name)

  result<-print_data_stats(data$all)
 
  
}


args = commandArgs(trailingOnly=TRUE)
if (length(args)<2) {
  stop("Please specify the input directory and the file containing the test document ids", call.=FALSE)
} 
input_dir = args[1]
test_doc_ids_file_name = args[2]

get_stats(input_dir, test_doc_ids_file_name)