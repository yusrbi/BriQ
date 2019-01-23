import regex as re
import utils
class Mention:
    def __init__(self, mention_id,mention,start_offset, end_offset):

        mention = mention.lower()
        mention = re.sub('\s+',' ', mention)
        if mention[0] == '.':
            mention = '0' + mention 
        self.mention_id = mention_id
#                self.document_id = document_id
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.surface_form = mention
        self.aggregate_kw = None
        self.absolute_value = None
        self.measure = None
        self.precision = 0.0
        self.negative_sign = False
        scale,unit = utils.get_scale_unit(mention)
        self.unit = unit
        self.scale = scale
        self.init_measure(mention)
        self.init_absolute_value(mention)
        self.init_precision(mention)
        self.aggregated_mentions_unit = None
        self.aggregated_cells = None
        self.aggregate_function = None
        self.sentence_span = None
        self.aggregate_kw = None
        self.table_id = None
        self.features = None
        self.aggregate_inverse= None
        self.aggregate_inverse_surfaceform = None
        self.max_relative_difference = 0.0
        self.max_no_scale_difference = 0.0  
        self.max_ltokens_sim = 0.0
        self.max_gtokens_sim = 0.0

    def update_max_ltokens_sim(self, val):
        if self.max_ltokens_sim < val:
            self.max_ltokens_sim = val
    
    def update_max_gtokens_sim(self,val):
        if self.max_gtokens_sim <val:
            self.max_gtokens_sim = val
    
    def get_max_ltokens_sim(self):
        if self.max_ltokens_sim !=0:
            return self.max_ltokens_sim
        else:
            return 1
    
    def get_max_gtokens_sim(self):
        if self.max_gtokens_sim !=0:
            return self.max_gtokens_sim
        else:
            return 1


    def get_sentence_start_offset(self):
        if self.sentence_span:
            return self.start_offset - self.sentence_span[0]  
        else:
            return self.start_offset

    def set_max_relative_difference(self, value):
        if value !=0:
            self.max_relative_difference = value
        else:
            self.max_relative_difference = 1.0
    def set_max_no_scale_difference(self, value):
        if value != 0:
            self.max_no_scale_difference = value
        else:
            self.max_no_scale_difference = 1.0



    def get_relation_name(self): # this method is used to check against the GT
        if self.aggregate_function:
            return self.aggregate_function
        else:
            return 'same'

    def __str__(self):
        mention_str = "(id:%s, mention: %s,strat:%d,end: %d)"%(self.mention_id,self.surface_form, self.start_offset, self.end_offset)
        return mention_str
    def get_full_id(self):
        id_ = str(self.mention_id)

        if self.table_id:
            id_= "%s.%s"%(self.table_id,id_)
        if self.aggregate_function:
            id_ = "%s.%s"%(id_, self.aggregate_function)

        return id_ #TODO add pageid,  document id, tableid
    def set_features(self, features):
        self.features = features
    def get_features(self, features):
        return self.features
    def set_table_id(self, table_id):
        self.table_id = table_id

    def init_unit(self, mention):
        if '%' in  mention:
            self.unit ='%'
        elif '$' in mention:
            self.unit ='$'
        else:
            self.unit ='other'
        #TODO consider other common units
        return self.unit
    def init_scale(self, mention):
        if 'million' in mention:
            self.scale = pow(10,6)
        elif 'thousand' in mention:
            self.scale = pow(10,3)
        elif 'hundred' in mention:
            self.scale = 100
        elif 'billion' in mention:
            self.scale = pow(10,9)
        else:
            self.scale = 0
        return self.scale
    def init_measure(self, mention):
        #TODO
        self.measure =''
        return ""
    def init_precision(self, mention):
        self.precision = 0
        if self.absolute_value:
            number_parts = self.absolute_value.split('.')
            if len(number_parts) <=1:
                self.precision =0
            else:
                self.precision = len(number_parts[1])

    def init_absolute_value(self, mention):
        #TODO
        number_regex =r'(-)?(\d+([, ]\d+)*(\.\d+)?)'
        self.absolute_value =''
        for match in re.finditer(number_regex, mention):
            #group 0 is the full match including the -ve sign, so we should take the number part only group #2
            #incase that the number in the form \d+,\d, replace the , with .
            number = match.group(2).strip()
            if re.fullmatch(ur'\d+,\d', number):
                number = number.replace(',', '.')
            else:
                number = number.replace(',','').replace(' ','')
            self.absolute_value = number

            if match.group(1): # get the sign
                self.negative_sign = True
