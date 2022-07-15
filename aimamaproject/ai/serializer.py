from rest_framework.serializers import (Serializer)
from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST

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
