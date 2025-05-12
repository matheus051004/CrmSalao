from pydantic import BaseModel


class Configs(BaseModel):
    crm_name: str
    follow_up_minutes: int
    msg_preference: str
    msg_cancel: str
    msg_follow_up: str
    assistant_name: str
    crm_slogan: str
    google_cred_json: str