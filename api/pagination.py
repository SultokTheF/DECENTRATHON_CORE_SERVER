from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5  
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # If 'page=all' is in the query parameters, return the entire queryset
        if request.query_params.get('page') == 'all':
            self.all_results = queryset
            return None
        
        # Otherwise, paginate as usual
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        # If 'page=all', return the entire queryset, but maintain the structure with 'count' and 'results'
        if hasattr(self, 'all_results'):
            count_pages = math.ceil(self.all_results.count() / self.page_size)
            return Response({
                'count': self.all_results.count(),
                'next': None,  # No next page because we're returning everything
                'previous': None,  # No previous page either
                'count_pages': count_pages,
                'results': list(self.all_results)  # Return all items in 'results'
            })

        # Default paginated response
        count_pages = math.ceil(self.page.paginator.count / self.page_size)
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count_pages': count_pages,
            'results': data
        })
