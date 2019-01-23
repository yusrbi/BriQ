# -*- coding: utf-8 -*-
#import nltk.tokenize.punkt
import regex as re
import nltk.data

#This module is used to define a regex-based in order mention extractor
stop_words=None
# ex. $45.09 milliom 45$ $50K 
#NUMBER ='\d+\.\d+|\d+(,\d{1,3})+|\d+'
HEADING_NUM_REGEX= r'\d+\.\s'
MONEY_REGEX = r'(\p{Sc}\(?\d+([\.\,]\d+)*\)?)((\s[mM]illions?|\s[tT]housands?|\s[hH]undereds?|\s[bB]illions?|\s?[Tt]|\s?[Mm]n?|\s?[Kk]|\s?[Bb]n?)\b)?'
#ex. +$1,200 to $1,300 million
MONEY_COMPLEX =r'\p{Sc}\d+([\,\.]\d+)*(\sto\s|\–|\-|\−|\s?\±\s?)\p{Sc}\d+([\,\.]\d+)*((\s[mM]illions?|\s[tT]housands?|\s[hH]undereds?|\s[bB]illions?|\s?[Tt]|\s?[Mm]n?|\s?[Kk]|\s?[Bb]n?)\b)?'
#ex. 12% 12 per cent 12 percent
PERCENT_REGEX = r'\b\d+(\.\d{1,3})?(\%|\s?[Pp]er\s?cent)'
#ex. 12 to 13 percent , 12-13%
PERCENT_COMPLEX = r'[\+\-\s]\d{1,3}(\.\d{1,2})?(\sto\s|\–|\-|\−|\s?\±\s?)[\+\-]?\d+(\.\d{1,2})?(\%|\s?[Pp]er\s?cent)'
#ex. January 12, 2015
DATE_REGEX_1 = r'\b([Jj]an(uary|.)?|[Ff]eb(ruary|.)?|[mM]ar(ch|.)?|[aA]pr(il|.)?|[mM]ay|[Jj]un(e|.)?|[Jj]ul(y|.)?|[aA]ug(ust|.)?|[sS]ep(tember|.)?|[oO]ct(ober|.)?|[nN]ov(ember|.)?|[dD]ec(ember|.)?)\s\d{1,2}\s?\,\s?\d{2,4}\b'
# ex 12 January Jan. 2015
DATE_REGEX_2 = r'(\d{1,2}\s)?([Jj]an(uary|.)?|[Ff]eb(ruary|.)?|[mM]ar(ch|.)?|[aA]pr(il|.)?|[mM]ay|[Jj]un(e|.)?|[Jj]ul(y|.)?|[aA]ug(ust|.)?|[sS]ep(tember|.)?|[oO]ct(ober|.)?|[nN]ov(ember|.)?|[dD]ec(ember|.)?)\s?\,?\s?(\d{2,4}|\'\d{2})'
#ex. 2014
DATE_REGEX_3 = r'\b\d{1,2}[\-\/]\d{1,2}[\-\/](19\d{2}|20\d{2})|(19\d{2}|20\d{2})[\-\/]\d{1,2}[\-\/]\d{1,2}\b'
#DATE_REGEX_4 = r'([Jj]an(uary|.)?|[Ff]eb(ruary|.)?|[mM]ar(ch|.)?|[aA]pr(il|.)?|[mM]ay|[Jj]un(e|.)?|[Jj]ul(y|.)?|[aA]ug(ust|.)?|[sS]ep(tember|.)?|[oO]ct(ober|.)?|[nN]ov(ember|.)?|[dD]ec(ember|.)?)\s?.\s?\d+'
DATE_REGEX_5= r'\b(19\d{2}|20\d{2})\s?[\-\/\.]\s?\d{1,2}\b|\b\d{1,2}\s?[\-\/\.]\s?(19\d{2}|20\d{2})\b'
YEAR_REGEX = r'\(?\b(19\d{2}|20\d{2})\b\)?'
# ex. section 1.2 table 1, fig. 1.2 to 1.6
TITLES_REGEX = r'(([Ll]ine|[Ss]ec(tion|\.)?|[tT]ab(le|\.)?|[Aa]ppendix|[cC]h(apter|\.)?|[fF]ig(ure|\.)?)\s?)\d+(\.\d+)*(\sto\s\d+(\.\d+)*)?'
#ex. 1.2.3.5 A Study of Efficacy
TITLES_REGEX_2 = r'\d+\.\d+(\.\d+)+'
# ex. one fourth, half, one third, two quarters, first, second
ORDINAL_FRAC_REGEX = r'((one|two|three|four|five|six|seven|eight|nine|ten)\s)?(first|second|half|third(s)?|fourth(s)?|quarter(s)?|fifth(s)?|sixth(s)?|seventh(s)?|eighth(s)?|ninth(s)?|tenth(s)?)'
# ex 1 in 100
FRAC = r'\s\d+\sin\s\d+' #1 in 10
#ex. 2-3-4 1:2 23/60
SCORES_REGEX =r'\b\d{1,3}(\s[\:\/\-\\]\s\d{1,3})+\b|\b\d{1,3}([\:\/\-\\]\d{1,3})+\b'
#ex. phone..... +49 123 4567 89
PHONE_NUM_REGEX = r'(\(?\+?\d{2,}\)?[\- ])?(\(\d{3,}\)\s?|\d{3,}[\- ])\d{3,}([\- ]\d{2,})*' 
#r'(\+?\d+[\- ])?(\(\d+\)\s?|\d+[\- ])\d+([\- ]\d+)*'
#ex. 10:30am, 1:20 PM
TIME_REGEX=r'\d{1,2}:\d{2}\s?([Pp][Mm]|[Aa][Mm]|[Aa]\.[Mm]\.|[pP]\.[Mm]\.)'
TIME_REGEX_3 = r'\d{1,2}:\d{2}(:\d{2})?\s?([Pp][Mm]|[Aa][Mm]|[Aa]\.[Mm]\.|[pP]\.[Mm]\.)?'
TIME_REGEX_2 = r'\d+\s([Mm]inutes?|[Ss]econds?|[Hh]ours?|[Ss]ec|[mM]ins?|[hh]rs?)'
# 123 km/hr to 300 km per hour
COMPLEX_UNIT_0 =r'[\+\-\–]?\d+([\,\.]\d+)?(\s?[^\s\d]+(\sper\s|\s?\/\s?)[^\s]+)(\s?(to|\–|\-|\−)\s?[\+\-\–]?\d+([\,\.]\d+)?)\s?[^\s\d]+(\sper\s|\s?\/\s?)[^\s]+'
#ex. + 123 KM per hour , 100km/hr, 100 to 5 km/hr
COMPLEX_UNIT=r'[\+\-\–]?\d+([\,\.]\d+)?(\s?(to|\–|\-|\−)\s?[\+\-\–]?\d+([\,\.]\d+)?)?\s?[^\s\d]+(\sper\s|\s?\/\s?)[^\s]+'
#10 x 100 km/hr
COMPLEX_UNIT_2=r'[\+\-\–]?\d+([\,\.]\d+)?\s?(\×|\±)\s?[\+\-\–]?\d+([\,\.]\d+)?\s?[^\s\d]+(\sper\s|\s?\/\s?)[^\s]+'
#ex. 100 to 123 users , 123 items
COMPLEX_UNIT_3=r'\b\d+([\,\.]\d+)*((\sto\s|\–|\-|\−|\s?\×\s?|\s?\±\s?)\d+([\,\.]\d+)*)?(\s[mM]illions?|\s[tT]housands?|\s[hH]undereds?|\s[bB]illions?|\s?[Tt]|\s?[Mm]n?|\s?[Kk]|\s?[Bb]n?|\s[Kk]ilos?)?\b'
REF_REGEX = r'\[\d+\]'
class Mention:
	def __init__(self, start_offset,end_offset, mention, sent_start_offset, sent_end_offset):
		self.start_offset = start_offset
		self.end_offset = end_offset
		self.mention = mention 
		self.sent_start_offset = sent_start_offset
		self.sent_end_offset = sent_end_offset
	def __str__(self):
		return  "start %d, end %d, sent_start %d, sent_end %d, mention %s"%(self.start_offset,self.end_offset,self.sent_start_offset,self.sent_end_offset,self.mention)
