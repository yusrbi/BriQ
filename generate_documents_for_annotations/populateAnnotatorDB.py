# -*- coding: utf-8 -*-
import os
import glob 
import sys
import utils
from lxml import html,etree
import regex as re
from mention_extractor import  extract_mentions_from_text,  test_mentions_extraction_2
import database
from html_parser import HTMLPage
#This code is used to populate the database for the annotation app!

#This file process a set of web pages as follows:
# * It first extracts all the table and text
# * Then it segments the text into blocks 
# * Then for each text block it finds all related tables 
# * Text blocks with no related tables are discarded
# * For quantity recogonition it define a set of Regexs to include/exclude and a specific ordering among them.
# * It execute the regex in order on the text and identifies all potential entiites 
# * for each entity it looks for the most related table(s) using string overlap 
# * It then writes the entity-table pairs to the Database along with their page,text block(document), etc
'''
class Table:
	def __init__(self,table, table_id, word_set):
		self.table = table
		self.table_id = table_id
		self.word_set = word_set
	def __str__(self):
		return ' '.join( w for w in self.word_set)#etree.tostring(self.table,pretty_print=True).decode('utf-8')
'''
class Document:
	def __init__ (self, text, word_set, mentions,table_ref):
		self.text = text 
		self.word_set = word_set
		self.mentions = mentions
		self.table_ref = table_ref
	def __str__(self):
		m =''
		for mention in self.mentions:
			m  = m+ " ["+mention.mention+"]"
		return "text:"+self.text +"\nmentions:"+m+"\n"



categories_count ={}

def get_mentions(text):
	mentions=[]
         #print text +'\n'
	text = text.replace(u'\xa0',' ')
	for match in re.finditer(r"(?:[\s\.\,\?\!\;\(])(([\<\>\~\+\-]\s?)?(\p{Sc}\s?)?\d+([\.\,]\d+)*(\s?\p{Sc})?(\%|(\s?[Pp]er\s?cent))?((\s[mM]illions?|\s[tT]housands?|\s[hH]undereds?|\s[bB]illions?|\s?[Tt]|\s?[Mm]n?|\s?[Kk]|\s?[Bb]n?)\b)?)\)?",text):
		#print match.group(0)

		if re.match( r'\(?\s?(19\d{2}|20\d{2})\s?\)?',match.group(0).strip()):
			continue #skip years, and dates too!TODO
		#skip tables, figures, sections step comments etc.
		mention = (match.start(),match.end(), match.group(0).strip())
		mentions.append(mention)
	return mentions
'''
def get_tables(json_obj):
	try:
		root = html.document_fromstring(json_obj['fullText'].encode('utf-8'))
	except:
		return None, None, None
	titles = root.xpath("//title")
	page_title=''
	for title in titles:
		page_title = title.text_content()
		break
	#print (page_title)
	tables = root.xpath('//table')
	selected_tables = []
	table_id =1
	for table in tables:
		count_cells =0
		count_cells_with_numbers=0
		if table.xpath('.//table')!=[]:
			#skip table that has nasted tables 
			continue
		else :
			#print table.text_content()
			table_words =[]
			for cell in table.xpath('.//td|.//th'):
				for br in cell.xpath(".//br"):
					br.tail = " " + br.tail if br.tail else " "
				content =  cell.text_content().strip().lower()
				#content =  re.sub(r'\<\s?br\s?\/?\>',' ',content)
				count_cells+=1	
				if len(content) < 1:
					continue 
				#  and  not re.fullmatch(r'\p{Sc}?\d+([.,]\d+)?\%?\p{Sc}?', content):
				#	table_words.extend(get_non_stop_words( content.split(' ')))
				if re.fullmatch(r'\p{Sc}?\d+([.,:\-\–\-\−\±]\d+)?\%?\p{Sc}?',content):
					#count cells that has numerical values
					count_cells_with_numbers+=1
				else:
					table_words.extend(utils.filter_stop_words( content.split(' ')))
			word_set = set(table_words)			
			if count_cells <= 100 and count_cells>8 and  float(count_cells_with_numbers)/count_cells >= 0.4:
				selected_tables.append(Table(table,table_id,word_set))
				table_id+=1
			table.getparent().remove(table)
	scripts = root.xpath('//script')
	if scripts:
		for script in scripts:
			script.getparent().remove(script)
	styles = root.xpath('//style')		
	if styles:
		for style in styles:
			style.getparent().remove(style)

	return selected_tables, root.text_content(),page_title '''
def has_number(text):
	match = re.search(r"([\d\%\$\.\,\-]+)",text)
	if match:
		return True
	else:
		return False
def count_char(text, c):
	count =0 
	for ch in text:
		if ch ==c:
			count+=1
	return count
