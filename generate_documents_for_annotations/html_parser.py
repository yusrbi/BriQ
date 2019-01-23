# this code extract tables from a givenn html page
# it works with input string, however it is easy to get the html page and laod it as a string 
import regex as re
from lxml import html,etree
import utils

class HTMLPage:
	class Table:
		def __init__(self,table, table_id, content_by_row,nrows,ncolumns,ncells,nquantity_cells,table_header,word_set,quantities,footer,caption):
			self.table = table
			self.table_id = table_id
			self.content_by_row = content_by_row
			self.nrows = nrows
			self.ncolumns = ncolumns
			self.ncells = ncells
			self.nquantity_cells = nquantity_cells
			self.header = table_header
			self.word_set = word_set
			self.quantities = set(quantities)
			self.caption = caption
			self.footer = footer
			
			#self.create_word_set()
		def create_word_set(self):
			if not self.header and self.content_by_row:
				self.header.extend(self.content_by_row[0])
			keywords =[]
			for row in self.content_by_row:
				if row:
					keywords.extend(utils.get_word_list(row[0]))
			for cell in self.header:
				if cell:
					keywords.extend(utils.get_word_list(cell))
			self.word_set = set(keywords)
		def get_percent_qmentions(self):
			if self.ncells is not 0:
				return float(self.nquantity_cells)/(float(self.ncells))
			else:
				return 0

		def caption_contains(self,term):
			# search for an exact match in the first and the last row
			term = term.lower().strip()
			if term in self.caption:
				return True

			for col in self.footer:
				if term in col:
					return True
			for col in self.header:
				if term in col:
					return True
			for col in self.content_by_row[0]:
				if term in col:
					return True
			for col in self.content_by_row[self.nrows-1]:
				if term in col:
					return True
			return False

		def __str__(self):
			return ','.join( w for w in self.word_set)#etree.tostring(self.table,pretty_print=True).decode('utf-8')


	def __init__(self,html_content):
		self.html_content = html_content
		self.title=''
		self.tables=[]
		self.content =''
		self.process_page(self.html_content)
	def get_tables(self,min_rows, max_rows, min_col, max_col, min_cells,max_cells, percent_quantity_cells):
		selected =[]
		
		if len(self.tables) <1:
			return selected
		for table in self.tables:
			if ( self.in_range(table.nrows,min_rows, max_rows) and self.in_range(table.ncolumns, min_col, max_col)) or self.in_range(table.ncells,min_cells,max_cells):
				if table.get_percent_qmentions() >= percent_quantity_cells:
					selected.append(table)
		return selected

	def get_all_tables(self):
		return self.tables
 
	def in_range(self, target,min,max):
		return target >=min and target <=max
	def get_percent_qmentions(self,table):
		if table.ncells is not 0:
			return float(table.nquantity_cells)/(float(table.ncells))
		else:
			return 0
	def get_header_content(self, header_cells):
		content =[]
		for header in header_cells:
			for br in header.xpath('.//br'):
				br.tail = " " + br.tail if  br.tail else " "
			content.append(header.text_content().strip().lower())
		return content
	def get_caption_content(self,cap):
		content = ''
		for tag in cap:
			content = content + self.get_tag_content(tag)
		return content

	def get_tag_content(self,tag):
		for br in tag.xpath(".//br"):
			br.tail = " " + br.tail if br.tail else " "
		content =  tag.text_content().strip().lower()
		return content
	def process_page(self, html_content):
		#This function 
		try:
			root = html.document_fromstring(html_content.encode('utf-8'))
		except:
			return 
		titles = root.xpath("//title")
		for title in titles:
			self.title = title.text_content()
			break
		tables = root.xpath('//table')
		table_id =0
		for table in tables:
			if table.xpath('.//table')!=[]:
			#skip table that has nasted tables
				continue
			else:
				table_id+=1
				ncells =0
				nquantity_cells=0
				nrows=0
				ncolumns=0
				# process the table row by row 
				table_quantities =[]
				table_words = []
				table_rows = table.xpath('.//tr')
				content_by_row =[]
				table_headers =[]
				table_footer =[]
				table_caption = ''
				headers = table.xpath('.//th')
				footer = table.xpath('.//tfoot//td')
				caption = table.xpath('.//caption')
				if caption:
					table_caption = self.get_caption_content(caption)

				table_footer = self.get_header_content(footer)
				table_headers = self.get_header_content(headers)

				for cell in table_headers:
					table_words.extend(utils.get_word_list(cell))
				for cell in table_footer:
					table_words.extend(utils.get_word_list(cell))
				table_words.extend(utils.get_word_list(table_caption))
				
				for row in table_rows:
					row_content=[]
					nrows+=1
					
					
					table_cells = row.xpath('.//td')					
					ncolumns = max(ncolumns, len(table_cells))
					
					for col_idx,cell in enumerate(table_cells):
						#print("col:%d, %s"%(col_idx,cell))
						content =  self.get_tag_content(cell)
						#print(content)
						if len(content) == 0:
							continue # don't count empty cells
						ncells+=1
						row_content.append(content)
						if self.is_quantity(content) and col_idx is not 0:
							nquantity_cells+=1
							table_quantities.append(content)
						else:
							table_words.extend(utils.get_word_list(content))
					content_by_row.append(row_content)
				table_words_set = set().union(table_words)
				self.tables.append(HTMLPage.Table(table,table_id,content_by_row,nrows,ncolumns, ncells,nquantity_cells,table_headers,table_words_set, table_quantities, table_footer, table_caption))
				table.getparent().remove(table)# remove the table content from the page content 

			# remove the scripts from the page content
			scripts = root.xpath('//script')
			if scripts:
				for script in scripts:
					script.getparent().remove(script)
			styles = root.xpath('//style')
			if styles:
				for style in styles:
					style.getparent().remove(style)
			self.content = root.text_content()				
						
			


	def is_quantity(self,text):
		if re.fullmatch(r'[+-]?\p{Sc}?\d+([.,:\-\–\-\−\±]\d+)*\%?\p{Sc}?',text):
			return True
		else:
			return False

