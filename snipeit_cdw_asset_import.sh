#!/bin/bash
#Because of https://snipe-it.readme.io/v4.6.3/docs/importing and no python in the docker image, this is to be placed inside the docker container's necesssary cron folder.

DATE=$(date +%m%d%Y)
cd /var/www/html
php artisan snipeit:import --verbose /assetmanagement/assetrecord_"$DATE".csv
