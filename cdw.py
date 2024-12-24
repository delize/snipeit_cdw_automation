#!/usr/bin/python3
import os
import sys
import argparse
import shutil
import pysftp
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
DEFAULT_DATE = datetime.now().strftime("%m%d%Y")

# Argument Parser
parser = argparse.ArgumentParser(description="Process inputs for asset automation for CDW Records.")
parser.add_argument('-rf', '--remote_filename', type=str, default=f"/Outbox/CDW_Asset_{DEFAULT_DATE}.csv", help="Remote file path")
parser.add_argument('-dl', '--download_location', type=str, default=f"/tmp/CDW_Asset_{DEFAULT_DATE}.csv", help="Local download path")
parser.add_argument('-t', '--template', type=str, default="/snipeit/assetmanagement/resources/template.csv", help="Template file path")
parser.add_argument('-of', '--output_file', type=str, default=f"/snipeit/assetmanagement/output/assetrecord_{DEFAULT_DATE}.csv", help="Output file path")
parser.add_argument('-af', '--archive_file', type=str, default=f"/snipeit/assetmanagement/archive/{DEFAULT_DATE}.csv", help="Archive file path")
parser.add_argument('-sa', '--server_address', type=str, default="gis.cdw.com", help="Server address")
parser.add_argument('-sp', '--server_password', type=str, default="<%= @cdw_password %>", help="Server password")
parser.add_argument('-su', '--server_username', type=str, default="SSHUSERNAME", help="Server username")
parser.add_argument('-mf', '--min_filesize', type=int, default=600, help="Minimum file size")
parser.add_argument('-kh', '--known_hosts', type=str, default='/snipeit/assetmanagement/resources/cdw.knownhosts', help="Known hosts file")
parser.add_argument('-n', '--cdw_name', type=str, default="Company Name", help="CDW customer name")
parser.add_argument('-cn', '--customer_name', type=str, default="Company Name", help="Override CDW customer name")
args = parser.parse_args()

# Functions
def download_file(remote_filename, local_filename, known_hosts, server, username, password):
    """Download file via SFTP."""
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys.load(known_hosts)
    try:
        with pysftp.Connection(server, username=username, password=password, cnopts=cnopts) as sftp:
            if sftp.isfile(remote_filename):
                sftp.get(remote_filename, local_filename)
            else:
                raise FileNotFoundError(f"Remote file {remote_filename} not found.")
    except Exception as e:
        print(f"Error during SFTP download: {e}")
        sys.exit(1)

def validate_file_size(file_path, min_size):
    """Check if file size meets the minimum requirement."""
    if not os.path.exists(file_path):
        print("Downloaded file does not exist.")
        sys.exit(1)
    size = os.path.getsize(file_path)
    if size < min_size:
        os.remove(file_path)
        print("File size below threshold. File removed.")
        sys.exit(0)

def process_files(template_file, download_file, output_file, archive_file, cdw_name, customer_name):
    """Process files and generate the output."""
    try:
        shutil.copy(download_file, archive_file)
        df_template = pd.read_csv(template_file)
        df_downloaded = pd.read_csv(download_file)
        
        # Validate headers
        required_headers = {'Order Date', 'Order Number', 'Invoice Date', 'Invoice Number', 
                            'Serial Number', 'Asset Tag', 'Item Description', 'Customer Name'}
        if not required_headers.issubset(df_downloaded.columns):
            raise ValueError("Missing required headers in the downloaded file.")

        # Filter and transform data
        df_downloaded['Asset Tag'].replace('', np.nan, inplace=True)
        df_downloaded.dropna(subset=['Asset Tag'], inplace=True)
        df_downloaded['Customer Name'].replace(cdw_name, customer_name, inplace=True)

        # Map data to template
        df_template['Item Name'] = df_downloaded['Item Description']
        df_template['Serial'] = df_downloaded['Serial Number']
        df_template['Asset Tag'] = df_downloaded['Asset Tag']
        df_template['Company'] = df_downloaded['Customer Name']

        # Add static fields
        df_template['Supplier'] = "CDW"
        df_template['Status'] = "Ready to Deploy"

        # Save output
        df_template.to_csv(output_file, index=False, encoding="utf-8")
    except Exception as e:
        print(f"Error during file processing: {e}")
        sys.exit(1)

# Main
if __name__ == "__main__":
    download_file(args.remote_filename, args.download_location, args.known_hosts, args.server_address, args.server_username, args.server_password)
    validate_file_size(args.download_location, args.min_filesize)
    process_files(args.template, args.download_location, args.output_file, args.archive_file, args.cdw_name, args.customer_name)