class Sentence:
	def __init__(self,sentence, start_offset, end_offset):
		self.sentence = sentence
		self.start_offset = start_offset
		self.end_offset = end_offset
	def __str__(self):
		return "starts at %d , ends at %d, sentence: %s"%(self.start_offset, self.end_offset,self.sentence)
def get_exclude_first_list():
	
	regex_list=[]
	regex_list.append(DATE_REGEX_1)
	regex_list.append(DATE_REGEX_2)
	regex_list.append(DATE_REGEX_3)
	#regex_list.append(DATE_REGEX_4)
	regex_list.append(DATE_REGEX_5)
	regex_list.append(TITLES_REGEX)
	regex_list.append(TIME_REGEX)
	regex_list.append(TIME_REGEX_2)
	#regex_list.append(YEAR_REGEX)
	return regex_list
def get_exclude_second_list():
	regex_list =[]	
	regex_list.append(PHONE_NUM_REGEX)
	regex_list.append(YEAR_REGEX)
	regex_list.append(HEADING_NUM_REGEX)
	regex_list.append(TITLES_REGEX_2)
	regex_list.append(TIME_REGEX_3)
	regex_list.append(REF_REGEX)
	return regex_list

def get_include_first_list():
	regex_list=[]
	regex_list.append(COMPLEX_UNIT_0)
	regex_list.append(COMPLEX_UNIT)
	regex_list.append(COMPLEX_UNIT_2)
	regex_list.append(PERCENT_COMPLEX)
	regex_list.append(MONEY_COMPLEX)
	regex_list.append(MONEY_REGEX)
	regex_list.append(PERCENT_REGEX)
	#regex_list.append(FRAC)
	#regex_list.append(ORDINAL_FRAC_REGEX)
	return regex_list
