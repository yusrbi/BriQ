#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import  sys
import findspark
findspark.init()

from pyspark import SparkContext, SparkConf
from loader import Document_Loader 
from extractor import FeatureExtractor
import extractor
import codecs

class PipeLine:
    def __init__(self):
        #TODO remover the setMaster, when running on the cluster
        self.conf = SparkConf().setAppName("TableCRR").setMaster('local')
        self.sc = SparkContext(conf=self.conf)
    def __enter__(self):
        return self      
    def start(self, n_negative_instances):
        # spark context 
        sc = self.sc
        # load documents 
        batch_no =1 
        #log4jLogger = sc._jvm.org.apache.log4j
#       logging.getLogger("py4j").setLevel(logging.ERROR)
#       logger = logging.getLogger("py4j")
        #log4jLogger.LogManager.getLogger("TableQCRR")
        log4jLogger = sc._jvm.org.apache.log4j
        LOGGER = log4jLogger.LogManager.getLogger(__name__)
        LOGGER.info("Hello logger...")
        LOGGER.info("pyspark script logger initialized")
        doc_loader = Document_Loader(batch_size = 150)
                
        while doc_loader.load_next_batch():
            documents = doc_loader.get_batch()

            if not documents:
                break
            partition_num = 2
            doc_rdd = sc.parallelize(documents, partition_num)
            #print("Documents were loaded")
            LOGGER.info("Loaded Batch %d"%batch_no)
            #for doc in documents.values():
            #print(doc.doc_id)
            # extract features
            doc_rdd.flatMap(lambda x: x.get_all_edges()).saveAsTextFile('results_%sneg_mod/edges_%s'%(n_negative_instances,batch_no))

            #TODO write document edges
            
            feature_extractor = FeatureExtractor(n_negative_instances) 
            doc_rdd.map(feature_extractor.extract_features_for_document)\
                .flatMap(feature_extractor.extract_mention_pairs_with_features)\
                .flatMap(lambda x: [mp.get_as_csv_line().encode('utf-8') for mp in x])\
                .saveAsTextFile('results_%sneg_mod/output_%s'%(n_negative_instances,batch_no))
            
            '''
            #print("Feature Extraction Done") 
            doc_features_rdd  = doc_rdd.map(feature_extractor.extract_features_for_document)
            mention_pairs_features = doc_features_rdd.flatMap(feature_extractor.extract_mention_pairs_with_features)
            #print("mention pairs Created")
            mention_pairs_csv = mention_pairs_features.flatMap(lambda x: [mp.get_as_csv_line().encode('utf-8') for mp in x])
            mention_pairs_csv.saveAsTextFile('output_%s'%batch_no)'''

            batch_no = batch_no +1
            for log_msg in feature_extractor.logger:
                print(log_msg)
                LOGGER.info(log_msg)
#mention_pairs = mention_pairs_csv.collect()

#print ("mXId\tmTid\tdiff\tdiff_max\tdif_sum\tscale\tprec\tunit\tmod\ttokn\tnps\tsurfaceform\tGT")
                #print mention_pairs
                
                
                '''with codecs.open('output.csv','w','utf-8') as out:
            out.write("mXId\tmTid\tdiff\tdiff_max\tdif_sum\tscale\tprec\tunit\tmod\ttokn\tnps\tsurfaceform\tGT\n")
            for mention_list  in mention_pairs:
                for lin in mention_list:
                    out.write(lin)
            for mention_pair_list in mention_pairs:
                for mention_pair in mention_pair_list:
                    #if mention_pair.ground_truth:
                    out.write(mention_pair.get_as_csv_line().encode('utf-8')) #the line include a new line character
                    '''
                
            # done  
                #for log_msg in feature_extractor.logger:
                 #   LOGGER.info(log_msg)
    def __exit__(self, exc_type, exc_value, traceback):
        self.sc.stop()

def main():
    n_neg = 1
    if len(sys.argv) > 1:
        n_neg = int(sys.argv[1])
    else:
        n_neg = 5
    print("Generating mention-pairs with %s negative samples"%n_neg)
    
    with PipeLine() as pipeline:
        pipeline.start(n_neg)

if __name__ == '__main__':
    main()

