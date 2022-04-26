from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import APIException

from django.conf import settings

from ram_redis_app import utils, serializers
from ram_redis_app.config import REDIS_DB_INDEX

import redis
import json


class RamViewSet(ViewSet):

    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT, 
                                       db=REDIS_DB_INDEX)

    def get_all_loads(self, request, *args, **kwargs):
        cpu_usage = utils.get_cpu_usage()
        ram_usage = utils.get_ram_usage()
        gpu_usage = utils.get_gpu_usage()

        utils.save_request_data(request, self.redis_instance)

        response_dict = {
            'cpu': cpu_usage,
            'ram': ram_usage,
            'gpu': gpu_usage
        }

        return Response(response_dict, status=status.HTTP_200_OK)

    def get_single_load(self, request, *args, **kwargs):
        keyword = 'load_type'

        serializer = serializers.SingleLoadSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            load_func = getattr(utils, 'get_{}_usage'.format(serializer.data.get(keyword)), None)

            if load_func is not None:
                utils.save_request_data(request, self.redis_instance)
                return Response({serializer.data.get(keyword): load_func()}, status=status.HTTP_200_OK)
            else:
                raise APIException('Please, do not rename utils functions')

    def get_queries(self, request, *args, **kwargs):
        date_from_score, date_to_score, hash_keys = self.__get_scores_and_keys_for_queries(request, *args, **kwargs)
        hash_values = utils.get_hash_values(self.redis_instance, hash_keys)

        response_dict = {}
        for key, value in zip(hash_keys, hash_values):
            jsonify_value = value if value is not None else "null"
            response_dict[key] = json.loads(jsonify_value)

        utils.save_request_data(request, self.redis_instance)
        return Response(response_dict, status=status.HTTP_200_OK)

    def delete_queries(self, request, *args, **kwargs):
        date_from_score, date_to_score, hash_keys = self.__get_scores_and_keys_for_queries(request, *args, **kwargs)
        deleted_count = utils.remove_queries_data(self.redis_instance, date_from_score, date_to_score, hash_keys)

        utils.save_request_data(request, self.redis_instance)
        return Response({'deleted_count': deleted_count}, status=status.HTTP_204_NO_CONTENT)

    def __get_scores_and_keys_for_queries(self, request, *args, **kwargs):
        serializer = serializers.DateTimeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            date_from, date_to = serializer.data.get('date_from'), serializer.data.get('date_to')
            
            date_from_score, date_to_score = utils.get_from_to_scores(self.redis_instance, date_from, date_to)
            hash_keys = utils.get_hash_keys(self.redis_instance, date_from_score, date_to_score)
            return date_from_score, date_to_score, hash_keys