def get_include_second_list():
	regex_list =[]
	regex_list.append(SCORES_REGEX)
	regex_list.append(COMPLEX_UNIT_3)
#	regex_list.append(COMPLEX_UNIT_2)
	return regex_list
def mention_extractor(text,sent_start_offset,sent_end_offset, regex_list):
	current_text = text.replace(u'\xa0',' ')
	all_mentions = []
	for regex in regex_list:
		current_text,mentions = get_mentions_and_clear(current_text,sent_start_offset,sent_end_offset,regex)
		all_mentions[len(all_mentions):] = mentions
	return current_text, all_mentions
def get_mentions_and_clear(text, sent_start_offset, sent_end_offset,regex):
	mentions=[]
	modified_text = text
	#print(regex)
	for match in re.finditer(regex,text):
		mention_text = match.group(0).strip()
		if len(mention_text) <= 1:
			continue
		mention = Mention(sent_start_offset+match.start(),sent_start_offset+match.end(), mention_text,sent_start_offset,sent_end_offset)
		mentions.append(mention)
		modified_text = modified_text[:match.start()]	+ ' ' * (match.end()-match.start()) +modified_text[match.end():]

	#print ("Length of text %d, after mod: %d"%(len(text),len(modified_text)))
	#print ("original text : %s\nmodified text : %s " %(text, modified_text))
	return modified_text, mentions
def mention_excluder(text,sent_start_offset,sent_end_offset,regex_list):
	current_text = text.replace(u'\xa0',' ')
	for regex in regex_list:
		current_text,_ = get_mentions_and_clear(current_text,sent_start_offset,sent_end_offset, regex)
	return current_text
def run_mention_extraction_in_order(text, start_offset, end_offset):
	
	text_chunk = text[start_offset:end_offset]

	all_mentions =[]
	updated_text = mention_excluder(text_chunk, start_offset,end_offset, get_exclude_first_list())
	#print (updated_text)
	updated_text, mentions = mention_extractor(updated_text,start_offset,end_offset,get_include_first_list())
	all_mentions.extend(mentions)
	updated_text = mention_excluder(updated_text,start_offset,end_offset, get_exclude_second_list())
	#print (updated_text)
	updated_text, mentions = mention_extractor(updated_text,start_offset,end_offset,get_include_second_list())
	all_mentions.extend(mentions)
	return all_mentions
