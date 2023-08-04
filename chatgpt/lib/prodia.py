# """
#     handle the prodia api
# """
# import requests
# import time
# from ramda import path_or
# from .clients import ProdiaAI


# class Prodia:
#     """
#     handles the prodia
#     """

#     def image(self, prompt: str):
#         """
#         generate image
#         """
#         payload = {
#             "prompt": prompt,
#             "negative_prompt": "badly drawn",
#             "steps": 25,
#             "cfg_scale": 7,
#             "seed": -1,
#             "upscale": False,
#         }
#         url = ProdiaAI().generate_url()
#         headers = ProdiaAI().get_client()["headers"]
#         #response = requests.post(url, headers=headers, json=payload)
#         #response_json = response.text
#         #time.sleep(3)
#         #job_id = path_or("",["job"], response_json)
#         job_id = "1c626e11-2bc7-4f4b-8b17-bda4ed01c5f0"
#         image_response = requests.get(
#             url=ProdiaAI().get_job_url().format(job_id), headers=headers
#         )
#         print("3333333333333",image_response.text)
#         return path_or("", ["imageUrl"], image_response.text)
