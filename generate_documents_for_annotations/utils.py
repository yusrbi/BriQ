# -*- coding: utf-8 -*-
import os
import json 
import codecs
import sys
import glob 
import regex as re


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

stop_words = load_stop_words('stopwords.txt')
