from django.urls import path

from ram_redis_app.viewsets import RamViewSet


urlpatterns = [
    path('all_loads/', RamViewSet.as_view({
         'get': 'get_all_loads',
         })
    ),
    path('single_load/', RamViewSet.as_view({
         'post': 'get_single_load',
         })
    ),
    path('queries/', RamViewSet.as_view({
         'post': 'get_queries',
         'delete': 'delete_queries',
         })
    ),
]
