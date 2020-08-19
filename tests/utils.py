import json

from flask import Response
from werkzeug.utils import cached_property


class JSONResponse(Response):
    # pylint: disable=too-many-ancestors
    """
    A Response class with extra useful helpers, i.e. ``.json`` property.
    """
    @cached_property
    def json(self):
        return json.loads(self.get_data(as_text=True))
