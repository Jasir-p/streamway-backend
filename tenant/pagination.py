from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_next_link(self):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        return f'{self.request.path}?page={page_number}'

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        return f'{self.request.path}?page={page_number}'
