from google.api_core.exceptions import AlreadyExists
from google.cloud import iot_v1
from google.cloud import pubsub
from google.oauth2 import service_account
from google.protobuf import field_mask_pb2 as gp_field_mask
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from errors import RegistryExistsException

project_id = 'switcherbot'
cloud_region = 'us-central1'

def create_registry(registry_id):
    client = iot_v1.DeviceManagerClient()
    pubsub_topic = f'{registry_id}-device-events'
    parent = f"projects/{project_id}/locations/{cloud_region}"
    topic = "projects/{}/topics/{}".format(project_id, pubsub_topic)

    body = {
        "event_notification_configs": [{"pubsub_topic_name": topic}],
        "id": registry_id,
    }

    try:
        response = client.create_device_registry(
            request={"parent": parent, "device_registry": body}
        )
        print("Created registry")
        return response
    except HttpError:
        print("Error, registry not created")
        raise
    except AlreadyExists:
        print("Error, registry already exists")
        raise RegistryExistsException
    except Exception as error:
        print(error)
        raise
