import os
import nltk
nltk.data.path.append(os.environ.get('PWD'))
import time
from nltk.corpus import stopwords
import nltk.data
import string
import re
from nltk.stem.porter import *

#nltk.download('stopwords')
#nltk.download('maxent_treebank_pos_tagger')
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')

grammer ='''
        NP: {<DT|PP\$>?<JJ>*<NN>}   # chunk determiner/possessive, adjectives and noun
            {<NNP>+}                # chunk sequences of proper nouns

        '''
stopwords_lst = set([word for word in stopwords.words('english')]) 
stemmer = PorterStemmer()
def get_most_frequent_words(word_list):
    global stopwords_lst
    filtered_words =[]
    #print(word_list)

    for word in word_list:
        #print (word)
        if word in stopwords_lst or word in string.punctuation:
            continue
        filtered_words.append(stem(word.lower()))

    word_frequency = nltk.FreqDist(filtered_words)
    return word_frequency.most_common(50)

def get_tokens(sentence):
    sentence = sentence.lower()
    tokens = re.split(r'[\s.,?;\(\)\"\'!]+',sentence)
    #stopwords_lst = set([word  for word in stopwords.words('english')]) # decoding will interpret the string as UTF-8
    return tokens



def get_tokens_and_filter_stop_words(sentence):
    global stopwords_lst
    sentence = sentence.lower()
    tokens = re.split(r'[\s.,?;\(\)\"\'!]+',sentence)
    #stopwords_lst = set([word  for word in stopwords.words('english')]) # decoding will interpret the string as UTF-8
    filtered_tokens = [ ]
    for i in range(len(tokens)):
        token = tokens[i].strip()
        if not token or token in stopwords_lst:
            continue
        filtered_tokens.append(token)
    return filtered_tokens


def get_sentences_spans(text):
    sentence_detector  = nltk.data.load('tokenizers/punkt/english.pickle')

    sentences_span = sentence_detector.span_tokenize(text)
    return sentences_span
def fast_extract_noun_phrases(sentence):
    global stopwords_lst
   
    sentence = sentence.lower()
    tokens = re.split(r'[\s.,?;\(\)\"\']',sentence)
    #stopwords_lst = set([word for word in stopwords.words('english')]) # decoding will interpret the string as UTF-8
    filtered_tokens = [ ]
    nps = []
    #for token in tokens:
    #    token= token.strip()
    #    if token and token not in stopwords_lst:
    #        filtered_tokens.append(token)

    for i in range(len(tokens)):
        token = tokens[i].strip()

        if not token or token in stopwords_lst:
            continue
        filtered_tokens.append(token)
        if i+1 < len(tokens):
            next_token = tokens[i+1].strip()
            if next_token and next_token not in stopwords_lst:
                np_ = '%s %s'%(token,next_token)
                nps.append(np_)

    return set(filtered_tokens), set(nps)

def extract_noun_phrases_no_stem(sentence):
#        time_ = time.clock()
#        print ("strat : %f"% time_)
    global stopwords_lst
    #stemmer = PorterStemmer()

    #stopwords_lst = set([word  for word in stopwords.words('english')]) # decoding will interpret the string as UTF-8
#       print ("load stop words : %f"% (time_ - time.clock()))
#        time_ = time.clock()
    chunker = nltk.RegexpParser(grammer)
#       print ("regex chunk : %f"%(time_ - time.clock()))
#        time_ = time.clock()
    tokens = nltk.word_tokenize(sentence)
    tokens = [word.lower() for word in tokens]

    #tokens_stem = [stemmer.stem(word) for word in tokens] #stemmer will transform to lower case and stemming is faster than lemmatization
#        print ("tokenize : %f"%(time_ - time.clock()))
#        time_ = time.clock()

    tokens_pos = nltk.pos_tag(tokens)
#        print ("pos : %f"%(time_ -  time.clock()))
#        time_ = time.clock()

    parse_tree = chunker.parse(tokens_pos)
#       print ("parse tree : %f"%(time_ -  time.clock()))
#        time_ = time.clock()

    noun_phrases = get_noun_phrases(parse_tree)
#        print ("NP : %f"%(time_- time.clock()))
    #time_ = time.clock()

    nps =[]
    for np in noun_phrases:
        words = ' '.join([word.lower() for word,tag in np])
        nps.append(words)
#                print 'words:%s, np: %s'%(repr(words),np)
    #filtered_tokens = []
    #for token in tokens:
        #if token not in stopwords_lst and  token not in string.punctuation:
        #    filtered_tokens.append(token.lower())
    return tokens, nps

def extract_noun_phrases(sentence):
#        time_ = time.clock()
#        print ("strat : %f"% time_)
    global stopwords_lst, stemmer

    #stopwords_lst = set([word  for word in stopwords.words('english')]) # decoding will interpret the string as UTF-8
