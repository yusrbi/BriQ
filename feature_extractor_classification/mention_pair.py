import utils
import math

class MentionPair:

    def __init__(self,doc_id, text_mention, table_mention, val_diff=0.0, sim =0.0):
        self.doc_id = doc_id
        if text_mention and table_mention:
            self.text_mention = text_mention
            self.table_mention = table_mention
            self.val_diff = 0
            self.val_rel_diff_max = 0
            self.val_rel_diff_sum =0
            self.scale_diff =0
            self.unit_sim =0
            self.precision_diff =0
            self.modifier = None
            self.aggr_func_sim = None
            self.tokens_overlap =0
            self.global_tokens_overlap = 0
            self.np_sim =0
            self.global_np_sim = 0
            self.surface_form_sim  =0
            self.val_rel_diff_no_scale=0
            self.sim =None
            self.process(text_mention, table_mention)
            
        else:
            self.text_mention =''
            self.table_mention =''
            self.val_rel_diff_max = val_diff
            self.sim = sim
            

	self.ground_truth = False

    

    def __str__(self):
        mention_pair_str =  "X:%s,T:%s,sim:%2.2f"%(self.text_mention, self.table_mention,  self.sim)
	return mention_pair_str.encode('utf-8')

    def process(self,text_mention, table_mention):
        #value similarity
        
        text_mention_val = text_mention.get_value()
        table_mention_val = table_mention.get_value()
        
        if text_mention_val < 1 and table_mention.features['unit'] == '%':
            text_mention_val = text_mention_val * 100 # eg .232 vs 23.2%

        diff = abs(text_mention_val - table_mention_val)
        
        # check if the table has an inverse value --> calculated for percentage, difference and ratio: the ordered  aggregates
        inverse = table_mention.get_aggregate_inverse()
        table_val_without_scale = table_mention.get_value_without_scale()
        text_val_without_scale = text_mention.get_value_without_scale() 
        table_mention_surfaceform = table_mention.surface_form

        # select the inverse mention if it is closer in value to the text mention
        if inverse:
            diff2 = abs(text_mention_val - inverse)
            # Now use the inverse as the second value in all calculations
            if diff2 < diff:
                table_mention_val = inverse
                table_mention_surfaceform = table_mention.aggregate_inverse_surfaceform 
                diff = diff2
                table_val_without_scale = inverse


        val_diff_no_scale = abs(text_val_without_scale- table_val_without_scale)

        max_no_scale = abs(max(text_val_without_scale, table_val_without_scale))

        if max_no_scale !=0:
            self.val_rel_diff_no_scale = val_diff_no_scale / max_no_scale
        else:
            self.val_rel_diff_no_scale = val_diff_no_scale



        self.val_diff = diff 

        div =abs( max(text_mention_val, table_mention_val))
        if div == 0:
            self.val_rel_diff_max = float(self.val_diff) 
        else:
            self.val_rel_diff_max = float(self.val_diff) / div
        div = abs(text_mention_val + table_mention_val)
        if div ==0:
            self.val_rel_diff_sum = float(self.val_diff)
        else:
            self.val_rel_diff_sum = float(self.val_diff)/ div
        # scale agreement
        text_scale = text_mention.features['scale']
        table_scale = table_mention.features['scale']
        if text_scale and table_scale:
            self.scale_diff = abs(math.log(text_scale,10) - math.log(table_scale,10))
        else:
            self.scale_diff = 0
        # unit agreement
        text_unit = text_mention.features['unit']
        table_unit = table_mention.features['unit']
        if text_unit and table_unit:
            self.unit_sim = utils.get_unit_sim(text_unit, table_unit)
        else:
            self.unit_sim = 0
        
        text_precision = text_mention.features['precision']
        table_precision = table_mention.features['precision']

        if text_precision and table_precision:
            self.precision_diff  = abs(text_precision - table_precision)
        else:
            self.precision_diff =0
        # approximate
        # bounds
        # exact
        self.modifier = text_mention.features['modifiers']
	# aggregate function
        text_aggr = text_mention.features['aggregate_function']
        table_aggr = table_mention.features['aggregate_function']
        self.aggregate_function = table_aggr
        if text_aggr and table_aggr and text_aggr == table_aggr:
            self.aggr_func_sim = 1
        else:
            self.aggr_func_sim =0 

        #context token overlap
        self.tokens_overlap = utils.get_tokens_overlap(text_mention.get_context_tokens(), table_mention.get_context_tokens())
        self.global_tokens_overlap = utils.get_tokens_overlap(text_mention.get_global_context_tokens(), table_mention.get_global_context_tokens())
        #context np similarities
        self.np_sim = utils.get_tokens_overlap(text_mention.get_context_np(), table_mention.get_context_np())
        self.global_np_sim = utils.get_tokens_overlap(text_mention.get_global_context_np(), table_mention.get_global_context_np())#get_nps_sim
        #surface form similarity
        self.surface_form_sim  = utils.get_surfaceform_sim(text_mention.surface_form, table_mention_surfaceform)
        self.text_mention_val = text_mention_val
        self.table_mention_val = table_mention_val
        self.text_tokens = text_mention.get_context_tokens()
        self.table_tokens = table_mention.get_context_tokens()
    
    def get_approx_sim(self):
        if not self.sim:
            #sims = self.tokens_overlap +self.global_tokens_overlap + self.np_sim + self.global_np_sim
            sims = self.unit_sim + self.surface_form_sim+ self.aggr_func_sim
            self.sim = sims - self.val_rel_diff_max 
        return self.sim


    def get_value_difference(self):
        return self.val_rel_diff_max

    def is_potential_mention_pair(self):
        # weighted sum of all the similarities
       
        if self.val_rel_diff_max <= 0.5:
            return True
        if self.surface_form_sim >= 0.3:
            return True
        if self.tokens_overlap >= 0.1:
            return True
        return False

    def set_ground_truth(self, value):
        self.ground_truth = value
    def get_ground_truth(self):
        if self.ground_truth:
            return 1
        else:
            return 0

    def get_as_csv_line(self):
            # mentions identifiers followed by the similarity features and other features 
            # the last line should contain 0/1 for the classification gold standards

        line =''
        ids = '%s\t%s\t%s'%(self.doc_id, self.text_mention.get_full_id(), self.table_mention.get_full_id())
        line = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n'%(
            ids, self.val_rel_diff_no_scale , self.val_rel_diff_max, self.val_rel_diff_sum, self.scale_diff,self.precision_diff, 
            self.unit_sim, self.modifier,self.aggr_func_sim,self.tokens_overlap, self.np_sim,self.global_tokens_overlap,self.global_np_sim,self.surface_form_sim,self.get_approx_sim(),self.text_mention_val, self.table_mention_val,self.text_mention.features['scale'], self.table_mention.features['scale'],self.get_ground_truth(),self.aggregate_function)

        #mXId\tmTid\tdiff\tdiff_max\tdif_sum\tscale\tprec\tunit\tmod\taggr\ttokn\tnps\gtokns\gnps\tsurfaceform\tGT

        return line 

