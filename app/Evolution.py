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
            'apikey': self.api_key
        }
        body = {
            'number': number,
            'text': message
        }
        result = requests.post(
            url=f"{self.base_url}/message/sendText/{self.instance}",
            headers=headers,
            json=body
        )
        json_result = result.json()
        return self.response(True if json_result['status'] == 'PENDING' else False,
                             json_result['error'] if 'error' in json_result else 'Mensagem enviada com sucesso')

    def response(self, success=True, message="", data=None):
        return {
            "success": success,
            "message": message,
            "data": data
        }
