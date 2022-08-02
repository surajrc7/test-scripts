from django.urls import include, path
from .views import (COREFetch, CORETimeline, COREVennDiagram, CitationRefFetch, CitiationsFetch, CitiationsCountFetch,
                    MetainfoCitationFetch, RefrenceCountFetch, RefrenceFetch, CORECitationsRefrence, COREDocumentByCoreId)

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('ai/v1/FetchRecordsFromKey/', COREFetch.as_view(), name='COREFetch'),
    path('ai/v1/FecthRecordsWithTimeline/',CORETimeline.as_view(), name='CORETimeline'),
    path('ai/v1/VennDiagramData/',COREVennDiagram.as_view(), name='COREVennDiagram'),
    path('ai/v1/fetchCitations/',CitiationsFetch.as_view(), name='CitiationsNames'),
    path('ai/v1/fetchCitationsCount/',CitiationsCountFetch.as_view(), name='CitiationsCount'),
    path('ai/v1/fetchRefrenceCount/',RefrenceCountFetch.as_view(), name='RefrenceCountFetch'),
    path('ai/v1/fetchRefrence/',RefrenceFetch.as_view(), name='RefrenceFetch'),
    path('ai/v1/fetchCitationMetaInfo/',MetainfoCitationFetch.as_view(), name='MetainfoCitationFetch'),
    path('ai/v1/fetchCitationsRef/',CitationRefFetch.as_view(), name='CitationRefFetch'),
    path('ai/v1/RefRelationWithCiatation/',CORECitationsRefrence.as_view(), name='CORECitationsRefrence'),
    path('ai/v1/getDocumentbyCoreId/',COREDocumentByCoreId.as_view(), name='COREDocumentByCoreId')
]
