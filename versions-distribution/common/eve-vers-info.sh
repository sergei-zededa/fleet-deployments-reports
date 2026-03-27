#!/bin/sh

eve1ver="11.0.12"

datafolder=${1}
if [ "N${datafolder}" = "N" ]
then
  datafolder="../../reports/automatization-os"
fi
#echo "datafolder = ${datafolder}"


#nodefile="all-reduced-20251021.json"
nodefilezip=`ls ${datafolder}/jsons | grep all-reduced-20 | tail -1`
#echo "nodefilezip = ${nodefilezip}"
unzip -o ${datafolder}/jsons/${nodefilezip} > /dev/null
nodefile=`ls all-reduced-20* | tail -1`
#echo "nodefile = ${nodefile}"


nodes=`cat ${nodefile} | jq .totalCount`
echo "nodestotal = ${nodes}"

evevers=`cat ${nodefile} | jq .summaryByEVEDistribution.values`
echo ${evevers} | jq



#fortigatesonly=`echo ${apps} | jq 'with_entries(select(.key | startswith("global-fortigate")))'`
eve1veronly=`echo ${evevers} | jq 'with_entries(select(.key | startswith("'"${eve1ver}"'")))'`
echo ${eve1veronly} | jq


eve1veronlytotal=`echo ${evevers} | jq 'to_entries | map(select(.key | startswith("'"${eve1ver}"'"))) | map(.value) | add'`
echo "EVE ${eve1ver} total = ${eve1veronlytotal}"


percent1ver=`echo "scale=2; (${eve1veronlytotal} * 100) / ${nodes}" | bc`
echo "percent of EVE ${eve1ver} = ${percent1ver}"

rm -f ${nodefile}
