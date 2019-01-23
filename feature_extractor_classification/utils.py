# -*- coding: utf-8 -*-
import os
import json 
import codecs
import sys
import glob 
import regex as re
from nltk.metrics  import distance

def isQuantity(mention):
        mention = mention.strip()
        #this does not work as it ignore some values!
        #if re.fullmatch(r'19\d{2}|20[01]\d', mention):# years are not mentions 
        #        return False
	if re.fullmatch(r'\(?[+-]?\p{Sc}?\d+([., ]\d+)*\%?\p{Sc}?\)?',mention):
		return True
        if re.fullmatch(r'\(?[+-]?\d+([., ]\d+)*\)?.*',mention): # accept a number followed by  a word, it might be a unit
                return True
        if re.fullmatch(r'.*\(?[+-]?\d+([., ]\d+)*\)?',mention): # accept a number proceeded by  a word only 8 characters, it might be a unit
                return True 
        if re.fullmatch(r'.{1,20}\(?[+-]?\d+([., ]\d+)*\)?.{1,20}',mention): # accept a number proceeded or followed by  a word only 8 characters, it might be a unit
                return True 
	else:
		return False

def load_stop_words(file_name):
	word_list=[]
	with codecs.open(file_name,'r','UTF-8') as words:
		for word in words:
			word_list.append(word.strip())
	return set(word_list)

def load_json_file(input_file):
	json_objects =[]
	with codecs.open(input_file,'r','UTF-8') as json_lines:
		for json_line in json_lines:
			json_obj = json.loads(json_line)
			json_objects.append(json_obj)
	return json_objects
def filter_stop_words(word_list):
	global stop_words
	new_word_list=[]
	for word in word_list:
		if word not in stop_words and len(word) >1:
			new_word_list.append(word)
	return new_word_list
def get_word_set(text):
	words = re.split(r'[\.\,\:\?\;\/\(\)\[\]\"\'\-\!\&\s\%\$\#\\]+',text.lower())
	return set(filter_stop_words(words))
def get_word_list(text):
	words = re.split(r'[\.\,\:\?\;\/\(\)\[\]\"\'\-\!\&\s\%\$\#\\]+',text.lower())
	return filter_stop_words(words)
def write_as_html( page_url, page_id, text_block, mentions, tables):
	print ('<html><body>')
	print (text_block.encode('UTF-8'))
	print (mentions )
	sorted_tables = sorted(tables, key=lambda tup:tup[2],reverse=True)

	for table_id, table, num_matches in sorted_tables:
		print (num_matches)
		print (etree.tostring(table))
	print ('</body></html>')


def save_json(file_name, json_objects):
	with codecs.open(file_name,'w','UTF-8') as writer:
		for obj in json_objects:
			json.dump(obj,writer)
def save_file(file_name,content):
	with codecs.open(file_name,'w','UTF-8') as writer:
		writer.writelines(content)

def overlap( word_set1, word_set2):
	count =0
	for word in word_set1:	
		if word in word_set2:
			count +=1
	return count
def read_tsv_as_dictionary(file_name, key =0):
	data={}
	with codecs.open(file_name,'r','UTF-8') as file_content:
		for line in file_content:
                        line = line.strip().encode('UTF-8')
                        if not line:
                            continue
                        temp = re.split('\s+',line)
                        if len(temp) < 2:
                            continue
                        if temp[key] in data:
                            data[temp[key]].append(temp [key+1:])
                        else:
                            data[temp[key]] = [temp[key+1:]]

	return data

def read_tsv_files(list_of_files, key =0):
    data={}
    for file_name in list_of_files:
        #print("Reading file %s"%file_name)

        with codecs.open(file_name,'r','UTF-8') as file_content:
            for line in file_content:
                line = line.strip().encode('UTF-8')
                if not line:
                    continue
                temp = re.split('\s+',line)
                if len(temp) < 2:
                    continue
                if temp[key] in data:
                    data[temp[key]].append(temp [key+1:])
                else:
                    data[temp[key]] = [temp[key+1:]]
        #print("data length %s"% len(data))

    return data



def load_file_as_dictionary(file_name):
	data={}
	with codecs.open(file_name,'r','UTF-8') as file_content:
		for line in file_content:
			data[line.strip()]=1
	return data
def write(file_name, data):
	with codecs.open(file_name,'w','UTF-8') as writer:
		for item in data:
			writer.write(item+'\n')
def get_scale_unit(string):# assume the string always lower case 
	# ($M) $(million) thousand$ 1000$
	#TODO make this string search faster
	scale = None
	unit= None
        if not string:
            return (scale,unit)
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
		if '$' in string or 'usd' in string:
		    unit = '$' 
		elif '%' in string or 'percent' in string:
		    unit ='%'
	return (scale, unit)

