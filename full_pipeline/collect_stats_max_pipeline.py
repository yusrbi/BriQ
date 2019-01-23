# -*- coding: utf-8 -*-
import  sys
#import findspark
#findspark.init()

from pyspark import SparkContext, SparkConf
from loader import Document_Loader
import extractor
import codecs
from utils import read_file_as_list
from graph_algorithm import solve_document_rwr
from classifier import classify
from html_page import HtmlPage
from statcollector import StatCollector
class PipeLine:
    def __init__(self, files_list):
        #TODO remover the setMaster, when running on the cluster
        self.list_of_files = read_file_as_list(files_list)
        self.conf = SparkConf().setAppName("Collect Stats Maximum Counts")#.setMaster('local')
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
        stat_collector = StatCollector()
        accum = {}
        old_stats = None
        while doc_loader.load_next_json_objects_by_page():#doc_loader.load_next_josn_objects_batch():
            print("Loaded new batch")

            json_objects = doc_loader.get_json_objects()
            partition_num = 200            
            
            json_objects_rdd = sc.parallelize(json_objects, partition_num)
            print("parallelize json objects")
        
            stats = json_objects_rdd.map(lambda json_obj: HtmlPage(json_obj['fullText'],-1))\
                .flatMap(stat_collector.get_counts)\
                .reduceByKey(lambda a,b: max(a,b))\
                .collectAsMap()
            
            if old_stats:
                print("Join!")
                for key in stats.keys():
                    old_stats[key] = max(old_stats[key], stats[key])
                #old_stats = old_stats.union(stats)\
                #        .reduceByKey(lambda a,b: max(a,b))\
                #        .collectAsMap()


            else:
                print("Assign New")
                old_stats = stats

            #print("This Batch Counst:")
            #print(stats)
            #if not accum:
            #    accum = stats
            #else:
            #    for key,value in stats.items():
            #        accum[key] = accum[key] + value



            #print("Counts So Far")
            #print(accum)
            batch_no = batch_no +1


        results = old_stats
        print("results is:")

        print(results)
        #print(accum)
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
