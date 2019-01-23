# -*- coding: utf-8 -*-
import psycopg2
import multiprocessing as mp
#from config import config
from document import Document 
from html_page import HtmlPage
import traceback
import os
import glob 
import sys
import utils
import json
from config import config
class Document_Loader:
    #select_documents_sql_stmt =""" 
    #SELECT PAGE_ID, USERSTUDY_DOCUMENT.ID AS DOCUMENT_ID,  TEXT FROM USERSTUDY_DOCUMENT WHERE pool_id in (1,2)  AND USERSTUDY_DOCUMENT.SKIP =FALSE
    #ORDER BY PAGE_ID, USERSTUDY_DOCUMENT.ID;
    #"""
    #select_documents_sql_stmt ="""
    #        SELECT distinct PAGE_ID, USERSTUDY_DOCUMENT.ID AS DOCUMENT_ID,  TEXT FROM USERSTUDY_DOCUMENT 
    #        WHERE USERSTUDY_DOCUMENT.ID  in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s)
    #        ORDER BY PAGE_ID, USERSTUDY_DOCUMENT.ID;
    #    """
    test_doc_ids='4543,8424,17472,19547,15908,27287,9772,1833,1834,10182,4147,3796,11115,36092,20960,31107,31759,30331,16168,28109,25061,15936,5063,25065,20458,31540,26849,6225,10052,17399,26736,3330,265,2263,17405,25458,23371,29754,31666,34935,15004,34316,23282,17804,32761,13698,23266,19971,25990,20502,19979,17142,25443,11368,30395,7434,31106,29528,17096,11937,420,28489,32228,31109,29296,21110,21117,32773,16121,1332,1178,34744,26993,1727,29301,1846,20583,29389,14381,331,24950,26500,1875,15003,8294,21608,1871,28181,26984,26985,4741,20463,25725,30330,7551,9133,19338,9131,25645,27873,23234,26978,25650,31537,35675,13804,5558,28579,1188,2894,2891,24276,22296,1748,20809,1747,8938,30031,13345,30327,25641,22758,22298,6628,9750,20460,5889,6624,33099,15066,31829,29408,8926,3974,1154,18527,16023,1752,20708,18549,18301,32049,18546,34016,22063,20266,20574,34381,21889,35393,5633,30733,22756,30738,25768,10945'
    select_tables_sql_stmt_test = """
            SELECT distinct PAGE_ID, DOCUMENT_ID, TEXT, USERSTUDY_TABLE.ID AS TABLE_ID, USERSTUDY_TABLE.TABLE_ID AS TABLE_NUM, TABLE_HTML, CAPTION AS TABLE_CAPTION 
            FROM USERSTUDY_DOCUMENT
            INNER JOIN USERSTUDY_TABLE ON DOCUMENT_ID = USERSTUDY_DOCUMENT.ID 
            INNER JOIN userstudy_mention_table on userstudy_mention_table.table_id = userstudy_table.id 
            WHERE DOCUMENT_ID in (%s) 
            ORDER BY PAGE_ID, DOCUMENT_ID, USERSTUDY_TABLE.ID ;
    """%test_doc_ids


    select_tables_sql_stmt = """
            SELECT distinct PAGE_ID, DOCUMENT_ID, TEXT, USERSTUDY_TABLE.ID AS TABLE_ID, USERSTUDY_TABLE.TABLE_ID AS TABLE_NUM, TABLE_HTML, CAPTION AS TABLE_CAPTION 
            FROM USERSTUDY_DOCUMENT
            INNER JOIN USERSTUDY_TABLE ON DOCUMENT_ID = USERSTUDY_DOCUMENT.ID 
            INNER JOIN userstudy_mention_table on userstudy_mention_table.table_id = userstudy_table.id 
            WHERE DOCUMENT_ID in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s) 
            ORDER BY PAGE_ID, DOCUMENT_ID, USERSTUDY_TABLE.ID ;
    """
    select_tables_sql_stmt_test_docs = """
        SELECT distinct PAGE_ID, DOCUMENT_ID, TEXT, USERSTUDY_TABLE.ID AS TABLE_ID, USERSTUDY_TABLE.TABLE_ID AS TABLE_NUM, TABLE_HTML, CAPTION AS TABLE_CAPTION 
        FROM USERSTUDY_DOCUMENT
        INNER JOIN USERSTUDY_TABLE ON DOCUMENT_ID = USERSTUDY_DOCUMENT.ID 
        INNER JOIN userstudy_mention_table on userstudy_mention_table.table_id = userstudy_table.id 
        WHERE DOCUMENT_ID in (select distinct document_id from mention_ground_truth 
            inner join userstudy_document on document_id = userstudy_document.id
            where count >=2 and  (page_id %10) = 7) 
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
    select_mentions_sql_stmt_test = """
            
            select distinct userstudy_mention.id as MENTION_ID, MENTION, text_mention_start_offset as START_OFFSET, text_mention_end_offset  as END_OFFSET
            , DOCUMENT_ID, pool_id 
            from userstudy_mention inner join userstudy_document on document_id = userstudy_document.id 
            where DOCUMENT_ID in (%s) 
            order by DOCUMENT_ID, MENTION_ID, START_OFFSET; 
    """%test_doc_ids

    select_mentions_sql_stmt = """
            
            select distinct userstudy_mention.id as MENTION_ID, MENTION, text_mention_start_offset as START_OFFSET, text_mention_end_offset  as END_OFFSET
            , DOCUMENT_ID, pool_id 
            from userstudy_mention inner join userstudy_document on document_id = userstudy_document.id 
            where DOCUMENT_ID in (select distinct document_id from mention_ground_truth where count > 1 order by document_id limit %s offset %s) 
            order by DOCUMENT_ID, MENTION_ID, START_OFFSET; 
    """
    select_mentions_sql_stmt_test_docs ="""
        select distinct userstudy_mention.id as MENTION_ID, MENTION, text_mention_start_offset as START_OFFSET, text_mention_end_offset  as END_OFFSET
        , DOCUMENT_ID, pool_id 
        from userstudy_mention inner join userstudy_document on document_id = userstudy_document.id 
        where DOCUMENT_ID in ( select distinct document_id from mention_ground_truth 
            inner join userstudy_document on document_id = userstudy_document.id
            where count >=2 and (page_id %10) = 7)
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
    select_mention_ground_truth_test = """
           select document_id, table_id, mention_id , relation, related_table_cells, count 
           from mention_ground_truth where count > 1 
           and DOCUMENT_ID in (%s)  
           order by document_id, table_id, mention_id ;
    """ %test_doc_ids
    select_mention_ground_truth_test_docs = """
           select document_id, table_id, mention_id , relation, related_table_cells, count 
           from mention_ground_truth where count > 1 
           and DOCUMENT_ID in (select distinct document_id from mention_ground_truth 
           inner join userstudy_document on document_id = userstudy_document.id
           where count >=2 and  (page_id %10) = 7)
           order by document_id, table_id, mention_id ;
    """


        
    def __init__(self, batch_size, list_of_files):
                self.limit= batch_size
                self.offset = 0 
                self.files = list_of_files #[file_name for file_name in glob.glob(os.path.join(path,'**/*.json'), recursive=True)]
                print(self.files)
                self.documents = None
                self.json_objects = None
                self.buffer = []
                self.file_indx =0
                
    def get_batch(self):
        return self.documents
    def get_json_objects(self):
        return self.json_objects


    def load_next_json_objects_by_page(self):
        result = False
        print("offset %s and limit %s"%(self.offset,self.limit))
        try:
            self.json_objects = None
            if not self.buffer:
                self.buffer = self.load_next_file()
            if self.buffer:
                start = 0
                end = min(self.limit, len(self.buffer))
                self.json_objects = self.buffer[start:end]
                self.buffer = self.buffer[end:]
                self.offset = self.offset + self.limit
                print("Loaded %s pages"%len(self.json_objects))
                result = True
        except(Exception) as error:
            print(error)
            traceback.print_exc()
            result = False
        return result


    def load_next_file(self):

        while self.file_indx < len(self.files) and not self.load_next_json_file():
            self.file_indx = self.file_indx +1
        self.file_indx = self.file_indx+1

        return self.json_objects


    def load_next_json_file(self):
        self.json_objects = None

        input_file = self.files[self.file_indx]
        print("Loading file %s"%input_file)
        try:
            json_objects = utils.load_json_file(input_file)
            print(" %s json objects were loaded"%len(json_objects))
            self.json_objects = json_objects
        except(Exception) as error:
            print(error)
            traceback.print_exc()
            return False

        return True
        



    def load_next_josn_objects_batch(self):
        result = False
        print("offset %s and limit %s"%(self.offset,self.limit))
        try:
            self.json_objects = None
            while self.offset < len(self.files) and not self.load_json_objects():
                self.offset = self.offset + self.limit
            self.offset = self.offset + self.limit

            if  self.json_objects:
                result = True
            else:
                print("No Objects were loaded")
                result = False

        except(Exception) as error:
            print(error)
            traceback.print_exc()
            result = False
        return result
    
    def load_next_batch(self):
        result = False
        try:
            self.loadDocumentsFromDatabase()
            self.offset = self.offset + self.limit
            if  self.documents and len(self.documents) > 0:
                result = True
            else:
                result = False

        except:
            result = False
        return result

    def collect_statistics(self):
        table_stats ={'max':0,'min':10000,'total':0}
        mention_stats ={'max':0,'min':10000,'total':0}
        pages_count = 0
        documents_count = 0

        for input_file in self.files:
            try:
                json_objects = utils.load_json_file(input_file)
            except:
                continue
            n =0 
            for json_obj in json_objects:
                html_content = json_obj['fullText']

                if html_content:
                    html_page = HtmlPage(html_content, pages_count)
                    page_docs = html_page.create_documents()
                    if not page_docs:
                        continue
                    pages_count = pages_count +1

                    documents_count = documents_count + len(page_docs)
                    #min number of tables per page
                    tables_count = html_page.get_tables_count()
                    mentions_count = html_page.get_mentions_count()
                    if tables_count < table_stats['min']:
                        table_stats['min'] = tables_count
                    if mentions_count < mention_stats['min']:
                        mention_stats['min'] = mentions_count
                    #min number of tables per page
                    if tables_count > table_stats['max']:
                        table_stats['max'] = tables_count
                    if mentions_count > mention_stats['max']:
                        mention_stats['max'] = mentions_count
                    # add counts to total
                    table_stats['total'] = table_stats['total'] + tables_count
                    mention_stats['total'] = mention_stats['total'] + mentions_count
                print("Updates for page: %s"%pages_count)
                print("Total Number of documents: %s"%documents_count)
                print("Tables : max, min, total :%s, %s, %s"%(table_stats['max'],table_stats['min'], table_stats['total']))
                print("Mentions: max, min, total: %s, %s, %s"%(mention_stats['max'], mention_stats['min'], mention_stats['total']))
                print("-------------------------------------------")
            sys.stdout.flush()

    def separate_pages_by_category(self, output_dir):
        categories_buffers ={}
        cat_keywords = utils.load_categories_keywords('resources')
        category_counter ={}
        for input_file in self.files:
            json_objects = utils.load_json_file(input_file)
            for json_obj in json_objects:
                category = utils.get_category(json_obj['termSet'],cat_keywords)
                if category in categories_buffers:
                    categories_buffers[category].append(json_obj)
                    if len(categories_buffers[category]) >= 1000:
                            file_name = "part"+ str(category_counter[category]).zfill(7)
                            utils.write_category_pages(category, file_name, output_dir, categories_buffers[category])
                            categories_buffers[category] = []
                            category_counter[category] = category_counter[category] + 1


                else:
                    categories_buffers[category] =[json_obj]
                    category_counter[category] = 0
        for category, pages in categories_buffers.items():
            if len(categories_buffers[category]) > 0:
                file_name = 'part'+ str(category_counter[category]).zfill(7)
                utils.write_category_pages(category,file_name, output_dir, pages)
                category_counter[category] = category_counter[category] + 1
    def loadDocuments(self):
        documents = []
        try:
            start = self.offset
            end = min(len(self.files),self.offset + self.limit)
            for i in range(start,end):
                input_file = self.files[i]
                #text_file_content = self.sc.textFile('hdfs:///user/yibrahim/'+input_file)
                #print(text_file_content)
                try:
                    json_objects = utils.load_json_file(input_file)
                except:
                    continue

                html_pages = map(lambda json_obj: HtmlPage(json_obj['fullText']), json_objects)
                documents = map(lambda page: page.create_documents(),html_pages)
                documents = [ doc for  doclist in documents for doc in doclist]

                #for json_obj in json_objects:
                #    html_content = json_obj['fullText']
                #    if html_content:
                #        html_page = HtmlPage(html_content, i)
                #        documents.extend(html_page.create_documents())
        except (Exception) as error:
            print(error)
            traceback.print_exc()
            raise 

        print ("loaded %s documents"%len(documents))
        self.documents = documents
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
            self.documents = documents_map.values()
            if conn is not None:
                conn.close()
                
                
    def loadTestDocumentsFromDatabase(self):
        conn = None
        id =-1
        documents_map ={}
        try:
            params= config()
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            cur.execute(Document_Loader.select_tables_sql_stmt_test_docs)
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
            cur.execute(Document_Loader.select_mentions_sql_stmt_test_docs)
            for mention in cur.fetchall():
                mention_id = mention[0]
                mention_text = mention[1].decode('utf-8')
                start_offset = mention[2]
                end_offset = mention[3]
                doc_id = mention[4]
                if doc_id in documents_map:
                    doc = documents_map[doc_id]
                    doc.add_mention( mention_id, mention_text, start_offset, end_offset)
            cur.execute(Document_Loader.select_mention_ground_truth_test_docs)
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
            self.documents = documents_map.values()
            if conn is not None:
                conn.close()
        return self.documents
    

        

    def load_json_objects(self):
        all_json_objects = []
        try:
            start = self.offset
            end = min(len(self.files),start + self.limit)
            for i in range(start,end):
                input_file = self.files[i]
                print("Loading file %s"%input_file)
                try:
                    json_objects = utils.load_json_file(input_file)
                    print(" %s json objects were loaded"%len(json_objects))

                except(Exception) as error:
                    print(error)
                    traceback.print_exc()
                    continue
                all_json_objects.extend(json_objects)
        except(Exception) as error:
            print(error)
            traceback.print_exc()


        self.json_objects = all_json_objects[1:10]  
        return all_json_objects

                

def run_separate_by_cat(list_of_files):
    loader = Document_Loader(None,1,list_of_files)
    loader.separate_pages_by_category('output_test')

def run_collect_stats(list_of_files):
    loader = Document_Loader(None, 1, list_of_files)
    loader.collect_statistics()
def main():
    if len(sys.argv) < 2:
        print("Please enter the file name with the list of files to process")
        return
    input_files = sys.argv[1]   
    list_of_files = utils.read_file_as_list(input_files)
    run_collect_stats(list_of_files)

if __name__ == '__main__':
    main()
#test()
#TODO load the Ground Truth