def test_mentions_extractor():
	text = " "
	assert(" " == mention_excluder(text,[MONEY_REGEX]))
	text = "$245 million ;and 23% of the revenue in 2013 was in the fourth Quarter of 2010 that is December, 2010 544$b"
	text_2, mentions = mention_extractor(text,[MONEY_REGEX])
	assert(text_2 =="____________ ;and 23% of the revenue in 2013 was in the fourth Quarter of 2010 that is December, 2010 _____")
	text = "$245 million ;and 23% of the revenue in 2013 was in the fourth Quarter of 2010 that is December, 2010 544$b"
	text2 = mention_excluder(text, get_exclude_first_list())
	text2 = mention_excluder(text2, get_exclude_second_list())
	assert(text2=="$245 million ;and 23% of the revenue in______was in the fourth Quarter of______that is ______________ 544$b")
	text = "Section 1.2.2 chapter 1.1"
	text2 = mention_excluder(text,get_exclude_first_list())
	text2 = mention_excluder(text2, get_exclude_second_list())
	assert(text2=="_____________ ___________")
	
	text =        "Monday at 2:00pm and Tuesday at 2:00 a.m. 25$ 1.2%"
	text2 = mention_excluder(text,get_exclude_first_list())
	text2 = mention_excluder(text2, get_exclude_second_list())
	assert(text2=="Monday at ______ and Tuesday at _________ 25$ 1.2%")

	text = "look in ch. 1 and sec.2 Now 1 in 10 at the one fourth of the third quarter" 
	text2 = mention_excluder(text,get_exclude_first_list())
	text2 = mention_excluder(text2, get_exclude_second_list())
	assert(text2=="look in _____ and _____ Now 1 in 10 at the one fourth of the third quarter")
	
	
	text =        "it was in part 1.2.2 on 21 Dec. 2010 and Nov. 2,2011 but january 3, 2017" 
	text2 = mention_excluder(text,get_exclude_first_list())
	text2 = mention_excluder(text2, get_exclude_second_list())
	assert(text2=="it was in part _____ on ____________ and ___________ but _______________")

	print (mentions)
