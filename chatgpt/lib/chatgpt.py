"""
    handle the chatgpt
"""
from ramda import path_or
from openai.error import RateLimitError
from .clients import OpenApiClient


class ChatGpt:
    """
    handles the chat with chatgpt
    """

    def _get_client(self):
        """
        this function return the open ai client
        """
        return OpenApiClient().get_client()

    def generate_image(self, image_prompt: str):
        """
        Generate image
        """
        # return "https://images.freeimages.com/images/large-previews/228/chain-links-1312683.jpg"
        try:
            open_ai_client = self._get_client()
            response = open_ai_client.Image.create(
                prompt=image_prompt, n=1, size="1024x1024"
            )
            image_url = path_or("", ["data", 0, "url"], response)
            return image_url
        except Exception:
            return ""

    def chat(self, messages: list):
        """
        chat with chatgpt
        """
        # return "sorry we are unavailable at this moment, please try again"
        try:
            open_api_client = self._get_client()
            response = open_api_client.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages
            )
            message = path_or("", ["choices", 0, "message", "content"], response)
            return message
        except (RateLimitError, Exception) as error:
            print("Error", error)
            return "There is a issue at our system, please contact admin to resolve this issue."

    def completions(self, promt: str):
        """
        promt completions
        """
        try:
            chat = [
                {
                    "role" :"user",
                    "content" : promt
                }
            ]
            response = self._get_client().ChatCompletion.create(
                model="gpt-3.5-turbo", messages=chat
            )
            message = path_or("", ["choices", 0, "message", "content"], response)
            return message
        except Exception as error:
            print("error------------->", error)
            return "Unexpected response from Makechat AI bot"

    def form_conversations(self, user_messages):
        """
        This function will form the previous messages in conversational format
        """
        messages = []
        for user_msg in user_messages:
            messages.append({"role": user_msg.role, "content": user_msg.content})
        messages.reverse()
        return messages
