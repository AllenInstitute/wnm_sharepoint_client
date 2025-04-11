import json
from io import BytesIO, StringIO
from pathlib import Path
import pandas as pd
import requests

from .auth import token_manager
from .config import SITE_ID, DRIVE_ID

class SharePointClient:
    def __init__(self, site_id: str = SITE_ID, drive_id: str = DRIVE_ID):
        """
        Initialize the SharePoint client with site and drive identifiers.

        :param site_id: The unique identifier of the SharePoint site.
        :param drive_id: The unique identifier of the SharePoint document library (drive).
        """
        self.site_id = site_id
        self.drive_id = drive_id

    def _build_url(self, path: str) -> str:
        """
        Build a SharePoint Graph API URL for a given path.

        :param path: Path to the file or folder within the document library.
        :return: Full API URL.
        """
        return f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root:/{path}"

    def list_items(self, folder_path: str):
        """
        List file and folder names within a given folder.

        :param folder_path: Folder path relative to the drive root (e.g., "Documents/Reports").
        :return: List of item names.
        """
        url = self._build_url(f"General/{folder_path}:/children")
        print(url)
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        return [d['name'] for d in response.json()['value']]

    def get_document(self, folder: str, file_name: str) -> dict:
        """
        Retrieve metadata for a document in a specified folder.

        :param folder: Folder path relative to "General".
        :param file_name: The name of the file.
        :return: Metadata dictionary.
        """
        url = self._build_url(f"General/{folder}/{file_name}")
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        return response.json()

    def read_spreadsheet(self, folder_path: str, file_name: str) -> pd.DataFrame:
        """
        Download and read an Excel or CSV file into a pandas DataFrame.

        :param folder_path: Folder where the spreadsheet is stored.
        :param file_name: Name of the file (should end in .xlsx or .csv).
        :return: DataFrame with file contents.
        """
        meta = self.get_document(folder_path, file_name)
        url = meta['@microsoft.graph.downloadUrl']
        r = requests.get(url)
        r.raise_for_status()

        if file_name.endswith(".xlsx"):
            return pd.read_excel(BytesIO(r.content))
        elif file_name.endswith(".csv"):
            return pd.read_csv(BytesIO(r.content))

    def read_json(self, folder_path: str, file_name: str) -> dict:
        """
        Read and parse a JSON file from SharePoint.

        :param folder_path: Folder path where the JSON file is located.
        :param file_name: Name of the JSON file.
        :return: Parsed JSON content as a dictionary.
        """
        meta = self.get_document(folder_path, file_name)
        url = meta['@microsoft.graph.downloadUrl']
        r = requests.get(url)
        r.raise_for_status()
        return json.loads(r.content)

    def read_swc(self, folder_path: str, file_name: str) -> pd.DataFrame:
        """
        Read an SWC neuron morphology file into a pandas DataFrame.

        :param folder_path: Folder path to the SWC file.
        :param file_name: Name of the SWC file.
        :return: DataFrame with SWC structure.
        """
        meta = self.get_document(folder_path, file_name)
        url = meta['@microsoft.graph.downloadUrl']
        r = requests.get(url)
        lines = [l for l in StringIO(r.text) if not l.startswith("#")]
        parsed = [line.strip().split() for line in lines]
        columns = ['n', 'type', 'x', 'y', 'z', 'radius', 'parent']
        return pd.DataFrame(parsed, columns=columns)

    def upload_json(self, data: dict, folder: str, file_name: str) -> dict:
        """
        Upload a JSON dictionary as a file to SharePoint.

        :param data: Dictionary to upload.
        :param folder: Target folder on SharePoint.
        :param file_name: Name of the file to create (must end in .json).
        :return: Upload response metadata.
        """
        url = self._build_url(f"General/{folder}/{file_name}:/content")
        buffer = BytesIO(json.dumps(data, indent=4).encode("utf-8"))
        buffer.seek(0)
        headers = token_manager.get_headers()
        headers["Content-Type"] = "application/json"
        response = requests.put(url, headers=headers, data=buffer)
        response.raise_for_status()
        return response.json()

    def upload_csv(self, df: pd.DataFrame, folder: str, file_name: str) -> dict:
        """
        Upload a pandas DataFrame as a CSV to SharePoint.

        :param df: DataFrame to upload.
        :param folder: Target folder.
        :param file_name: File name (must end in .csv).
        :return: Upload response metadata.
        """
        url = self._build_url(f"General/{folder}/{file_name}:/content")
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        headers = token_manager.get_headers()
        headers["Content-Type"] = "text/csv"
        response = requests.put(url, headers=headers, data=buffer)
        response.raise_for_status()
        return response.json()

    def upload_swc(self, df: pd.DataFrame, folder: str, file_name: str) -> dict:
        """
        Upload a neuron morphology DataFrame as an SWC file.

        :param df: DataFrame in SWC format.
        :param folder: SharePoint folder path.
        :param file_name: File name (must end in .swc).
        :return: Upload response metadata.
        """
        url = self._build_url(f"General/{folder}/{file_name}:/content")
        buffer = StringIO()
        buffer.write('# ' + ' '.join(df.columns) + '\n')
        df.to_csv(buffer, sep=' ', header=False, index=False)
        buffer.seek(0)
        headers = token_manager.get_headers()
        headers["Content-Type"] = "text/plain"
        response = requests.put(url, headers=headers, data=buffer)
        response.raise_for_status()
        return response.json()

    def upload_file(self, local_path: str, folder: str) -> dict:
        """
        Upload a local file to SharePoint.

        :param local_path: Path to the local file.
        :param folder: Folder path on SharePoint to upload into.
        :return: Upload response metadata.
        """
        local_path = Path(local_path)
        url = self._build_url(f"General/{folder}/{local_path.name}:/content")
        headers = token_manager.get_headers()
        headers["Content-Type"] = "application/octet-stream"
        with open(local_path, "rb") as f:
            response = requests.put(url, headers=headers, data=f)
        response.raise_for_status()
        return response.json()

    def download_file(self, item_id: str, output_path: str):
        """
        Download a file by item ID from SharePoint to a local path.

        :param item_id: SharePoint item ID.
        :param output_path: Path to save the downloaded file.
        """
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/items/{item_id}/content"
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
