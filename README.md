
# Snipe-IT and CDW Asset Automation

## What does this do
This project will contain various scripts to automate the asset system with our supplier(s).

This script, automatically reaches out to CDW's B2B FTP Server to download and archive Asset Purchases, and then automatically imports the assets into SnipeIT. A companion bash script, opens up the docker container to automatically run the import utiltiies.

This is a self contained file, that we use with custom Snipe-IT asset fields to automatically import our CDW purchases into Snipe-IT (dockerized). We have been using this tool for ~2 years now in production.

This was mainly developed for use with the dockerized version of Snipe-IT. 


## How to run
`cdw.py` should be placed on the host or in a sidecar container, with a cron job that runs it at a set schedule.  
`snipeit_cdw_asset_import.sh` should be placed inside the docker volume mount for `/etc/cron.*` so that Snipe-IT will continue to process the shell script.

The way that we have traditionally done this (we have not revised our ITAM system in some time, and this could use some improvement), was by creating bind mounts in the following locations:
```
"/snipeit/cron.daily:/etc/cron.daily",
"/snipeit/cron.hourly:/etc/cron.hourly",
"/snipeit/assetmanagement/output:/assetmanagement"
```
 

### Arguments
All are strings unless otherwise noted.
```
-rf, --remote_filename
```
**Details:**  
This is the file located on CDW's file servers. It defaults on the file with the current date, based on CDW's file bucket.  
default="/Outbox/CDW_Asset_"+time.strftime("%m%d%Y")+".csv

```
-dl, --download_location 
```
**Details:**  
This is the download location on the local server where you are saving the file from the remote server. This defaults to /tmp directory. I would recommend using a more long term location storage or cloud storage bucket.  
default="/tmp/CDW_Asset_"+time.strftime("%m%d%Y")+".csv"


```
-t, --template
```
**Details:**  
The template file that the program will use as a baseline for what the file will look like for this tool to manipulate (based on the pre-determined columnns being used in SnipeIT and CDW). There is a file included here for example purposes.  
default="/snipeit/assetmanagement/resources/template.csv"

```
-of, --output_file
```
**Details:**  
The output fie that will be automatically imported into Snipe-IT. This will be imported on an hourly basis.  
default="/snipeit/assetmanagement/output/assetrecord_"+time.strftime("%m%d%Y")+".csv"

```
-af, --archive_file
```
**Details:** 
Where to move the the download location after manipulating it. In case you have any issues with the output file, or need to reference later on after the program has run.  
default="/snipeit/assetmanagement/archive/"+time.strftime("%m%d%Y")+".csv"

```
-sa, --server_address 
```
**Details:** 
Connect to CDW's Server/URL Address.  
default="gis.cdw.com"

```
-sp, --server_password
```
**Details:** 
Password to use for connecting to server_addresss, recommendation to use a secrets vault or encrypted secrets store to pass the password in.  
default="<%= @cdw_password %>"

```
-su, --server_username
```
**Details:**  
The username that CDW provides to you.  
default="SSHUSERNAME"

```
-mf, --min_filesize
```
**Details:**  
Minimum file size with an additional allotment of bytes to detect if the file has been modified or is empty.  
type=int, default=600

```
-kh, --known_hosts
```
**Details:** 
The .ssh/known_hosts file that pysftp will use to validate the connection.  
default='/snipeit/assetmanagement/resources/cdw.knownhosts'

```
-n, --cdw_name
```
**Details:**  
This is the predetermined CDW customer name. Reach out to CDW for verification.  
default='Company Name'

```
-cn, --customer_name
```
**Details:**  
Sets the new company name that you want to override CDW value of Company Name in the CDW files.  
default='Company Name'





## Room for improvements
* Add SSH Known Hosts dynamically
* Incoprorate the use of Snipe-IT's API - this was not available at the time of writing this
* Get rid of need for templates file

PR's are more than welcome for the above

## Support

There isn't any support provided this, but if you have questions feel free to find me on MacAdmins' #snipe-it channel or file an issue and I will see what I can do. 
