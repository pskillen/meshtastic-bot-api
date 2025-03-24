import logging

logger = logging.getLogger(__name__)


class LogBadRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log bad requests to /api/raw-packet since these are malformed packets coming from the bot
        if response.status_code == 400 and request.path == '/api/raw-packet':
            logger.error(f"400 Bad Request: {request.path}")
            logger.error(f"Request body: {request.body}")
            logger.error(f"Request headers: {request.headers}")

        return response