def test_mentions_extraction_2():
	text =u""" The economic potentials for GHG mitigation at different costs have been reviewed for 2030 on the basis of bottom:up studies. The review confirms the Third Assessment Report (TAR) finding that there are substantial opportunities for mitigation levels of about 6 GtCO2-eq involving net benefits (costs less than 0), with a large share being located in the buildings sector. Additional potentials are 7 GtCO2-eq at a unit cost (carbon price) of less than 20 US$/tCO2-eq, with the total, low-cost, potential being in the range of 9 to 18 GtCO2-eq. The total range is estimated to be 13 to 26 GtCO2-eq, at a cost of less than 50 US$/tCO2-eq and 16 to 31 GtCO2-eq at a cost of less than 100 US$/tCO2-eq (370 US$/tC-eq). As reported in Chapter 3, these ranges are comparable with those suggested by the top-down models for these carbon prices by 2030, although there are differences in sectoral attribution (medium agreement, medium evidence).

The total estimated development capital cost for the Project is $1,865 million inclusive of a $190 million contingency. The estimated development capital cost is based on the third quarter 2013 capital environment. The development capital cost equates to $266 per recoverable gold ounce over the current reserve life of the Project


Diverse evidence indicates that carbon prices in the range 20–50 US$/tCO2 (US$75–185/tC), reached globally by 2020–2030 and sustained or increased thereafter, would deliver deep emission reductions by mid-century consistent with stabilization at around 550ppm CO2-eq (Category III levels, see Table 3.10) if implemented in a stable and predictable fashion. Such prices would deliver these emission savings by creating incentives large enough to switch ongoing investment in the world’s electricity systems to low-carbon options, to promote additional energy efficiency, and to halt deforestation and reward afforestation.[2].

Pathways towards 650ppm CO2-eq (Category IV levels; see Table 3.10) could be compatible with such price levels being deferred until after 2030. Studies by the International Energy Agency suggest that a mid-range pathway between Categories III and IV, which returns emissions to present levels by 2050, would require global carbon prices to rise to 25 US$/tCO2 by 2030 and be maintained at this level along with substantial investment in low-carbon energy technologies and supply (high agreement, much evidence)."""	
	'''	sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
	mentions_set = extract_mentions_from_text(text)
	mentions_set.sort(key = lambda mention : mention.start_offset)
	for mention in mentions_set:
		print (str(mention))
	'''
	text = '''Generally the one-vCPU test showed lower latency at 1600 MHz than at 1066 MHz, and that latency difference became exaggerated at approximately 65 virtual desktops (8.13 vCPUs per core). This effect had a large impact on overall density in the one-vCPU tests. Figure 12. Intel Xeon E5-2643 at Different Memory Speeds Figure 13 shows the same combinations of tests as Figure 12, but on the Intel Xeon E5-2665 system. Scalability increases by 3 to 4 percent when the memory speed is 1600 MHz.
On 7/12/1986 at 08:19:37, a magnitude 4.5 (4.5 MB, Class: Light, Intensity: IV - V) earthquake occurred 50.0 miles away from the city centerOn 9/12/2004 at 13:05:19, a magnitude 3.8 (3.5 MB, 3.8 MW, 3.6 LG, Depth: 3.8 mi, Class: Light, Intensity: II - III) earthquake occurred 90.3 miles away from Uniondale centerOn 4/17/1990 at 10:27:34, a magnitude 3.0 (3.0 LG, Depth: 3.1 mi) earthquake occurred 32.8 miles away from the city centerMagnitude types: regional Lg-wave magnitude (LG), body-wave magnitude (MB), moment magnitude (MW)Natural disasters:The number of natural disasters in Wells County (12) is near the US average (12).Major Disasters (Presidential) Declared: 7Emergencies Declared: 5Causes of natural disasters: Floods: 4, Storms: 4, Tornadoes: 3, Winter Storms: 3, Storm: 1, Hurricane: 1, Ice Storm: 1, Snow: 1, Snowstorm: 1, Tornado: 1 (Note: Some incidents may be assigned to more than one category)
text:Ryan Howard powered the Phils past the the Marlins last night. He hit two home runs, including a mammoth shot to the opposite field, and the Phillies rolled to an 11-1 win. In 116 career at-bats against the Marlins, Howard is hitting 371/535/793 with 13 home runs.  1.5GB
In the Outer Ring already referred to, the population increased by 45.5 per cent. in the ten years 1891-1901, the rates of increase in the preceding three decennia having been 50.7, 50.0, and 50.1 per cent. respectively. It would thus appear that, as suggested in the Report for 1891, the overflow of the Metropolitan population may now extend even beyond "Greater London.
15.09 in 1871-81
4,567,890 in the next 
Jul 17
2011-11
The aggregate area of England and Wales, including land and inland water but excluding tidal water and foreshore, is 37,327,479 statute acres or 58,324 square miles, The total population at the date of the Census was 32,527,843, and therefore each square mile would, on the assumption that the population was evenly distributed over the entire area, have been occupied by 558 persons. On the same assumption, the space available for each person would have been 1.15 acres, and the proximity of person to person, or the distance from person to person, 80 yards

'''
	text ='''
I’m not sure that’s right, Danny. I assume you’re talking about CTR, and if you had, say, 1000 ad impressions that generated 17 clicks, by your formula you’d have
17/1000 = 0.017 or 1.7%
Doing it the other way would be
1000/17 = 58.82
Uh, um, you’re right, I’m wrong.
'''
	mentions = extract_mentions_from_text(text) #run_mention_extraction_in_order(text,0,len(text))
	mentions.sort(key = lambda mention:mention.start_offset)#sort by start offset

	for mention in mentions:
		text_ = text[:mention.start_offset]+"[" + mention.mention +"]"+ text[mention.end_offset:]
		print(text_)
		print (str(mention))

def extract_mentions_from_text(text):
	sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
	all_mentions=[]
	for start,end in sent_detector.span_tokenize(text):
		mentions = run_mention_extraction_in_order(text,start,end)
		all_mentions.extend(mentions)
	return all_mentions
if __name__ == '__main__':
#	test_mentions_extractor()
	test_mentions_extraction_2()
		
