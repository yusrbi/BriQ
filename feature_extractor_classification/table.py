from lxml import html, etree
import utils
from sentence_processor import extract_noun_phrases, fast_extract_noun_phrases 
from mention import Mention
from sets import Set
import regex as re
class Table(object):
	def __init__ (self, table_id, table_num, table_html, table_caption):
		self.table_id = table_id
		self.table_num = table_num
		self.html = table_html
                self.matrix = None
                self.col_count =0
                self.row_count =0
                self.row_context = None
                self.col_context = None 
                self.row_np = None
                self.col_np = None
                self.col_meta = None
                self.row_meta = None 
                self.cell_indx_to_matrix_ij = None
                self.header_tokens = None 
                self.footer_tokens = None 
                self.caption_tokens = None
                self.header_np = None
                self.footer_np = None 
                self.caption_np = None 
		self.mentions = None
		self.aggregate_mentions = None
                self.scale = None
                self.unit = None
               	self.table_to_matrix()
                self.extract_mentions()
                self.html = None # not needed anymore 
                self.generate_aggregate_mentions()
                self.get_table_global_scale_unit()

                #print_table(self)
                #raw_input("Table End")
	def __str__(self):
		table_str = "(%d,%d,<HTML>, %s)"%(self.table_id, self.table_num,self.caption_tokens)
		return table_str.encode('utf-8')
	def set_mentions(self, mentions):
		self.mentions = mentions
        def get_cells_distance(self, positions1, positions2):
            distance = 0
            for i1,j1 in positions1:
                for i2,j2 in positions2:
                    if i1==i2:
                        distance = abs(j1-j2)
                        break
                    if j1 == j2:
                        distance = abs(i1-i2)
                        break
            return distance

        def get_table_table_edge_list(self, doc_id):
            edges =[]
            if self.col_count ==0 or self.row_count ==0:
                return edges
            if doc_id == 176139:
               print(self.cell_indx_to_matrix_ij)
            #get all the cells
            cells = self.cell_indx_to_matrix_ij.keys()
            for i in range(len(cells)):
                cell1 = cells[i]
                if cell1 not in self.mentions:
                    continue
                cell1_positions = self.cell_indx_to_matrix_ij[cell1]
                
                for j in range(i+1, len(cells)):
                    cell2 = cells[j]
                    if cell2 not in self.mentions:
                        continue
                    cell2_positions = self.cell_indx_to_matrix_ij[cell2]
                    
                    distance = self.get_cells_distance(cell1_positions, cell2_positions)
                    if doc_id == 176139 and distance > 0:
                        print("cell %s, cell %s"%(cell1,cell2))
                        print(cell1_positions)
                        print(cell2_positions)
                        print (distance)

                    if distance ==0 :
                        continue # don't add zero-weight edges
                    
                    mention1 = self.mentions[cell1]
                    m1 = mention1.get_full_id()
                    mention2 = self.mentions[cell2]
                    m2 = mention2.get_full_id()
                    surfaceform_sim = utils.get_surfaceform_sim(mention1.surface_form, mention2.surface_form)
                    val_diff =abs( mention1.get_value()-mention2.get_value())
                    max_val = abs(max(mention1.get_value(),mention2.get_value()))
                    if max_val !=0:
                        val_diff = val_diff/max_val
                    proximity = 1.0/ float(distance)
                    edges.append("%s\t%s\t%s\t%s\t%s\t%s\n"%(doc_id, m1,m2,proximity,surfaceform_sim,val_diff))

                #Done !

            # Connect aggregate mentions to mentions used in the aggregations  ONLY 
            for cells, aggr_mentions in self.aggregate_mentions.iteritems():
                cells = cells.split(',')
                #print("cells%s"%cells)
                proximity = 1.0/len(cells)
                for cell in cells:
                    cell = int(cell)
                    if cell in self.mentions:#should always be true
                        mention1 = self.mentions[cell]
                        m1 = mention1.get_full_id()
                        #print("mention found:%s"%str(m1))
                        for mention2 in aggr_mentions:
                            m2 = mention2.get_full_id()
                            surfaceform_sim = utils.get_surfaceform_sim(mention1.surface_form, mention2.surface_form)
                            val_diff =abs( mention1.get_value()-mention2.get_value())
                            max_val = abs(max(mention1.get_value(),mention2.get_value()))
                            if max_val !=0:
                                val_diff = val_diff/max_val

                            edges.append("%s\t%s\t%s\t%s\t%s\t%s\n"%(doc_id, m1,m2,proximity,surfaceform_sim, val_diff))
            
            return edges

        '''
            weight = 1.0/self.col_count
            normalization_factor = (self.col_count-1) *(self.col_count) /2 # n*(n+1)/2, n = self.col_count-1
            done =[]
            # we only generate to mentions that share the same row or column
            for row in range(self.row_count):
                for col1 in range(self.col_count):
                    cell1,_ = self.matrix[row][col1]
                    if cell1 in done or cell1 not in self.mentions:
                        continue
                    mention1 = self.mentions[cell1]
                    m1 = mention1.get_full_id()
                    for col2 in range(col1+1, self.col_count):
                        cell2,_  = self.matrix[row][col2]
                        if cell1 == cell2 or cell2 not in self.mentions:
                            continue
                        mention2 = self.mentions[cell2]
                        m2 = mention2.get_full_id()
                        surfaceform_sim = utils.get_surfaceform_sim(mention1.surface_form, mention2.surface_form)
                        val_diff =abs( mention1.get_value()-mention2.get_value())
                        max_val = abs(max(mention1.get_value(),mention2.get_value()))
                        if max_val !=0:
                            val_diff = val_diff/max_val
                        distance = (col2 - col1) #/ normalization_factor 
                        proximity = 1/ distance
                        edges.append("%s\t%s\t%s\t%s\t%s\t%s\n"%(doc_id, m1,m2,proximity,surfaceform_sim,val_diff))
                    done.append(cell1)
        
            # now do the same for columns 
            weight = 1.0/self.row_count
            normalization_factor = (self.row_count -1)*(self.row_count) /2# 1+2+3+...+(self.row_count -1)
            done =[]
            for col in range(self.col_count):
                for row1 in range(self.row_count):
                    cell1,_ = self.matrix[row1][col]
                    if cell1 in done or cell1 not in self.mentions:
                        continue
                    mention1 = self.mentions[cell1]
                    m1 = mention1.get_full_id()
                    for row2 in range(row1+1,self.row_count):
                        cell2,_ = self.matrix[row2][col]
                        if cell1 == cell2 or cell2  not in self.mentions:
                            continue
                        mention2 = self.mentions[cell2]
                        surfaceform_sim = utils.get_surfaceform_sim(mention1.surface_form, mention2.surface_form)
                        val_diff =abs( mention1.get_value()-mention2.get_value())
                        max_val = abs(max(mention1.get_value(),mention2.get_value()))
                        if max_val !=0:
                            val_diff = val_diff/max_val
                        distance = (row2-row1)#/normalization_factor
                        proximity = 1/distance
                        m2 = mention2.get_full_id()
                        edges.append("%s\t%s\t%s\t%s\t%s\t%s\n"%(doc_id, m1,m2,proximity,surfaceform_sim, val_diff))
                    done.append(cell1)
            '''

	def get_mentions(self):
		#if not  self.mentions:
		#	self.extract_mentions()
                # add the aggregate mrntions
                all_mentions =[]
                if self.mentions:
                    all_mentions.extend(self.mentions.values())
                if self.aggregate_mentions:
                    for aggr_mentions in self.aggregate_mentions.values():
                        all_mentions.extend(aggr_mentions)
		return all_mentions

	def get_aggregate_mentions(self):
		if not self.aggregate_mentions:
			self.generate_aggregate_mentions()
		return self.aggregate_mentions
	def get_row_values(self, row_indx):
		row_values =[]
		for j in range(self.col_count):
                        #if j == self.col_count-1 and self.is_aggregate_col(j):
                                # last col , check if it is an aggregate and skip if so
                                #print j
                                #print self.matrix[row_indx][j]
                        #        continue
			# check repeated values 'colspan'
                        if not self.matrix[row_indx][j]:
                                continue
                        indx, value  = self.matrix[row_indx][j] #get the value and the index of the cell
			if len(row_values)> 0 and indx == row_values[-1][0]:#check if this index is already processed 
				continue
                        if indx in self.mentions: #and not self.is_aggregate_cell(indx):#check if it is a quantity mention and the row does not contains total, avg, etc
				value = self.mentions[indx].get_value()	#get the value with the scale!
                                precision = self.mentions[indx].precision
				unit = self.mentions[indx].unit
                                if not unit:
                                    unit = self.get_mention_unit(self.mentions[indx]) #get the unit from table 
                                row_values.append((indx, value,unit,precision))
		#print("%s row values: %s"%(row_indx,row_values))
		return row_values 

	def get_col_values(self, col_indx):#same as get_row_values, but on column
		col_values = []
		for i in range(self.row_count):
                        #if i == self.row_count -1 and self.is_aggregate_row(i):
                                #last row check if it is an aggregate, like total and skip
                        #        continue
                        if not self.matrix[i][col_indx]:
                                continue
			indx, value = self.matrix[i][col_indx]
			# checlk repeated values 'rowspan'
			if len(col_values)> 0 and indx == col_values[-1][0]:
				continue
                        if indx in self.mentions:#and not self.is_aggregate_cell(indx):
				value = self.mentions[indx].get_value()
                                precision = self.mentions[indx].precision
                                unit = self.mentions[indx].unit
                                if not unit:
                                    unit = self.get_mention_unit(self.mentions[indx]) #get the unit from the table
				col_values.append((indx,value,unit,precision))

		#print("%s col values: %s"%(col_indx,col_values))
            
		return col_values 
        def is_aggregate_col(self,col ):
            if len(self.col_context[col]) > 0:
                col_header = self.matrix[0][col][1]
                #print("col header %s" %col_header)
                if self.is_aggregate_header(col_header):
                    return True
            return False

        def is_aggregate_row(self, row ):
            if len(self.row_context[row]) >0:
                row_header = self.matrix[row][0][1]

                #print("row header %s "%row_header)
                if self.is_aggregate_header(row_header):
		    return True
	    return False

        def is_aggregate_cell(self, indx):

		row,col = self.get_first_matrix_row_col(indx)
                if row < (self.row_count -1) and col < (self.col_count -1):
                    # if the row/col are not the end, then skip, and return as not aggregate
                    return False 
                if len(self.col_context[col]) > 0:
                        col_header = self.col_context[col][0]
                        if col >= (self.col_count-1)  and  self.is_aggregate_header(col_header):
                                return True
                if len(self.row_context[row]) >0:
                        row_header = self.row_context[row][0]
                        if row >= (self.row_count-1) and self.is_aggregate_header(row_header):
			    return True
		return False
	def is_aggregate_header(self, header):
                if not header:
                        return False
		if 'total' in header or 'change' in header:#'total' in header  we need total for percentages 
			return True
		if 'percent' in header or header == '%' or 'average' in header or 'avg' in header:
			return True
		if 'diff' in header or 'difference' in header:
			return True
		return False

	def generate_aggregate_mentions(self):
		self.aggregate_mentions = {}
		# for evry row
		for i in range(self.row_count):
			row_values = self.get_row_values(i)
			if len(row_values) > 1:
				self.generate_aggregate_mentions_row(row_values)
		# for every column 
		for j in range(self.col_count):
			col_values = self.get_col_values(j)
			if len(col_values) > 1:
				self.generate_aggregate_mentions_col(col_values)
	def generate_aggregate_mentions_col(self, col_values):
		subsets = []
		subsets.append([col_values,0])
                #print("col values %s"%col_values)
                if len(col_values) > 4:
                    #check if the last row is an aggregate 
                    indx,_,_,_ = col_values[-1]
                    row,col = self.get_first_matrix_row_col(indx)
                    if self.is_aggregate_row(row):
                        new_values = col_values[:-1]
                        subsets.append([new_values,0])
                        #print("detect row as aggregate %s"%subsets)

		combinations = self.get_all_combinations(col_values)
		for combination in combinations:
			subsets.append([combination,2])
		self.compute_aggregates_for(subsets)


	def generate_aggregate_mentions_row(self, row_values):
		subsets = []
		# aggregate all values 
                #print("row values %s"%row_values)
		subsets.append([row_values, 0])
                if len(row_values) > 4:
                    indx,_,_,_ = row_values[-1]
                    row,col = self.get_first_matrix_row_col(indx)
                    if self.is_aggregate_col(col):
                        new_values = row_values[:-1]
                        subsets.append([new_values,0])
                        #print("detect col aggregate %s"%subsets)

		#aggregate subset of two 
		combinations = self.get_all_combinations(row_values)
		for combination in combinations:
			subsets.append([combination,2])
		
		self.compute_aggregates_for(subsets)
	def get_all_combinations(self, values):
                #print("combine: %s"%values)
            #when generate the different combinations check that the mentions has the same unit
		combinations =[]
		n = len(values)
		for i in range(n):
			for j in range(i+1,n):
                                _,_,unit1,_ = values[i]
                                _,_,unit2,_ = values[j]
                                if (unit1 and unit2 and unit1 == unit2) or (not unit1 and  not unit2) :#only combine if they are of the same unit, will work if both have none unit
                                    combinations.append([values[i], values[j]])
                                    #remove this part and only consider combinations of 2 cells
                                    #for k in range(j+1,n):
                                    #    _,_,unit3,_ = values[k]
                                    #    if(unit3 and unit1 and unit2 and unit3 == unit1) or (not unit3 and not unit1 and not unit2):
                                    #        combinations.append([values[i],values[j], values[k]])#add combinations of 3 
                #print ("combinations:%s"%combinations)
                return combinations
	
	def compute_aggregates_for(self, subset):
		for values in subset:
			key = self.get_key(values[0])
			if key  in self.aggregate_mentions:
				continue
			self.aggregate_mentions[key] = [] 
		# compute sum and average 
                        if values[1] == 0:
                            self.compute_sum_and_avg(key, values[0])
			if len(values[0]) > 2:
				continue
		#compute diff
			self.compute_diff(key,values[0])
		#compute change ratio
			self.compute_ratio(key, values[0])
		# compute percentage 
			self.compute_percent(key, values[0])
	def get_key(self, values):
		key = ','.join(str(x) for x,_,_,_ in values)
		return key

	def compute_percent(self,key, values):
		cell_indx1,value1,unit1,prec1 = values[0]
		cell_indx2, value2,unit2,prec2 = values[1]
                if unit1 == '%':
                    return # No percentage aggregation for percentage 
                if value1==0 or value2 == 0:	
                        return 
		percent = 100.0* (value1/value2)#"%s/%s"%(value1,value2)#value1/value2
		percent = round(percent,2)
		mention = Mention(key, str(percent)+'%', 0,0)
                mention.set_table_id(self.table_id)
		mention.add_aggregate('percentage',[cell_indx1, cell_indx2],unit1)
		inverse = 100.0 *(value2/value1) #"%s/%s"%(value2,value1) #value2/value1
		inverse = round(inverse,2)
                mention.add_aggregate_inverse(inverse, str(inverse)+'%')
		mention.precesion = 0 #max(prec1,prec2) # the max os the 2 quantities precision 
                mention.unit='%'
		self.aggregate_mentions[key].append(mention)


		
	def compute_diff(self,key, values):
		indx1,value1,unit1,prec1 = values[0]
		indx2,value2,unit2,prec2 = values[1]
                if value1 ==0 or value2==0:
                        return 

		diff = value1-value2 #"%s-%s"%(value1,value2) #value1-value2
		mention = Mention(key, str(diff),0,0)
		mention.set_table_id(self.table_id)
                mention.add_aggregate('dif', [indx1,indx2],unit1)
		inverse = value2-value1 #"%s-%s"%(value2,value1)
		mention.add_aggregate_inverse(inverse, str(inverse))
		mention.precision = max(prec1,prec2)
		self.aggregate_mentions[key].append(mention)

	def compute_ratio(self,key, values):
		indx1,value1,unit1,prec1 = values[0]
		indx2, value2,unit2,prec2 = values[1]
                if unit1 == '%':
                    return 
	        if value1 ==0 or value2 == 0:
                    return 
		ratio = 100.0*abs(value1-value2)/float(value2)#"(%s-%s)/%s"%(value1,value2,value2) #(value1-value2)/value2
                ratio = round(ratio,2)
		mention = Mention(key, str(ratio)+'%',0,0)
                mention.set_table_id(self.table_id)
		mention.add_aggregate('rat',[indx1,indx2],unit1)
		inverse = 100.0*abs(value2-value1)/float(value1)#"(%s-%s)/%s"%(value2,value1,value1) #(value2-value1)/value1
                inverse = round(inverse,2)
		mention.add_aggregate_inverse(inverse, str(inverse)+'%')
		mention.precision = 0 #max(prec1,prec2)
                mention.unit ='%'
		self.aggregate_mentions[key].append(mention)

	def compute_sum_and_avg(self,key,  values):
		sum_=0
	
		key_lst = []
                acc_unit = None 
                max_prec = 0
		for indx,value,unit, prec in values:
                        if unit != acc_unit and len(key_lst) > 0:
                            continue # skip units that does not match
                        acc_unit = unit # capture unit if the list is still empty
			key_lst.append(indx)
			sum_ = sum_+value
                        max_prec = max(max_prec,prec)
		#sum_ ="sum"
                if sum_ == 0:
                    return 
		mention = Mention(key, str(sum_),0,0)
                mention.set_table_id(self.table_id)
		mention.add_aggregate('sum', key_lst,acc_unit)
		mention.precision =max_prec
		self.aggregate_mentions[key].append(mention)
		avg = sum_/len(values)
		mention = Mention(key, str (avg), 0,0)
                mention.set_table_id(self.table_id)
		mention.add_aggregate('avg', key_lst,acc_unit)
		mention.precision = max_prec
		self.aggregate_mentions[key].append( mention)

	def get_column_count(self, row):
		columns = row.xpath('.//td|.//th')
		count =0;
		for col in columns:
			if 'colspan' in col.attrib:
				count = count + int(col.attrib['colspan'])
			else:
				count = count+1
		return count
	def get_cell_index(row, col):
		return row* len(self.matrix[0]) + col+1
	def get_header_indx(row,col):
		return -1* (row * len(self.matrix[0]) + col+1)

	def table_to_matrix(self):
		table = html.fragment_fromstring(self.html, create_parent = 'div') 		
		rows = table.xpath('.//tr')
		first_row = rows[0]

		col_count = self.get_column_count(first_row)
                if col_count ==0 and len(rows) > 1:
                    col_count = self.get_column_count(rows[1])

		row_count= len(rows)
		matrix = [ [('',None) for j in range(col_count)] for i in range(row_count)] #init the matrix
		row_indx =0
		#print ('row count: %d, col count: %d'%(row_count, col_count))
