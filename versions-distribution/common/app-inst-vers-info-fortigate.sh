#!/bin/sh

apptpl="global-fortigate"
apptpl1ver="global-fortigate-7.2.10"

datafolder=${1}
if [ "N${datafolder}" = "N" ]
then
  datafolder="../../reports/automatization-os"
fi
#echo "datafolder = ${datafolder}"


#appsfile="all-apps-2025102119.json"

appsfilezip=`ls ${datafolder}/apps | grep all-apps-20 | tail -1`
#echo "appsfilezip = ${appsfilezip}"
unzip -o ${datafolder}/apps/${appsfilezip} > /dev/null
appsfile=`ls all-apps-20* | tail -1`
#echo "appsfile = ${appsfile}"


apps=`cat ${appsfile} | jq .summaryByAppInstanceDistribution.values`
#echo ${apps} | jq

#theapponly=`echo ${apps} | jq 'with_entries(select(.key | startswith("global-fortigate")))'`
theapponly=`echo ${apps} | jq 'with_entries(select(.key | startswith("'"${apptpl}"'")))'`
echo ${theapponly} | jq

theapptotal=`echo ${apps} | jq 'to_entries | map(select(.key | startswith("'"${apptpl}"'"))) | map(.value) | add'`
echo "${apptpl} total = ${theapptotal}"


theapp1vertotal=`echo ${apps} | jq 'to_entries | map(select(.key | startswith("'"${apptpl1ver}"'"))) | map(.value) | add'`
echo "${apptpl1ver} total = ${theapp1vertotal}"


percent1ver=`echo "scale=2; (${theapp1vertotal} * 100) / ${theapptotal}" | bc`
echo "percent of ${apptpl1ver} = ${percent1ver}"

rm -f ${appsfile}
