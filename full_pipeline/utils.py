# -*- coding: utf-8 -*-
import os
import json
import codecs
import sys
import glob
import regex as re
from nltk.metrics  import distance
import sentence_processor 
from pyjarowinkler import distance as jarodist
import string
import traceback

#unit_list = set(['%','$'])
#scale_list = {'billion':pow(10,9), 'giga':pow(10,9) ,  'million':pow(10,6), 'mega':pow(10,6), 'thousand':pow(10,3),'kilo':pow(10,3), 'hundred':100  }
unit_list = {'%':'%', 'perc':'%', 'per cent':'%', 'percent':'%', 'percentage':'%', 'dollar':'$', 'dollars':'$','$':'$', 'usd':'$', 'eur':'eur', 'euro':'eur', u'€':'eur', u'\xa3':'pound' }
scale_list = {'billion':pow(10,9), 'giga':pow(10,9) ,  'million':pow(10,6), 'mega':pow(10,6), 'thousand':pow(10,3),'kilo':pow(10,3), 'hundred':100, 'cents':0.01  }
stop_words = sentence_processor.stopwords_lst
#diff_kw= ["difference","diff","drop","increase","change","gain","increment","raise","rise","boost","decline","reduction","loss","deteriorate","fall","reduce","up","grow","improve","add","relative","down","ratio"]
#rat_kw = diff_kw

#percent_kw = ["percent","percentage","fraction","proportion","share", 'rate', 'compared']
#sum_kw = ["sum","overall","include", 'exclude','together',"total",'among','of','count','join']
keywords ={}

#keywords["diff"] =["increase","decrease","difference","drop","change","gain","increment","raise","rise","boost","decline","reduction","deteriorate", "fall", "reduce", "up", "grow", "improve", "add", "down","loss"]

#keywords["rat"] =["growth","adjust","perform","driven","reflect","dividend","part","show","improve","ratio", "relative","profit","segment","diluted","higher","earn"]

#keywords["sum"]  =["include","account","overall","exclude", "together", "among","joint","sum","labour","population"]

#keywords["perc"]=["sat","subject","proportion","percentage","fraction","candidate", "gross","respect"]

#keywords["finance"] =["stock","net","revenue","income","sale","expense","quarter","cashe","market","cost","financial","company","share"]
#keywords["stats"] = ["census","people","family","parent","children","male","female","count","government","employment","aborigine","forest","unemployment","total"]
#keywords["unit"] =["hectar","meter","cubic","volume","cent"]
#keywords["temp"] = ["month","week","year","day","night","period"]
##############################################################
keywords["diff"] =["difference","drop","change","gain","increment","raise","rise","boost","decline","reduction","deteriorate", "fall", "reduce", "grow", "add", "earn","loss"]

keywords["rat"] =["increase","decrease","growth","adjust", "improve","perform","driven","reflect","dividend","part","show","ratio", "relative","higher","up","down"]

keywords["sum"]  =["include","account","overall","exclude", "together", "among","joint","sum"]

keywords["perc"]=["proportion","percentage","fraction","candidate", "gross","respect"]

keywords["finance"] =["stock","net","revenue","income","sale","expense","quarter","cashe","market","cost","financial","company","share","profit","segment","diluted"]
keywords["stats"] = ["census","people","family","parent","children","male","female","count","government","employment","aborigine","forest","unemployment","labour","population","total" ]
keywords["unit"] =["hectar","meter","cubic","volume","cent"]
keywords["temp"] = ["month","week","year","day","night","period"]


for key in keywords.keys():
    keywords[key] = set([sentence_processor.stem(word.lower()) for word in keywords[key]])


#diff_kw = set([sentence_processor.stem(word) for word in diff_kw])
#percent_kw = set([sentence_processor.stem(word) for word in percent_kw])
#sum_kw = set([sentence_processor.stem(word) for word in sum_kw])
#rat_kw = set([sentence_processor.stem(word) for word in rat_kw])


def count_aggr_kw(tokens):
    counts ={}
    for key in keywords.keys():
        counts[key]=0

    for token in tokens:
        token = sentence_processor.stem(token.lower())
        for key, words in keywords.items():
            if token in words:
                counts[key] += 1
                break

    return counts



def isYear(mention):
    mention = mention.strip()
    if re.fullmatch(r'19\d{2}|20[01]\d', mention):# years are not mentions
        return True
    return False

