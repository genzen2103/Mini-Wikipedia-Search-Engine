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
import os
import operator
import math
import time
reload(sys)  
sys.setdefaultencoding('UTF8')

tokens_dict={}
stemmed_terms_dict={}
index_terms={}
doc_file_dict={}
idfs={}
index_token_count=0
stop_words = set(stopwords.words('english'))
porter_stemmer = PorterStemmer()
unwanted_words={ k:1 for k in  list(stop_words) }

tot_time=0

def process_text_to_terms(text_data):
	tokens=regexp_tokenize(text_data, pattern='[a-z]+')

	valid_tokens=[]
	for t in tokens:
		if not tokens_dict.has_key(t):
			val=0
			if not ( unwanted_words.has_key(t)  or any(ord(c)>128 for c in t )) :
				val+=1
			tokens_dict.update({t:val})
		if tokens_dict[t]==1:
				valid_tokens.append(t)

	#print valid_tokens
	
	term_dist={}
	
	for vt in valid_tokens:
		if len(vt)>0 and len(vt)<50:
			if not stemmed_terms_dict.has_key(vt):
				try:
					stem= porter_stemmer.stem(vt)
				except IndexError:
					continue
				stemmed_terms_dict.update({vt:stem})

			stem=stemmed_terms_dict[vt]
			if len(stem)>1:
				if not term_dist.has_key(stem):
					term_dist.update({stem:0.0})
				term_dist[stem]+=1.0

	if len(stemmed_terms_dict)+ len(tokens_dict) >100000000:
		stemmed_terms_dict.clear()
		tokens_dict.clear()


	return term_dist,len(valid_tokens)		

def get_sort_merge(file):
	result={}

	for line in open(file,'r').readlines():
		#print line
		term,plist=line.strip().split(':')
		if term not in result:
			result.update({term:[]})
		result[term]=result[term]+[ [int(a),float(b)] for a,b in  [ t.split(",") for t in  plist.split(";") ] ]

	for term in result:
		result[term]=sorted(result[term] , key=lambda x : x[0])

	return result




def build_inverted_index(data_file):

	#print 'starting building index'
	start_time=time.time()
	context = ET.iterparse(data_file, events=("start", "end"))
	context = iter(context)
	event, root = context.next()
	temptag=root.tag
	tagMatchObj=re.search(r'\{.*\}',root.tag)
	mainTag=temptag[tagMatchObj.start():tagMatchObj.end()]
	pre=mainTag
	index_token_count=0
	parsed=0

	alpha_dict1={ c+d:[] for c in 'abcdefghijklmnopqrstuvwxyz' for d in 'abcdefghijklmnopqrstuvwxyz' }
	
	for k in alpha_dict1:
		fp=open('posting_'+k,'w')
		fp.close()

	start_time = time.time()
	prev_end_time=start_time
	clean_reg_time=0
	text_process_time=0
	index_time=0

	for event,page in context:
		if event == "end" and page.tag == pre+'page':

			if parsed>0 and parsed%1000==0:
				print parsed,' completed'
				print time.time()-start_time
			# 	break
			#

			title_data=page.find(pre+'title').text
			revision=page.findall(pre+'revision')
			if revision is not None:
				text_data=revision[0].find(pre+'text').text

			if not ( text_data is not None and title_data is not None):
				continue
			
			text_data=title_data+'\n'+text_data
			text_data=text_data.lower()
			
			#Tag clean up
			text_data=re.sub(r'http[^ ]* ',' ',text_data)
			text_data=re.sub(r'<poem[^<]*</poem>',' ',text_data)
			text_data=re.sub(r'<math[^<]*</math>',' ',text_data)
			text_data=re.sub(r'image[^ ]* ',' ',text_data)
			text_data=re.sub(r'&[^\s]*;',' ',text_data)
			text_data=re.sub(r'\[\[File:[^\[\]]*\]\]',' ',text_data)


			#Process Text
			# s=time.time()
			term_dist,v_count=process_text_to_terms(text_data)
			# global tot_time
			# tot_time+=(time.time()-s)
			doc_file_dict.update({parsed: map(str,[parsed,title_data,v_count])})
			

			
			#Add to index
			for term in term_dist:
				if not index_terms.has_key(term):
					index_terms.update({term:[] })
					idfs.update({term:0})
				index_terms[term].append([parsed,term_dist[term]] )
				idfs[term]+=1.0
				index_token_count+=1


			# Flush Index
			if index_token_count>100000000:
				print "flushing Index"
				alpha_dict={ c+d:[] for c in 'abcdefghijklmnopqrstuvwxyz' for d in 'abcdefghijklmnopqrstuvwxyz' }
				for k in index_terms:
					key=k[0:2]
					alpha_dict[key].append(k)

				for c in sorted(alpha_dict):
					if len(alpha_dict[c])>0:
						fp=open('posting_'+c,'a')
						fp.write("\n".join(  [ ':'.join( [k,";".join([",".join(map(str,tup)) for tup in index_terms[k] ] ) ] )  for k in sorted(alpha_dict[c]) if len(index_terms[k])>0] ))
						fp.write("\n")
						fp.close()
				index_terms.clear()
				index_token_count=0


			parsed+=1

			root.clear()

	# print tot_time
	# exit()
	doc_file=open('doc_info','w')
	doc_file.write("\n".join([ ":::".join(doc_file_dict[k]) for k in doc_file_dict.keys()] ) )	
	doc_file.close()
	
	doc_file_dict.clear()
	tokens_dict.clear()
	stemmed_terms_dict.clear()

	#Flush Index
	print "flushing Index"
	alpha_dict={ c+d:[] for c in 'abcdefghijklmnopqrstuvwxyz' for d in 'abcdefghijklmnopqrstuvwxyz' }
	for k in index_terms:
		key=k[0:2]
		alpha_dict[key].append(k)

	for c in sorted(alpha_dict):
		if len(alpha_dict[c])>0:
			fp=open('posting_'+c,'a')
			fp.write("\n".join(  [ ':'.join( [k,";".join([",".join(map(str,tup)) for tup in index_terms[k] ] ) ] )  for k in sorted(alpha_dict[c]) if len(index_terms[k])>0] ))
			fp.write("\n")
			fp.close()
	index_terms.clear()
	index_token_count=0


	#Write IDFS
	print "Writing IDFs"
	index_file=open('index_info','w')
	for term in idfs:
		idfs[term]=math.log(parsed/idfs[term],2)
		index_file.write(":".join(map(str,[ term,idfs[term] ]) )+"\n" )
	index_file.close()

	idfs.clear()

	#Merge files
	for c in sorted(alpha_dict1.keys()):
		print "Indexing file ",c
			
		c_posting = get_sort_merge('posting_'+c)

		os.remove('posting_'+c)

		fp=open('posting_'+c,'w')

		fi=open('index_'+c,'w')
		
		fp.write("\n".join(  [ ':'.join( [k,";".join([",".join(map(str,tup)) for tup in c_posting[k] ] ) ] )  for k in sorted(c_posting.keys()) ] ))
		
		offsets=[ len(':'.join( [k,";".join([",".join(map(str,tup)) for tup in c_posting[k] ] ) ] ) )+1 for k in sorted(c_posting.keys()) ] 
		
		cumu_offsets=[ [k,0] for k in sorted(c_posting.keys()) ]

		for i in xrange(len(offsets)-1):
			cumu_offsets[i+1][1]=cumu_offsets[i][1]+offsets[i]
		fi.write( "\n".join(":".join(map(str,cumu_offsets[i])) for i in xrange(len(cumu_offsets))) )
		fp.close()
		fi.close()
	
	#print "Total Documents=",parsed