def get_text_blocks(text):
	text_blocks = re.split(r'(?:[\.\;](?:\n|\r\n|\r)|(?:\n|\r\n|\r){2,})',text)
	docs =[]
	#check on a single \n ommit all the lists!
	for block in text_blocks:
		block = re.sub('\s{2,}',' ', block.strip())
		if block is '' or not has_number(block):
			continue
		if len(block)< 100 or len(block)>1000:
			continue
		if count_char(block,'\n') > 4:
			continue # most likely it is a list
		#block = re.sub(r'\r\n|\n',' ', block)
		#print(block)
		mentions = extract_mentions_from_text(block)
		if len(mentions)<2:
			continue
		word_set = utils.get_word_set(block) #set(utils.filter_stop_words(block.lower().split(' ')))
		table_references =[]
		for match in re.finditer(r'[tT]able\.? ?\d+(\.\d+)*',block):
			table_references.append(match.group(0))

		docs.append(Document(block,word_set,mentions,table_references))

	return docs


	


def filter_selections(text,mentions,tables):
	selected_tables =[]
	if len(mentions)<1:
		return []#no mentions to match
	for table_id,table, num_matches in tables:
		#check if table matches the text?TODO
		#print etree.tostring(table, pretty_print = True)
		selected_tables.append((table_id,table,num_matches))
	return selected_tables


def find_matching_mention_table(mentions, possible_related_tables,text):
	pairs=[]
	#count = 0
	#print("New Document:")
	exact_count =0
	global_max_matches =0
	for mention in mentions:
		sentence = text[mention.sent_start_offset:mention.sent_end_offset]
		
		words = utils.get_word_set(sentence) # set(utils.filter_stop_words(words))
		max_n_matches = -1
		max_matched_tables =[]
		ref_tables=[]
		#print("Mention: {}".format(mention.mention))
		for table,n,table_ref in possible_related_tables:
			#print(str(table))
			n_matches = utils.overlap(words, table.word_set)
			if (n_matches >=2) and (table_ref or n_matches >= max_n_matches):
				if table_ref:
					#print("Table ref.")
					ref_tables.append((table,n_matches+1))
					continue
				if n_matches > max_n_matches:
					#print("More matches")
					max_matched_tables =[]
				max_matched_tables.append((table,n_matches))
				max_n_matches = n_matches
				global_max_matches = max(global_max_matches,max_n_matches)
		#paired = False
		max_matched_tables.extend(ref_tables)

		for table, nmatches  in max_matched_tables:
			#print("matched: %d"%max_n_matches)
			#print(table.word_set)
			#print(words)
			#paired = True
			#check if the table has a reasonable size that the user can work with 
			if table.ncells > 150:
				continue
			#is this mention in the table ==> prefer this 
			if mention.mention in table.quantities:
				exact_count+=1
				#exact match
				#print ("mention found in table:%s"%mention.mention)
			#else:
				#print ("mention NOT  found in table:%s"%mention.mention)
			pairs.append((mention,table,nmatches))
		#if paired:
		#	count+=1
	pairs.sort(key = lambda r : r[2],reverse=True)	
	if len(ref_tables) > 0 or exact_count > 1 or global_max_matches > 4:
	# if there exist a table ref. in text or there is an exact mention matched or there is enough cues that they are related
		#print("mentions has matches, exacte %d, count: %d"%(exact_count, global_max_matches))
		return pairs,exact_count
	else:
		#print("No matches returned")
		return [],0
def load_processed_urls():
	urls={}
	try:
		urls = utils.load_file_as_dictionary("processed_urls.txt")
	except:
		urls ={}
	return urls
def write_processed_urls(urls):
	try:
		utils.write("processed_urls.txt",urls)

	except:
		return -1
	return 0

def is_table_ref_in_text(doc, table):
	for table_ref in doc.table_ref:
		if table.caption_contains(table_ref):
			return True
	return False
	
