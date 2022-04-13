import os
import ldclient
from ldclient.config import Config
from backend.secrets import get_secret_value


def get_feature_flag_value(flag_id):
    server_side_key = get_secret_value("LAUNCH_DARKLY_SERVER_SIDE_KEY")
    ldclient.set_config(Config(server_side_key))

    with ldclient.get() as client:
        user = {"key": os.environ["LAUNCH_DARKLY_KEY"]}
        feature_flag_value = client.variation(flag_id, user, False)
        return feature_flag_value
