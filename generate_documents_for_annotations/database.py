# -*- coding: utf-8 -*-
import psycopg2
from lxml import html,etree
from config import config 

page_insert_sql_stmt =""" INSERT INTO userstudy_page(page_id,page_url,html_content,title,category,category_kw_count)
	VALUES (%s,%s,%s,%s,%s,%s) RETURNING id; """
document_insert_sql_stmt ="""INSERT INTO userstudy_document(text, page_id,skip,exact_match_count,has_table_reference)
    VALUES  (%s, %s,'False',%s,%s) RETURNING id; """
mention_insert_sql_stmt =""" INSERT INTO userstudy_mention(
             mention, text_mention_start_offset, text_mention_end_offset, 
            document_id,annotated,skip)
    VALUES (%s, %s, %s,%s,'False','False') RETURNING id;
"""
mention_table_insert_sql_stmt =""" INSERT INTO userstudy_mention_table(related,  mention_id, table_id)
    VALUES ('True',%s, %s) RETURNING id;"""
table_insert_sql_stmt =""" INSERT INTO userstudy_table(
            table_html, table_id,nrows,ncols,ncells, document_id, referenced_in_text, caption)
    VALUES (%s, %s,%s,%s,%s, %s,%s, %s) RETURNING id;"""

def write_page(page_id,page_url, page_html_content,title,category,category_kw_counts):
	page_pk = insert (page_insert_sql_stmt, (page_id,page_url,page_html_content,title,category,category_kw_counts))
	return page_pk
def write_mention(doc_pk,mention):
	mention_pk = insert(mention_insert_sql_stmt, (mention.mention,mention.start_offset,mention.end_offset,doc_pk))
	return mention_pk
def write_mentions(doc_pk, mentions):
	mention_id_pk_map ={}
	for mention in mentions:
		mention_pk = write_mention(doc_pk, mention)
		mention_id_pk_map[mention.start_offset] = mention_pk
	return mention_id_pk_map
def write_table(doc_pk, table,ref_in_text):
	table_pk = insert(table_insert_sql_stmt, (etree.tostring(table.table).decode("utf-8"),table.table_id,table.nrows,table.ncolumns,table.ncells,doc_pk,ref_in_text, table.caption))
	return table_pk
def write_document(page_pk, text_block, exact_count, has_table_ref):
	return insert(document_insert_sql_stmt, (text_block,page_pk,exact_count, has_table_ref))

def write_mention_table(doc_pk, mention_table_pairs,mention_id_pk_map, table_id_pk_map):
	for mention, table,_  in mention_table_pairs:
		mention_pk = mention_id_pk_map[mention.start_offset]
		if mention_pk ==-1 :
			continue
		table_pk = table_id_pk_map[table.table_id]
		if table_pk ==-1:
			continue
		insert(mention_table_insert_sql_stmt, (mention_pk,table_pk))
def write_tables(doc_pk, tables_list):
	table_id_pk_map ={}
	for table,_,ref_in_text  in tables_list:
		table_pk = write_table(doc_pk, table,ref_in_text)
		table_id_pk_map[table.table_id] = table_pk
	return table_id_pk_map

def write_to_DB(page_pk, text_block, mentions, tables):
	
	#print '<html><body>'
	#print text_block.encode('UTF-8')
	#print mentions	
	sorted_tables = sorted(tables, key=lambda tup:tup[2],reverse=True)
	doc_pk = insert(document_insert_sql_stmt, (text_block,page_pk))
	if doc_pk ==-1:
		return	
#	print "page pk = %d, document pk = %d" %(page_pk,doc_pk)
	mentions_pks =[]
	for mention in mentions:
		mention_pk = insert(mention_insert_sql_stmt, (mention.mention,mention.start_offset,mention.end_offset,doc_pk))
		if mention_pk !=-1:
			mentions_pks.append(mention_pk)
	tables_pks =[]
	for table_id, table, num_matches in sorted_tables:
		table_pk = insert(table_insert_sql_stmt, (etree.tostring(table),table_id,doc_pk))
		if table_pk !=-1:
			tables_pks.append(table_pk)
		#print num_matches
		#print etree.tostring(table)
	#print '</body></html>'
	for mention_pk in mentions_pks:
		for table_pk in tables_pks:
			insert(mention_table_insert_sql_stmt, (mention_pk,table_pk))

def insert(sql_stmt, values):
	conn = None
	id =-1
	try:
		params= config()
		conn = psycopg2.connect(**params)
		cur = conn.cursor()
		cur.execute(sql_stmt,values)
		id = cur.fetchone()[0]
		conn.commit()
		cur.close()
		conn.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
#	print (sql_stmt)
#	print (values)
	return id
#	return 1
