from table import Table
from mention import Mention
import nltk.data 
import nltk 
from sentence_processor import get_sentences_spans, extract_noun_phrases, fast_extract_noun_phrases , get_tokens_and_filter_stop_words
import utils
from sets import Set
import  re

class Document:
        
        approximation_kw = set(['about', 'approximately', 'around', 'roughly', 'nearly', 'close to', 'almost', 'slightly' ])
        exact_kw = set(['exactly','exact', 'precisely','specifically', 'strictly','literally'])
        bounds_kw = set(['less than', 'lower than' 'at most', 'below', 'under' ,'more than','at least','above', 'greater than', 'higher than' ])
        aggregate_kw = set (['total','overall','sum','average','decrease','increase','percent', 'percentage','difference','decreased','increased','up','down','-','+'])
        aggregate_kw_to_function ={'total':'sum','overall':'sum','sum':'sum','average':'avg','decrease':'rat','increase':'rat','percent':'percentage', 'percentage':'percentage','difference':'dif', 'decreased':'rat', 'increased':'rat','up':'rat', 'down':'rat','-':'rat','+':'rat'}
        MAX_TABLES = 10
	def __init__(self, page_id, doc_id, text):
		self.page_id = page_id
		self.text = text
		self.doc_id = doc_id 
		self.tables = [] # list of related tables 
		self.mentions=[]
		self.sentences = {}
                self.ground_truth = {}
                self.all_ground_truth ={}

        def get_text_text_edge_list(self):
            edges =[]
            text_size = len(self.text)
            total_distance = [0 for i in range(len(self.mentions))]

            for i in range(len(self.mentions)):
                for j in range(i+1,len(self.mentions)):
                    mention1 = self.mentions[i]
                    mention2 = self.mentions[j]
                    distance = float(abs(mention1.start_offset - mention2.start_offset))/5.0 # 5 is the average word length
                    total_distance[i] = total_distance[i] + distance

            normalization_factor = total_distance
            for i  in range(len(self.mentions)):
                for j in range(i+1, len(self.mentions)):
                    m1 = self.mentions[i].get_full_id()
                    m2 = self.mentions[j].get_full_id()
                    mention1 = self.mentions[i]
                    mention2 = self.mentions[j]
                    distance = float(abs(mention1.start_offset - mention2.start_offset))/5.0 # 5 is the average word length 

                    #distance = distance/total_distance[i]  # do not do this as in case of 2 mentions the distnace is 1 and proximity is 0
                    proximity = 1/distance # use the inverse of the distnace, dont use the text length as the value will be more than one
                    # compute the surface form and the value similarity for the graph and ILP 
                    surface_form_sim = utils.get_surfaceform_sim(mention1.surface_form, mention2.surface_form)
                    val_diff = abs(mention1.get_value()-mention2.get_value())
                    max_val = abs(max(mention1.get_value(),mention2.get_value()))
                    if max_val != 0:
                        val_diff = val_diff/max_val
                    val_diff_no_scale = abs(mention1.get_value_without_scale()- mention2.get_value_without_scale())
                    max_no_scale = abs(max(mention1.get_value_without_scale(), mention2.get_value_without_scale()))
                    if max_no_scale !=0:
                        val_diff_no_scale = val_diff_no_scale / max_no_scale

                    final_diff = (val_diff + val_diff_no_scale)/2 # take the average of the two values 
                    edges.append("%s\t%s\t%s\t%s\t%s\t%s\n"%(self.doc_id, m1,m2,proximity,surface_form_sim,final_diff))
            return edges
        def get_all_edges(self):
            edges= self.get_text_text_edge_list()
            for table in self.tables:
                edges.extend(table.get_table_table_edge_list(self.doc_id))
            return edges 

	def __str__(self):
		doc_str = "page:%d\ndoc id:%d\n text:%s\n"%(self.page_id, self.doc_id , self.text)
		#for table in self.tables:
		#	doc_str = "%s \n table: %s "%(doc_str, str(table))
		for mention in self.mentions:
			doc_str = "%s \n  mention: %s "%(doc_str, str(mention))
		return doc_str
	def add_table(self, table_id, table_num, table_html, table_caption):
                #if len(self.tables) >= Document.MAX_TABLES:
                #    return # it did not work as it missed a lot of tables in the GT, most of the GT was 0!
		table = Table(table_id, table_num, table_html, table_caption)
		self.tables.append(table)
        def approximate_mention(self, mention):
            #print("orig mention %s"%mention)
            mod_mention = mention
            number_regex =r'\d+([, ]\d+)*(\.\d+)?'
            
            value = ''

            for match in re.finditer(number_regex, mention):
                value = match.group(0).strip()
                break

            if value:
                value_mod = value.replace(',','').replace(' ','')
                if '.' in value_mod :
                    value_mod = float(value_mod)
                    value_mod = round(value_mod, 0)
                else:
                    n = len(value_mod)#number of digits
                    value_mod = float(value_mod)
                    round_n = int(n/2)
                    value_mod = round(value_mod, -1 * round_n)
                mod_mention  = mod_mention.replace(value, str(value_mod))
            #print("modified mention %s"%mod_mention)
            return mod_mention
	def add_mention(self, mention_id, mention, start_offset, end_offset):
		# mentions are ordered according to the start offset
		mention_mod = self.approximate_mention(mention)
                mention = Mention(mention_id, mention_mod, start_offset,end_offset)
		self.mentions.append(mention) # ordered list 
        def add_ground_truth(self, mention_id, table_id, relation, related_cells, count):
            # Note that this function will add at most a single ground truth for each mention
            # It will prefer the aggregate mentions over the others
            # make sure in the mention-pair composition not to add the other GT mentions 

            aggregates = Set(["avg","dif","percentage","rat","sum"])
            mention_gt = []
            if mention_id in self.ground_truth:
                mention_gt = self.ground_truth[mention_id]

            #print ("before%s"%mention_gt)
            if len(mention_gt) >=1:
                _,old_relation,_,_ = mention_gt[0]
                if old_relation =='same' and relation in aggregates:
                    mention_gt[0] = (table_id,relation,related_cells, count)
                
                else:
                    #do nothing in all other cases, keep the aggregate relation 
                    pass
            else:
                mention_gt.append((table_id,relation,related_cells, count))

            #print("sim =%s"%mention_pair.get_approx_sim())
            #print mention_gt
            self.ground_truth[mention_id]= mention_gt

            #Now add to all_ground_truth
            mention_gt =[]
            if mention_id in self.all_ground_truth:
                mention_gt = self.all_ground_truth[mention_id]
            mention_gt.append((table_id,relation,related_cells, count))
            self.all_ground_truth[mention_id] = mention_gt


        def get_ground_truth(self, mention_id):
            # this will return a single ground truth for evaluation

            if mention_id in self.ground_truth:
                return self.ground_truth[mention_id]
            else:
                return []
        def get_all_ground_truth(self, mention_id):
            # this will return a list of all GT
            if mention_id in self.all_ground_truth:
                return self.all_ground_truth[mention_id] 
            else:
                return []
        def get_table_mention_for_gt(self, gt):
            table_id,relation,related_cells,_ = gt
            target_table = None

            for table in self.tables:
                if table_id == table.table_id:
                    target_table = table
                    break
            if not target_table:
                print("Table Not Found! %d"%table_id)
                return None #TODO this should never be!
            cells= related_cells
            if cells[-1] == ',':
                cells = cells[:-1]
            mention = None
            if relation =='same':
                print("relation is same %s"%relation)
                #single cell
                cell = int(cells)
                if cell in target_table.mentions:
                    mention = target_table.mentions[cell]

            else:
                print("relation is aggreagte %s"%relation)
                #aggregate mention
                if cells not in target_table.aggregate_mentions:
                    cells = utils.sort_cells(cells)
                    print("cells sorted %s"%cells)
                if cells in target_table.aggregate_mentions:
                    aggregates = target_table.aggregate_mentions[cells]
                    for aggregate_mention in aggregates:
                        if aggregate_mention.get_relation_name() == relation:
                            mention = aggregate_mention
                            break
                    if not mention:
                        print("relation not found in aggr. %s"%relation)

            return mention # it can be None if the cell is not detected as a quantity!

                

        def process_mention_context(self):
		# extract the sentences in the text 
		sentences_span = get_sentences_spans(self.text)
		sent_indx =0
		curr_sentence = sentences_span[sent_indx]
		self.tokenize(curr_sentence)
		for mention in self.mentions:
			if mention.start_offset > curr_sentence[1]:
				sent_indx = sent_indx +1
				curr_sentence = sentences_span[sent_indx]
				self.tokenize(curr_sentence)
			# get the words of the sentence 
			if mention.end_offset <= curr_sentence[1]:
				mention.set_sentence_span(curr_sentence)
			else:
                                #print mention
                                #print self.text
                                #print curr_sentence

				next_sentence = sentences_span[sent_indx +1]
                                self.tokenize(next_sentence)
				mention.set_sentence_span([curr_sentence[0], next_sentence[0]]) 
                                # store the start point of the two sentences as the end is already stored in the self.sentences map 

				# it is very unlikely that a mention spans 2 sentences 
				#and it is rare to span more than two sentences
                self.tokenize(curr_sentence)

	def tokenize(self, sentence_span):
		if sentence_span[0] in self.sentences:
			return 
		
		# the tokens will include the mentions themselves and that's ok as it is used in the matching anyway!
		start,end = sentence_span 
		sentence = self.text[start:end]
		tokens, noun_phrases = extract_noun_phrases(sentence)
	        self.sentences[start] = (start,end,tokens,noun_phrases)
                #print 'sentence %s, tokens %s, nps %s'%(repr(sentence), repr(tokens), repr(noun_phrases))

	def get_mention_modifiers(self, mention):
	    start1,end1  = mention.sentence_span
            sentence = self.text[start1:end1]
            sentence_before = sentence[:mention.start_offset] 
            sentence_after = sentence[mention.end_offset +1:]
            tokens_before = get_tokens_and_filter_stop_words(sentence_before)
            tokens_after = get_tokens_and_filter_stop_words(sentence_after)            
            limit_before = min(5, len(tokens_before))
            limit_after = min (5, len(tokens_after))
            
            tokens_before = tokens_before[-limit_before:]
            tokens_after = tokens_after[:limit_after]
            
            modifier = None
            aggregate = None
            for word in tokens_before:  #reversed(sentence_before.split(' '))
                if not modifier and word in Document.approximation_kw:
                    modifier = 'approx'
                elif not modifier and word in Document.exact_kw:
                    modifier = 'exact'
                elif not modifier and word in Document.bounds_kw:
                    modifier = 'bound'
                elif not aggregate and word in Document.aggregate_kw:
                    aggregate = word 

            for word in tokens_after:
                if not modifier and word in Document.approximation_kw:
                    modifier = 'approx'
                elif not modifier and word in Document.exact_kw:
                    modifier = 'exact'
                elif not modifier and word in Document.bounds_kw:
                    modifier = 'bound'
                elif not aggregate and word in Document.aggregate_kw:
                    aggregate = word 

            if aggregate:
                mention.set_aggregate_kw(Document.aggregate_kw_to_function[aggregate])

            return modifier

	def get_mention_context(self, mention):
	# we need to process the text sentnece by sentence and keep track of the sentence corresponding to each mention 
                start1,end1  = mention.sentence_span
                start,end, tokens, np = self.sentences[start1]
                if end1 != end:
                    # get the following sentence 
                        start2 = end1
                        start2,end2,tokens2,np2 = self.sentences[start2]
                        end = end2
                        tokens = tokens.union(tokens2)
                        np = np.union(np2)
                #print 'mention: %s, tokens %s, nps %s'%(mention, tokens, np)
                #x = raw_input("Enter")

                return tokens, np
        def get_document_context(self):
            all_tokens = Set([])
            all_nps = Set([])
            for start,end,tokens, nps in self.sentences.values():
                all_tokens = all_tokens.union(tokens)
                all_nps = all_nps.union(nps)
            return all_tokens, all_nps

	def get_mention_scale_unit(self, mention):
		#TODO
                # check the word after the mention
            start1,end1  = mention.sentence_span
            sentence = self.text[start1:end1]
            sentence_before = sentence[start1:mention.start_offset] 
            sentence_after = sentence[mention.end_offset +1:]
            unit = None
            scale = None
            for word in sentence_after.split(' '):
                if word in utils.scale_list:
                    scale = utils.scale_list[word]
                if word in utils.unit_list:
                    unit = word
                if unit and scale:
                    break
            return scale,unit

	def get_mention_measure(self, mention):
		#TODO
		pass


	def test_get_mention_modifiers(self, sentence, start_offset, end_offset):
            sentence_before = sentence[:start_offset] 
            sentence_after = sentence[end_offset +1:]
            tokens_before = get_tokens_and_filter_stop_words(sentence_before)
            tokens_after = get_tokens_and_filter_stop_words(sentence_after)
            
            limit_before = min(5, len(tokens_before))
            limit_after = min (5, len(tokens_after))
            
            tokens_before = tokens_before[-limit_before:]
            tokens_after = tokens_after[:limit_after]
            
            print(tokens_before)
            print(tokens_after)

            modifier = None
            aggregate = None
            for word in reversed(tokens_before):  #reversed(sentence_before.split(' '))
                if not modifier and word in Document.approximation_kw:
                    modifier = 'approx'
                elif not modifier and word in Document.exact_kw:
                    modifier = 'exact'
                elif not modifier and word in Document.bounds_kw:
                    modifier = 'bound'
                elif not aggregate and word in Document.aggregate_kw:
                    aggregate = word 

            for word in tokens_after:
                if not modifier and word in Document.approximation_kw:
                    modifier = 'approx'
                elif not modifier and word in Document.exact_kw:
                    modifier = 'exact'
                elif not modifier and word in Document.bounds_kw:
                    modifier = 'bound'
                elif not aggregate and word in Document.aggregate_kw:
                    aggregate = word 

            #mention.set_aggregate_kw(Document.aggregate_kw_to_function[aggregate])

            return modifier, aggregate



