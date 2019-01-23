from table import Table
from mention import Mention
import nltk.data
import nltk
from sentence_processor import get_sentences_spans, extract_noun_phrases, get_tokens_and_filter_stop_words, get_tokens,extract_noun_phrases_no_stem 
import utils
from extractor import FeatureExtractor
import  re

class Document:

    approximation_kw = set(['about', 'approximately', 'around', 'roughly', 'nearly', 'close', 'almost', 'slightly' ])
    exact_kw = set(['exactly','exact', 'precisely','specifically', 'strictly','literally'])
    bounds_kw = set(['less', 'lower' 'most', 'below', 'under' ,'more','least','above', 'greater', 'higher' ])
    aggregate_kw = set (['total','overall','sum','average','decrease','increase','percent', 'percentage','difference','decreased','increased','up','down','-','+'])
    aggregate_kw_to_function ={'total':'sum','overall':'sum','sum':'sum','average':'avg','decrease':'rat','increase':'rat','percent':'percentage', 'percentage':'percentage','difference':'dif', 'decreased':'rat', 'increased':'rat','up':'rat', 'down':'rat','-':'rat','+':'rat'}
    MAX_TABLES = 10
    m_type =''
    def __init__(self, page_id, doc_id, text):
        self.page_id = page_id
        self.text = text
        self.doc_id = doc_id
        self.tables = [] # list of related tables
        self.mentions=[]
        self.sentences = {}
        self.ground_truth = {}
        self.all_ground_truth ={}
        self.mention_pairs = None
        self.classification_results = None
        self.sentences_span = None

    def set_classification_results(self, results):
        #print(results)
        self.classification_results  = results
    def get_classification_results(self):
        return self.classification_results 
    
    def set_mention_pairs(self, mention_pairs):
        self.mention_pairs = mention_pairs
    def get_mention_pairs(self):
        return self.mention_pairs

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
                edges.append([self.doc_id, m1,m2,proximity,surface_form_sim,final_diff])
        return edges
    def get_all_edges_as_csv_line(self):
        edges = self.get_all_edges()
        csv_lines = map(lambda l: '\t'.join(map(lambda x: str(x),l)) ,edges)
        return csv_lines

    def get_all_edges(self):
        edges= self.get_text_text_edge_list()
        for table in self.tables:
            edges.extend(table.get_table_table_edge_list(self.doc_id))
        return edges

    def __str__(self):
        doc_str = "page:%d\ndoc id:%d\n text:%s\n"%(self.page_id, self.doc_id , self.text)
        #for table in self.tables:
        #       doc_str = "%s \n table: %s "%(doc_str, str(table))
        for mention in self.mentions:
            doc_str = "%s \n  mention: %s "%(doc_str, str(mention))
        return doc_str
    def add_table(self, table_id, table_num, table_html, table_caption):
        #if len(self.tables) >= Document.MAX_TABLES:
        #    return # it did not work as it missed a lot of tables in the GT, most of the GT was 0!
        table = Table(table_id, table_num, table_html, table_caption)
        self.tables.append(table)
    def add_tables(self, tables_lst):
        self.tables = tables_lst

    #only numbers with decimal points for integers not truncation is possible
    def truncate_mention(self, mention):
        mod_mention = mention
        number_regex =r'\d+([, ]\d+)*(\.\d+)?'

        value = ''

        for match in re.finditer(number_regex, mention):
            value = match.group(0).strip()
            break

        if value:
            value_mod = value.replace(',','').replace(' ','')
            if '.' in value_mod :
                pos = value_mod.find('.')
                numbers_after_dec = len(value_mod) - pos -1
                if numbers_after_dec > 1:
                    #include only a single number after decimal point
                    value_mod = value_mod[:pos+2]
                else:
                    #remove the single number after decimal point
                    value_mod = value_mod[:pos]
                mod_mention  = mod_mention.replace(value,value_mod)
            elif len(value_mod) > 2: # for integers truncate half the numbers 
                n = len(value_mod)
                trunct_n = int(n/2)
                value_mod = value_mod[:-trunct_n] + '0' * trunct_n
                
                mod_mention  = mod_mention.replace(value,value_mod)

            #if does not contain any decimal point do nothing 

                    #print("modified mention %s"%mod_mention)
        return mod_mention

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
                value_mod = int(round(value_mod, -1 * round_n))
            mod_mention  = mod_mention.replace(value, str(value_mod))
        #print("modified mention %s"%mod_mention)
        return mod_mention
    def add_mentions(self, mentions_list):
        self.mentions = mentions_list
        self.mentions.sort(key= lambda x : x.start_offset)

    def get_local_relation_words(self):
        result =[]
        relations={}
        for mention in self.mentions:
            if mention.mention_id not in self.ground_truth:
                continue
            gt_relation = self.ground_truth[mention.mention_id]

            _,relation,_,_ = gt_relation[0]
            #print(relation)
            tokens, nps = self.get_mention_context(mention)
            
            if relation in relations:
                relations[relation].extend(tokens)
            else:
                relations[relation]= tokens

        for relation, tokens  in relations.items():
            result.append((relation, tokens))

        return result

    def get_global_relation_words(self):
        result =[]
        tokens, nps = self.get_document_context()
        relations={}
        for gt_relation in self.ground_truth.values():
            _,relation,_,_ = gt_relation[0]
            #print(relation)
            if relation in relations:
                continue
            relations[relation]=0
        for relation in relations.keys():
            result.append((relation, tokens))

        return result

    def add_mention(self, mention_id, mention, start_offset, end_offset):
            # mentions are ordered according to the start offset
        mention_mod = self.approximate_mention(mention)
        mention_trunc = self.truncate_mention(mention)

        #print(mention_mod)
        if Document.m_type == 'trunc':
            #print("TRUNC")
            mention_obj = Mention(mention_id, mention_trunc, start_offset,end_offset)
        elif Document.m_type == 'mod':
            mention_obj = Mention(mention_id, mention_mod, start_offset,end_offset)
            #print("MOD")
        else:
            mention_obj = Mention(mention_id, mention, start_offset,end_offset)
            #print("ORIG")

        self.mentions.append(mention_obj) # ordered list
    def add_ground_truth(self, mention_id, table_id, relation, related_cells, count):
        # Note that this function will add at most a single ground truth for each mention
        # It will prefer the aggregate mentions over the others
        # make sure in the mention-pair composition not to add the other GT mentions

        aggregates = set(["avg","dif","percentage","rat","sum"])
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
        self.sentences_span = sentences_span
        sent_indx =0
        curr_sentence = sentences_span[sent_indx]
        self.tokenize(curr_sentence)
        for mention in self.mentions:
            while mention.start_offset > curr_sentence[1] and sent_indx < len(sentences_span)-1:
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
        while sent_indx < len(sentences_span):
            self.tokenize(sentences_span[sent_indx])
            sent_indx = sent_indx +1
        
    def tokenize(self, sentence_span):
        #print("Tokenize sent %s, %s "%sentence_span)
        if sentence_span[0] in self.sentences:
            return

        # the tokens will include the mentions themselves and that's ok as it is used in the matching anyway!
        start,end = sentence_span
        sentence = self.text[start:end]
        #print(sentence_span, sentence)

        tokens, noun_phrases = extract_noun_phrases_no_stem(sentence)
        self.sentences[start] = (start,end,tokens,noun_phrases)
        #print(self.sentences[start])
        #print 'sentence %s, tokens %s, nps %s'%(repr(sentence), repr(tokens), repr(noun_phrases))

    def get_mention_modifiers(self, mention):
        start1,end1  = mention.sentence_span
        sentence = self.text[start1:end1]
        start_offset = mention.start_offset - start1
        end_offset = mention.end_offset - start1
        #print(start1, start_offset,end_offset)


        sentence_before = sentence[:start_offset]
        sentence_after = sentence[end_offset +1:]
        #print(sentence_before)
        #print(sentence_after)
        tokens_before = get_tokens(sentence_before) #get_tokens_and_filter_stop_words(sentence_before)
        tokens_after = get_tokens(sentence_after) #get_tokens_and_filter_stop_words(sentence_after)
        #print(tokens_before)
        #print(tokens_after)
        limit_before = min(5, len(tokens_before))
        limit_after = min (5, len(tokens_after))

        tokens_before = tokens_before[-limit_before:]
        tokens_after = tokens_after[:limit_after]
        #print(tokens_before)
        #print(tokens_after)


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
        #print("sentence span,", start1, end1)
        start,end, tokens, np = self.sentences[start1]
        if end1 != end:
            #print("different end",end)
                # get the following sentence
            start2 = end1
            start2,end2,tokens2,np2 = self.sentences[start2]
            end = end2
            tokens.extend(tokens2)
            np.extend(np2)
        #print 'mention: %s, tokens %s, nps %s'%(mention, tokens, np)
        #x = raw_input("Enter")
        #print(tokens, np)
        return tokens, np
    def get_document_context(self):
        all_tokens = []
        all_nps = []
        for start,end in self.sentences_span:
            _,_,tokens, nps = self.sentences[start]
            #print(start,end,tokens, nps)
            all_tokens.extend(tokens)
            all_nps.extend(nps)
        return all_tokens, all_nps

    def get_mention_scale_unit(self, mention):
        #TODO
            # check the word after the mention
        start1,end1  = mention.sentence_span
        sentence = self.text[start1:end1]
        #sentence = sentence.lower() no need to as the get_tokens will lower case all tokens 
        start_offset = mention.start_offset - start1
        end_offset = mention.end_offset - start1

        sentence_before = sentence[:start_offset]
        sentence_after = sentence[end_offset +1:]
        #print(sentence_before)
        #print(sentence_after)


        unit = None
        scale = 1
        tokens = get_tokens(sentence_after)

        #tokens = sentence_after.split(' ')
        tokens = tokens[:min(5, len(tokens))]
        #print(tokens)
        #tokens_before = sentence_before.split(' ')
        tokens_before = get_tokens(sentence_before)

        tokens_before = tokens_before[- min(5, len(tokens_before)):]
        
        #print(tokens_before)
        
        for word in tokens:
            if word in utils.scale_list:
                scale = utils.scale_list[word]
            if word in utils.unit_list:
                unit = utils.unit_list[word]
            if unit and scale:
                break
        if unit and scale:
            return scale,unit
        for word in reversed(tokens_before):
            if not word:
                continue
            if word in utils.scale_list:
                scale = utils.scale_list[word]
            if word in utils.unit_list:
                unit = utils.unit_list[word]

            if unit and scale:
                break
        return scale,unit
    def get_ground_truth_rel(self, mention):
        relation = None
        if mention.mention_id in self.ground_truth:
            _,relation,_,_ = self.ground_truth[mention.mention_id][0]


        return relation
    def is_gt_excluded(self, table_mention, mention):
        gt = self.get_ground_truth(mention.mention_id)
        all_gt = self.get_all_ground_truth(mention.mention_id)        

        if not gt:
            return False
        table_id,relation,cells,count = gt[0]
        if relation == 'same':# if the ground truth is not aggregate continue
            return False
        for table_id,relation, cells, count in all_gt:# if the gt is aggregate 
            # check if one of the other GT is same realtion and equal to the table mention
            if relation !='same':
                continue # do not check on other GT aggregates

            if table_id == table_mention.table_id and str(cells).strip(',') == str(table_mention.mention_id).strip(','):
                print("skip match in alternative GT", table_id,cells, str(table_mention))
                return True
        return False
        
    def get_exact_single_cell_match(self, mention):
        count =0 
        for table in self.tables:
            for table_mention in table.mentions.values():
                if self.is_gt_excluded(table_mention, mention):
                    continue
                #print("Comapre text and table mentions:", mention.surface_form, table_mention.surface_form)

                if utils.get_surfaceform_sim(mention.surface_form, table_mention.surface_form) > 0.90:
                    print("similar: ", mention.surface_form, table_mention.surface_form)
                    count +=1
        return count

        pass
    def get_mention_features_for_classification(self):
        lines = []

        for mention in self.mentions:
            ground_truth_rel = self.get_ground_truth_rel(mention)
            if not ground_truth_rel:
                ground_truth_rel ='None'

            exact_match_count = self.get_exact_single_cell_match(mention)
            print("exact match count %s"%(exact_match_count))

            #if ground_truth_rel == 'avg' or ground_truth_rel == 'same':
            #    ground_truth_rel = 'None'

            #if ground_truth_rel !='same':
            #    ground_truth_rel = 'aggr'

            line = mention.get_features_as_tsv(self.doc_id)
            if line:
                line = line + '\t'+ str(exact_match_count) + '\t' + ground_truth_rel
                lines.append(line)

        return lines


    def get_mention_measure(self, mention):
            #TODO
        pass


    def test_get_mention_modifiers(self, sentence, start_offset, end_offset):
        sentence_before = sentence[:start_offset]
        sentence_after = sentence[end_offset +1:]
        tokens_before = get_tokens(sentence_before) #get_tokens_and_filter_stop_words(sentence_before)
        tokens_after = get_tokens(sentence_after) #get_tokens_and_filter_stop_words(sentence_after)

        limit_before = min(5, len(tokens_before))
        limit_after = min (5, len(tokens_after))

        tokens_before = tokens_before[-limit_before:]
        tokens_after = tokens_after[:limit_after]

        #print(tokens_before)
        #print(tokens_after)

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
    #doc = Document(0,1,"But it is especially in the division of the non-textile industries that we find an enormous development of small factories. The 2,755,460 workpeople who are employed in all the non-textile branches with the exception of mining, are scattered in 79,059 factories, each of which has only an average of thirty-five workers. Moreover, the Factory Inspectors had on their lists 676,776 workpeople employed in 88,814 workshops (without mechanical power), which makes an average of eight persons only per workshop. These last figures are, however, as we saw, below the real ones, as another sixty thousand workshops occupying half a million more workpeople were not yet tabulated")

    #doc.add_mention(25, "676,776", 373,380)
    #doc.add_mention(26,"88,814", 404, 410)
     
     
    #doc = Document(1,1, u"""Distributable cash flow for the six months ended June 30, 2013 exceeded dividends by $51.6 million compared with $31.2 million for the six months ended June 30, 2012. The dividend payout ratio for the six months ended June 30, 2013 was 41% compared with 52% for the six months ended June 30, 2012. The increase in distributable cash flow and decrease in the dividend payout ratio are primarily due to a $22.2 million year over year increase in Adjusted EBITDA, a $1.7 million increase in share incentive compensation and a $2.6 million decrease in maintenance capital, partially offset by $3.5 million decrease in proceeds on disposals""")
    doc = Document(1,1,u"""On Census Night 7th August 2001, 5,911 people were counted in Fulham Gardens (State Suburbs): of these 49.2% were male and 50.8% were female. Of the total population 0.4% were Aboriginal and Torres Strait Islander people. I added new sentence with  Percent and Difference.""")

    doc.add_mention(10250,"0.4%",166,170)
    doc.add_table(202393,2, u"""<table>                                      <tr class="oddRow">    <th class="firstCol"><a href="/AUSSTATS/abs@.nsf/Previousproducts/B6615F8C5343B40ACA256B41007CC3D6?opendocument#Place%20of%20enumeration" class="dictionaryLink" title="Population is the count of people where they usually live." target="_blank">People</a></th>    <th class="geoCol">Fulham Gardens</th>    <th class="percentCol">%</th>    <th class="geoCol">Australia</th>    <th class="percentCol">%</th>                                     </tr>                                       <tr class="evenRow">    <td class="firstCol">Total</td>    <td>5,911</td>    <td><strong>--</strong></td>    <td>18,769,249</td>    <td><strong>--</strong></td>                                        </tr>                                       <tr class="oddRow">    <td class="firstCol">Male</td>    <td>2,907</td>    <td>49.2</td>    <td>9,270,466</td>    <td>49.4</td>                                     </tr>                                       <tr class="evenRow">    <td class="firstCol">Female</td>    <td>3,004</td>    <td>50.8</td>    <td>9,498,783</td>    <td>50.6</td>                                      </tr>                                       <tr class="oddRow">    <td class="firstCol" colspan="7">&#160;</td>                                     </tr>                                       <tr class="evenRow">    <td class="firstCol">Aboriginal and Torres Strait Islander people</td>    <td>23</td>    <td>0.4</td>    <td>410,003</td>    <td>2.2</td>                                       </tr>                                   </table>"""
    , "test")

    #doc.add_table(28, 3,"""<table>        <thead>        <tr>        <th>    1897                      </th>        <th>           Number of factories and workshops.     </th>        <th>           Number of operatives  of both sexes.     </th>        <th>        Average number   of operatives per  establishment.    </th>        </tr>        </thead>        <tfoot>        <tr>        <td>    Total...                 </td>        <td>      178,756                                    </td>        <td>           4,483,800                               </td>        <td>              25    </td>        </tr>        </tfoot>        <tbody>        <tr>        <td>    Textile factories..       </td>        <td>          10,883                                   </td>        <td>         1,051,564                                   </td>        <td>              97    </td>        </tr>        <tr>        <td>    Non-textile factories     </td>        <td>         79,059                                    </td>        <td>            2,755,460                                </td>        <td>             35    </td>        </tr>        <tr>        <td>    Various workshops.        </td>        <td>           88,814                                  </td>        <td>              676,776                                </td>        <td>                8    </td>        </tr>        </tbody>        </table>""", " Test Table")

    #print('2.3543',doc.truncate_mention('2.3543'))
    #print('2.3543 million$ 12', doc.truncate_mention('2.3543 million$ 12'))
    #print('2.1  Km', doc.truncate_mention('2.1  Km'))
    #print('500,893 cm per year', doc.truncate_mention('500,893 cm per year'))
    #print('$2.3', doc.truncate_mention('$2.3'))
    #print('km 2.33', doc.truncate_mention('km 2.33'))
    #print('$35,043',doc.truncate_mention('$35,043'))
    #print('$35,0',doc.truncate_mention('$35'))
    #print('$35',doc.truncate_mention('$35'))
    #print('$3',doc.truncate_mention('$3'))
    #print('$34563',doc.truncate_mention('$34563'))
    #print('$3456',doc.truncate_mention('$3456'))

    #print('$.94', doc.truncate_mention('$.94'))
    doc.add_ground_truth(10250, 202393, 'same', '2', 2)
    doc.add_ground_truth(10250, 202393, 'sum', '2,4', 2)

    #doc.add_ground_truth(8, 1, 'avg', '1,3,4', 2)
    #doc.add_ground_truth(9, 2, 'sum', '5,6', 2)
    #doc.add_ground_truth(9, 2, 'same', '7', 2)
    #doc.add_ground_truth(10, 3, 'same', '10', 2)
    #doc.add_ground_truth(10, 3, 'same', '9', 2)
    #doc.add_ground_truth(11, 4, 'same', '89', 2)
    feature_extractor = FeatureExtractor(5)
    feature_extractor.extract_features_for_document(doc)
    doc.get_mention_features_for_classification()
    
    print("relation and words:")
    print(doc.get_local_relation_words())
    feature_extractor.extract_mention_pairs_with_features(doc)
    results = map(lambda x: [mp.get_as_csv_line().encode('utf-8') for mp in x], doc.get_mention_pairs())
    for r in results:
        print(r)
    for mention in doc.mentions:
        print(mention.features)
        print(mention.get_features_as_tsv(doc.doc_id))


                                                                                 
    """   
    #print(doc.test_get_mention_modifiers("This +5% is a teste sentence decrease in last year 5% approximately increase!",6,8))
    #print(doc.test_get_mention_modifiers("Moreover, the Factory Inspectors had on their lists 676,776 workpeople employed in 88,814 workshops (without mechanical power), which makes an average of eight persons only per workshop.",83,89))
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
    """ 



if __name__ == '__main__':
    test()

