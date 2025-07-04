import os
import json
from azure.digitaltwins.core import DigitalTwinsClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from datetime import datetime

# Authentication
adt_instance_url = "https://sis.api.weu.digitaltwins.azure.net"
credential = DefaultAzureCredential()
client = DigitalTwinsClient(adt_instance_url, credential)

print("Service client created – ready to go")

# Upload model
print("Upload a model")
with open("DTDL models/container_metrics_dtdl_model.json", "r") as f:
    dtdl = json.load(f)

models = [dtdl]
print(f"models: {models}")

try:
    client.create_models(models)
    print("Models uploaded successfully.")
except HttpResponseError as e:
    print(f"Upload model error: {e.status_code}: {e.message}")

# Print models
model_data_list = client.list_models()
for model in model_data_list:
    print(f"Model: {model.id}")


prefix = "container-"
for i in range(3):
    twin_id = f"{prefix}{i}"
    twin_data = {
        "$metadata": {
            "$model": "dtmi:example:MeshMetrics;1"
        },
        "height": 3.7787,
        "boundingBox": {
            "width": 11.0940,
            "length": 11.4506,
            "height": 3.7787
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        client.upsert_digital_twin(twin_id, twin_data)
        print(f"Created twin: {twin_id}")
    except HttpResponseError as e:
        print(f"Create twin error: {e.status_code}: {e.message}")

# Create relationships
def create_relationship(client, src_id, target_id):
    rel_id = f"{src_id}-contains->{target_id}"
    relationship = {
        "$relationshipId": rel_id,
        "$sourceId": src_id,
        "$relationshipName": "contains",
        "$targetId": target_id
    }
    try:
        client.upsert_relationship(src_id, rel_id, relationship)
        print("Created relationship successfully")
    except HttpResponseError as e:
        print(f"Create relationship error: {e.status_code}: {e.message}")

create_relationship(client, "container-0", "container-1")
create_relationship(client, "container-0", "container-2")

# List relationships
def list_relationships(client, src_id):
    try:
        relationships = client.list_relationships(src_id)
        print(f"Twin {src_id} is connected to:")
        for rel in relationships:
            print(f" -{rel['$relationshipName']}->{rel['$targetId']}")
    except HttpResponseError as e:
        print(f"Relationship retrieval error: {e.status_code}: {e.message}")

list_relationships(client, "container-0")

# Query twins
query = "SELECT * FROM digitaltwins"
try:
    results = client.query_twins(query)
    for twin in results:
        print(json.dumps(twin, indent=2))
        print("---------------")
except HttpResponseError as e:
    print(f"Query error: {e.status_code}: {e.message}")
