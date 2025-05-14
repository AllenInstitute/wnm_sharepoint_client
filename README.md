# wnm_sharepoint_client

A simple Python client for interacting with Microsoft SharePoint sites via the Microsoft Graph API. Supports downloading, uploading, and reading various file formats including CSV, Excel, JSON, and SWC.

---

## Features

-  List items in a SharePoint folder  
-  Read and upload CSV, Excel (.xlsx), JSON, and SWC files  
-  Upload any local file to SharePoint  
-  Download files by file name  
-  Automatically handles authentication via a singleton `TokenManager`  

---

## Installation

Install:

```bash
git clone https://github.com/AllenInstitute/wnm_sharepoint_client.git  
cd wnm_sharepoint_client    
pip install .  
```

---
## Setup Instructions

Before running the application, you need to set up your environment by creating a `config.json` file and setting its path using the `CONFIG_JSON_PATH` environment variable.

---

### Step 1: Create a `config.json`

This file holds Microsoft authentication credentials and SharePoint site metadata.

#### Example `config.json`:

```json
{
  "auth": {
    "CLIENT_ID": "your-client-id",
    "TENANT_ID": "your-tenant-id",
    "CLIENT_SECRET": "your-client-secret",
    "SCOPE": "https://graph.microsoft.com/.default",
    "GRAPH_API_BASE_URL": "https://graph.microsoft.com/v1.0",
    "TOP": 5000
  },
  "sites": {
    "NEUROANATOMY": {
      "SITE_ID": "some-sharepoint-site",
      "DRIVE_ID": "some-drive-id",
      "SITE_URL": "some-site-url"
    },
    "HORTA": {
      "SITE_ID": "some-other-sharepoint-site",
      "DRIVE_ID": "some-other-drive-id-site",
      "SITE_URL": "some-other-site-url"
    }
  }
}
```

---

### Step 2: Set the config path using an environment variable

Export the path to your `config.json` file before running the application:

#### Linux/macOS:
```bash
export CONFIG_JSON_PATH="/full/path/to/your/config.json"
```

#### Windows (PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("CONFIG_JSON_PATH", "C:\full\path\to\your\config.json", "User")
```

---

## About `config.json`

The `config.json` file is a site-specific configuration that defines both:

### 1. Microsoft Graph Authentication

Located under the top-level `"auth"` key:

| Key                 | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `CLIENT_ID`          | Azure AD application (client) ID                                            |
| `TENANT_ID`          | Azure AD tenant ID                                                          |
| `CLIENT_SECRET`      | Secret string generated for your app registration                           |
| `SCOPE`              | Graph API scope (usually `https://graph.microsoft.com/.default`)            |
| `GRAPH_API_BASE_URL` | Microsoft Graph API base URL (`https://graph.microsoft.com/v1.0`)           |
| `TOP`                | Optional limit for pagination of Graph results                              |

These follow Microsoft's OAuth2 and Graph API conventions.

---

### 2. SharePoint Site Definitions

Located under the `"sites"` key. Each site is a dictionary with these keys:

| Key         | Description                                                                    |
|--------------|--------------------------------------------------------------------------------|
| `SITE_ID`     | SharePoint site ID in Microsoft format (`hostname,groupId,siteId`)           |
| `DRIVE_ID`    | Unique ID of the SharePoint document library (drive)                         |
| `SITE_URL`    | Human-readable SharePoint site URL                                           |

These values are required for Microsoft Graph to resolve and access SharePoint site contents.

---

If the config file is missing any required values, the application will raise an error during initialization.

---

## Examples

### Initialize the Client

```python
from wnm_sharepoint_client.client import SharePointClient

client = SharePointClient("HORTA")
```

---

### Find available root directories 

```python
client.list_top_level_folders()

['General']

```

---

### Recursively show file structure
```python
client.print_directory('General', indent=0, show_files=False)

AIBS Completed SWC Files
    dataset_exaSPIM_653159
    dataset_exaSPIM_674185
        complete
    dataset_exaSPIM_686955
        complete
    dataset_exaSPIM_713601
        complete
        ...
```

---


### List files in a folder

```python
items = client.list_items("General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD")
print(items)
```

---

### Read a spreadsheet

```python
df = client.read_spreadsheet("General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD", "example.xlsx")
print(df.head())
```

---

### Read a JSON file

```python
data = client.read_json("General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD", "settings.json")
print(data)
```

---

### Read an SWC file to a dataframe

```python
df = client.read_swc("General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD", "cell_001.swc")
print(df.head())
```

---

### Upload a DataFrame as CSV

```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
client.upload_csv(df, folder="General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD", file_name="data.csv")
```

---

### Upload a JSON file

```python
data = {"name": "example", "version": 1}
client.upload_json(data, folder="General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD", file_name="example.json")
```

---

### Upload a local file

```python
client.upload_file("local/path/to/file.txt", folder="General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD")
```

---

### Move a file 

```python
client.move_file(source_folder="General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD",
file_name = "sourcefile.txt", dest_folder = "General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD", new_file_name = "movedfile.txt")
```

---

### Create a folder 

```python
client.create_folder(parent_path="General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD",
new_folder_name = "SomeSubFolder")
``````
---

##  Notes

- All authentication is handled via `TokenManager` in `auth.py`. No need to manually refresh tokens.


## Requirements

- A registered Azure AD App with permissions for Microsoft Graph API:
  - `Files.ReadWrite.All`
  - `Sites.Read.All`

---