from rest_framework.pagination import PageNumberPagination


class PageNumberAndPageSizePagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100
