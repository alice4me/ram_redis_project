import json
import psutil
import GPUtil

from datetime import datetime

from ram_redis_app.config import REDIS_ZSET_NAME, REDIS_HASH_NAME, DATETIME_FORMAT


def get_cpu_usage():
    return psutil.cpu_percent(percpu=True)


def get_ram_usage():
    mem = psutil.virtual_memory()
    return mem.percent


def get_gpu_usage():
    return [round(gpu.load*100, 1) for gpu in GPUtil.getGPUs()]


def save_request_data(request, redis_instance):
    hash_key, zscore = generate_hash_key(redis_instance)
    redis_instance.zadd(REDIS_ZSET_NAME, {hash_key: zscore})

    hash_data = {'method': request.method, 'path': request.path, 'data': request.data}
    redis_instance.hset(REDIS_HASH_NAME, hash_key, json.dumps(hash_data))


def generate_hash_key(redis_instance):
    now = datetime.now().strftime(DATETIME_FORMAT)
    last_key_with_score = redis_instance.zrange(REDIS_ZSET_NAME, -1, -1, withscores=True)

    if not last_key_with_score:
        return now + ':1', 1

    last_key = last_key_with_score[0][0].decode('utf-8')
    score = last_key_with_score[0][1]

    last_key_arr = last_key.split(':')
    if now == ':'.join(last_key_arr[:-1]):
        new_key = now + ':{}'.format(int(last_key_arr[-1])+1)
        new_score = score
    else:
        new_key = now + ':1'
        new_score = score + 1

    return new_key, new_score


def get_hash_values(redis_instance, list_of_keys):
    if not list_of_keys:
        return []
    return redis_instance.hmget(REDIS_HASH_NAME, list_of_keys)


def get_hash_keys(redis_instance, date_from_score, date_to_score):
    if not all([date_from_score, date_to_score]):
        return []

    bytes_key_list = redis_instance.zrangebyscore(REDIS_ZSET_NAME, date_from_score, date_to_score)
    return [byte_key.decode('utf-8') for byte_key in bytes_key_list]


def get_from_to_scores(redis_instance, date_from, date_to):
    zcard = redis_instance.zcard(REDIS_ZSET_NAME)

    if zcard == 0:
        return None, None

    date_from_score = binary_get_score(redis_instance, date_from, zcard, right=True) if date_from\
        else redis_instance.zrange(REDIS_ZSET_NAME, 0, 0, withscores=True)[0][1]

    if date_from_score:
        date_to_score = binary_get_score(redis_instance, date_to, zcard, right=False) if date_to\
            else redis_instance.zrange(REDIS_ZSET_NAME, -1, -1, withscores=True)[0][1]
    else:
        date_to_score = None

    return date_from_score, date_to_score


def binary_get_score(redis_instance, target_time, zcard, right=True):
    left_index = 0
    right_index = zcard - 1
    candidate = None

    while left_index <= right_index:
        current_index = (left_index + right_index) // 2

        key_with_score = redis_instance.zrange(REDIS_ZSET_NAME, current_index, current_index, withscores=True)
        key = key_with_score[0][0].decode('utf-8')

        datetime_key = datetime.strptime(':'.join(key.split(':')[:-1]), DATETIME_FORMAT)
        datetime_target = datetime.strptime(target_time, DATETIME_FORMAT)

        if datetime_key < datetime_target:
            left_index = current_index + 1
            if not right:
                candidate = key_with_score[0][1]
        elif datetime_key > datetime_target:
            right_index = current_index - 1
            if right:
                candidate = key_with_score[0][1]
        else:
            return key_with_score[0][1]

    return candidate


def remove_queries_data(redis_instance, date_from_score, date_to_score, hash_keys):
    if not hash_keys:
        return 0
    redis_instance.zremrangebyscore(REDIS_ZSET_NAME, date_from_score, date_to_score)
    redis_instance.hdel(REDIS_HASH_NAME, *hash_keys)
    return len(hash_keys)
