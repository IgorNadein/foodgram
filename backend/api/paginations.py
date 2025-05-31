from rest_framework.pagination import PageNumberPagination

from .constants import PAGINATION_LIMIT


class LimitPagination(PageNumberPagination):
    page_size = PAGINATION_LIMIT
    page_size_query_param = 'limit'
