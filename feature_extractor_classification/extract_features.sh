#!/bin/bash

spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 1
hadoop fs -get /user/yibrahim/results_1neg .
spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 2 
hadoop fs -get /user/yibrahim/results_2neg .

spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 3 
hadoop fs -get /user/yibrahim/results_3neg .
spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 4
hadoop fs -get /user/yibrahim/results_4neg .
spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 5
hadoop fs -get /user/yibrahim/results_5neg .

spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 6 
hadoop fs -get /user/yibrahim/results_6neg .

spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 7
hadoop fs -get /user/yibrahim/results_7neg .

spark-submit --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./QCR/qrr_env/bin/python --conf spark.yarn.appMasterEnv.NLTK_DATA=./ --master yarn-cluster --archives qcr_env.zip#QCR,tokenizers.zip#tokenizers,taggers.zip#taggers --py-files libs.zip --files database.ini --num-executors 8 --executor-memory 15G --driver-memory 30G  --executor-cores 6 pipeline.py 10
hadoop fs -get /user/yibrahim/results_10neg .