def isQuantity(mention):
    mention = mention.strip()
    #this does not work as it ignore some values!
    #if re.fullmatch(r'19\d{2}|20[01]\d', mention):# years are not mentions
    #        return False
    if re.fullmatch(ur'\(?[+-]?\p{Sc}?\d+([., ]\d+)*\%?\p{Sc}?\)?',mention):
        return True
    if re.fullmatch(r'\(?[+-]?\d+([., ]\d+)*\)?.{1,10}',mention): # accept a number followed by  a word, it might be a unit
        return True
    if re.fullmatch(r'.{1,10}\(?[+-]?\d+([., ]\d+)*\)?',mention): # accept a number proceeded by  a word only 8 characters, it might be a unit
        return True
    if re.fullmatch(r'.{1,10}\(?[+-]?\d+([., ]\d+)*\)?.{1,10}',mention): # accept a number proceeded or followed by  a word only 8 characters, it might be a unit
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
            try:
                json_obj = json.loads(json_line)
                json_objects.append(json_obj)

            except(Exception) as error:
                print(error)
                traceback.print_exc()
    print(" Number of pages loaded : %s"%len(json_objects))
    return json_objects

def load_json_file_once(input_file):
    with codecs.open(input_file,'r') as json_lines:
        json_objects = json.load(json_lines)
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
def read_tsv_file(file_name):
    data = []
    with codecs.open(file_name,'r','UTF-8') as file_content:
        for line in file_content:
            line = line.strip().encode('UTF-8').split('\t')
            data.append(line)
    return data


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
def load_priors_by_mention_id(file_name):
    data ={}
    with codecs.open(file_name,'r','UTF-8') as priors:
        for prior in priors:
            prior = prior.rstrip().split('\t')
            mention_id = prior[2]
            if mention_id in  data:
                data[mention_id].append(prior)
            else:
                data[mention_id] =[prior]
    return data
def load_mention_classifications(file_name):
    data ={}
    with codecs.open(file_name,'r','UTF-8') as classifications:
        for line in classifications:
            line = line.rstrip().split('\t')
            mention_id = line[2].strip()
            if mention_id in  data:
                data[mention_id].append(line)
            else:
                data[mention_id] =[line]
    return data
def get_aggr_fnc_from_id(table_mention_id):
    if 'rat' in table_mention_id:
        return 'rat'
    if 'percentage' in table_mention_id:
        return 'percentage'
    if 'dif' in table_mention_id:
        return 'dif'
    if 'avg' in table_mention_id:
        return 'avg'
    return 'same'






def read_file_as_list(path):
    results = []
    with codecs.open(path,'r','UTF-8') as file_data:
        for line in file_data:
            results.append(line.strip())

    return results

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
def write_category_pages(category, file_name, output_dir, pages):
    file_name = os.path.join(output_dir, category, file_name)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with codecs.open(file_name,'w','UTF-8') as writer:
        for page in pages:
            data = json.dumps(page, ensure_ascii=False)+'\n'

            writer.write(data)
def write_list_as_tsv(file_name, data):
    with codecs.open(file_name,'w','UTF-8') as output:
        for item in data:
            output.write('\t'.join(item)+'\n')

def load_keywords(file_name):
    keywords=[]
    with codecs.open(file_name,'r', 'utf-8') as content:
        for line in content:
            if line.strip() !='':
                keywords.append(line.strip().lower())
    return keywords 
def load_categories_keywords(dir_name):
    cat_keywords ={}
    cat_keywords['finance'] = load_keywords(os.path.join(dir_name,'finance_keywords.txt'))
    cat_keywords['environment']  = load_keywords(os.path.join(dir_name,'environment_keywords.txt'))
    cat_keywords['health'] = load_keywords(os.path.join(dir_name,'health_keywords.txt'))
    cat_keywords['sports'] =  load_keywords(os.path.join(dir_name,'sports_keywords.txt'))
    #cat_keywords['entertainmnet'] = load_keywords(os.path.join(dir_name,'entertainment_keywords.txt'))
    cat_keywords['politics'] = load_keywords(os.path.join(dir_name,'politics_keywords.txt'))
    return cat_keywords
    
def get_category(term_set, cat_keywords):
    max_matches =0
    cat =''
    for category in cat_keywords.keys():
        matches = count_matches(term_set, cat_keywords[category])
        if  matches > max_matches:
            max_matches = matches
            cat = category
    return cat

def count_matches(list1, list2):
    count = 0 
    for term1 in list1:
        for term2 in list2:
            if term1.lower() == term2.lower():
                count = count + 1
    return count
def get_zero_based_scale(string):
    if re.search(ur"($000|\D000's|\D000s)", string):
        return pow(10,3)
    elif re.search(ur"($000000|\D000000's|\D000000s)", string):    
        return pow(10,6)
    return 1