def process_file(input_file):
	global categories_count
	json_objects = utils.load_json_file(input_file)
	count_docs =0
	processed_urls= load_processed_urls()	
	min_cells =0 #10
	max_cells =0 #100
	max_rows =20
	min_rows =2
	max_col = 20
	min_col = 2
	percent_quantity_cells = 0.4
	for json_obj in json_objects:
		#json_obj.pop("tableMentions", None)
		#json_obj.pop("matches",None)
		#json_obj.pop("CountMentionswithCandidates",None)
		html = json_obj['fullText']
		#utils.save_file('file.html',html)
		page = HTMLPage(html)
		#tables= page.get_all_tables()
		tables = page.get_tables(min_rows,max_rows,min_col,max_col,min_cells,max_cells,percent_quantity_cells)
		full_text = page.content
		
		page_title = page.title
		if not tables:
			continue
		documents = get_text_blocks(full_text)
		#if len(documents) < 2 or len(documents) > 15:
		#	continue

		url = json_obj["url"]
		category = json_obj["category"]
		category_kw_counts = json_obj["category_support_word_count"]

		if url in processed_urls:
			continue
		else:
			processed_urls[url]=1
		
		page_id = json_obj["docID"]
		table_id = json_obj["tableNum"]
		page_created = False
		page_pk =-1
		for document in documents:
			if len(document.mentions) <=0:
				continue
			matching_tables =[]
			table_id=1
			doc_with_table_ref = False
			for table in tables:
				n = utils.overlap(table.word_set, document.word_set)
				if n >1:
					has_table_ref = False
					if is_table_ref_in_text(document, table):
						has_table_ref = True
						doc_with_table_ref = True
					matching_tables.append((table,n,has_table_ref))
			# End for loop on tables 
			#print(str(document))
			#print("Text :{}".format(document.text))

			mention_table_pair,exact_count = find_matching_mention_table(document.mentions, matching_tables,document.text)
			#print(f"Text :{document.text}")
			if len(mention_table_pair) > 1:
				if not page_created:
					if category in categories_count:
						categories_count[category] = categories_count[category]+1
					else:
						categories_count[category] = 1
					page_pk = database.write_page(page_id,url, html,page_title,category,category_kw_counts)
					page_created=True
				if page_pk ==-1:
					break
				doc_pk = database.write_document(page_pk, document.text,exact_count, doc_with_table_ref)
				#print("text: %s, exact_count:%d, table refs: %s"%(str(document),exact_count,doc_with_table_ref))
				count_docs+=1
				table_id_map = database.write_tables(doc_pk, matching_tables)
				mention_id_map = database.write_mentions(doc_pk, document.mentions)
				database.write_mention_table(doc_pk, mention_table_pair,mention_id_map,table_id_map)
				#database.write_to_DB(page_pk,text_block,mentions, matching_tables) 
				#utils.write_as_html(url,page_id,text_block,mentions, matching_tables)
		###End for loop on text blocks
	#utils.save_json(input_file.replace(".json", "_mod.json"), json_objects)
	write_processed_urls(processed_urls.keys())
	print("Total Generated Documents: %d"%count_docs)
def main():
	global categories_count
	input_folder= sys.argv[1]
	files = [file_name for file_name in glob.glob(os.path.join(input_folder,'*.json'))]
	for file_name in files:
		print ("processing file %s"%file_name)
		process_file(file_name)
	#print("Categories : Number of Pages")
	for category,count in categories_count.items():
		print("%s : %d"%(category,count))
	
def test_overlap():
	set1 = set(utils.filter_stop_words(["the","yes","same","is","xyz"]))
	set2 = set(utils.filter_stop_words(["same","the","No","si","xyz"]))
	print (utils.overlap(set1,set2))
def test():
	document ={}
	html =''
	with codecs.open('sample_page.html','r','UTF-8') as example:
		for line in example:
			html += line	
	document['fullText'] = html
	tables = get_tables(document)
	if(tables!= None and  len(tables) !=2):
		print ("Wrong!")
		return
def test_has_number():
	print ("has number 'the 20 percent  of the '  %r"% has_number('the 2004 of the '))
	print ("has number  'the \$123 million dreams' %r"% has_number('the $123 million dreams'))
	print ("has number 'and now it is -12 less' %r"% has_number(' and now it is -12 less'))
	print ("has number 'it was 1.5c '  %r"% has_number('it was 1.5c '))
	print ("has number 'it was No number '  %r"% has_number('it was No Number '))

def test_regex():
	text = "In response to the devastating impact that suicide has on families and communities, the U.S. Surgeon General issued a public health call to action for suicide prevention in 1999.1 However, research that examined suicides between 1986 and 2005 showed that the overall suicide rate declined an average of 1.2 percent each year between 1986 and 1999 and then increa sed an average of 0.7 percent between 1999 and 2005.2 The increase between 1999 and 2005 was caused primarily by the increased suicide rates among white persons aged 40 to 64, a demographic not commonly perceived as high risk. Specifically, suicide rates during this time period increased in this age group by 2.7 percent annually for white men and 3.9 percent annually for white women.\nCompleted suicides represent only part of this public health problem. Suicide attempts remain one of the most important risk factors for completed suicides.3.8,22\n\nEmergency department (ED) data provide a window into recent trends for suicide attempts that were serious enough to necessitate emergency treatment. Between 1992 and 2001, there was a 47 percent increase in all suicide attempts. 4  More recent data from the Drug Abuse Warning Network (DAWN) show that the number of ED visits for drug-related suicide attempts increased 21 percent from 2005 to 2006, with the most recent (34%)"
	print (text)
	text_blocks = re.split(r'(?:[\.](?:\n|\r\n|\r)|(?:\n|\r\n|\r){2,})',text)
	text_with_word_set =[]
	for block in text_blocks:	
		print (block)
	content ="Percent<br>Aged 65 or Older"
	content =  re.sub(r'\<\s?br\s?\/?\>',' ',content)
	print (content)
	#print re.fullmatch(r'\p{Sc}?\d+([.,]\d+)?\%?\p{Sc}?',"$14234,23")
	#print re.fullmatch(r'\p{Sc}?\d+([.,]\d+)?\%?\p{Sc}?',"2.3")
	#print re.fullmatch(r'\p{Sc}?\d+([.,]\d+)?\%?\p{Sc}?',"1,3003")

if __name__ == '__main__':
	#test()
#	test_mentions_extractor()
#	test_mentions_extraction_2()
	main()
	#test_regex()
	#test_has_number()
	#test_overlap()
