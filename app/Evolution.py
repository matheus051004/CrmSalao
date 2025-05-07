import requests


class Evolution:
    base_url: str
    api_key: str
    instance: str

    def __init__(self, base_url: str, api_key: str, instance: str):
        self.base_url = base_url
        self.api_key = api_key
        self.instance = instance

    def simple_text(self, number, message):
        headers = {
            'X-Api-Key': self.api_key
        }
        body = {
            "chatId": f"{number}@c.us",
            "reply_to": None,
            "text": f"{message}",
            "linkPreview": None,
            "linkPreviewHighQuality": False,
            "session": f"{self.instance}"
        }
        requests.post(
            url=f"{self.base_url}/api/sendText",
            headers=headers,
            json=body
        )
        return self.response(True, 'Mensagem enviada com sucesso')

    def response(self, success=True, message="", data=None):
        return {
            "success": success,
            "message": message,
            "data": data
        }
