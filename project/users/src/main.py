from cmath import log
from dataclasses import dataclass
import json
import ast
import logging
from unittest import result
from urllib import response
from pkg_resources import working_set
import numpy as np
import pandas as pd
from apyori import apriori
from django.conf import settings
import requests
import re
#import nest_asyncio
import aiohttp
import math
from numpy import linalg as LA
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sklearn.feature_extraction.text import TfidfVectorizer

#nest_asyncio.apply()

def findWholeWord(word:str):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search

def mapsets(results:list,remove_cols:list):
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
        Data['datePublished']= idx.datePublished.strftime('%Y-%m-%d')
        Data['datePublishedYear'] = idx.datePublished.strftime('%Y')
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
        if len(remove_cols)>0:
            for idx in remove_cols:
                del Data[idx]
        response.append(Data)
    return response


class Citations:
    def __init__(self):
        self.coreUrl = "https://opencitations.net/index/api/v1/"
        self.robotxt = {'citattionsCount':'/citation-count/',
                        'citations':'/citations/',
                        'references':'/references/',
                        'referenceCount':'/reference-count/',
                        'citation':'/citation/',
                        'metadata':'/metadata/'}
    
    def fetchCitationsCount(self, doi:str)->dict:
        try:
            response = requests.get(self.coreUrl + "citation-count/{}".format(doi))
            return response.json()
        except Exception as e:
            return {"data":[],"messages":"Error:->{}".format(e)}
        
    def fetchCitations(self,doi:str)->dict:
        try:
            response = requests.get(self.coreUrl + "citations/{}".format(doi))
            return response.json()
        except Exception as e:
            return {"data":[],"messages":"Error:->{}".format(e)}
    
    def fetchRefrences(self,doi:str)->dict:
        try:
            response = requests.get(self.coreUrl + "references/{}".format(doi))
            return response.json()
        except Exception as e:
            return {"data":[],"messages":"Error:->{}".format(e)}
    
    def fetchRefrencesCount(self,doi:str)->dict:
        try:
            response = requests.get(self.coreUrl + "reference-count/{}".format(doi))
            return response.json()
        except Exception as e:
            return {"data":[],"messages":"Error:->{}".format(e)}
        
    def fetchCitationMetaInfo(self,oci:str)->dict:
        try:
            response = requests.get(self.coreUrl + "citation/{}".format(oci))
            return response.json()
        except Exception as e:
            return {"data":[],"messages":"Error:->{}".format(e)}
        
    def fetchMetadata(self,doi:str)->dict:
        try:
            response = requests.get(self.coreUrl + "metadata/{}".format(doi))
            return response.json()
        except Exception as e:
            return {"data":[],"messages":"Error:->{}".format(e)}
        
    async def gather_with_concurrency(self,n, *tasks):
        semaphore = asyncio.Semaphore(n)
        async def sem_task(task):
            async with semaphore:
                return await task

        return await asyncio.gather(*(sem_task(task) for task in tasks))

    async def get_async(self,url, session, results):
        async with session.get(url) as response:
            i = url.split('/')[-1]
            obj = await response.text()
            results[i] = obj
            
    def makeUrls(self, ids:str,mode:str)->list:
        """
        Bulk Extraction
        Args:
            ids (str): _description_
            mode (str): [citattionsCount,citations,references,referenceCount,citation,metadata]

        Returns:
            list[str]: _description_
        """
        return [self.coreUrl+self.robotxt[mode]+idx for idx in ids.split('|')]
        
    async def fetchBulkcitations(self,urls:list)->dict:
        conn = aiohttp.TCPConnector(limit=None, ttl_dns_cache=300)
        session = aiohttp.ClientSession(connector=conn)
        results = {}
        conc_req = len(urls)//2
        await self.gather_with_concurrency(conc_req, *[self.get_async(i, session, results) for i in urls])
        return results
    
    def getBulkCitations(self,ids:str,mode:str)->list:
        URLS = self.makeUrls(ids,mode)
        return self.fetchBulkcitations(URLS)
      