#                print("negative sign", mention, self.negative_sign)
            break


    def has_scale(self):
        if self.scale and self.scale != 1:# not the default value!
            return True
        return False
    def has_unit(self):
        if self.unit:
            return True
        return False
    def has_measure(self):
        if self.measure:
            return True
        return False
    def add_aggregate(self,aggregate_function_name, cells_indexes_lst,mentions_orig_unit):
        self.aggregate_function = aggregate_function_name
        self.aggregated_cells = cells_indexes_lst
        self.unit = mentions_orig_unit
    def add_aggregate_inverse(self, inverse_value,surface_form):
        self.aggregate_inverse = inverse_value
        self.aggregate_inverse_surfaceform = surface_form

    def get_aggregate_inverse(self):
        return self.aggregate_inverse

    def get_value(self):
        #TODO process the scale with the value
        if self.unit is '%':# do not scale percentages, as it does not make sense!!!
            return float(self.absolute_value)

        #if self.scale:
        #   return float(self.absolute_value) * self.scale
        if self.features and 'scale' in self.features:
            scale = self.features['scale']
            return float(self.absolute_value) * float(scale)
        elif self.scale and self.scale != 1:
            return float(self.absolute_value) * self.scale
        else:
            return float(self.absolute_value)
    def get_value_without_scale(self):
        return float(self.absolute_value)

    def set_sentence_span(self,sent_span):
        self.sentence_span = sent_span
    def set_aggregate_kw(self, word):
        self.aggregate_kw = word
    def get_aggregate_function(self):
        aggr = None
        if self.aggregate_function:
            aggr = self.aggregate_function
        elif self.aggregate_kw:
            aggr = self.aggregate_kw #TODO
        return aggr
    def get_context_tokens(self):
        return self.features['context_tokens']
    def get_context_np(self):
        return self.features['context_noun_phrases']

    def get_global_context_tokens(self):
        return self.features['global_context_tokens']
    def get_global_context_np(self):
        return self.features['global_context_noun_phrases']

    def get_modifier(self):
        if 'modifier' in self.features:
            return self.features['modifier']
        else:
            return 'None'

    def get_features_as_tsv(self, doc_id):
        mention_id = self.get_full_id()
        if not self.features:
            return None
        desired_features_keys = [ "modifiers","precision", "scale", "unit", "aggregate_function","glbl_perc","glbl_sum","glbl_diff", "glbl_rat","lcl_perc", "lcl_sum","lcl_diff", "lcl_rat","glbl_stats","glbl_finance","glbl_unit","glbl_temp","lcl_stats","lcl_finance","lcl_unit","lcl_temp"]
        desired_features =[str(doc_id), str(mention_id)]
        for feature in desired_features_keys:
            desired_features.append(str(self.features[feature]))
                
        
        return '\t'.join(desired_features)

    def get_features_names_as_tsv(self):
        desired_features_keys = ["docid", "mention_id", "modifiers","precision", "scale", "unit", "aggregate_function","global_percent_kw_count", "global_sum_kw_count", "global_diff_kw_count","global_rat_kw_count", "local_percent_kw_count", "local_sum_kw_count", "local_diff_kw_count","local_rat_kw_count"]

        return '\t'.join(desired_features_keys)


def test():
    mention = Mention(123, '56,1', 12, 16)
    print(mention.absolute_value)
    mention = Mention(123,'56,000', 12,18)
    print(mention.absolute_value)
    mention = Mention(123,'56 000', 12, 18)
    print(mention.absolute_value)
    mention = Mention(123,'56,340,1', 12, 20)
    print (mention.absolute_value)


#test()
