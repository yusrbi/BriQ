class StatCollector:

    def get_counts(self, html_page):
        counts =[]
        page_docs = html_page.create_documents()
        if page_docs:
            counts.append(('page_count',1))
            counts.append(('documents_count', len(page_docs)))

            #min number of tables per page
            counts.append(('tables_count', html_page.get_tables_count()))
            counts.append(('mentions_count', html_page.get_mentions_count()))
            counts.append(("avg. rows", html_page.get_avg_row_count()))
            counts.append(("avg. cols", html_page.get_avg_col_count()))
            counts.append(("avg. q cells", html_page.get_avg_qcell_count()))
            counts.append(("avg. virtual cells", html_page.get_avg_vcell_count()))

        return counts
    def get_header_terms_count(self,html_page):
        counts = []
        tables = html_page.tables
        for table in tables:
            if table.consider_table:
                counts.extend(table.get_header_keywords_count())

        return counts

    def get_table_terms_count(self, html_page):
        counts = []
        tables = html_page.tables
        for table in tables:
            if table.consider_table:
                counts.extend(table.get_keywords_count())

        return counts







