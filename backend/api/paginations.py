from foodgram_backend.settings import PAGINATION_LIMIT
from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size = PAGINATION_LIMIT
    page_size_query_param = 'limit'
