import json
import ast
from urllib import response

from attr import assoc
from pkg_resources import working_set
import numpy as np
import pandas as pd
from apyori import apriori
from django.conf import settings
import re
import math
from numpy import linalg as LA



def mapsets(results:list):
    response:list=[]
    for _,idx in enumerate(results):
        Data:dict = {}
        Data['row'] = _
        Data['uuid']=idx.uuid
        Data['doi'] = idx.doi
        Data['coreId'] = idx.coreId
        Data['title'] = idx.title
        Data['oai'] = idx.oai
        Data['issn'] = idx.issn
        Data['downloadUrl'] = idx.downloadUrl
        Data['fullText'] = idx.fullText
        Data['publisher'] = idx.publisher
        Data['abstract'] = idx.abstract
        Data['datePublished']= idx.datePublished
        Data['dateUpdated'] = idx.dateUpdated
        Data['pdfHashValue'] = idx.pdfHashValue
        Data['year'] = idx.year
        Data['magId'] = idx.magId
        Data['urls'] = idx.urls
        Data['relations'] = idx.relations
        Data['authors'] = idx.authors
        Data['fullTextIdentifier']= idx.fullTextIdentifier
        Data['topics'] = idx.topics
        Data['subjects'] = idx.subjects
        Data['contributors'] = idx.contributors
        Data['identifiers'] = idx.identifiers
        Data['enrichments'] = ast.literal_eval(idx.enrichments)
        if idx.language:
            Data['language'] = {k:y for k,y in idx.language.items()}
        else:
            Data['language'] = None
        if idx.journals:
            journals = []
            for idy in idx.journals:
                journal = {}
                journal['identifiers'] = idy.identifiers
                journal['title'] = idy.title
                journals.append(journal)
            Data['journals'] = journals
        else:
            Data['journals'] = None
        response.append(Data)
    return response



