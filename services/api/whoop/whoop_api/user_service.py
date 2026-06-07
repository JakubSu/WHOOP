from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.dto import UserBasicProfile, UserBodyMeasurement
from whoop.whoop_api.parsers import parse_user_basic_profile, parse_user_body_measurement


class UserService:
    def __init__(self, client: BaseWhoopClient) -> None:
        self.client = client

    def get_basic_profile(self) -> UserBasicProfile:
        return parse_user_basic_profile(self.client.get("/v2/user/profile/basic"))

    def get_body_measurements(self) -> UserBodyMeasurement:
        return parse_user_body_measurement(self.client.get("/v2/user/measurement/body"))