def test():
	html_page =''' <html>
<head>
<title>Test Page</title>
</head>
<body>
<table border="0" cellpadding="0" cellspacing="3" width="650">
				<tbody><tr>
					<td width="175"></td>
					<th width="130">
						<div align="center">
							Killed in Action</div>
					</th>
					<th width="130">
						<div align="center">
							Died of Wounds</div>
					</th>
					<th width="130">
						<div align="center">
							Wounded in Action</div>
					</th>
					<th width="85">
						<div align="center">
							Totals</div>
					</th>
				</tr>
				<tr>
					<td width="175">
						<div align="center">
						2005</div>
					</td>
					<td width="130">
						<div align="center">
							 7</div>
					</td>
					<td width="130">
						<div align="center">
							unknown</div>
					</td>
					<td width="130">
						<div align="center">
							14</div>
					</td>
					<td width="85">
						<div align="center">
							23</div>
					</td>
				</tr>
				<tr>
					<td width="175">
						<div align="center">
							2013</div>
					</td>
					<td width="130">
						<div align="center">
							-</div>
					</td>
					<td width="130">
						<div align="center">
							-</div>
					</td>
					<td width="130">
						<div align="center">
							3</div>
					</td>
					<td width="85">
						<div align="center">
							3</div>
					</td>
				</tr>
				<tr>
					<td width="175">
						<div align="center">
							Bluejackets</div>
					</td>
					<td width="130">
						<div align="center">
							17</div>
					</td>
					<td width="130">
						<div align="center">
							2</div>
					</td>
					<td width="130">
						<div align="center">
							51</div>
					</td>
					<td width="85">
						<div align="center">
							70</div>
					</td>
				</tr>
				<tr>
					<td width="175">
						<div align="center">
							Marine Corps Enlisted Men</div>
					</td>
					<td width="130">
						<div align="center">
							47</div>
					</td>
					<td width="130">
						<div align="center">
							-12</div>
					</td>
					<td width="130">
						<div align="center">
							+139</div>
					</td>
					<td width="85">
						<div align="center">
							198</div>
					</td>
				</tr>
				<tr>
					<td width="175">
						<div align="center">
							<b>Totals</b></div>
					</td>
					<td width="130">
						<div align="center">
							<b>71</b></div>
					</td>
					<td width="130">
						<div align="center">
							<b>16%</b></div>
					</td>
					<td width="130">
						<div align="center">
							<b>207</b></div>
					</td>
					<td width="85">
						<div align="center">
							<b>$294</b></div>
					</td>
				</tr>
				<tr>
				<td> </td>
				<td> </td>
				<td> </td>
				<td> _  </td>
				</tr>
			</tbody>
			<tfoot>
				<tr>
				<td> Hello Footer </td>
				<td> another Footer </td>
				</tr>
			</tfoot>
			<caption> Table 1 h a Caption is given!</caption>
		</table>
	this is the only content
	<script type="text/javascript" src="/static/admin/js/vendor/xregexp/xregexp.js"></script>
	
</body>
</html>
'''

	page = HTMLPage(html_page)
	print(page.content)
	print(page.title)
	for table in page.tables:
		print("Table nRows:%d, nColumns:%d, nCells:%d, nQCells: %d"%(table.nrows,table.ncolumns,table.ncells,table.nquantity_cells))
		print("Table by rows:")
		print(table.content_by_row)
		print("Word set:")
		print(table.word_set)
		print("Header:")
		print (table.header)
		print("Quantity %")
		print (table.get_percent_qmentions())
		print("Quantities")
		print (table.quantities)
		print(table.caption_contains('Table 2'))
		print("Table Footer")
		print(table.footer)
		print("Caption:")
		print(table.caption)
		print("ncells")
		print(table.ncells)
	print(page.get_tables(0,20,20,30,10,220,0.5))
	print(page.get_all_tables())

if __name__=='__main__':
	test()
			
