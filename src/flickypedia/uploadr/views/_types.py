from flask import Response as FlaskResponse
from werkzeug.wrappers.response import Response as WerkzeugResponse


ViewResponse = str | FlaskResponse | WerkzeugResponse
