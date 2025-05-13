import json
from io import BytesIO, StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import psutil
import requests

from .auth import token_manager
from .config import SITE_MANAGER
from .logger import logger


class SharePointClient:
    def __init__(self, site_name: str):
        """
        Initialize the SharePoint client with site and drive identifiers.

        :param site_name: The unique identifier for a SharePoint site. Should exist as a key in the 'sites' section of config.json file.
        """
        # verify the site name and then load the site_id and drive_id
        if site_name not in SITE_MANAGER["sites"].keys():
            err_msg = f"Given site_name is not in known list of sites from .env file:\n{list(SITE_MANAGER.keys())}"
            raise ValueError(err_msg)
        else:
            site_id = SITE_MANAGER["sites"][site_name]["SITE_ID"]
            drive_id = SITE_MANAGER["sites"][site_name]["DRIVE_ID"]

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
        url = self._build_url(f"{folder_path}:/children")
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        return [d["name"] for d in response.json()["value"]]

    def get_document(self, folder: str, file_name: str) -> dict:
        """
        Retrieve metadata for a document in a specified folder.

        :param folder: Folder path relative to "General".
        :param file_name: The name of the file.
        :return: Metadata dictionary.
        """
        url = self._build_url(f"{folder}/{file_name}")
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        return response.json()

    def read_spreadsheet(
        self, folder_path: str, file_name: str
    ) -> pd.DataFrame:
        """
        Download and read an Excel or CSV file into a pandas DataFrame.

        :param folder_path: Folder where the spreadsheet is stored.
        :param file_name: Name of the file (should end in .xlsx or .csv).
        :return: DataFrame with file contents.
        """
        meta = self.get_document(folder_path, file_name)
        url = meta["@microsoft.graph.downloadUrl"]
        r = requests.get(url)
        r.raise_for_status()

        if file_name.endswith(".xlsx"):
            return pd.read_excel(BytesIO(r.content))
        if file_name.endswith(".csv"):
            return pd.read_csv(BytesIO(r.content))
        raise ValueError(f"Unsupported file type for spreadsheet: {file_name}")

    def read_json(self, folder_path: str, file_name: str) -> dict:
        """
        Read and parse a JSON file from SharePoint.

        :param folder_path: Folder path where the JSON file is located.
        :param file_name: Name of the JSON file.
        :return: Parsed JSON content as a dictionary.
        """
        meta = self.get_document(folder_path, file_name)
        url = meta["@microsoft.graph.downloadUrl"]
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
        url = meta["@microsoft.graph.downloadUrl"]
        r = requests.get(url)
        lines = [line for line in StringIO(r.text) if not line.startswith("#")]
        parsed = [line.strip().split() for line in lines]
        columns = ["n", "type", "x", "y", "z", "radius", "parent"]
        return pd.DataFrame(parsed, columns=columns)

    def upload_json(self, data: dict, folder: str, file_name: str) -> dict:
        """
        Upload a JSON dictionary as a file to SharePoint.

        :param data: Dictionary to upload.
        :param folder: Target folder on SharePoint.
        :param file_name: Name of the file to create (must end in .json).
        :return: Upload response metadata.
        """
        url = self._build_url(f"{folder}/{file_name}:/content")
        buffer = BytesIO(json.dumps(data, indent=4).encode("utf-8"))
        buffer.seek(0)
        headers = token_manager.get_headers()
        headers["Content-Type"] = "application/json"
        response = requests.put(url, headers=headers, data=buffer)
        response.raise_for_status()
        return response.json()

    def upload_csv(
        self, df: pd.DataFrame, folder: str, file_name: str
    ) -> dict:
        """
        Upload a pandas DataFrame as a CSV to SharePoint.

        :param df: DataFrame to upload.
        :param folder: Target folder.
        :param file_name: File name (must end in .csv).
        :return: Upload response metadata.
        """
        url = self._build_url(f"{folder}/{file_name}:/content")
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        headers = token_manager.get_headers()
        headers["Content-Type"] = "text/csv"
        response = requests.put(url, headers=headers, data=buffer)
        response.raise_for_status()
        return response.json()

    def upload_swc(
        self, df: pd.DataFrame, folder: str, file_name: str
    ) -> dict:
        """
        Upload a neuron morphology DataFrame as an SWC file.

        :param df: DataFrame in SWC format.
        :param folder: SharePoint folder path.
        :param file_name: File name (must end in .swc).
        :return: Upload response metadata.
        """
        url = self._build_url(f"{folder}/{file_name}:/content")
        buffer = StringIO()
        buffer.write("# " + " ".join(df.columns) + "\n")
        df.to_csv(buffer, sep=" ", header=False, index=False)
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
        url = self._build_url(f"{folder}/{local_path.name}:/content")
        headers = token_manager.get_headers()
        headers["Content-Type"] = "application/octet-stream"
        with open(local_path, "rb") as f:
            response = requests.put(url, headers=headers, data=f)
        response.raise_for_status()
        return response.json()

    def download_file(
        self, folder_path: str, file_name: str, output_path: str
    ):
        """
        Download a file from SharePoint to a local path using its folder and file name.

        :param folder_path: Folder path.
        :param file_name: File name to download.
        :param output_path: Path to save the downloaded file locally.
        """
        meta = self.get_document(folder_path, file_name)
        url = meta["@microsoft.graph.downloadUrl"]

        response = requests.get(url)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    def create_folder(self, parent_path: str, new_folder_name: str) -> dict:
        """
        Create a new folder in SharePoint.

        :param parent_path: Path to the parent folder (relative to the 'General' folder).
        :param new_folder_name: Name of the folder to create.
        :return: Response metadata from SharePoint.
        """
        url = self._build_url(f"{parent_path}:/children")
        headers = token_manager.get_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "name": new_folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def move_file(
        self,
        source_folder: str,
        file_name: str,
        dest_folder: str,
        new_file_name: Optional[str] = None,
    ) -> dict:
        """
        Safely move a file from one folder to another, optionally renaming it:
        - Downloads file content into memory first.
        - Moves the file via Graph API.
        - If move fails, restores original file from memory.

        :param source_folder: Current folder path .
        :param file_name: Name of the file to move.
        :param dest_folder: Destination folder path .
        :param new_file_name: Optional new name for the file at the destination.
        :return: Metadata of the moved file.
        """
        headers = token_manager.get_headers()
        headers["Content-Type"] = "application/json"

        dest_file_name = new_file_name or file_name

        # Build paths
        src_path = f"{source_folder}/{file_name}"
        dest_path = f"{dest_folder}/{dest_file_name}"

        file_bytes = None  # safeguard in case download fails

        try:
            # Step 1: Get file metadata
            meta = self.get_document(source_folder, file_name)
            item_id = meta["id"]
            download_url = meta["@microsoft.graph.downloadUrl"]

            logger.info(
                f"[SAFE_MOVE_FILE] Preparing to move file '{file_name}' from '{source_folder}' to '{dest_folder}' as '{dest_file_name}'",
            )

            # Step 2: Download content into memory and check size
            file_response = requests.get(download_url)
            file_response.raise_for_status()
            file_bytes = file_response.content

            max_safe_size = get_dynamic_max_safe_size()
            if len(file_bytes) > max_safe_size:
                raise MemoryError(
                    f"[SAFE_MOVE_FILE] File too large to safely move in memory "
                    f"({len(file_bytes)} bytes > {max_safe_size} bytes)",
                )

            # Step 3: Check for conflict at destination
            dest_check = requests.get(
                self._build_url(dest_path), headers=headers
            )
            if dest_check.status_code == 200:
                raise Exception(
                    f"[SAFE_MOVE_FILE] Conflict: '{dest_file_name}' already exists at destination '{dest_folder}'.",
                )

            # Step 4: Get destination folder's item ID
            dest_folder_meta = requests.get(
                self._build_url(f"{dest_folder}"), headers=headers
            )
            dest_folder_meta.raise_for_status()
            parent_id = dest_folder_meta.json()["id"]

            # Step 5: Try to move and rename the file via PATCH
            patch_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/items/{item_id}"
            payload = {
                "parentReference": {"id": parent_id},
                "name": dest_file_name,
            }

            move_response = requests.patch(
                patch_url, headers=headers, json=payload
            )
            move_response.raise_for_status()

            logger.info(
                f"[SAFE_MOVE_FILE] Successfully moved '{file_name}' to '{dest_folder}/{dest_file_name}'",
            )
            return move_response.json()

        except Exception as e:
            logger.error(
                f"[SAFE_MOVE_FILE] Move failed for '{file_name}': {e}"
            )

            # Step 6: Attempt recovery only if file was downloaded
            if file_bytes:
                try:
                    recovery_url = self._build_url(src_path + ":/content")
                    recovery_headers = token_manager.get_headers()
                    recovery_headers["Content-Type"] = (
                        "application/octet-stream"
                    )
                    recovery_response = requests.put(
                        recovery_url, headers=recovery_headers, data=file_bytes
                    )
                    recovery_response.raise_for_status()

                    logger.warning(
                        f"[SAFE_MOVE_FILE] Recovered original file '{file_name}' to '{source_folder}'",
                    )
                except Exception as recover_err:
                    logger.critical(
                        f"[SAFE_MOVE_FILE] Failed to recover original file '{file_name}': {recover_err}",
                    )
                    raise
            else:
                logger.warning(
                    "[SAFE_MOVE_FILE] Skipped recovery: No file_bytes to restore."
                )

            raise

    def list_drives(self) -> list:
        """
        List all drives (document libraries) available under the site.

        :return: List of drives with metadata (id, name, etc.).
        """
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        drives = response.json()["value"]
        logger.info(f"[DISCOVERY] Found {len(drives)} drives.")
        return drives

    def list_top_level_folders(self):
        """
        List top-level folders in the SharePoint site's document library.

        :return: List of top-level folder names.
        """
        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root/children"
        response = requests.get(url, headers=token_manager.get_headers())
        response.raise_for_status()
        return [
            item["name"]
            for item in response.json()["value"]
            if "folder" in item
        ]

    def print_directory(
        self, folder_path: str, indent: int = 0, show_files: bool = False
    ):
        """
        Recursively prints the folder (and optionally file) structure of a SharePoint directory.

        :param folder_path: The relative path from the drive root
        :param indent: Current indentation level (used in recursion)
        :param show_files: Whether to include files in the output
        """
        try:
            url = self._build_url(
                "root"
                if folder_path.strip() in ("", "/")
                else f"{folder_path}:/children"
            )
            response = requests.get(url, headers=token_manager.get_headers())
            response.raise_for_status()
            items = response.json().get("value", [])
        except Exception as e:
            print(" " * indent + f"[ERROR] {folder_path} - {e}")
            return

        for item in items:
            is_folder = item.get("folder")
            if is_folder:
                print(" " * indent + item["name"])
                new_path = (
                    f"{folder_path}/{item['name']}"
                    if folder_path
                    else item["name"]
                )
                self.print_directory(new_path, indent + 4, show_files)
            elif show_files:
                print(" " * indent + item["name"])


def get_dynamic_max_safe_size(fraction: float = 0.2) -> int:
    """
    Returns a dynamic max safe size in bytes, based on a fraction of available memory.
    """
    available_bytes = psutil.virtual_memory().available
    return int(available_bytes * fraction)
