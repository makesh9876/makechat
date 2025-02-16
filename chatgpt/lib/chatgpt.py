"""
    handle the chatgpt
"""
from ramda import path_or
from .clients import OpenApiClient
from ..models import FreeAiRequests


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
            FreeAiRequests().get_instance().save()
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
                model="gpt-4", messages=messages
            )
            message = path_or("", ["choices", 0, "message", "content"], response)
            FreeAiRequests().get_instance().save()
            return message
        except (Exception) as error:
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
                model="gpt-4", messages=chat
            )
            message = path_or("", ["choices", 0, "message", "content"], response)
            FreeAiRequests().get_instance().save()
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
    
    def get_image_response(self, base64_image):
        response = self._get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze and describe the contents of this image in detail. Identify objects, people, places, or actions.

    - If the image contains food, provide its estimated nutritional values (calories, fat, protein, carbohydrates, etc.).
    - If it is a natural scene, describe the environment and any notable elements like weather, animals, or plants.
    - If it contains text, extract and summarize its meaning.
    - If it is traffic-related, describe the scene, vehicles, road signs, and possible traffic conditions.
    - If it contains a person, describe their appearance, expression, and possible emotions (without making personal judgments).
    - If it is a piece of code, summarize what it does and mention the programming language.
    - If it is an object or an unknown scene, describe it as clearly as possible.

    Do not ask for any clarifications—provide the best possible description based on the image alone.""",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail" : "low"},
                        },
                    ],
                }
            ],
        )
        print("======Response", response)
        return response
