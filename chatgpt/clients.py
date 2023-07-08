"""
    This module handle the client creations
"""
from abc import ABC, abstractmethod
from twilio.rest import Client
import openai

ACCOUNT_ID_TWILLIO = "AC7bb006e27c87a985c52e832c34c781b5"
AUTH_TOPKEN_TWILLIO = "e67f9b297a51192ec03263001283ab17" # provide the correct key
OPENAPI_ORG = "org-QmSKgWgHBLzhgxBcP6RUgtcc"
OPEN_API_KEY = "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"


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
