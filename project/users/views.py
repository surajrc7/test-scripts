import re
from unittest import result
from urllib import response
from django.shortcuts import render
from django.http import JsonResponse
#from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from drf_yasg import openapi
from rest_framework.generics import GenericAPIView
from drf_yasg.utils import swagger_auto_schema
from .serializers import (TextSerializer, CitationSerializer, TimelineSerializer, OpenCitationSerializer)
from datetime import datetime
import logging
import numpy as np
import pandas as pd
import json
from bson.objectid import ObjectId
import uuid
import os
from itertools import groupby
import requests
from django.conf import settings
from .src import main
from .apps import UsersConfig
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required


logging.basicConfig(format='%(levelname)-s %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%s')


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)
        
        
class COREFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = TextSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'Text': openapi.Schema(type=openapi.TYPE_STRING, description='Keyword to search for finidng associations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['Text', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        text = data['Text']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if text == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            rows = settings.CASSANDRA.query_topics(collection="datasource_core",keywords=text,limit=100)
            records = main.mapsets(list(rows),remove_cols=["fullText","abstract"])
            response_dict = {"RawText": text, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)
        
class CORETimeline(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = TimelineSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'Text': openapi.Schema(type=openapi.TYPE_STRING, description='Keyword to search for finidng associations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
            'FromYear': openapi.Schema(type=openapi.TYPE_INTEGER, description='From The Year')
        },
        required=['Text', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_503_SERVICE_UNAVAILABLE: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        text = data['Text']
        request_id = data['Key']
        fromDate = data['FromYear']
        objInstance = ObjectId(request_id)
        if text == '':
            return Response("Got Empty String", status=status.HTTP_400_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            try:
                rows = settings.CASSANDRA.query_topics(collection="datasource_core",keywords=text)
                logging.info("Len-> Found"+str(len(rows)))
                records = main.mapsets(list(rows),remove_cols=["fullText","abstract",])
                records.sort(key=lambda x:x['datePublishedYear'])
                result:dict = {}
                for k,v in groupby(records,key=lambda x:x['datePublishedYear']):
                    if fromDate:
                        if int(k)>=fromDate:
                            result[k] = list(v)
                    else:
                        result[k] = list(v)
                response_dict = {"RawText": text, "ProcessedData": result,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
                return JsonResponse(response_dict, status=200)
            except Exception as e:
                response_dict = {"Error": {"Reason": "Internal Server Error-{}".format(e)}}
                return JsonResponse(response_dict,status=503)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)


class COREVennDiagram(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = TextSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'Text': openapi.Schema(type=openapi.TYPE_STRING, description='Keyword to search for finidng associations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['Text', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_503_SERVICE_UNAVAILABLE: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }
    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        text = data['Text']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if text == '':
            return Response("Got Empty String", status=status.HTTP_400_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            try:
                rows = settings.CASSANDRA.query_topics(collection="datasource_core",keywords=text)
                logging.info("Number of Records Found:{}".format(len(list(rows))))
                result = UsersConfig.Associations.pipeline(text,list(rows))
                response_dict = {"RawText": text, "ProcessedData": result,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": status.HTTP_200_OK,
                        "Version": settings.VERSION}
                #logging.info(response_dict)
                return JsonResponse(response_dict, status=status.HTTP_200_OK)
            except Exception as e:
                response_dict = {"Error": {"Reason": "Internal Server Error-{}".format(e)}}
                return JsonResponse(response_dict,status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=status.HTTP_401_UNAUTHORIZED)



class CitiationsFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = CitationSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'DOI': openapi.Schema(type=openapi.TYPE_STRING, description='ID for finding the Citations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['DOI', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        doi = data['DOI']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if doi == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            records = UsersConfig.Citations.fetchCitations(doi)
            response_dict = {"RawText": doi, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)
        
class CitiationsCountFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = CitationSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'DOI': openapi.Schema(type=openapi.TYPE_STRING, description='ID for finding the Citations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['DOI', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        doi = data['DOI']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if doi == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            records = UsersConfig.Citations.fetchCitationsCount(doi)
            response_dict = {"RawText": doi, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)
        
class RefrenceFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = CitationSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'DOI': openapi.Schema(type=openapi.TYPE_STRING, description='ID for finding the Citations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['DOI', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        doi = data['DOI']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if doi == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            records = UsersConfig.Citations.fetchRefrences(doi)
            response_dict = {"RawText": doi, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)
        
class RefrenceCountFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = CitationSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'DOI': openapi.Schema(type=openapi.TYPE_STRING, description='ID for finding the Citations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['DOI', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        doi = data['DOI']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if doi == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            records = UsersConfig.Citations.fetchRefrencesCount(doi)
            response_dict = {"RawText": doi, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)
        
class CitationRefFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = OpenCitationSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'OAI': openapi.Schema(type=openapi.TYPE_STRING, description='ID for finding the Citations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['OAI', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        doi = data['OAI']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if doi == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            records = UsersConfig.Citations.fetchCitationMetaInfo(doi)
            response_dict = {"RawText": doi, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)
        
class MetainfoCitationFetch(GenericAPIView):  # generics.CreateAPIView
    # permission_classes = (Check_API_KEY_Auth,)
    serializer_class = CitationSerializer
    
    login_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'DOI': openapi.Schema(type=openapi.TYPE_STRING, description='ID for finding the Citations'),
            'Key': openapi.Schema(type=openapi.TYPE_STRING, description='16 Chars long Private Key'),
        },
        required=['DOI', 'Key']
    )
    
    login_schema_response = {
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'RawText': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    }

    @swagger_auto_schema(request_body=login_schema, responses=login_schema_response)
    def post(self, request):
        """
        This text is the description for this API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        doi = data['DOI']
        request_id = data['Key']
        objInstance = ObjectId(request_id)
        if doi == '':
            return Response("Got Empty String", status=status.HTTP_500_BAD_REQUEST)
        Database = settings.MONGO.find_one(collection='users_customuser',query={'_id':objInstance}) #62cb0800822bd4f866bb1284
        if Database:
            records = UsersConfig.Citations.fetchMetadata(doi)
            response_dict = {"RawText": doi, "ProcessedData": records,
                        'ProcessedDate': datetime.utcnow().__str__(),
                        "RequestID": request_id, "status": 200,
                        "Version": settings.VERSION}
            return JsonResponse(response_dict, status=200)
        else:
            response_dict = {"Error": {"Reason": "Unauthorized Access, Please Use The Right Key"}}
            return JsonResponse(response_dict,status=401)