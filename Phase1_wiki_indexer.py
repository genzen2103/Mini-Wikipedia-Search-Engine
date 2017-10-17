# Basic Indexer Module
# Takes all words in the document after removel of all punctuations and invalid symbols
# Then stop words are eliminated and stemming is done.

# Size ratio = Size(Index)/Size(corpus)

# Size Ratio of Basic Indexer = ?
import xml.etree.ElementTree as ET
import re
import string
from nltk.tokenize import WordPunctTokenizer
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk import FreqDist
from nltk import word_tokenize
import time
from nltk.tokenize import regexp_tokenize
import sys
reload(sys)  
sys.setdefaultencoding('UTF8')
start_time = time.time()
tree = ET.parse( str(sys.argv[1]) )
root = tree.getroot()
stop_words = set(stopwords.words('english'))
#tokenizer=MosesTokenizer()
porter_stemmer = PorterStemmer()
word_tokenizer = WordPunctTokenizer()
index_terms={}
tokens_dict={}
docs=[]
stemmed_terms_dict={}
#print 'Parsing XML file'

unwanted_words={ k:1 for k in  list(stop_words) }
parsed=0
total=len(root.findall('{http://www.mediawiki.org/xml/export-0.10/}page'))
print total
for page in root.findall('{http://www.mediawiki.org/xml/export-0.10/}page'):
	print parsed
	if parsed==100:
		break
	print (parsed/float(total))*100.0,'% completed'
	page_title_data=page.find('{http://www.mediawiki.org/xml/export-0.10/}title').text
	revision=page.findall('{http://www.mediawiki.org/xml/export-0.10/}revision')
	text_data=revision[0].find('{http://www.mediawiki.org/xml/export-0.10/}text').text
	text_data=text_data.lower()



	#Tag clean up
	# text_data=re.sub(r'\[\[[^\[\]]*\]\]',' ',text_data)
	# text_data=re.sub(r'{{[^{}]*}}',' ',text_data)
	text_data=re.sub(r'http[^ ]* ',' ',text_data)
	text_data=re.sub(r'image[^ ]* ',' ',text_data)
	# text_data=re.sub(r'<ref[^<>]*>[^<>]*</ref>',' ',text_data)
	# text_data=re.sub(r'<([^<>]*)>[^<>]*<\1>',' ',text_data)
	# text_data=re.sub(r'<[^/>]*/>',' ',text_data)
	# text_data=re.sub(r'<[^<>]*>',' ',text_data)
	text_data=re.sub(r'&nbsp',' ',text_data)
	# text_data=re.sub(r'{[^{}]*}',' ',text_data)

	# tokens= word_tokenizer.tokenize(page_title_data.lower())
	# for sentence in sent_tokenize(text_data.lower()):
	# 	tokens.extend( word_tokenizer.tokenize(sentence) )

	# text_data=re.sub(r'\[\[[^\[\]]*\]\]',' ',text_data)
	# text_data=re.sub(r'{{[^{}]*}}',' ',text_data)
	text_data=re.sub(r'http[^ ]* ',' ',text_data)
	# text_data=re.sub(r'<ref[^<>]*>[^<>]*</ref>',' ',text_data)
	text_data=re.sub(r'<([^<>]*)>[^<>]*<\1>',' ',text_data)
	# text_data=re.sub(r'<[^/>]*/>',' ',text_data)
	# text_data=re.sub(r'<[^<>]*>',' ',text_data)
	text_data=re.sub(r'&nbsp',' ',text_data)
	# text_data=re.sub(r'{[^{}]*}',' ',text_data)

	reduced_title=[]
	for t in word_tokenize( page_title_data):
		if t.isalpha() and not (unwanted_words.has_key(t)):
			reduced_title.append(porter_stemmer.stem(t))

	reduced_title="_".join(reduced_title)
	docs.append([parsed,reduced_title])

	tokens=regexp_tokenize(text_data.lower(), pattern='[a-z]+|\d+')

	valid_tokens=[]
	for t in tokens:
		if tokens_dict.has_key(t):
			if tokens_dict[t]==1:
				valid_tokens.append(t)
		else:
			val=0
			if not (unwanted_words.has_key(t)  or any(ord(c)>128 for c in t)) :
				val+=1
			tokens_dict.update({t:val})
	
	term_dist={}
	
	for vt in valid_tokens:
		
		if not stemmed_terms_dict.has_key(vt):
			stem= porter_stemmer.stem(vt)
			stemmed_terms_dict.update({vt:stem})

		stem=stemmed_terms_dict[vt]

		if term_dist.has_key(stem):
			term_dist[stem]+=1
		else:
			term_dist.update({stem:1})			

	for term in term_dist.keys():
		if index_terms.has_key(term):
			diff=parsed-index_terms[term][len(index_terms[term])-1][0]
			index_terms[term].append([diff,term_dist[term]] )
		else:
			index_terms.update({term:[ [parsed,term_dist[term]] ] })
	parsed+=1

with open(str(sys.argv[2]), 'w') as fp:
	fp.write("\n".join(  [ ':'.join([k,";".join([",".join(map(str,tup)) for tup in index_terms[k] ] ) ] )  for k in sorted(index_terms.keys()) ] ))

with open('document_info.txt','w') as fp:
	fp.write("\n".join([':'.join(map(str,[d[0],d[1]])  ) for d in docs ]))

print "Total Documents=",parsed
print 'Total Execution Time=',time.time()-start_time
print "Total Index terms",len(index_terms.keys())
