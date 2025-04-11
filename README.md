# wnm_sharepoint_client

A simple Python client for interacting with the Horta Microsoft SharePoint via the Microsoft Graph API. Supports downloading, uploading, and reading various file formats including CSV, Excel, JSON, and SWC.

---

## Features

-  List items in a SharePoint folder  
-  Read and upload CSV, Excel (.xlsx), JSON, and SWC files  
-  Upload any local file to SharePoint  
- Download files by item ID  
- Automatically handles authentication via a singleton `TokenManager`  

---

## Installation

Install:

```bash
coming soon
```

---
## Setup Instructions

Before running the application, you need to set up your environment variables. There are two ways to do this:

### Option 1: Use an `.env` file (Recommended)

1. Copy the `.env.example` file found in this repo to `.env` somewhere accessible to your machine. (e.g. `/my/custom/file/.env`)
2. Open the `.env` file and replace the placeholders with your actual values:
   ```dotenv
   TENANT_ID=your-tenant-id
   CLIENT_ID=your-client-id
   CLIENT_SECRET=your-client-secret
   SITE_ID=your-site-id
   DRIVE_ID=your-drive-id
   SCOPE=https://graph.microsoft.com/.default
   ```
3. Specify the path to that file using the `DOTENV_PATH` environment variable.

```bash
export DOTENV_PATH="/my/custom/file/.env"
```

Now, when you run the application the `dotenv` package will load the configuration from the specified `.env` file.


### Option 2: Set Environment Variables Manually

You can also set the environment variables manually in your terminal before running the application.

For **Linux/macOS**, you can use:

```bash
export TENANT_ID=your-tenant-id
export CLIENT_ID=your-client-id
export CLIENT_SECRET=your-client-secret
export SITE_ID=your-site-id
export DRIVE_ID=your-drive-id
export SCOPE=https://graph.microsoft.com/.default
```

For **Windows (PowerShell)**, use:

```powershell
$env:TENANT_ID = "your-tenant-id"
$env:CLIENT_ID = "your-client-id"
$env:CLIENT_SECRET = "your-client-secret"
$env:SITE_ID = "your-site-id"
$env:DRIVE_ID = "your-drive-id"
$env:SCOPE = "https://graph.microsoft.com/.default"
```

Once the environment variables are set, you can run the application.

---
## Examples

### Initialize the Client

```python
from wnm_sharepoint_client.client import SharePointClient

client = SharePointClient()
```

---


### List files in a folder

```python
items = client.list_items("SomeFolder/Subfolder/")
print(items)
```

---

### Read a spreadsheet

```python
df = client.read_spreadsheet("Data", "example.xlsx")
print(df.head())
```

---

### Read a JSON file

```python
data = client.read_json("Configs", "settings.json")
print(data)
```

---

### Read an SWC file (neuron morphology)

```python
df = client.read_swc("Morphologies", "cell_001.swc")
print(df.head())
```

---

### Upload a DataFrame as CSV

```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
client.upload_csv(df, folder="Uploads", file_name="data.csv")
```

---

### Upload a JSON file

```python
data = {"name": "example", "version": 1}
client.upload_json(data, folder="Configs", file_name="example.json")
```

---

### Upload a local file

```python
client.upload_file("local/path/to/file.txt", folder="GeneralDocs")
```

---


---

##  Notes

- All paths in SharePoint are relative to the `General` folder by default.
- All authentication is handled via `TokenManager` in `auth.py`. No need to manually refresh tokens.


## Requirements

- A registered Azure AD App with permissions for Microsoft Graph API:
  - `Files.ReadWrite.All`
  - `Sites.Read.All`
- The `site_id` and `drive_id` can be retrieved using the Graph Explorer or `GET /sites` and `/drives` endpoints.

---

##  Coming Soon

- Ability to make dirs and move files
- Automatic drive/folder discovery  
- Optional caching layer for metadata  

---