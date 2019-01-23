import regex as re
import utils
class Mention:
	def __init__(self, mention_id,mention,start_offset, end_offset):

		mention = mention.lower().encode('utf-8')
                mention = re.sub('\s+',' ', mention)
                if mention[0] =='.':
                    mention = '0'+ mention

		self.mention_id = mention_id
#                self.document_id = document_id
		self.start_offset = start_offset
		self.end_offset = end_offset
		self.surface_form = mention
                self.aggregate_kw = None
                self.absolute_value = None
                self.measure = None
                self.precision = None
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



        def get_relation_name(self): # this method is used to check against the GT 
            if self.aggregate_function:
                return self.aggregate_function
            else:
                return 'same'

        def __str__(self):
            mention_str = "(id:%s, mention: %s,strat:%d,end: %d)"%(self.mention_id,self.surface_form, self.start_offset, self.end_offset)
	    return mention_str
        def get_full_id(self):
            id_ = self.mention_id 

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
		self.precision = -1 
		if self.absolute_value:
			number_parts = self.absolute_value.split('.')
			if len(number_parts) <=1:
				self.precision =0
			else:
				self.precision = len(number_parts[1])

	def init_absolute_value(self, mention):
		#TODO
		number_regex =r'\d+([, ]\d+)*(\.\d+)?'
		self.absolute_value =''
		for match in re.finditer(number_regex, mention):
			self.absolute_value = match.group(0).strip().replace(',','').replace(' ','')
                        break


	def has_scale(self):
		if self.scale:
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
                self.aggregated_mentions_unit = mentions_orig_unit
	def add_aggregate_inverse(self, inverse_value,surface_form):
		self.aggregate_inverse = inverse_value
                self.aggregate_inverse_surfaceform = surface_form

        def get_aggregate_inverse(self):
            return self.aggregate_inverse
    
	def get_value(self):
		#TODO process the scale with the value 
                if self.unit is '%':# do not scale percentages, as it does not make sense!!!
                    return float(self.absolute_value) 

                if self.scale:
			return float(self.absolute_value) * self.scale
                elif self.features and 'scale' in self.features and self.features['scale']:
                        return float(self.absolute_value) * float(self.features['scale'])
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