def get_posting(word):
	key=word[0:2]
	fi=open('index_'+key,'r')
	if fi:
		word_index = { a:b for a,b in  [ line.strip().split(":") for line in fi.readlines() ] }
		if word_index.has_key(word):
			fp=open('posting_'+key,'r')
			fp.seek(int(word_index[word]))
			result=fp.readline()
			fp.close()
			return result
		else:
			return []
	return []


if __name__=='__main__':


	#build_inverted_index(str(sys.argv[1]))
	print "Loading Resources"

	all_docs={}
	for line in open('doc_info','r'):
		id,t,c=line.strip().split(":::")
		all_docs.update({id:[t,c]})

	all_idf={}
	for line in open('index_info','r'):
		k,v=line.strip().split(":")
		all_idf.update({k:float(v)})	

	while True:
		
		query=raw_input("\nEnter Query(exit to end):")

		start_time = time.time()

		if query=="exit":
			break
		
		print "Processing Query:"
		processed_query=process_text_to_terms(query)[0]

		if len(processed_query)==0:
			print "Query not found"
			continue 

		query_postings={ term:get_posting(term) for term in sorted(processed_query) }

		if len(query_postings.keys())==0 or all(query_postings[p]==[] for p in sorted(processed_query)):
			print "Query not found"
			continue 
		
		print "Generating candidates:"
		candidate_docs = {}
		for p in sorted(processed_query):
			docs = [ t.split(",")[0] for  t in query_postings[p].strip().split(":")[1].split(";") ]
			tfs = [ t.split(",")[1] for  t in query_postings[p].split(":")[1].split(";") ]
			for i in xrange(len(docs)):
				if not candidate_docs.has_key(docs[i]):
					candidate_docs.update({docs[i]: { term:0 for term in sorted(processed_query) } })
				candidate_docs[docs[i]][p]=float(tfs[i])

		query_postings.clear()

		top_scores=[0]*10
		top_docs=[""]*10

		print "Ranking "+str(len(candidate_docs))+" candidates"
		for doc in candidate_docs:
			s=[]
			for t in sorted(processed_query):
				try:
					s.append( ( all_idf[t] if all_idf.has_key(t) else 0 ) * ( (candidate_docs[doc][t]+1) / float(int(   (all_docs[doc][1] if all_docs.has_key(doc) else 0)  )+1)  ) )
				except ValueError:
					continue
				#print idf_final[t], (candidate_docs[doc][t]+1) ,float(int(doc_final[doc][1])+1) 
			score=sum(s)
			for i in range(len(top_scores)):
				if score>top_scores[i]:
					top_scores[i]=score
					top_docs[i]=doc
					break


		candidate_docs.clear()
		#print scores

		top=sorted(dict(zip(top_docs,top_scores)).items(),key=operator.itemgetter(1),reverse=True)

		for id,score in top:
			print score," : ",all_docs[id][0]

		print "Execution Time=",time.time()-start_time

		
