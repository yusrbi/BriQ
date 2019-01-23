# -*- coding: utf-8 -*-
import  sys
#import findspark
#findspark.init()

from pyspark import SparkContext, SparkConf
from loader import Document_Loader
from extractor import FeatureExtractor
import extractor
import codecs
from utils import read_file_as_list
from graph_algorithm import solve_document_rwr
from classifier import classify
from html_page import HtmlPage

class PipeLine:
    def __init__(self, files_list):
        #TODO remover the setMaster, when running on the cluster
        self.list_of_files = read_file_as_list(files_list)
        self.conf = SparkConf().setAppName("TableCRR")#.setMaster('local')
        self.sc = SparkContext(conf=self.conf)
    def __enter__(self):
        return self
    def start(self):
        # spark context
        sc = self.sc
        # load documents
        batch_no =1
        n_negative_instances=5
        
        doc_loader = Document_Loader( 200, self.list_of_files)
        feature_extractor = FeatureExtractor(n_negative_instances)

        while doc_loader.load_next_json_objects_by_page():#doc_loader.load_next_josn_objects_batch():
            print("Loaded new batch")

            json_objects = doc_loader.get_json_objects()
            partition_num = 200
            
            
            json_objects_rdd = sc.parallelize(json_objects, partition_num)
            print("parallelize json objects")
            
            json_objects_rdd.map(lambda json_obj: HtmlPage(json_obj['fullText'],-1))\
                .flatMap(lambda html_pg: html_pg.create_documents())\
                .map(feature_extractor.extract_features_for_document)\
                .map(feature_extractor.extract_mention_pairs_with_features)\
                .map(classify)\
                .map(solve_document_rwr).collect()

            batch_no = batch_no +1

            #documents = doc_loader.get_batch()

            #partition_num = 2
            #doc_rdd = sc.parallelize(documents, partition_num)
            #print("Documents were loaded")
            #LOGGER.info("Loaded Batch %d"%batch_no)
            #for doc in documents.values():
            #print(doc.doc_id)
            # extract features
            #doc_rdd.flatMap(lambda x: x.get_all_edges()).saveAsTextFile('results_%sneg_mod/edges_%s'%(n_negative_instances,batch_no))
            #print("Documnets are saved")
            #TODO write document edges

            #doc_rdd.map(feature_extractor.extract_features_for_document)\
            #    .flatMap(feature_extractor.extract_mention_pairs_with_features)
                #.flatMap(lambda x: [mp.get_as_csv_line().encode('utf-8') for mp in x])\
                #.saveAsTextFile('results_%sneg_mod/output_%s'%(n_negative_instances,batch_no))

            #doc_rdd.map(classify)

            #doc_rdd.map(solve_document_rwr)

            #Then save the documents


           

    def __exit__(self, exc_type, exc_value, traceback):
        self.sc.stop()

def main():
    n_neg = 1
    if len(sys.argv) > 1:
        input_path  = sys.argv[1]
    else:
        print("Please provide input Folder!")
        return 

    print("processing data in folder %s"%input_path)

    with PipeLine(input_path) as pipeline:
        pipeline.start()

if __name__ == '__main__':
    main()
