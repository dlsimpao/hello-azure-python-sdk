# Import the needed credential and management objects from the libraries.
import os, random, dotenv

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.v2023_01_01.models import StorageAccountCreateParameters, NetworkRuleSet, Bypass, VirtualNetworkRule, IPRule

dotenv.load_dotenv()
RG_NAME = "hello-pysdk-rg"
LOCNAME = "centralus"

SA_NAME = "hellopysdksa"

# Acquire a credential object using CLI-based authentication.
credential = AzureCliCredential()

# Retrieve subscription ID from environment variable.
subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

# Obtain the management object for resources.
resource_client = ResourceManagementClient(credential, subscription_id)

# Provision the resource group.
rg_result = resource_client.resource_groups.create_or_update(
    f"{RG_NAME}", {"location": f"{LOCNAME}"}
)

print(
    f"Provisioned resource group {rg_result.name} in \
        the {rg_result.location} region"
)

rg_result = resource_client.resource_groups.create_or_update(
    f"{RG_NAME}",
    {
        "location": f"{LOCNAME}",
        "tags": {"environment": "test", "department": "tech"},
    },
)

print(f"Updated resource group {rg_result.name} with tags")

# Optional lines to delete the resource group. begin_delete is asynchronous.
# poller = resource_client.resource_groups.begin_delete(rg_result.name)
# result = poller.result()

# Creating the Storage Account

storage_client = StorageManagementClient(credential, subscription_id)

## Configuring network rules
network_rule_set = NetworkRuleSet()

## Add a VirtualNetworkRule to the NetworkRuleSet object
virtual_network_rule = VirtualNetworkRule()
virtual_network_rule.virtual_network_resource_id = ""
network_rule_set.virtual_network_rules.append(virtual_network_rule)

#STORAGE_ACCOUNT_NAME = f"pythonazurestorage{random.randint(1,100000):05}"
STORAGE_ACCOUNT_NAME = f"{SA_NAME}{random.randint(1,100000):05}"

# Check if the account name is available. Storage account names must be unique across
# Azure because they're used in URLs.
availability_result = storage_client.storage_accounts.check_name_availability(
    { "name": STORAGE_ACCOUNT_NAME }
)

if not availability_result.name_available:
    print(f"Storage name {STORAGE_ACCOUNT_NAME} is already in use. Try another name.")
    exit()

# The name is available, so provision the account
poller = storage_client.storage_accounts.begin_create(RG_NAME, STORAGE_ACCOUNT_NAME,
    {
        "location" : LOCNAME,
        "kind": "StorageV2",
        "sku": {"name": "Standard_LRS"},
        "is_hns_enabled":True
    }
)

# Long-running operations return a poller object; calling poller.result()
# waits for completion.
account_result = poller.result()
print(f"Provisioned storage account {account_result.name}")


# Step 3: Retrieve the account's primary access key and generate a connection string.
keys = storage_client.storage_accounts.list_keys(RG_NAME, STORAGE_ACCOUNT_NAME)

print(f"Primary key for storage account: {keys.keys[0].value}")

conn_string = f"DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={keys.keys[0].value}"

print(f"Connection string: {conn_string}")

# Step 4: Provision the blob container in the account (this call is synchronous)
CONTAINER_NAME = "hello-container"
container = storage_client.blob_containers.create(RG_NAME, STORAGE_ACCOUNT_NAME, CONTAINER_NAME, {})

# The fourth argument is a required BlobContainer object, but because we don't need any
# special values there, so we just pass empty JSON.

print(f"Provisioned blob container {container.name}")