from typing import Union

from flask import Response as FlaskResponse
from werkzeug.wrappers.response import Response as WerkzeugResponse


ViewResponse = Union[str, FlaskResponse, WerkzeugResponse]