class Associations:
    def __init__(self):
        self.Exe = ['NORP','LOC','GPE', 'New research','Article',"Research"]
        self.cleaned_words = []
        self.logger = logging.getLogger() 
    
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
    
    def consine_similarity(self,v1, v2):
        return np.dot(v1,v2)/float(LA.norm(v1)*LA.norm(v2))
    
    def compute_relevance(self,query_vector, documents):
        scores:list[float] = []
        for i, doc in enumerate(documents):
            if any(self.tf_idf_matrix[:,i].reshape(1, len(self.tf_idf_matrix)) and query_vector):
                similarity = self.consine_similarity(self.tf_idf_matrix[:,i].reshape(1, len(self.tf_idf_matrix)), query_vector)
                if float(similarity[0])>0.80:
                    scores.append(similarity[0].tolist())
        scores = [idx[0] for idx in scores if scores]
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
        for idx in string:
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
            #desity     = [idx*0.0 for idx in range(len(output))] 
            return list(zip(lhs, rhs, support, confidence, lift))
        
    def cleanTags(self,text:str)->str:
        text = text.lstrip()
        text = re.sub("_"," ",str(text))
        text = re.sub(r'^and\s+','', str(text))
        text = re.sub(r'(\\u[0-9]+)','',text)
        return text
         
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
    
    def fetch_documents(self,association_dataset:pd.DataFrame):
        documents = association_dataset.fullText.dropna().tolist()
        return [idx for idx in documents if idx!='None']
    
    def get_density(self,keyword:str)->dict:
        self.tf_idf_matrix = self.generateVectors(keyword, self.documents)
        query_vector = self.build_query_vector(keyword, self.documents)
        return {keyword:self.compute_relevance(query_vector, self.documents)}
    
    def computeDocumentTfidf(self):
        self.tf = TfidfVectorizer(analyzer='word')
        self.tfidf_matrix =  self.tf.fit_transform(self.documents)
        
    def build_query_vector(self,query:list):
        self.query_vector = self.tf.transform(query)
        
    def applyQueryCoverage(self)->list:
        return [idx.max() for idx in self.query_vector.toarray()]
    
    def apply_density(self,codecoverage:list,querywords:list)->list:
        return [{"word":idx, "coverage":idy} for idx,idy in zip(codecoverage,querywords)]

    def apply_associations(self, associated_word_density:dict, output_DataFrame:dict):
        if output_DataFrame['Left_Hand_Side'] in associated_word_density:
            output_DataFrame['Desity'] = associated_word_density[output_DataFrame['Left_Hand_Side']]
        elif output_DataFrame['Right_Hand_Side'] in associated_word_density:
            output_DataFrame['Desity'] = associated_word_density[output_DataFrame['Right_Hand_Side']]
        elif output_DataFrame['Right_Hand_Side'] in associated_word_density and output_DataFrame['Left_Hand_Side'] in associated_word_density:
            output_DataFrame['Desity'] = associated_word_density[output_DataFrame['Right_Hand_Side']]+associated_word_density[output_DataFrame['Left_Hand_Side']]
        else:
            output_DataFrame['Desity'] = 0.0
        return output_DataFrame
    
    def indirect_association(self,keyword:str,output:list):
        results = []
        for element in output:
            if re.sub(r'^[^a]*', '',keyword) == re.sub(r'^[^a]*', '',element['Left_Hand_Side'])  or re.sub(r'^[^a]*', '',keyword) == re.sub(r'^[^a]*', '',element['Right_Hand_Side']):
                element['association'] = "direct"
                element['Left_Hand_Side'] = self.cleanTags(element['Left_Hand_Side']) 
                element['Right_Hand_Side'] = self.cleanTags(element['Right_Hand_Side'])
            elif findWholeWord(keyword)(element['Left_Hand_Side'])  or findWholeWord(keyword)(element['Right_Hand_Side']):
                element['association'] = "in-direct"
                element['Left_Hand_Side'] = self.cleanTags(element['Left_Hand_Side']) 
                element['Right_Hand_Side'] = self.cleanTags(element['Right_Hand_Side'])
            results.append(element)
        return results
    
    def makeDictionary(self, keyword):
        pass
    
    def normalizeOutput(self,output:list):
        records,results = [], []
        for _,idx in enumerate(output):
            dataAccess:dict = {}
            if idx['Left_Hand_Side'] in records:
                pass
            elif idx['Right_Hand_Side'] in records:
                pass
            else:
                dataAccess['id'] = _
                dataAccess['keyword'] = idx
                pass
                     
    def pipeline(self,keyword:str,results:list,min_support:float=0.003,min_lift:int=3,min_length:int=1,max_length:int=2):
        response = mapsets(results, remove_cols=[])
        self.logger.info("Mapping Set Function Executed")
        articles,association_dataset = self.process_data(response)
        self.logger.info("Associations Created")
        self.documents = self.fetch_documents(association_dataset)
        self.logger.info("Documents Created")
        output = list(apriori(articles, min_support = min_support, min_lift = min_lift, min_length = min_length, max_length = max_length))
        self.logger.info("Output Created")
        output_DataFrame = pd.DataFrame(self.inspect(output), columns = ['Left_Hand_Side', 'Right_Hand_Side', 'Support', 'Confidence', 'Lift'])
        self.logger.info("Output DataFrame Created")
        associated_query = output_DataFrame[(output_DataFrame['Left_Hand_Side'].str.contains(keyword.lower()))|(output_DataFrame['Right_Hand_Side'].str.contains(keyword.lower()))]
        self.logger.info("Associated Query Created")
        associated_query_dict = associated_query.to_dict(orient='records')
        self.logger.info("Associated Query DICTIONARY Created")
        associated_query_dict = self.indirect_association(keyword,associated_query_dict)
        associated_words = list(set(associated_query['Right_Hand_Side'].unique()).union(set(associated_query['Left_Hand_Side'].unique())))
        self.computeDocumentTfidf()
        self.build_query_vector(associated_words)
        results = self.apply_density(self.applyQueryCoverage(),associated_words)
        self.logger.info(results)
        #associated_words = self.filtering_Location(associated_words)
        #self.logger.info("Associated Words II Created")
        #self.logger.info(associated_words)
        #associated_word_density = [self.get_density(idx) for idx in associated_words]
        #self.logger.info("Associated Words Density Created")
        #self.logger.info(associated_word_density)
        #associated_output = output_DataFrame.apply(lambda x:self.apply_associations(associated_word_density,x),axis=1)
        #logging.info(associated_query_dict)
        #logging.info(associated_output.to_dict())
        return associated_query_dict