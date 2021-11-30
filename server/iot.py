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
registry_id = 'registry'

client = iot_v1.DeviceManagerClient()

def toggle_device(device_id):
    device_path = client.device_path(project_id, cloud_region, registry_id, device_id)

    # command = 'Hello IoT Core!'
    data = 'toggle'.encode("utf-8")

    return client.send_command_to_device(
	request={"name": device_path, "binary_data": data}
    )

def get_device_info(device_id):
    device_path = client.device_path(project_id, cloud_region, registry_id, device_id)

    # See full list of device fields: https://cloud.google.com/iot/docs/reference/cloudiot/rest/v1/projects.locations.registries.devices
    # Warning! Use snake_case field names.
    field_mask = gp_field_mask.FieldMask(
	paths=[
	    "id",
	    "name",
	    "num_id",
	    "credentials",
	    "last_heartbeat_time",
	    "last_event_time",
	    "last_state_time",
	    "last_config_ack_time",
	    "last_config_send_time",
	    "blocked",
	    "last_error_time",
	    "last_error_status",
	    "config",
	    "state",
	    "log_level",
	    "metadata",
	    "gateway_config",
	]
    )
    return client.get_device(request={"name": device_path, "field_mask": field_mask})