class Associations:
    def __init__(self):
        self.Exe = ['NORP','LOC','GPE', 'New research','Article',"Research"]
        self.cleaned_words = []
    
    def __call__(self):
        pass
    
    def inverseDocumentFrequency(self,term, documents)->float:
        count = 0
        for doc in documents:
            if term.lower() in doc.lower().split():
                count += 1
        if count > 0:
            return 1.0 + math.log(float(len(documents))/count)
        else:
            return 1.0

    def tf_idf(self,term:str, document:str, documents):
        tf = self.termFrequency(term, document)
        idf = self.inverseDocumentFrequency(term, documents)
        return tf*idf

    def termFrequency(self,term, document):
        normalizeDocument = document.lower().split()
        return normalizeDocument.count(term.lower()) / float(len(normalizeDocument))

    def generateVectors(self,query, documents):
        tf_idf_matrix = np.zeros((len(query.split()), len(documents)))
        for i, s in enumerate(query.lower().split()):
            idf = self.inverseDocumentFrequency(s, documents)
            for j,doc in enumerate(documents):
                tf_idf_matrix[i][j] = idf * self.termFrequency(s, doc)
        return tf_idf_matrix
        
    def word_count(self,s):
        counts = dict()
        words = s.lower().split()
        for word in words:
            if word in counts:
                counts[word] += 1
            else:
                counts[word] = 1
        return counts
    
    def build_query_vector(self,query, documents):
        count = self.word_count(query)
        vector = np.zeros((len(count),1))
        for i, word in enumerate(query.lower().split()):
            vector[i] = float(count[word])/len(count) * self.inverseDocumentFrequency(word, documents)
        return vector
    
    def consine_similarity(self,v1, v2):
        return np.dot(v1,v2)/float(LA.norm(v1)*LA.norm(v2))
    
    def compute_relevance(self,query, documents):
        scores:list[float] = []
        for i, doc in enumerate(documents):
            similarity = self.consine_similarity(self.tf_idf_matrix[:,i].reshape(1, len(self.tf_idf_matrix)), self.query_vector)
            if float(similarity[0])>0.80:
                scores.append(similarity[0])
        return math.ceil(sum(scores)/len(documents))
    
    def add_unwanted_keywords(self,query:str):
        self.Exe.append(query)
        
    def isEnglish(self,s):
        try:
            s.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True
    
    def filtering_Location(self,string:str):
        results = []
        for idx in documents:
            idx = idx.strip().capitalize()
            if idx in self.Exe:
                continue
            if idx in self.cleaned_words:
                continue
            doc = settings.SPACYMODEL(idx)
            if doc.ents:
                for ent in doc.ents:    
                    if ent.label_ in self.Exe:
                        if self.isEnglish(idx):
                            if len(ent.text) >5:
                                if re.search(r'\d', idx):
                                    results.append(idx)
                            else:
                                results.append(idx)
                        else:
                            results.append(idx)
                    else:
                        results.append(idx)
            else:
                doc = settings.SPACYMODEL(idx.lower())
                if doc.ents:
                    for ent in doc.ents:    
                        if ent.label_ in self.Exe:
                            if self.isEnglish(idx):
                                if len(ent.text) >5:
                                    if re.search(r'\d', idx):
                                        results.append(idx)
                                else:
                                    results.append(idx)
                            else:
                                results.append(idx)
                        else:
                            results.append(idx)
                else:
                    results.append(idx)
        return results            

    def inspect(self,output):
            lhs         = [tuple(result[2][0][0])[0] for result in output]
            rhs         = [tuple(result[2][0][1])[0] for result in output]
            support    = [result[1] for result in output]
            confidence = [result[2][0][2] for result in output]
            lift       = [result[2][0][3] for result in output]
            return list(zip(lhs, rhs, support, confidence, lift))
    
    def process_data(self,json_obj):
        dataset = pd.DataFrame(json_obj)
        association_dataset = dataset[['coreId','topics','fullText']]
        association_dataset.set_index(association_dataset['coreId'],inplace=True)
        association_dataset.drop(columns=['coreId'],inplace=True)
        association_dataset['topics'] = association_dataset.topics.apply(lambda x:",".join(x))
        association_dataset['topics'] = association_dataset.topics.apply(lambda x:x.lower())
        association_dataset['topics'] = association_dataset.topics.apply(lambda x:str(x).replace('\n',''))
        association_dataset['topics'] = association_dataset.topics.apply(lambda x:str(x).replace('-',' '))
        association_dataset['topics'] = association_dataset.topics.apply(lambda x:str(x).replace('_',' '))
        association_dataset['fullText'] = association_dataset.fullText.apply(lambda x:str(x).replace('\n',''))
        association_dataset.topics.replace(r'^\s*$', np.nan, regex=True, inplace=True)
        bool_series = pd.notnull(association_dataset["topics"])
        association_dataset = association_dataset[bool_series]
        working_dataset = association_dataset["topics"].str.split(pat=",", expand=True)
        height,weight = working_dataset.shape
        articles = []
        for i in range(0,len(working_dataset)):
            articles.append([str(working_dataset.values[i,j]) for j in range(0,weight)])
        return articles,association_dataset
    
    def fetch_documents(self,association_dataset):
        documents = association_dataset.fullText.dropna().tolist()
        return [idx for idx in documents if idx!='None']
    
    def pipeline(self,results:list):
        response = mapsets(results)
        articles,association_dataset = self.process_data(response)
        rule = apriori(articles, min_support = 0.003, min_lift = 3, min_length = 1, max_length = 2)
        output = list(rule)
        output_DataFrame = pd.DataFrame(self.inspect(output), columns = ['Left_Hand_Side', 'Right_Hand_Side', 'Support', 'Confidence', 'Lift'])
        self.tf_idf_matrix = self.generateVectors(query, self.documents)
        self.query_vector = self.build_query_vector(query, self.documents)
        pass



