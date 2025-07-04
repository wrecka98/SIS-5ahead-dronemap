import logging
import os
import subprocess
from azure.storage.blob import BlobServiceClient
import azure.functions as func
import time
from azure.core.exceptions import ResourceNotFoundError

# Constants from env
ACCOUNT_NAME = os.environ['AZURE_STORAGE_ACCOUNT']
ACCOUNT_KEY = os.environ['AZURE_STORAGE_KEY']
SHARE_NAME = os.environ['AZURE_SHARE_NAME']
DOCKER_USER = os.environ['DOCKER_USERNAME']
DOCKER_PW = os.environ['DOCKER_PASS']
ACI_RG = os.environ['ACI_RESOURCE_GROUP']
MOUNT_PATH = f"/mnt/{SHARE_NAME}"  # assumes Azure File Share is mounted
BLOB_CONTAINER = "raw-images"

blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])

def main(blob: func.InputStream):
    logging.info(f"Processing uploaded blob: {blob.name} ({blob.length} bytes)")

    # Save blob to mounted Azure File Share
    file_name = os.path.basename(blob.name)
    local_image_path = os.path.join(MOUNT_PATH, "images", file_name)
    os.makedirs(os.path.dirname(local_image_path), exist_ok=True)

    with open(local_image_path, "wb") as f:
        f.write(blob.read())
    logging.info(f"Saved blob to mounted share: {local_image_path}")

    # Unique container name
    container_name = f"odm-job-{file_name.replace('.', '-')}".lower()

    # Run ACI job with ODM
    try:
        cmd = [
            "az", "container", "create",
            "--resource-group", ACI_RG,
            "--name", container_name,
            "--image", "opendronemap/odm",
            "--restart-policy", "Never",
            "--cpu", "4",
            "--memory", "8",
            "--registry-username", DOCKER_USER,
            "--registry-password", DOCKER_PASS,
            "--azure-file-volume-account-name", ACCOUNT_NAME,
            "--azure-file-volume-account-key", ACCOUNT_KEY,
            "--azure-file-volume-share-name", SHARE_NAME,
            "--azure-file-volume-mount-path", "/datasets/code",
            "--command-line", "odm --project-path /datasets"
        ]

        logging.info(f"Running ACI command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logging.info(f"ACI container started: {result.stdout}")

        def wait_for_aci_completion(resource_group, container_name, timeout_minutes=30):
            timeout = time.time() + timeout_minutes * 60
            while time.time() < timeout:
                result = subprocess.run(
                    ["az", "container", "show", "--resource-group", resource_group, "--name", container_name, "--query", "instanceView.state", "--output", "tsv"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                state = result.stdout.strip()
                logging.info(f"ACI state: {state}")
                if state == "Terminated":
                    return True
                time.sleep(10)
            logging.warning("Timeout reached while waiting for ACI to finish")
            return False

        # Wait for ACI to finish
        if wait_for_aci_completion(ACI_RG, container_name):
            # Upload ACI output
            output_path = os.path.join(MOUNT_PATH, "odm_orthophoto")  # or whatever folder ODM uses
            results_container = blob_service_client.get_container_client("odm-results")

            for root, dirs, files in os.walk(output_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, output_path)
                    blob_name = f"{file_name.split('.')[0]}/{rel_path.replace(os.sep, '/')}"
                    try:
                        with open(full_path, "rb") as data:
                            results_container.upload_blob(name=blob_name, data=data)
                        logging.info(f"Uploaded {blob_name} to odm-results")
                    except Exception as e:
                        logging.error(f"Upload failed for {blob_name}: {e}")
        else:
            logging.error("ACI processing did not complete in time.")

    except subprocess.CalledProcessError as e:
        logging.error(f"ACI launch failed: {e.stderr}")