def test():
    doc = Document(0,1,"Test document to make sure that the ground truth is added corectly")
    print(doc.test_get_mention_modifiers("This +5% is a teste sentence decrease in last year 5% approximately increase!",6,8))

    doc.add_ground_truth(8, 1, 'same', '1', 2)
    doc.add_ground_truth(8, 1, 'avg', '1,3,4', 2)
    doc.add_ground_truth(9, 2, 'sum', '5,6', 2)
    doc.add_ground_truth(9, 2, 'same', '7', 2)
    doc.add_ground_truth(10, 3, 'same', '10', 2)
    doc.add_ground_truth(10, 3, 'same', '9', 2)
    print(doc.get_ground_truth(8))
    print(doc.get_all_ground_truth(8))
    print(doc.get_ground_truth(9))
    print(doc.get_all_ground_truth(9))
    print(doc.get_ground_truth(10))
    print(doc.get_all_ground_truth(10))
    print(doc.approximate_mention("15 million"))
    print(doc.approximate_mention("123.784784 km/hr"))
    print(doc.approximate_mention("289.231 per 100 km hr"))
    print(doc.approximate_mention("1.893"))
    print(doc.approximate_mention("1525,922 million"))
    print(doc.approximate_mention("1"))
    print(doc.approximate_mention("12"))
    print(doc.approximate_mention("119"))
    print(doc.approximate_mention("15683"))
    print(doc.approximate_mention("1763267"))





#test()