def get_scale_unit(string):# assume the string always lower case
    # ($M) $(million) thousand$ 1000$
    #TODO make this string search faster
    scale = 1
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
    elif re.search(ur"(\bcents\b|\bcent\b)", string):
        scale = 0.01
        unit = '$'  
    elif re.fullmatch(ur'\p{Sc}\d+([.,]\d+)*bn?', string):
        scale = pow(10,9)
    elif re.fullmatch(ur'\p{Sc}\d+([.,]\d+)*mn?', string):
        scale = pow(10,6)
    elif re.fullmatch(ur'\p{Sc}\d+([.,]\d+)*k', string):
        scale = pow(10,3)
    elif re.fullmatch(ur'\(?\p{Sc}?000\'?s(\somitted)?\)?', string):
        scale = pow(10,3)
    elif re.fullmatch(ur'^\(?\p{Sc}?000\'?s.*', string):
        scale = pow(10,3)

    elif '$m' in string:
        scale = pow(10,6)
        unit ='$'
    elif '$b' in string:
        scale = pow(10,9)
        unit = '$'
    elif '$k' in string:
        scale = pow(10,3)
        unit = '$'
    elif u'\xa3m' in string:
        scale = pow(10,6)
        unit ='pound'

    elif u'\xa3b' in string:
        scale = pow(10,9)
        unit ='pound'

    elif u'\xa3k' in string:
        scale = pow(10,3)
        unit='pound'

    if not unit:
        if '$' in string or 'usd' in string or 'dollar' in string:
            unit = '$'
        elif 'eur' in string or u'€' in string or 'euro' in string:
            unit = 'eur'
        elif u'\xa3' in string or 'pound' in string:
            unit='pound'
        elif '%' in string or 'percent' in string or 'per cent' in string:
            unit ='%'
    return (scale, unit)

# TODO load units and measures
#unit_list = set(['%','$','eur'])


#stop_words = load_stop_words('hdfs:///user/yibrahim/stopwords.txt') on the cluster you need to use sc.textFile('hdfs:///user/vagrant/1970-Nixon.txt')
def get_position_in_list(indx, str_list):
    #print("mention strat offset %s"%indx)

    cur_indx =0
    pos =0
    while cur_indx < indx and pos < len(str_list):
        word_length = len(str_list[pos]) 
        if word_length > 1:
            word_length = word_length + 1
        cur_indx = cur_indx + word_length # +1 for punctuation, approx position
        pos = pos + 1
    if pos >= len(str_list):
        return len(str_list)-1
    else:
        return pos

def get_weighted_tokens_overlap(start_offset, tokens_a, tokens_b, step_size, step_weight):
    #print("get weighted tokens overlap for offset: %s"% start_offset)
    #print("tokensa,", tokens_a)
    #print("tokens_b,",tokens_b)
    #print(step_size,step_weight)
    if length_tokens(tokens_a) ==0 or length_tokens(tokens_b)==0: #non stop words and punc. tokens count
        #print("Empty or stop words")
        return 0.0
    
    pos = get_position_in_list(start_offset, tokens_a)
    if pos <0:
        #print("pos is invalid")
        return get_tokens_overlap(tokens_a, tokens_b)
    #print("position is %s"%pos)
    
    overlap_coef = 0.0
    intersection_count = 0.0
    accum_weights = 0.0
    for i in range(len(tokens_a)):
        
        distance = abs(pos -i)
        weight = max(0 , 1.0 - int(distance/step_size) * step_weight)
        if weight == 0 and i < pos:
            continue # no need to explore further context
        if weight ==0 and i > pos:
            break
        token = sentence_processor.stem(tokens_a[i])
        #print(token)
        #print("current term %s, distance: %s, weight %s"%(token,distance,weight))
        if token in stop_words or  token in string.punctuation:
            continue # don't consider

        if token in tokens_b:
            #print("match")
            intersection_count = intersection_count + 1 
            accum_weights = accum_weights + weight
            #print("inter. count: %s, accum_weight %s"%(intersection_count, accum_weights))

    #den = len(tokens_a)+len(tokens_b)-intersection_count
    den =length_tokens(tokens_b) #max(intersection_count, )
    #print(den)
    if den !=0:
         overlap_coef = float(accum_weights)/den
    else:
        overlap_coef = accum_weights/intersection_count # all tokens are the same

    #print("Overlap coeff %s"%overlap_coef)

    return overlap_coef
def length_tokens(tokens):
    n =0 
    for token in tokens:
        if token in stop_words or  token in string.punctuation:
            continue
        n = n+1
    return n

# the first tokens are from text and the second from table
def get_tokens_overlap(tokens_a, tokens_b):
    if len(tokens_a) ==0 or len(tokens_b)==0:
        return 0.0

    overlap_coef = 0.0
    intersection_count = 0
    for token in tokens_a:
        if token in stop_words or  token in string.punctuation:
            continue # don't consider
        token = sentence_processor.stem(token)
        if token in tokens_b:
            intersection_count += 1
    #den = min(len(tokens_a),len(tokens_b))
    #den = len(tokens_a)+len(tokens_b)-intersection_count
    #den = len(tokens_b)
    den = max(intersection_count, length_tokens(tokens_b))

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
def get_aggregate_function_sim(aggr_1, aggr_2):
    #print(aggr_1,aggr_2)
    if aggr_1 == aggr_2:
        #print("matching aggr.")
        return 1
    elif aggr_1 =='rat' and aggr_2 == 'dif':
        #print("matching aggr.")
        return 1
    else:
        return -1

