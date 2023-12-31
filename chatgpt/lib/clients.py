"""
    This module handle the client creations
"""
from abc import ABC, abstractmethod
from twilio.rest import Client
import openai
import razorpay

ACCOUNT_ID_TWILLIO = ""
AUTH_TOPKEN_TWILLIO = "" # provide the correct key
OPENAPI_ORG = ""
OPEN_API_KEY = ""
RAZORPAY_CLIENT_ID = ""
RAZORPAY_SECRET = ""

class ClientBuilder(ABC):
    """
    Provides the abstraction for all clients
    """

    @abstractmethod
    def get_client(self):
        """
        Abstarct method, the client builder logic will
        be implemented in this method of child classes
        """


class TwillioClient(ClientBuilder):
    """
    creates the client for twillio
    """

    def get_client(self):
        """
        Returns the client object
        """
        return Client(ACCOUNT_ID_TWILLIO, AUTH_TOPKEN_TWILLIO)

    def __str__(self) -> str:
        pass


class OpenApiClient(ClientBuilder):
    """
    This function creates the open api client
    """

    def get_client(self):
        """
        Returns the open api client
        """
        openai.organization = OPENAPI_ORG
        openai.api_key = OPEN_API_KEY
        return openai

    def __str__(self) -> str:
        pass

class RazorPayClient(ClientBuilder):
    """
        This class will return the razor pay client
    """
    def get_client(self):
        """
            return client
        """
        return razorpay.Client(auth=(RAZORPAY_CLIENT_ID, RAZORPAY_SECRET))