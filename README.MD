# SIS-5ahead-dronemap
Automated construction site status inference using drone imagery and 3D modeling — this project builds a digital twin of construction environments using UAV-captured data and Azure services.

## Project Overview
This system infers the status of construction sites by generating 3D models from drone-captured images and then computing the height and surface area of key objects. The results feed into an Azure Digital Twin, forming a real-time digital representation of the physical site.

## Key Features
- Automated pipeline for digital twin generation from UAV imagery

- Integration with Azure Blob Storage for image ingestion

- 3D reconstruction using OpenDroneMap

- Object analysis: surface area and height calculations

- Deployment via Azure Container Instances

- Sync with Azure Digital Twin for real-time visualization and querying

## Dependencies
- Azure Digital Twins SDK

- Open3D

- OpenDroneMap (via Docker)

- Azure Container Instances

- Python 3.8+

## Data Input/Output
### Input
Raw drone images uploaded to an Azure Blob Storage container

### Output
- 3D reconstructed models (e.g., .obj, .las)

- Surface area and height metadata

- Updated Digital Twin instances for real-time digital site visualization