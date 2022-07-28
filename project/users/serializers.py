from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import SendEmailResetSerializer
from .utils import validate_g_recaptcha_response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.serializers import (Serializer)

User = get_user_model()


# Serializers define the API representatio
class OpenAPISerializer(Serializer):
    class Meta():
        Text = serializers.CharField(label='Text as input', required=True)

class TextSerializer(Serializer):
    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: 'Bad Request'
        }
    Text = serializers.CharField(label='Text as input',required=True)
    Key = serializers.CharField(label='API Request ID', required=True)
    
class CitationSerializer(Serializer):
    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: 'Bad Request'
        }
    DOI = serializers.CharField(label='DOI as input',required=True)
    Key = serializers.CharField(label='API Request ID', required=True)

class OpenCitationSerializer(Serializer):
    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: 'Bad Request'
        }
    OAI = serializers.CharField(label='OAI as input',required=True)
    Key = serializers.CharField(label='API Request ID', required=True)



class TimelineSerializer(Serializer):
    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: 'Bad Request'
        }
    Text = serializers.CharField(label='Text as input',required=True)
    Key = serializers.CharField(label='API Request ID', required=True)  
    FromYear = serializers.IntegerField(label='From Year')
    

class CustomSendEmailResetSerializer(SendEmailResetSerializer):
    g_recaptcha_response = serializers.CharField(required=False)

    def validate(self, data):
        validated_data = validate_g_recaptcha_response(data)
        return validated_data
