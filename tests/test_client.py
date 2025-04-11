import time
import pytest
import pandas as pd
from datetime import datetime

from wnm_sharepoint_client.client import SharePointClient

FOLDER = "AIBS Completed SWC Files/wnm_sharepoint_client_CICD"
EXPECTED_TEST_FILES = [
    "test_json.json",
    "test_csv.csv"
]

@pytest.fixture(scope="module")
def client():
    return SharePointClient()

def test_upload_and_read_json(client):
    current_time = datetime.now().isoformat()
    test_data = {'test_time': current_time}
    file_name = "test_json.json"

    client.upload_json(test_data, FOLDER, file_name)
    downloaded = client.read_json(FOLDER, file_name)

    assert 'test_time' in downloaded
    assert downloaded['test_time'] == current_time

def test_upload_and_read_csv(client):
    current_time = datetime.now().isoformat()
    df = pd.DataFrame([{'test_time': current_time}])
    file_name = "test_csv.csv"

    client.upload_csv(df, FOLDER, file_name)
    downloaded = client.read_spreadsheet(FOLDER, file_name)

    assert 'test_time' in downloaded.columns
    assert downloaded['test_time'].iloc[0] == current_time

def test_list_files(client):
    listed_files = client.list_items(FOLDER)
    assert set(EXPECTED_TEST_FILES) == set(listed_files)
    
