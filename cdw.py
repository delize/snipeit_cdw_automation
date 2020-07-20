#!/usr/bin/python3
# Written by Andrew Doering for IT-295

import time
import sys
import os
import pysftp
import pandas as pd
import numpy as np
import shutil
import argparse

# ENV VARIABLES
parser = argparse.ArgumentParser(description="Process inputs for asset automation for CDW Records.")
parser.add_argument('-rf', '--remote_filename', type=str, default="/Outbox/CDW_Asset_"+time.strftime("%m%d%Y")+".csv", help='Path on the remote server where the download exists')
parser.add_argument('-dl', '--download_location', type=str, default="/tmp/CDW_Asset_"+time.strftime("%m%d%Y")+".csv", help='Path of the download location from the remote server to the local server')
parser.add_argument('-t', '--template', type=str, default="/snipeit/assetmanagement/resources/template.csv", help='Template file to use for the SnipeIT Asset System')
parser.add_argument('-of', '--output_file', type=str, default="/snipeit/assetmanagement/output/assetrecord_"+time.strftime("%m%d%Y")+".csv", help='Output file that will be automatically imported into SnipeIT on an hourly basis')
parser.add_argument('-af', '--archive_file', type=str, default="/snipeit/assetmanagement/archive/"+time.strftime("%m%d%Y")+".csv", help='Copy of Downloaded File, for archival purposes')
parser.add_argument('-sa', '--server_address', type=str, default="gis.cdw.com", help='Server address/url to connect')
parser.add_argument('-sp', '--server_password', type=str, default="<%= @cdw_password %>", help='Password to use for connecting to server_address')
parser.add_argument('-su', '--server_username', type=str, default="SSHUSERNAME", help='Username to user for connecting to server_address')
parser.add_argument('-mf', '--min_filesize', type=int, default=600, help='Minimum file size with an additional allotment of bytes to detect if the file has been modified or is empty')
parser.add_argument('-kh', '--known_hosts', type=str, default='/snipeit/assetmanagement/resources/cdw.knownhosts', help="The .ssh/known_hosts file that pysftp will use to validate the connection")
parser.add_argument('-n', '--cdw_name', type=str, default='Company Name', help="This is the predetermined CDW customer name. Reach out to CDW for verification.")
parser.add_argument('-cn', '--customer_name', type=str, default='Company Name', help="Sets the new company name that you want to override CDW value.")

args = parser.parse_args()
REMOTE_FILENAME = args.remote_filename
FILENAMETODOWNLOAD = args.download_location
TEMPLATEFILE = args.template
OUTPUTFILE = args.output_file
ARCHIVEFILE = args.archive_file
SERVERADDRESS = args.server_address
SERVERUSERNAME = args.server_username
SERVERPASSWORD = args.server_password
MINIMUMFILESIZE = args.min_filesize
KNOWNHOSTS = args.known_hosts
CDW_CUSTOMER_NAME = args.cdw_name
CUSTOMER_NAME = args.customer_name

# Code
# NOTE connect over SFTP and download file
cnopts = pysftp.CnOpts()
cnopts.hostkeys.load(KNOWNHOSTS)
with pysftp.Connection(SERVERADDRESS, username=SERVERUSERNAME, password=SERVERPASSWORD, cnopts=cnopts) as sftp:
    sftp.isfile(REMOTE_FILENAME)
    sftp.get(REMOTE_FILENAME, FILENAMETODOWNLOAD)
    time.sleep(2)
sftp.close()
# NOTE make a backup of the file, just incase something goes wrong
shutil.copyfile(FILENAMETODOWNLOAD, ARCHIVEFILE)

# NOTE Because the file may not exist until after SFTP command is finished, put env variables down here for file size check. This will check if the file meets the minimum requirements to test with
ACTUALSIZE = os.path.getsize(FILENAMETODOWNLOAD)
if ACTUALSIZE <= MINIMUMFILESIZE:
    print("File size of CSV is less than 600B, meaning we have not purchased anything in the past 24 hours. Removing file and exiting...")
    if not os.path.exists(FILENAMETODOWNLOAD):
        print("File does not exist, exiting")
        exit()
    else:
        os.remove(FILENAMETODOWNLOAD)
        exit()
else:
    # NOTE import
    df_template = pd.read_csv(TEMPLATEFILE, sep=',')
    df_downloaded = pd.read_csv(FILENAMETODOWNLOAD, sep=',')
    # TODO: Verify headers exist before proceeding further:
    df_headers_tocheck = {'Order Date', 'Order Number', 'Invoice Date', 'Invoice Number', 'Invoice Line Number', 'Customer PO', 'Customer Number', 'Customer Name', 'Contact', 'Item Number', 'Item Description', 'Item Type', 'Item Class', 'Item Group Major', 'Manufacturer Name', 'Mfg Part Number', 'Asset Type', 'Quantity', 'Unit Price', 'SalesDollarAmount', 'Serial Number', 'Asset Tag', 'Extended Price', 'Ship Date', 'Shipped To Customer Name', 'Shipped To Customer Address 1', 'Shipped To Customer Address 2', 'Shipped to City', 'Shipped to State', 'Shipped to Zip Code'}
    df_header_columns = list(df_downloaded.columns.values)
    if not set(df_headers_tocheck) = set(df_header_columns):
        raise ValueError("Data is not matching between what is expected and what is given, exiting...")
        exit()
    else:
        # NOTE remove any row that does not have an asset tag
        df_downloaded['Asset Tag'] = df_downloaded['Asset Tag'].replace(' ', np.nan)
        df_downloaded = df_downloaded.dropna(axis=0, subset=['Asset Tag'])
        # NOTE Modify any valid data in the dataset here:
        df_downloaded['Customer Name'].replace(CDW_CUSTOMER_NAME, CUSTOMER_NAME), inplace=True)
        # NOTE Import dataframe from downloaded file columns to add to templatefile and their respective columns
        df_template['Item Name'] = df_downloaded['Item Description']
        df_template['Model Name'] = df_downloaded['Item Description']
        df_template['Category'] = df_downloaded['Item Type']
        df_template['Manufacturer'] = df_downloaded['Manufacturer Name']
        df_template['Model Number'] = df_downloaded['Mfg Part Number']
        df_template['Serial'] = df_downloaded['Serial Number']
        df_template['Asset Tag'] = df_downloaded['Asset Tag']
        df_template['Location'] = df_downloaded['Shipped to City']
        df_template['Purchase Date'] = df_downloaded['Invoice Date']
        df_template['Purchase Cost'] = df_downloaded['Unit Price']
        df_template['Company'] = df_downloaded['Customer Name']
        df_template['Order Number'] = df_downloaded['Order Number']
        df_template['Invoice Number'] = df_downloaded['Invoice Number']
        df_template['Customer PO'] = df_downloaded['Customer PO']
        df_template['Purchased By'] = df_downloaded['Contact']
        #NOTE Create static entries or modify entries in the df_template file below
        df_template['Supplier'] = "CDW"
        df_template['Status'] = "Ready to Deploy"
        # TODO add serveral shipping columns in either the notes field or a shipping address database column - this will be helpful if we start shipping devices directly to employees.
        df_template.to_csv(OUTPUTFILE, sep=',', na_rep='', index=False, encoding="utf-8")
        exit()