#                print(self.html)
		cell_indx = 0
		header_indx = 0

		for row in rows:
			columns = row.xpath('.//th|.//td')			
			col_indx =0
                        #print (columns)
			for col in columns:
				indx =0
				if col.tag == 'td':
					cell_indx = cell_indx +1
					indx = cell_indx
				else: #th
					header_indx = header_indx -1
					indx = header_indx
				col_content =self.get_tag_content(col)
                                #if not col_content:
                                    #print("Empty Column")
                                    #col_content =''

				if 'colspan' in col.attrib:
					reps= int(col.attrib['colspan'])
				else:
					reps = 1 
				if 'rowspan' in col.attrib:
					row_span = int(col.attrib['rowspan'])
				else:
					row_span = 1


				for i in range(row_span):
					for j in range(reps):
                                                if col_indx + j >= col_count or row_indx+i >= row_count:
                                                    #print("Index out : row count:%d, col count%d, row_span %d, col span %d,row indx %d, col Indx %d"%(row_count,col_count,row_span,reps,  row_indx, col_indx))
                                                    break

						while matrix[row_indx+i][col_indx +j][0] != '':#skip non empty columns
							col_indx = col_indx + 1
                                                        if col_indx +j >= col_count:
                                                                #print("Index our of range, row span: %d, col span: %d: "%(row_span, reps))
                                                                break
						matrix[row_indx+i][col_indx+j] = (indx,col_content)
				col_indx = col_indx + reps			
			row_indx = row_indx + 1
		self.matrix = matrix
		self.row_count = len(matrix)
		self.col_count = len(matrix[0])
	        if self.table_id == 1503604:
                    print (matrix)
	def get_first_matrix_row_col(self, cell_index):
		return self.cell_indx_to_matrix_ij[cell_index][0]
	
	def extract_mentions(self):
                #print "extract mentions for table:%d"%self.table_id
		self.mentions ={}
		self.cell_indx_to_matrix_ij = {}
		
                self.header_tokens =[]
		self.footer_tokens =[]		
		self.caption_tokens =[]
                
                self.header_np =[]
                self.footer_np =[]
                self.caption_np =[]

		self.col_context = [[] for i in range(self.col_count)]
		self.row_context = [[] for i in range(self.row_count)]
                
                self.col_np =[[] for i in range(self.col_count)]
                self.row_np = [[] for i in range(self.row_count)]
		
                self.col_meta = [{} for i in range(self.col_count)] 
		self.row_meta =[ {} for i in range(self.row_count)]
		#parse table cells 
		parsed_table = html.fragment_fromstring(self.html, create_parent='div')
		caption_tag = parsed_table.xpath('.//caption')
		headers = parsed_table.xpath('.//th')
		footers = parsed_table.xpath('.//tfoot//td')
		#cells = parsed_table.xpath('.//td')
		for hdr_indx, header in enumerate( headers):
			content = self.get_tag_content(header)
                        tokens,nps = extract_noun_phrases(content)
                        self.header_tokens.extend(tokens)
			self.header_np.extend(nps)
		for footer in footers:
			content = self.get_tag_content(footer)
                        tokens,nps = extract_noun_phrases(content)
			self.footer_tokens.extend(tokens)
                        self.footer_np.extend(nps)
		for caption_item in caption_tag:
                        content = self.get_tag_content(caption_item)
                        tokens,nps = extract_noun_phrases(content)

			self.caption_tokens.extend(tokens)
                        self.caption_np.extend(nps)

		for i  in range(self.row_count):
			for j  in range(self.col_count):
                                if not self.matrix[i][j]:
                                        continue
				indx, col_val = self.matrix[i][j]
				if not col_val:
					continue

				pos = (i,j)
                                
				if indx in self.mentions:
					self.cell_indx_to_matrix_ij[indx].append(pos)
					continue
				else: 
					#print(pos)
                                        if indx in self.cell_indx_to_matrix_ij:
                                            self.cell_indx_to_matrix_ij[indx].append(pos)
                                        else:
                                            self.cell_indx_to_matrix_ij[indx] = [pos]
					if utils.isQuantity(col_val):
						#print( indx )
						mention = Mention(indx, col_val, 0, len(col_val))
                                                #print mention
                                                mention.set_table_id(self.table_id)
						self.mentions[indx] = mention
					else: # any token that is not a quantity is registered as context 
					# note that we don't need to split the context into sentences as the cell content is relatively short 
					# Not a Quantity add to the column and row context
                                                tokens, nps = extract_noun_phrases(col_val)
						self.row_context[i].extend(tokens)#column index is not needed
                                                self.row_np[i].extend(nps)
						self.col_context[j].extend(tokens)# row index is not needed
                                                self.col_np[j].extend(nps)
                                                # check here if the col_val contains a unit or scale
                                                #only for the first column 
                                                #print self.row_context[i]
                                                #print self.row_np[i]

		
			# Capture the unit/scale from the first non-empty non-number cell in the row
		        if len(self.row_context[i]) >0:
				scale,unit = utils.get_scale_unit(self.matrix[i][0][1])
				if scale or unit:
					self.row_meta[i]['scale'] = scale
					self.row_meta[i]['unit'] = unit
                                        if  not self.scale and not self.unit:
                                                self.scale = scale
                                                self.unit = unit 
                                      
		# capture the unit and scale for each column
                # this will check the first non-empty non-number cell content
                for col in range(self.col_count):
			if len(self.col_context[col]) > 0:
				scale,unit = utils.get_scale_unit(self.matrix[0][col][1])						
				if scale or unit:
					self.col_meta[col]['scale'] = scale
					self.col_meta[col]['unit'] = unit 	

		#for cell_indx, cell in enumerate(cells):
		#	content = self.get_tag_content(cell)
		#	if len(content) ==0:
		#		continue
		#
		#	mention = Mention(cell_indx, content, 0, len(content))
		#	self.mentions[cell_indx] = mention
	def get_tag_content(self,tag): # return stripped lowercase string
		for br in tag.xpath(".//br"):
			br.tail = " " + br.tail if br.tail else " "
		content =  tag.text_content().strip().lower()
		return re.sub('\s+',' ', content)


	def get_mention_scale(self,mention):
            
                #print( mention.mention_id)
                cells = str(mention.mention_id)
                if cells[-1] == ',':
                    cells = cells[:-1]
                #print(cells) 
                #print(cells.split(','))
                for cell in cells.split(','):
                    row,col = self.get_first_matrix_row_col(int(cell))
		    # how to get the scale for the aggregate mentions 
                    scale =  self.get_scale_col(col)
		    if scale:
                        break
                    scale = self.get_scale_row(row)
                    if scale:
                        break
                
		if not scale:
			scale = self.scale

		return scale

	def get_scale_col(self, col_indx):
		if 'scale' in self.col_meta[col_indx]:
			return self.col_meta[col_indx]['scale']
	def get_scale_row(self, row_indx):
		if 'scale' in self.row_meta[row_indx]:
			return self.row_meta[row_indx]['scale']


	def get_mention_measure(self, mention):
		#TODO
		pass
	def get_mention_unit(self,mention):
                cells = str(mention.mention_id)
                if cells[-1] == ',':
                    cells = cells[:-1]

                for cell in cells.split(','):
                    row,col = self.get_first_matrix_row_col(int(cell))
                    unit = self.get_unit_col(col)
                    if unit:
                        break
                    unit = self.get_unit_row(row)
		    if unit:
                        break
                if not unit:
                    unit = self.unit
         
		    return unit 

	def get_unit_row(self, row):
		if 'unit' in self.row_meta[row]:
			return self.row_meta[row]['unit']

	def get_unit_col(self,col):
		if 'unit' in self.col_meta[col]:
			return self.col_meta[col]['unit']

	def get_mention_context_words(self,mention):
		# it make sense to get only one of the positions of the cells 
		# as if it happened to span more than one row or column, its context should be similar, in otherwords its context cells will span the same rows and columns 
		cells = str(mention.mention_id)
                if cells[-1] == ',':
                    cells = cells[:-1]
                context = Set([])
                for cell in cells.split(','):
                    #print 'cell:%s'%cell
                    row,col = self.get_first_matrix_row_col(int(cell))
	            context = context.union(self.get_context_words_row(row))
		    context = context.union(self.get_context_words_col(col))
                #context = context.union(self.get_context_words_table()) # header, footer and caption
                #print context
		return set(context) 

	def get_context_words_row(self, row):
		#print self.row_context[row]
                return self.row_context[row]
	def get_context_words_col(self, col):
                #print self.col_context[col]
		return self.col_context[col]
        def get_context_table(self):
            return self.get_context_words_table(), self.get_np_table()
        def get_context_words_table(self):
		context = Set([])
		context = context.union(self.header_tokens)
		context = context.union(self.footer_tokens)
		context = context.union(self.caption_tokens)
                #add the context of column 0 and row0
                if(len(self.col_context) >0):
                    context = context.union(self.col_context[0])
                if(len(self.row_context)>0):
                    context = context.union(self.row_context[0])
		return context
	def get_np_table(self):
                np = Set([])
                np = np.union(self.header_np)
                np = np.union(self.footer_np)
                np = np.union(self.caption_np)
                # add the np of column0 and row 0
                if(len(self.col_np) >0):
                    np = np.union(self.col_np[0])
                if(len(self.row_np) >0):
                    np = np.union(self.row_np[0])
                return np

	def get_mention_noun_phrases(self,mention):
	        cells = str(mention.mention_id)
                if cells[-1] == ',':
                    cells = cells[:-1]

                nps=set()
                for cell in cells.split(','):

                    row,col = self.get_first_matrix_row_col(int(cell))
                    nps = nps.union(self.row_np[row])
                    nps = nps.union(self.col_np[col])
                #nps = nps.union(self.get_np_table())
                #print nps

                return nps

	def get_mention_modifiers(self, mention):
		#No modifiers in tables !
		pass
	def get_scale_unit(self, string):# assume the string always lower case 
		# ($M) $(million) thousand$ 1000$
		#TODO make this string search faster
		scale = None
		unit= None
		if 'million' in string  or 'mega' in string:
			scale = pow(10,6)
		elif 'billion' in string  or 'giga' in string:
			scale = pow(10,9)
		elif 'thousand' in string  or  'kilo' in string:
			scale = pow(10,3)
		elif 'hundred' in string:
			scale = 100
		elif '$m' in string:
			scale = pow(10,6)
			unit ='$'
		elif '$b' in string:
			scale = pow(10,9)
			unit = '$'
		elif '$k' in string:
			scale = pow(10,3)
			unit = '$'
		if not unit:
			if '$' in string:
				unit = '$'
			elif '%' in string:
				unit ='%'
		return (scale, unit)
	def get_table_global_scale_unit(self):
		# check the first non-empty cell in the first column  
		scale = None
		unit = None
		#TODO check if multiple scale and unit were found 
                # check the caption
		for capt in self.caption_tokens:
			scale,unit = utils.get_scale_unit(capt)
			if scale or unit:
				self.scale = scale
				self.unit = unit
				return
		#check the footer 
		for footer in self.footer_tokens:
			scale,unit = utils.get_scale_unit(footer)
			if scale or unit:
				self.scale = scale
				self.unit = unit 
				return 
