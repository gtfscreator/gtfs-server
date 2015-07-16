import datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from rest_framework import filters
from rest_framework import generics
from rest_framework.viewsets import GenericViewSet

from multigtfs.models import Stop, Service, Trip

from .helpers import active_services_from_date
from .serializers import (
    StopSerializerWithDistance, ServiceSerializer, TripSerializer,
    GeoStopSerializerWithDistance )
from .base_views import FeedNestedListAPIView

class StopsNearView(generics.ListAPIView):
    serializer_class = StopSerializerWithDistance
    queryset = Stop.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('feed', )


    def get_queryset(self):
        queryset = super(StopsNearView, self).get_queryset()
        queryset = self.filter_queryset(queryset)
        radius = self.request.query_params.get('radius', 1.0)
        radius = float(radius)
        x = self.kwargs['x']
        y = self.kwargs['y']
        point = Point(float(x), float(y))
        queryset = queryset.distance(point).filter(point__distance_lt=(point, D(km=radius)))
        return queryset


class GeoStopsNearView(StopsNearView):
    serializer_class = GeoStopSerializerWithDistance
    pagination_class = None



class ServicesActiveView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('feed', )

    def get_queryset(self):
        qset = super(ServicesActiveView, self).get_queryset()
        year, month, day = int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day'])
        requested_date = datetime.date(year, month, day)
        qset = active_services_from_date(requested_date, qset)
        return qset

class FeedServiceActiveView(FeedNestedListAPIView, ServicesActiveView):
    pass


class TripActiveView(generics.ListAPIView):
    serializer_class = TripSerializer
    queryset = Trip.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('service__feed', )

    def get_queryset(self):
        qset = super(TripActiveView, self).get_queryset()
        year, month, day = int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day'])
        requested_date = datetime.date(year, month, day)
        services = active_services_from_date(requested_date)
        active_trips = qset.filter(service__in=services)
        return active_trips

class FeedTripActiveView(FeedNestedListAPIView, TripActiveView):
    pass