def get_unit_sim(unit_a, unit_b):
    sim =-1.0
    dist = distance.edit_distance(unit_a,unit_b)
    if dist >= min(len(unit_a), len(unit_b)):
        sim = -1.0
    elif dist ==0:
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
    #dist = distance.edit_distance(surfaceform_a, surfaceform_b)
    dist = jarodist.get_jaro_distance(surfaceform_a, surfaceform_b, winkler=True, scaling=0.0)
    sim = dist
    '''if dist ==0:
        sim =1.0
    else:
        sim = 1.0/float(dist+0.2)
    '''
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
    #classifications = load_mention_classifications("mention_classification_test")
    
    print( sentence_processor.stem("Percentage"))
    print( sentence_processor.stem("Cent"))

    print(count_aggr_kw(["percent","ratio","diff","total","sum","cent"]))
    print(count_aggr_kw(["hello"]))
    print(get_scale_unit('6 926 thousand eur'))
    print(get_scale_unit('6 926 thousand $'))
    print(get_scale_unit('6 926 thousand euro'))
    print(get_scale_unit('6 926 cents'))
    print(get_scale_unit('6 per cent'))
    print(get_scale_unit(u'€6 926 thousand euro'))

    print(get_scale_unit('20 percentage'))
    print(get_scale_unit('80 cents'))
    print(get_scale_unit('(000s omitted)'))
    print(get_scale_unit('($000s)'))
    print(get_scale_unit('($000s, except per share amounts)'))
    print(get_scale_unit('(000\'s omitted)'))

    doc= '2012 Financial Results Premium Revenue (in billions) Operating Results Total premium revenue was $15.4 billion for 2012, an increase of 5 percent from 2011. Premium revenue from life insurance increased 4 percent during 2012 and included a 4 percent increase in renewal premiums from inforce policies. Annuity premium increased 12 percent from 2011, while premium revenue for disability and long-term care insurance increased 5 percent and 29 percent, respectively'
    print("length of tokens", length_tokens(['2011', 'one', 'Yusra','contact']))
    #sentences_span = sentence_processor.get_sentences_spans(doc)
    #tokens, nps =sentence_processor.extract_noun_phrases(doc[sentences_span[0][0]: sentences_span[0][1]])
    #mention_start_offset= 136
    #mention_end_offset = 145

    #print(get_weighted_tokens_overlap(6,9,  ['hello','5','kg','world','smile'],['hope', 'smile', 'hello']))
    #print(get_weighted_tokens_overlap(20,24,  ['hello','5','kg','world','smile'],['hope', 'smile', 'hello']))
    #print(get_weighted_tokens_overlap(0,4,  ['5','kg','world','smile', '-','-','-','-','hello'],['hope', 'smile', 'hello']))
    #print(get_weighted_tokens_overlap(6,9,  ['hello','5'],['hope', 'smile', 'hello']))
    #print(get_weighted_tokens_overlap(18,22,  ['hello','-','-','-','-','-','-','5'],['hope', 'smile', 'hello']))    
    #tokens, np = sentence_processor.extract_noun_phrases("this is a test-sentence with number, 5 that has some: context words hope it will work")
    #print(tokens)
    #print(np)
    #tokens2,np2 = sentence_processor.extract_noun_phrases("this is another: sentence, context.")
    #print(tokens2)
    #print(np2)
    #print(get_weighted_tokens_overlap(37, tokens, tokens2))


    #print(sort_cells("4,5,6,7,1,2,3,"))
    #print(sort_cells("1,2,3"))
    #print(sort_cells("4,3,6,10"))

    #file_name = 'test_edges.tsv'
    #data = read_tsv_as_dictionary(file_name)
    #print(data)
    #cells1 = '1,2,3'
    #cells2 = '3,2,1'
    #cells4 = '1,2,'
    #cells3 = '1,2,3,'
    #cells5 = '1,1,2,3,'
    #print is_equal_cells(cells1,cells5)

    #print get_surfaceform_sim('123.4', '125.4')
    #print get_measure_sim('infalation rate', 'rate of infalation')
    print get_unit_sim('km/hr', 'kmh')
    #print get_tokens_overlap(['hello','world','smile'],['hope', 'smile', 'hello'])
    #print get_np_sim(['similar','same','the same'],['the same','similar','same x'])
    #print get_np_sim(['similar','same','the same'],[])

#test()
