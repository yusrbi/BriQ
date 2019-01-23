# For extracting mentions I need the following
# dictionary for units/measures 
# -*- coding: utf-8 -*-
from mention_pair import MentionPair
import utils
import logging


logging.basicConfig(filename='log_fin.log', level=logging.INFO)
#logging.basicConfig(format="%(asctime)s %(message)s")
logging.info("init is done")

class FeatureExtractor:
        
        approximation_kw = set(['about', 'approximately', 'around', 'roughly', 'nearly', 'close to', 'almost', 'slightly' ])
        exact_kw = set(['exactly','exact', 'precisely','specifically', 'strictly','literally'])
        bounds_kw = set(['less than', 'lower than' 'at most', 'below', 'under' ,'more than','at least','above', 'greater than', 'higher than' ])
        def __init__(self, num_neg_instances):
            self.load_units()
            self.load_measures()
            self.load_scale()
            self.logger =[] 
            self.n_neg_instances = num_neg_instances


        def load_units(self):
            pass
        def load_measures(self):
            pass
        def load_scale(self):
            pass

        def add_mention_pair_to_list(self,mention_pair_list,  mention_pair, k, eta): 
            if eta !=0:
                if mention_pair.get_approx_sim() >= eta: #the sim might be -ve as of the value diff!
                    mention_pair_list.append(mention_pair)
            else: #add the emntion
                mention_pair_list.append(mention_pair)

            ground_truth_count =0
            if k != 0 and len(mention_pair_list)> k+1: #add one for the ground truth
                min_sim = 100000
                min_indx = -1
                # get the max value and index
                for i in range(len(mention_pair_list)):
                    item = mention_pair_list[i]

                    if item.ground_truth == True:
                        ground_truth_count = ground_truth_count +1
                        continue
                    sim = item.get_approx_sim()
                    if sim < min_sim:
                        min_sim = sim
                        min_indx = i
            
                if (len(mention_pair_list) - ground_truth_count) > k:
                    del mention_pair_list[min_indx]



            return mention_pair_list


        def extract_mention_pairs_with_features(self, document):
		# extract mention pairs for the final stage of training 
		# the mentions ids are important for the evaluation 
                mention_pairs = {}
                max_negative_pair = self.n_neg_instances 
                eta = 0

                
                logging.info("Extracting Mention Pairs for Document: %s"%document.doc_id)
                print("Extracting Mention Pairs for Document: %s"%document.doc_id)

                self.logger.append("Extracting Mention Pairs for Document: %s"%document.doc_id)
                for mention in document.mentions:
                        mention_gt = document.get_ground_truth(mention.mention_id)
                        if mention.mention_id in mention_pairs:
                            mention_pair_list = mention_pairs[mention.mention_id]
                        else:
                            #init the list with the ground truth mention --> should be one!
                            #TODO Pick one --> Done in the document add_ground_truth

                            mention_pair_list = []
                            for gt in mention_gt:
                                table_mention  = document.get_table_mention_for_gt(gt)
                                if table_mention:
                                    mention_pair = MentionPair(document.doc_id,mention,table_mention)
                                    mention_pair.set_ground_truth(True)
                                    mention_pair_list.append( mention_pair) # append directly
                                else:
                                    print("Error: Could not find %s,%s,%s,%s"%gt)

                                    logging.info("Error: Could not find %s,%s,%s,%s"%gt)
                                    self.logger.append("Error: Could not find %s,%s,%s,%s"%gt)

                        #if mention.mention_id == 1093604:
                            #print("Text Mention %s" %( mention.features['global_context_noun_phrases']))

                        # now load all the ground truth
                        mention_all_gt = document.get_all_ground_truth(mention.mention_id)

                        for table in document.tables:
                                #print("Table:%s"%table.table_id)
				for table_mention in table.get_mentions():
                                        #print mention, table_mention
					mention_pair = MentionPair(document.doc_id,mention, table_mention)
			                #if table.table_id ==1503604 and mention.mention_id == 1093604:
                                            #print ("table mention %s"%(table_mention.features['global_context_noun_phrases']))
                                        
                                        ground_truth = False
                                        for gt in mention_all_gt:
                                            table_id_gt,relation,related_cells,_ = gt
                                             #check on the ground truth
                                            if table_id_gt == table.table_id and utils.is_equal_cells(related_cells, str(table_mention.mention_id)) and relation == table_mention.get_relation_name():
                                                ground_truth = True
                                                break
                                        if not ground_truth:#TODO check/test
                                            #if it was one of the ground truth then it should have been added already
                                            mention_pair.set_ground_truth (ground_truth)
                                            mention_pair_list = self.add_mention_pair_to_list(mention_pair_list, mention_pair, max_negative_pair,eta)

                                #done for this mention
                        mention_pairs[mention.mention_id] = mention_pair_list



			'''if mention_pair.is_potential_mention_pair():
                                                #if table.table_id ==1503604 and mention.mention_id == 1093604:
                                                    #print ("table mention %s"%str(table_mention))
                                                    #print("Match Sim : %s"% mention_pair.get_approx_sim())

                                                # add the ground truth to it if it is a match or not
                                                for gt in mention_gt:
                                                    table_id_gt,relation,related_cells,exact,_ = gt
                                                    #check on the ground truth
                                                    if table_id_gt == table.table_id and utils.is_equal_cells(related_cells, str(table_mention.mention_id)) and relation == table_mention.get_relation_name():
                                                            ground_truth = True
                                                            break
                                                     
                                                mention_pair.set_ground_truth (ground_truth)
                                                if mention.mention_id in mention_pairs:
                                                    mention_pair_list = mention_pairs[mention.mention_id]
                                                else:
                                                    mention_pair_list = []

                                                mention_pair_list = self.add_mention_pair_to_list(mention_pair_list, mention_pair, max_negative_pair)
                                                mention_pairs[mention.mention_id] = mention_pair_list'''


                                        #elif table.table_id ==1503604 and mention.mention_id == 1093604:
                                            #print ("table mention %s"%str(table_mention))
                                            #print("No Match: sim : %s"% mention_pair.get_approx_sim())


                #TODO get the mention pairs edges 
                document.tables = None
                document.mentions = None
                logging.info("Done Extracting Mention Pairs for document: %s"%document.doc_id)
                print("Done Extracting Mention Pairs for document: %s"%document.doc_id)

                self.logger.append("Done Extracting Mention Pairs for document: %s"%document.doc_id)
		return mention_pairs.values()

	def extract_features_for_document(self, document):
		# extract features for document
                #init the context of mentions in the document #very IM
                print("Start Extracting features for Document %s"% document.doc_id)
                document.process_mention_context()
                all_doc_tokens, all_doc_nps = document.get_document_context()
		for mention in document.mentions:
			features = self.extract_features_for_text_mentions(mention, document, all_doc_tokens, all_doc_nps)
			mention.set_features(features)
		for table in document.tables:
                        table_tokens, table_np = table.get_context_table()
			mentions = table.get_mentions()
			for mention in mentions:
				features = self.extract_features_for_table_mentions(mention, table,table_tokens, table_np)
				mention.set_features(features)
		return document

	def extract_features_for_text_mentions(self,mention, doc,all_doc_tokens, all_doc_nps):
		features ={}
		# get the mention scale
		# to get the mention scale we need to look at the quantity and the words surrounding it 
		# the mention class should have the mention position in text.
		# the text document should be divided into sentences and each one with a set of words 
		# the list of units should be the basic units plus some frequently used units of measurements 
		        
                unit = None
                scale = None
                if mention.has_unit():
                        # if mention has the unit info then ignore the sentence 
			unit = mention.unit
                else:
                        scale,unit  =  doc.get_mention_scale_unit(mention)
                
                features['unit'] = unit 
                if unit is '%':
                    scale = None
                # be default set the scale and unit to those extracted from the mention's sentence 
                else:
                    if mention.has_scale():
                        # if the mention has the scale info then ignore the sentence
			scale = mention.scale
                
                    if not scale:
                        scale,unit  =  doc.get_mention_scale_unit(mention)
                
                features['scale']=scale
		# get the mention unit
                
		
		
		# get the measure of the mention syntactically
		if mention.has_measure():
			measure = mention.measure
		else:
			measure = doc.get_mention_measure(mention)
		features['measure'] = measure  
		# get the absolute value
		features['absolute_value'] = mention.absolute_value
		# get the surface from 
		features['surface_form'] = mention.surface_form 
		features['precision'] = mention.precision 
		features['modifiers'] = doc.get_mention_modifiers(mention)
		tokens, np = doc.get_mention_context(mention)
                features['context_tokens'] = tokens
		features['context_noun_phrases'] = np 
                features['global_context_tokens'] = all_doc_tokens
                features['global_context_noun_phrases'] = all_doc_nps
                features['aggregate_function'] = mention.get_aggregate_function()
                # TODO extract words and noun phrases for each mention 
