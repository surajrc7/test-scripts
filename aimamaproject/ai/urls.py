from django.urls import path
from django.conf.urls import url
from .views import COREFetch, create_todo, CORETimeline, COREVennDiagram


urlpatterns = [
    path('FetchRecordsFromKey/', COREFetch.as_view(), name='COREFetch'),
    path('create/', create_todo, name='create-todo'),
    path('FecthRecordsWithTimeline/',CORETimeline.as_view(), name='CORETimeline'),
    path('VennDiagramData/',COREVennDiagram.as_view(), name='COREVennDiagram'),
]
