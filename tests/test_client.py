import os
from datetime import datetime

import pandas as pd
import pytest
import requests

from wnm_sharepoint_client.auth import token_manager
from wnm_sharepoint_client.client import SharePointClient

FOLDER = "General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD"
EXPECTED_TEST_FILES = ["test_json.json", "test_csv.csv"]


@pytest.fixture(scope="module")
def client():
    return SharePointClient("HORTA")


def test_upload_and_read_json(client):
    current_time = datetime.now().isoformat()
    test_data = {"test_time": current_time}
    file_name = "test_json.json"

    client.upload_json(test_data, FOLDER, file_name)
    downloaded = client.read_json(FOLDER, file_name)

    assert "test_time" in downloaded
    assert downloaded["test_time"] == current_time


def test_upload_and_read_csv(client):
    current_time = datetime.now().isoformat()
    df = pd.DataFrame([{"test_time": current_time}])
    file_name = "test_csv.csv"

    client.upload_csv(df, FOLDER, file_name)
    downloaded = client.read_spreadsheet(FOLDER, file_name)

    assert "test_time" in downloaded.columns
    assert downloaded["test_time"].iloc[0] == current_time


def test_move_file(client):
    file_name = "test_csv.csv"
    moved_file_name = "test_csv_moved.csv"

    # Clean up: delete the destination file if it already exists
    source_files_og = client.list_items(FOLDER)
    if moved_file_name in source_files_og:
        moved_file_meta = client.get_document(FOLDER, moved_file_name)
        moved_file_id = moved_file_meta["id"]
        delete_url = f"https://graph.microsoft.com/v1.0/sites/{client.site_id}/drives/{client.drive_id}/items/{moved_file_id}"
        headers = token_manager.get_headers()
        delete_response = requests.delete(delete_url, headers=headers)
        delete_response.raise_for_status()

    # Move the file
    result = client.move_file(FOLDER, file_name, FOLDER, moved_file_name)
    assert result["name"] == moved_file_name

    # Confirm the file is no longer in the source
    source_files = client.list_items(FOLDER)
    assert file_name not in source_files

    # Confirm it's now in the dest
    assert moved_file_name in source_files

    # Move it back
    result = client.move_file(FOLDER, moved_file_name, FOLDER, file_name)


def test_list_files(client):
    listed_files = client.list_items(FOLDER)
    assert len(set(EXPECTED_TEST_FILES) - set(listed_files)) == 0


def test_read_spreadsheet_invalid_file_type(client):
    file_name = "test_json.json"
    with pytest.raises(Exception):
        client.read_spreadsheet(FOLDER, file_name)


def test_upload_and_download_file(client, tmp_path):
    file_name = "test_csv.csv"
    downloaded_path = tmp_path / "downloaded.csv"
    client.download_file(
        folder_path=FOLDER,
        file_name=file_name,
        output_path=str(downloaded_path),
    )

    downloaded_df = client.read_spreadsheet(FOLDER, file_name)
    local_df = pd.read_csv(downloaded_path)
    os.remove(downloaded_path)
    pd.testing.assert_frame_equal(downloaded_df, local_df)


def test_list(client):
    assert "General" in client.list_top_level_folders()


def test_print(client):
    client.print_directory(
        "General/AIBS Completed SWC Files/wnm_sharepoint_client_CICD"
    )
