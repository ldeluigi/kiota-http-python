import httpx

from .middleware import BaseMiddleware
from .options import UrlReplaceHandlerOption


class UrlReplaceHandler(BaseMiddleware):

    def __init__(self, options: UrlReplaceHandlerOption = UrlReplaceHandlerOption(), **kwargs):
        """Create an instance of UrlReplaceHandler

        Args:
            options (UrlReplaceHandlerOption, optional): The url replacement
            options to pass to the handler.
            Defaults to UrlReplaceHandlerOption
        """
        super().__init__()
        self.options = options

    async def send(
        self, request: httpx.Request, transport: httpx.AsyncBaseTransport
    ) -> httpx.Response:  #type: ignore
        """To execute the current middleware

        Args:
            request (httpx.Request): The prepared request object
            transport(httpx.AsyncBaseTransport): The HTTP transport to use

        Returns:
            Response: The response object.
        """
        current_options = self._get_current_options(request)

        url_string: str = str(request.url)  #type: ignore
        url_string = self.replace_url_segment(url_string, current_options)
        request.url = httpx.URL(url_string)
        response = await super().send(request, transport)
        return response

    def _get_current_options(self, request: httpx.Request) -> UrlReplaceHandlerOption:
        """Returns the options to use for the request.Overries default options if
        request options are passed.

        Args:
            request (httpx.Request): The prepared request object

        Returns:
            UrlReplaceHandlerOption: The options to be used.
        """
        current_options = self.options
        request_options = request.options.get(  # type:ignore
            UrlReplaceHandlerOption.get_key()
        )
        # Override default options with request options
        if request_options:
            current_options = request_options

        return current_options

    def replace_url_segment(self, url_str: str, current_options: UrlReplaceHandlerOption) -> str:
        if (current_options and current_options.is_enabled and current_options.replacement_pairs):
            for k, v in current_options.replacement_pairs.items():
                url_str = url_str.replace(k, v, 1)
        return url_str