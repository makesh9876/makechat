"""
    handle the twillio related stuff
"""
from .clients import TwillioClient


class OutgoingMessage:
    """
    send message to user
    """

    def _get_client(self):
        """
        This function return twillio client
        """
        return TwillioClient().get_client()

    def send_message_with_media(self, message_text, media_url, phone_number):
        """
        This function send the whatsapp message with media url
        """
        return self._get_client().messages.create(
            from_="whatsapp:+14847299654",
            body=message_text,
            media_url=media_url,
            to="whatsapp:+91" + phone_number,
        )

    def send_message_with_text(self, message_text, phone_number):
        """
        This function send text message in whatsapp
        """
        return self._get_client().messages.create(
            from_="whatsapp:+14847299654",
            body=message_text,
            to="whatsapp:+91" + phone_number,
        )

    def send(self, user_number, response_message: str, mediaurl: str = ""):
        """
        This function will send the message to users
        """
        print("======user number", user_number)
        resposnse_message_list = [
            response_message[i : i + 1600]
            for i in range(0, len(response_message), 1600)
        ]
        for msges in resposnse_message_list:
            if mediaurl:
                return self.send_message_with_media(
                    message_text=msges,
                    media_url=mediaurl,
                    phone_number=user_number
                )
            self.send_message_with_text(
                message_text=msges,
                phone_number=user_number
            )
        return {}
