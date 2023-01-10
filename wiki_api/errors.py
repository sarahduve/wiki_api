class WikiApiError(Exception):


    def __init__(self, status_code, **data):
        self.status_code = status_code
        self.data = data

    def __str__(self):
        return f"WikiApiError({self.status_code}): {self.data}"
