"""
    Handle the payments
"""
from abc import ABC, abstractmethod
from ramda import path_or
from .clients import RazorPayClient

class Payments(ABC):
    """
    This class is responsible for payments
    """

    @abstractmethod
    def get_client(self):
        """
        Return the client
        """


class RazorpayPayment(Payments):
    """
    This handles the razor pay payments
    """

    def get_client(self):
        """
        return the client
        """
        return RazorPayClient().get_client()


class PaymentLinks(RazorpayPayment):
    """
    This class handle the razorpay payment links
    """
    def _get_call_back_url(self, data : dict)-> str:
        """
            This function form a call back url and return
        """
        phone_number = path_or("", ["phone_number"], data)
        plan_id = path_or("", ["plan_id"], data)
        root_url = "https://makechat.pythonanywhere.com/"
        call_back_path = "payment_redirect/"
        return root_url + call_back_path + "?phone_number=" +phone_number + "&plan_id=" + plan_id

    def generate_link(self, data: dict):
        """
        generate link for payments
        """
        return self.get_client().payment_link.create(
            {
                "upi_link": False,
                "amount": path_or(5, ["amount"], data),
                "currency": "INR",
                "accept_partial": False,
                "description": "For makechat subscription",
                "customer": {
                    "contact": path_or("", ["phone_number"], data),
                },
                "notify": {"sms": False, "email": False,"whatsapp" :True},
                "reminder_enable": False,
                "notes": {"plan_id": path_or("", ["plan_id"], data)},
                "callback_url": self._get_call_back_url(data=data),
                "callback_method": "get",
            }
        )
