"""

Downloader for "gold" release files from the aapb-annotation repository.

This is somewhat fragile in that the code relies on an undocumented API endpoint
on GitHub.

"""

import json
import os
from urllib.parse import urljoin
from pathlib import Path
import requests
import tempfile


def download_golds(batch_dir_url, folder_name=None):
    """
    This function is here mostly so that code in other modules can keep calling
    it without breaking. It now just forwards to a more properly named function
    (proper relative to what it does). It should be considered deprecated.
    """
    return download_batch_files(batch_dir_url, folder_name)


def download_batch_files(batch_dir_url: str, output_folder=None) -> str:
    """
    Download batch files from the aapb-annotations repository and save them to
    a local directory. If no output folder is given then it saved to a temporary
    directory. Returns the name of the local directory.
    """

    if output_folder is None:
        output_folder = tempfile.TemporaryDirectory().name
    # Create a new directory to store the downloaded files on local computer
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    # Check if the directory is empty
    if not (len(os.listdir(output_folder)) == 0):
        raise Exception(f"The folder '{output_folder}' already exists and is not empty")

    # Send a GET request to the repository URL and extract the content
    response = requests.get(batch_dir_url, headers={"Accept": "application/json"})
    try:
        payload = json.loads(response.text)['payload']
        with open('x.json', 'w') as fh:
            fh.write(json.dumps(json.loads(response.text), indent=2))
    except json.JSONDecodeError:
        raise Exception(
            f"Failed to load the directory URL: {batch_dir_url} . As the gold "
            "retriever relies on an undocumented API endpoint of GitHub, it may "
            "be broken. Please report this issue to the developers at "
            "https://github.com/clamsproject/clams-utils/issues .")
    batch_files = [
        item['path'] for item in payload['codeViewTreeRoute']['tree']['items']
        if item['path'].endswith('.txt')]
    branch = payload['codeViewTreeRoute']['refInfo']['name']

    # Download each file in the list into the created folder
    for batch_file in batch_files:
        raw_url = urljoin(
            'https://raw.githubusercontent.com/',
            str(Path('clamsproject') / 'aapb-annotations' / branch / batch_file))
        print('--', raw_url)
        file_name = os.path.basename(batch_file)
        file_path = os.path.join(output_folder, file_name)
        with open(file_path, 'wb') as file:
            response = requests.get(raw_url)
            file.write(response.content)
    return output_folder


def prep_argparser(subparsers):
    """
    Prepare the argument parser for the goldretriever command.
    """
    goldretriever_parser = subparsers.add_parser(
        __name__.split('.')[-1],
        description="Download 'gold' release files from a GitHub repository.",
        help="Download 'gold' release files from a GitHub repository.")
    goldretriever_parser.add_argument("batch_dir_url", help="URL to a directory in a GitHub repository")
    goldretriever_parser.add_argument("-o", "--output-folder", dest="folder_name", help="local folder to store the downloaded files")
    goldretriever_parser.set_defaults(func=main)


def main(args):
    """
    Main function for the goldretriever command.
    """
    folder = download_golds(args.batch_dir_url, args.folder_name)
    print(f"Downloaded files to: {folder}")
