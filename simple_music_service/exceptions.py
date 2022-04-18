from rest_framework.exceptions import APIException
from rest_framework import status


class AlreadyExistingObjectException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Object already exists"


class UnableSpeechRecognitionException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Unable to recognize this speech"