def print_table(table):
	print (table.matrix)
	simple_mentions = table.get_mentions()
	print("Simple Mentions:")
	for mention in simple_mentions:
		print(mention)
	aggregates = table.get_aggregate_mentions()
	print("Aggregate Mentions")
	for aggregate in aggregates.values():
		for mention in aggregate:
			print(mention)		
def test():
	table = """
<table style="width:100%">
  <tr>
    <th>Firstname</th>
    <th>Lastname</th> 
    <th>Age</th>
  </tr>
  <tr>
    <td>Jill</td>
    <td>Smith</td> 
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td> 
    <td>94</td>
  </tr>
	</table>"""
	#table_obj1 = Table(0,0,table,"")
	#print_table(table_obj1)
	
	table2 = """
	<table style="width:100%">
  <tr>
    <th>Name:</th>
    <td colspan = 2>Bill Gates</td>
  </tr>
  <tr>
    <th rowspan="3">Telephone:</th>
    <td colspan ="2" >55577854</td>
  </tr>
  <tr>
    <td rowspan="2">55577855</td>
    <td>hjfhjsa</td>
  </tr>
  <tr> <td> abdc </td> </tr>
</table>
	"""

	#table_obj2 = Table(0,0,table2,"")
	#print_table(table_obj2)
	table3= """
<table style="width:100%">
	<tr>
    	<td colspan="2" rowspan="2">
        	both 
        </td>
        <td> part 1</td>
	<td> %</td>
    </tr>
    <tr>
       <td> part2 </td>
       <td> 55 </td>
    </tr>
    <tr>
    <th>Name:</th>
    <td colspan = 2>Bill Gates</td>
    <td> 45 </td>
  </tr>
  <tr>
    <th rowspan="3">Telephone:</th>
    <td colspan ="2" >55577854</td>
    <td> 20 </td>
  </tr>
  <tr>
    <td rowspan="2">55577855</td>
    <td>hjfhjsa</td>
    <td> 10 </td>
  </tr>
  <tr> <td> abdc </td> <td> 65 </td> </tr>
</table>
	"""
	#table_obj3 = Table(0,0,table3,"")
	#print_table(table_obj3)
	
	table4 = """
	<table>
<tr>
  <th>col1</th>
  <td colspan="2">col2/col3</td>
</tr>
<tr>
  <th rowspan="2">number</th>
  <td colspan="2">8</td>
</tr>
<tr>
  <td>number2</td>
  <td> 12</td>
</tr>
<tr>
<td> Total values </td>
<td> 1</td>
<td>3</td>
</tr>
</table>

	"""
	#table_obj4 = Table(0,0,table4,"")
	#print_table (table_obj4)
        
        table3= '''
        <table cellspacing="0" border="0">
        <tr class="cnwBoldUnderlinedCell">
        <td colspan="4">
        <b>Sales Volumes </b>
        </td>
        </tr>
        <tr valign="top">
        <td align="left" colspan="2">
        &#160;
        </td>
        <td align="right" colspan="2" nowrap="nowrap">
        Three months ended March 31,
        </td>
        </tr>
        <tr valign="top" class="cnwUnderlinedCell">
        <td align="left">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        <td align="right">
        2014
        </td>
        <td align="right">
        2013
        </td>
        </tr>
        <tr valign="top">
        <td align="left">
        Light oil and condensate
        </td>
        <td align="center">
        (bbls/d)
        </td>
        <td align="right">
        6,899
        </td>
        <td align="right">
        3,714
        </td>
        </tr>
        <tr valign="top">
        <td align="left">
        NGLs (excluding condensate)
        </td>
        <td align="center">
        (bbls/d)
        </td>
        <td align="right">
        5,432
        </td>
        <td align="right">
        2,072
        </td>
        </tr>
        <tr valign="top" class="cnwUnderlinedCell">
        <td align="left">
        Heavy oil
        </td>
        <td align="center">
        (bbls/d)
        </td>
        <td align="right">
        74
        </td>
        <td align="right">
        197
        </td>
        </tr>
        <tr valign="top" class="cnwUnderlinedCell">
        <td align="left">
        Total crude oil, condensate and NGLs
        </td>
        <td align="center">
        (bbls/d)
        </td>
        <td align="right">
        12,405
        </td>
        <td align="right">
        5,983
        </td>
        </tr>
        <tr valign="top">
        <td align="left">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        </tr>
        <tr valign="top" class="cnwUnderlinedCell">
        <td align="left">
        Natural gas
        </td>
        <td align="center">
        (mcf/d)
        </td>
        <td align="right">
        135,865
        </td>
        <td align="right">
        80,158
        </td>
        </tr>
        <tr valign="top">
        <td align="left">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        <td align="right">
        &#160;
        </td>
        </tr>
        <tr valign="top" class="cnwBoldUnderlinedCell">
        <td align="left">
        Total boe/d
        </td>
        <td align="center">
        (6:1)
        </td>
        <td align="right">
        35,049
        </td>
        <td align="right">
        19,343
        </td>
        </tr>
        </table>
        
        '''
        table ='''
            <table>
                                                <tr class="oddRow">
                                                <th class="firstCol"><a href="/ausstats/abs@.nsf/Lookup/2901.0Chapter38702011" class="dictionaryLink" title="Classifies people as employed working full-time, part-time or away from work, unemployed looking for full-time work, looking for part-time work, or not in the labour force." target="_blank">Employment</a></th>
                                                <th class="geoCol">The Rocks (Sydney - NSW)</th>
                                                <th class="percentCol">%</th>
                                                <th class="geoCol">New South Wales</th>
                                                <th class="percentCol">%</th>
                                                <th class="geoCol">Australia</th>
                                                <th class="percentCol">%</th>
                                                                                    </tr>
                                                                                                                        <tr class="evenRow">
                                                                                                                        <td class="firstCol" colspan="7"><em>People who reported being in the labour force, aged 15 years and over</em></td>
                                                                                                                                          </tr> 
                                                                                                                                                            <tr class="oddRow"> 
                                                                                                                                                            <td class="firstCol">Worked full-time</td>
                                                                                                                                                            <td>204</td>
                                                                                                                                                            <td>73.4</td>
                                                                                                                                                            <td>2,007,924</td>
                                                                                                                                                            <td>60.2</td>
                                                                                                                                                            <td>6,367,554</td>
                                                                                                                                                            <td>59.7</td>
                                                                                                                                                                              </tr>
                                                                                                                                                                                                <tr class="evenRow"> 
                                                                                                                                                                                                <td class="firstCol">Worked part-time</td>
                                                                                                                                                                                                <td>39</td>
                                                                                                                                                                                                <td>14.0</td>
                                                                                                                                                                                                <td>939,465</td>
                                                                                                                                                                                                <td>28.2</td>
                                                                                                                                                                                                <td>3,062,976</td>
                                                                                                                                                                                                <td>28.7</td>
                                                                                                                                                                                                                  </tr>
                                                                                                                                                                                                                                    <tr class="oddRow"> 
                                                                                                                                                                                                                                    <td class="firstCol">Away from work</td>
                                                                                                                                                                                                                                    <td>21</td>
                                                                                                                                                                                                                                    <td>7.6</td>
                                                                                                                                                                                                                                    <td>190,944</td>
                                                                                                                                                                                                                                    <td>5.7</td>
                                                                                                                                                                                                                                    <td>627,797</td>
                                                                                                                                                                                                                                    <td>5.9</td>
                                                                                                                                                                                                                                                      </tr>
                                                                                                                                                                                                                                                                        <tr class="evenRow"> 
                                                                                                                                                                                                                                                                        <td class="firstCol">Unemployed</td>
                                                                                                                                                                                                                                                                        <td>14</td>
                                                                                                                                                                                                                                                                        <td>5.0</td>
                                                                                                                                                                                                                                                                        <td>196,525</td>
                                                                                                                                                                                                                                                                        <td>5.9</td>
                                                                                                                                                                                                                                                                        <td>600,133</td>
                                                                                                                                                                                                                                                                        <td>5.6</td>
                                                                                                                                                                                                                                                                                          </tr>
                                                                                                                                                                                                                                                                                                            <tr class="oddRow"> 
                                                                                                                                                                                                                                                                                                            <td class="firstCol">Total in labour force</td>
                                                                                                                                                                                                                                                                                                            <td>278</td>
                                                                                                                                                                                                                                                                                                            <td><strong>--</strong></td>
                                                                                                                                                                                                                                                                                                            <td>3,334,858</td>
                                                                                                                                                                                                                                                                                                            <td><strong>--</strong></td>
                                                                                                                                                                                                                                                                                                            <td>10,658,460</td>
                                                                                                                                                                                                                                                                                                            <td><strong>--</strong></td>
                                                                                                                                                                                                                                                                                                                              </tr>
                                                                                                                                                                                                                                                                                                                                                                <tr class="evenRow">
                                                                                                                                                                                                                                                                                                                                                                <td class="firstCol" colspan="7">&#160;</td>
                                                                                                                                                                                                                                                                                                                                                                                                    </tr>
                                                                                                                                                                                                                                                                                                                                                                                                                                        <tr class="evenRow">
                                                                                                                                                                                                                                                                                                                                                                                                                                        <td class="firstCol" colspan="7"><a href="/websitedbs/censushome.nsf/home/factsheetslfsc?opendocument&amp;navpos=450" target="_blank"><em>View the labour force fact sheet</em></a></td>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                            </tr>                  
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            </table>
        '''
        table_obj = Table(0,0,table,"")
        print(table_obj.matrix)
        print(table_obj.mentions)
        print(table_obj.aggregate_mentions)
#test()
