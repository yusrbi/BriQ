# -*- coding: utf-8 -*-
import psycopg2
import multiprocessing as mp
from config import config
from document import Document 
import traceback

class Document_Loader:
	#select_documents_sql_stmt =""" 
	#SELECT PAGE_ID, USERSTUDY_DOCUMENT.ID AS DOCUMENT_ID,  TEXT FROM USERSTUDY_DOCUMENT WHERE pool_id in (1,2)  AND USERSTUDY_DOCUMENT.SKIP =FALSE
	#ORDER BY PAGE_ID, USERSTUDY_DOCUMENT.ID;
	#"""
        select_documents_sql_stmt ="""
            SELECT distinct PAGE_ID, USERSTUDY_DOCUMENT.ID AS DOCUMENT_ID,  TEXT FROM USERSTUDY_DOCUMENT 
            WHERE USERSTUDY_DOCUMENT.ID  in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s)
            ORDER BY PAGE_ID, USERSTUDY_DOCUMENT.ID;
        """
	select_tables_sql_stmt = """
            SELECT distinct PAGE_ID, DOCUMENT_ID, TEXT, USERSTUDY_TABLE.ID AS TABLE_ID, USERSTUDY_TABLE.TABLE_ID AS TABLE_NUM, TABLE_HTML, CAPTION AS TABLE_CAPTION 
            FROM USERSTUDY_DOCUMENT
            INNER JOIN USERSTUDY_TABLE ON DOCUMENT_ID = USERSTUDY_DOCUMENT.ID 
            INNER JOIN userstudy_mention_table on userstudy_mention_table.table_id = userstudy_table.id 
            WHERE DOCUMENT_ID in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s) 
            ORDER BY PAGE_ID, DOCUMENT_ID, USERSTUDY_TABLE.ID ;
        """
       # Note that the mention_table id is ordered per mention from the most matching to the least!
       # The tables in userstudy_table are entered by the order of appearance only## This is very important
       # joining with the userstudy_mention_table will limit the tables laoded to the tables that matches the text only!

        """
	SELECT PAGE_ID, DOCUMENT_ID, TEXT, USERSTUDY_TABLE.ID AS TABLE_ID, TABLE_ID AS TABLE_NUM, TABLE_HTML, CAPTION AS TABLE_CAPTION 
	FROM USERSTUDY_DOCUMENT
        INNER JOIN USERSTUDY_TABLE ON DOCUMENT_ID = USERSTUDY_DOCUMENT.ID 
        WHERE  pool_id in (5,7)  AND USERSTUDY_DOCUMENT.SKIP =FALSE 
	ORDER BY PAGE_ID, DOCUMENT_ID, TABLE_ID;
	"""
	select_mentions_sql_stmt = """
            
            select distinct userstudy_mention.id as MENTION_ID, MENTION, text_mention_start_offset as START_OFFSET, text_mention_end_offset  as END_OFFSET
            , DOCUMENT_ID, pool_id 
            from userstudy_mention inner join userstudy_document on document_id = userstudy_document.id 
            where DOCUMENT_ID in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s) 
            order by DOCUMENT_ID, MENTION_ID, START_OFFSET; 
        """
        
        """
	    select userstudy_mention.id as MENTION_ID, MENTION, text_mention_start_offset as START_OFFSET, text_mention_end_offset  as END_OFFSET
	    , DOCUMENT_ID, pool_id 
	    from userstudy_mention inner join userstudy_document on document_id = userstudy_document.id 
	    where annotation_count >=3 and userstudy_mention.skip = false and userstudy_document.skip= False and pool_id in (5,7) order by DOCUMENT_ID, MENTION_ID, START_OFFSET;
	"""
        select_mention_ground_truth = """
           select document_id, table_id, mention_id , relation, related_table_cells, count 
           from mention_ground_truth where count > 1 
           and DOCUMENT_ID in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s)  
           order by document_id, table_id, mention_id ;
        """ #20464 40 something table
	def __init__(self, batch_size=50):
                self.limit= batch_size
                self.offset = 0 
        
        def get_batch(self):
            if self.documents_map:
                return self.documents_map.values()
            else:
                return None

        def load_next_batch(self):
            result = False
            try:
                self.loadDocumentsFromDatabase()
                self.offset = self.offset + self.limit
                if len(self.documents_map) > 0:
                    result = True
                else:
                    result = False

            except:
                result = False
            return result

	#def load(self):
	#	self.loadDocumentsFromDatabase()
	#	return self.documents_map
	
	def iter_doc(cursor, size=1000):
		while True:
			rows = cursor.fetchmany(size)
			if not rows:
				break
			for row in rows:
				yield row

	def loadDocumentsFromDatabase(self):
		conn = None
		id =-1
		documents_map ={}
		try:
			params= config()
			conn = psycopg2.connect(**params)
			cur = conn.cursor()
			cur.execute(Document_Loader.select_tables_sql_stmt%(self.limit, self.offset))
			for document in cur.fetchall():
				page_id = document[0]
				doc_id = document[1]
				text = document[2].decode('utf-8')
				table_id = document[3]
				table_num = document[4]
				table_html = document[5].decode('utf-8')
				table_caption = document[6].decode('utf-8')
				if doc_id in documents_map:
					doc = documents_map[doc_id]
				else:
					doc = Document(page_id, doc_id, text)	
					print "Creating New Doc %s"%str(doc_id)
                                        documents_map[doc_id] = doc				
				doc.add_table(table_id,table_num, table_html, table_caption)
			cur.execute(Document_Loader.select_mentions_sql_stmt%(self.limit, self.offset))
			for mention in cur.fetchall():
				mention_id = mention[0]
				mention_text = mention[1].decode('utf-8')
				start_offset = mention[2]
				end_offset = mention[3]
				doc_id = mention[4]
                                if doc_id in documents_map:
					doc = documents_map[doc_id]
					doc.add_mention( mention_id, mention_text, start_offset, end_offset)
                        cur.execute(Document_Loader.select_mention_ground_truth%(self.limit, self.offset))
                        for gt in cur.fetchall():
                            doc_id = gt[0]
                            table_id = gt[1]
                            mention_id = gt[2]
                            relation = gt[3].decode('utf-8').strip()
                            related_cells = gt[4]
                            count = int(gt[5])
                            if doc_id in documents_map:
                                doc = documents_map[doc_id]
                                doc.add_ground_truth(mention_id, table_id, relation, related_cells, count)

			cur.close()
			conn.close()
		except (Exception, psycopg2.DatabaseError) as error:
			print(error)
			traceback.print_exc()
                        raise 
		finally:
			self.documents_map = documents_map
			if conn is not None:
				conn.close()

#TODO load the Ground Truth