#       print ("load stop words : %f"% (time_ - time.clock()))
#        time_ = time.clock()
    chunker = nltk.RegexpParser(grammer)
#       print ("regex chunk : %f"%(time_ - time.clock()))
#        time_ = time.clock()
    tokens = nltk.word_tokenize(sentence)
    tokens_stem = [stemmer.stem(word.lower()) for word in tokens] #stemmer will transform to lower case and stemming is faster than lemmatization
#        print ("tokenize : %f"%(time_ - time.clock()))
#        time_ = time.clock()

    tokens_pos = nltk.pos_tag(tokens)
#        print ("pos : %f"%(time_ -  time.clock()))
#        time_ = time.clock()

    parse_tree = chunker.parse(tokens_pos)
#       print ("parse tree : %f"%(time_ -  time.clock()))
#        time_ = time.clock()

    noun_phrases = get_noun_phrases(parse_tree)
#        print ("NP : %f"%(time_- time.clock()))
    #time_ = time.clock()

    nps =[]
    for np in noun_phrases:
        words = ' '.join([word.lower() for word,tag in np])
        nps.append(words)
#                print 'words:%s, np: %s'%(repr(words),np)
    #filtered_tokens = []
    #for token in tokens:
        #if token not in stopwords_lst and  token not in string.punctuation:
        #    filtered_tokens.append(token.lower())
    return tokens_stem, nps

def get_noun_phrases(tree):
    for subtree in tree.subtrees(filter=lambda t: t.label() == 'NP'):
        yield subtree.leaves()

def stem(token):
    return stemmer.stem(token)


def test():
    text = '''Generally the one-vCPU test showed lower latency at 1600 MHz than at 1066 MHz, and that latency difference became  exaggerated at approximately 65 virtual desktops (8.13 vCPUs per core).
This effect had a large impact on overall density in the o ne-vCPU tests. Figure 12. Intel Xeon E5-2643 at Different Memory Speeds Figure 13 shows the same combinations of tests as Figure 12 , but on the Intel Xeon E5-2665 system. Scalability increases by 3 to 4 percent when the memory speed is 1600 MHz.
On 7/12/1986 at 08:19:37, a magnitude 4.5 (4.5 MB, Class: Light, Intensity: IV - V) earthquake occurred 50.0 miles away from the city center On 9/12/2004 at 13:05:19, a magnitude 3.8 (3.5 MB, 3.8 MW, 3.6 LG, Depth: 3.8 mi, Class: Light, Intensity: II - III) earth quake occurred 90.3 miles away from Uniondale center On 4/17/1990 at 10:27:34, a magnitude 3.0 (3.0 LG, Depth: 3.1 mi) earthquake occurred 32.8 miles away from the city center Magnitude types: regional Lg-wave magnitude (LG), body-wave magnitude (MB), moment magnitude (MW) Natural disasters:The number of natural disasters in Wells County (12) is near the US average (12).Major Disasters (Presid ential) Declared: 7 Emergencies Declared: 5 Causes of natural disasters: Floods: 4, Storms: 4, Tornadoes: 3, Winter Storms: 3, Storm:  1, Hurricane: 1, Ice Storm: 1, Snow: 1, Snowstorm: 1, Tornado: 1 (Note: Some incidents may be assigned to more than one category) text: Ryan Howard powered the Phils past the the Marlins last night. He hit two home runs, including a mammoth shot to the opposite  field, and the Phillies rolled to an 11-1 win. In 116 career at-bats against the Marlins, Howard is hitting 371/535/793 with 13 hom e runs.  1.5GB In the Outer Ring already referred to, the population increased by 45.5 percent. in the ten years 1891-1901, the rates of increase  in the preceding three decennia having been 50.7, 50.0, and 50.1 per cent. respectively. It would thus appear that, as suggested i n the Report for 1891, the overflow of the Metropolitan population may now extend even beyond "Greater London. 15.09 in 1871-81 4,567,890 in the next  Jul 17 2011-11
The aggregate area of England and Wales, including land and inland water but excluding tidal water and foreshore, is 37,327,479 statute acres or 58,324 square miles, The total population at the date of the Census was 32,527,843, and therefore each square mile would, on the assumption that the population was evenly distributed over the entire area, have been occupied by 558 persons. On the same assumption, the space available for each person would have been 1.15 acres, and the proximity of person to person, or the distance from person to person, 80 yards'''

    spans = get_sentences_spans(text)
    
    for start,end  in spans:
        tokens,noun_phrases = extract_noun_phrases(text[start:end])
        print("word frequency")
        print(get_most_frequent_words(tokens))

        #print("Tokens:")
        for token in tokens:
            #pass
            print(token)
    #       print("Noun Phrases:")
        for np in noun_phrases:
            print(np)
            #pass


if __name__ == '__main__':
    test()