#                print(features) 

		return features	
	
	def extract_features_for_table_mentions(self, mention, table, table_tokens, table_np):
		features={}
		# get mention scale
                # get mention unit
		if mention.has_unit():
			unit = mention.unit 
		else:
			unit = table.get_mention_unit(mention)
		features['unit'] = unit 
                if unit is '%':
                    scale = None
                else:
                    if mention.has_scale():
			scale  = mention.scale
		    else :
			scale = table.get_mention_scale(mention)
		features['scale'] =scale

		
		# get mention measure
		if mention.has_measure():
			measure = mention.measure
		else:
			measure = table.get_mention_measure(mention)
		features['measure'] = measure
		# get mention absolute value
		features['absolute_value'] = mention.absolute_value
		# get the surface form of a mention 
		features['surface_form'] = mention.surface_form
		
		features['precision'] = mention.precision 
		
                features['context_tokens'] = table.get_mention_context_words(mention)
		features['context_noun_phrases'] = table.get_mention_noun_phrases(mention)
                features['global_context_tokens'] = table_tokens
                features['global_context_noun_phrases'] = table_np
		features['modifiers'] = table.get_mention_modifiers(mention)
		features['aggregate_function'] = mention.get_aggregate_function()

		return features  


def test():
    extractor = FeatureExtractor()
    
    mp1 = MentionPair(-1,None,None, 0.1,0.5)
    mp2 = MentionPair(-1, None, None, 0.2,0.1)
    mp3 = MentionPair(-1,None, None, 0.6, 0.3)
    mp4 = MentionPair(-1, None, None, 0.9,0.01)

    mp5 = MentionPair(-1, None, None, 0.5,0.4)

    mp5.ground_truth = True
    mp2.ground_truth = True    
    mp_lst = []
    k = 0 
    eta = 0.3
    mp_lst = extractor.add_mention_pair_to_list(mp_lst, mp1, k,eta)
    mp_lst = extractor.add_mention_pair_to_list(mp_lst, mp2, k,eta)
    mp_lst = extractor.add_mention_pair_to_list(mp_lst, mp4, k,eta)

      
    print ','.join([str(item) for item in mp_lst])
    mp_lst = extractor.add_mention_pair_to_list(mp_lst, mp3, k,eta)
    print ','.join([str(item) for item in mp_lst])
    mp_lst = extractor.add_mention_pair_to_list(mp_lst, mp5, k,eta)
    print ','.join([str(item) for item in mp_lst])


if __name__ =='__main__':
    test()