# TODO load units and measures
unit_list = set(['%','$'])
scale_list = {'billion':pow(10,9), 'giga':pow(10,9) ,  'million':pow(10,6), 'mega':pow(10,6), 'thousand':pow(10,3),'kilo':pow(10,3), 'hundred':100  }

#stop_words = load_stop_words('hdfs:///user/yibrahim/stopwords.txt') on the cluster you need to use sc.textFile('hdfs:///user/vagrant/1970-Nixon.txt')


def get_tokens_overlap(tokens_a, tokens_b):
        if len(tokens_a) ==0 or len(tokens_b)==0:
            return 0.0

        overlap_coef = 0.0
        intersection_count = 0
        for token in tokens_a:
            if token in tokens_b:
                intersection_count += 1
        #den = min(len(tokens_a),len(tokens_b))
        den = len(tokens_a)+len(tokens_b)-intersection_count
        if den !=0:
            overlap_coef = float(intersection_count)/den
        else:
            overlap_coef = 1 # all tokens are the same 

        return overlap_coef

def get_np_sim(nps_a, nps_b):
        if len(nps_a) ==0 or len(nps_b) ==0:
            return 0
    # pre store this values 
        sim = 0.0
        min_dist = 1000000
        for np_a in nps_a:
            #print "np_a%s"%np_a
            for np_b in nps_b:
                #print "nb_b%s"%np_b
                dist  = distance.edit_distance(np_a,np_b)
                #print"dist:%s"%dist
                if dist < min_dist:
                    min_dist = dist
        if min_dist ==0 :
            sim =1.0
        else:
            sim  = 1.0/float(min_dist+0.2)# I added the 0.2, as if the min_dist = 1, the sim should be less than one
        return sim 

def get_unit_sim(unit_a, unit_b):
        sim =0.0
        dist = distance.edit_distance(unit_a,unit_b)
        if dist >= min(len(unit_a), len(unit_b)):
            return 0.0
        if dist ==0:
            sim =1.0
        else:
            sim = 1.0/float(dist+0.2)

        return sim
def string_sim(str1,str2):
    sim =0.0
    dist = distance.edit_distance(str1,str2)
    if dist ==0:
        sim =1.0
    else:
        sim = 1.0/float(dist+0.2)
    return sim


def get_measure_sim(measure_a, measure_b):
        sim = 0.0
        dist = distance.edit_distance(measure_a,measure_b)

        if dist ==0:
            sim =1.0
        else:
            sim = 1.0/float(dist+0.2)

        return sim
def get_surfaceform_sim(surfaceform_a, surfaceform_b):
        sim = 0.0
        dist = distance.edit_distance(surfaceform_a, surfaceform_b)
        if dist ==0:
            sim =1.0
        else:
            sim = 1.0/float(dist+0.2)

        return sim
def is_equal_cells(cells1, cells2):
    if cells1[-1] ==',':
        cells1 = cells1[:-1]
    if cells2[-1] == ',':
        cells2= cells2[:-1]

    cells1 = cells1.split(',')
    cells2 = cells2.split(',')
    
    if len(cells1) != len(cells2):
        return False;
    for cell1 in cells1:
        if cell1 not in cells2:
            return False
    return True

def sort_cells(cells):
    cells = cells.split(',')
    int_cells = []
    for cell in cells:
        if cell:
            int_cells.append(int(cell))

    int_cells.sort()
    return ','.join([str(x) for x in int_cells])


def test():

    print(sort_cells("4,5,6,7,1,2,3,"))
    print(sort_cells("1,2,3"))
    print(sort_cells("4,3,6,10"))

    #file_name = 'test_edges.tsv'
    #data = read_tsv_as_dictionary(file_name)
    #print(data)
    #cells1 = '1,2,3'
    #cells2 = '3,2,1'
    #cells4 = '1,2,'
    #cells3 = '1,2,3,'
    #cells5 = '1,1,2,3,'
    #print is_equal_cells(cells1,cells2)
    #print is_equal_cells(cells1,cells3)
    #print is_equal_cells(cells1, cells4)
    #print is_equal_cells(cells1,cells5)
    
    #print get_surfaceform_sim('123.4', '125.4')
    #print get_measure_sim('infalation rate', 'rate of infalation')
    #print get_unit_sim('km/hr', 'kmh')
    #print get_tokens_overlap(['hello','world','smile'],['hope', 'smile', 'hello'])
    #print get_np_sim(['similar','same','the same'],['the same','similar','same x'])
    #print get_np_sim(['similar','same','the same'],[])

#test()
