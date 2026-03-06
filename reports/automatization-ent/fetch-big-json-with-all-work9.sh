#!/bin/sh


echo "=============================================="
echo "== Starting fetch-big-json-with-all-work..."


#-----------------------------------------------------------
#reading variables:
VARFILE="./fetch-big-json-with-all-work-config.sh"
if [ ! -f "$VARFILE" ]; then
    echo "Config file $VARFILE missing. Exiting right away."
    exit 1
fi
echo "Reading variables from ${VARFILE}"
. ${VARFILE}
#-----------------------------------------------------------


echo "Using ${WORKFOLDER} as a work folder"
cd ${WORKFOLDER}


CURDATE=`date +%Y%m%d`
YESTERDAY=`date --date="yesterday" +%Y%m%d`
CURDATEHOUR=`date +%Y%m%d%H`
CURDATETIME=`date +%Y%m%d%H%M%S`
DOWTODAY=`date +%a`
DOMTODAY=`date +%d`
WEEKAGO=`date --date="-7days" +%Y%m%d`
TOKEN=`cat ${WORKFOLDER}/${TOKENFILE}`
JSONSFOLDER="${WORKFOLDER}/jsons"
APPSFOLDER="${WORKFOLDER}/apps"
CSVREPORTSFOLDER="${WORKFOLDER}/csvreports"
ZIPREPORTSFOLDER="${WORKFOLDER}/zipreports"
BIGJSONFILE="${WORKFOLDER}/all-${CURDATEHOUR}.json"
REDUCEDJSONFILE="${WORKFOLDER}/all-reduced-${CURDATE}.json"
BIGAPPSJSONFILE="${WORKFOLDER}/all-apps-${CURDATEHOUR}.json"
BIGAPPINSJSONFILE="${WORKFOLDER}/all-appins-${CURDATEHOUR}.json"
REPORTTODAY="${WORKFOLDER}/report-${CURDATE}.csv"
XLSTODAY="${WORKFOLDER}/report-${CURDATE}.xlsx"
REPORTYESTERDAY="${CSVREPORTSFOLDER}/report-${YESTERDAY}.csv"
COMPARE1DAY="${WORKFOLDER}/compare-1day.txt"
COMPARE1WEEK="${WORKFOLDER}/compare-1week.txt"
COMPARE1MON="${WORKFOLDER}/compare-1month.txt"
COMPARE1QT="${WORKFOLDER}/compare-1quarter.txt"
ANALYZECOUNTRY="${WORKFOLDER}/analyze-country.txt"
ZIPTOSEND="${WORKFOLDER}/tosend-${CURDATE}.zip"

echo "Current time = ${CURDATETIME}"



#exit


#------------------------------------------------------------------------------------------------------------
#  creating zcli container:
docker run -id --rm -v ${PWD}:/in --name ${CONTAINERNAME} -e ZENTERPRISE=${ENT} ${CONTAINERTAG}
sleep 5
#  authentication
docker exec -i ${CONTAINERNAME} zcli configure -T "${TOKEN}" --user="${AUTHEMAIL}" --server="${SERVER}" --output=json
sleep 1
#docker exec -i ${CONTAINERNAME} zcli login

echo "Fetching big json for edge-nodes..."
docker exec -i ${CONTAINERNAME} zcli -o json edge-node show > ${BIGJSONFILE}
sleep 1
echo "Fetching edge-apps..."
docker exec -i ${CONTAINERNAME} zcli -o json edge-app show > ${BIGAPPSJSONFILE}
sleep 1
echo "Fetching edge-app-instances..."
docker exec -i ${CONTAINERNAME} zcli -o json edge-app-instance show > ${BIGAPPINSJSONFILE}

# killing zcli container:
#docker ps -a
docker stop ${CONTAINERNAME}
#docker ps -a




#------------------------------------------------------------------------

# checking big json file size

outfilesize=`wc -c ${BIGJSONFILE} | awk '{print $1}'`

if [ ${outfilesize} -le ${OUTFILEMINSIZE} ]
then
  subj="${ENT}: Report: bad big json size! ${CURDATE}"
  message="${ENT}: File ${BIGJSONFILE} is too small: ${outfilesize} bytes"
  echo ${message}
  uuid=`uuidgen`
  /usr/local/bin/mailsend-go -smtp ${SMTPSERVER} -port ${SMTPPORT} -t ${BCC} -f ${FROM} -fname "${ROBOTNAME}" -sub "${subj}" body -msg "${message}" auth -user ${SMTPUSER} -pass ${SMTPPASS} header -name Message-ID -value "<${uuid}@${MESSIDDOMAIN}>" -log mailsend.log

  echo "----------"
  exit 100
else
  echo "File ${BIGJSONFILE} is big enough: ${outfilesize} bytes"
fi
#------------------------------------------------------------------------


# creating folders for outputs if there no folders yet
mkdir -p ${JSONSFOLDER}
mkdir -p ${APPSFOLDER}
mkdir -p ${CSVREPORTSFOLDER}
mkdir -p ${ZIPREPORTSFOLDER}


#------------------------------------------------------------------------


#  genereting today report.csv:
./gen-report19.py ${BIGJSONFILE}
#  genereting today xls:
./gen-report-excel10.py ${REPORTTODAY}
# analyze countries:
./analyze-countries7.py ${REPORTTODAY} > ${ANALYZECOUNTRY}
# compare 1day:
./compare-csv9.py ${REPORTYESTERDAY} ${REPORTTODAY} > ${COMPARE1DAY}
#------------------------------------------------------------------------

#exit 0

# sending files via email:


SENDEMAILTODAY="NO"
subj="edgeboxes deployment report, ${ENT}, ${CURDATE}"
message="Hi! Here are today's files with the deployment report."
filestoattach="${REPORTTODAY} ${XLSTODAY} ${ANALYZECOUNTRY} ${COMPARE1DAY}"
zip -9 --junk-paths ${ZIPTOSEND} ${filestoattach}

uuid=`uuidgen`
echo -n "/usr/local/bin/mailsend-go -smtp ${SMTPSERVER} -port ${SMTPPORT} -t ${TO} -cc ${CC} -bcc ${BCC} -f ${FROM} -fname \"${ROBOTNAME}\" -sub \"${subj}\" body -msg \"${message}\" auth -user ${SMTPUSER} -pass ${SMTPPASS} header -name Message-ID -value \"<${uuid}@${MESSIDDOMAIN}>\" -log mailsend.log attach -file ${REPORTTODAY} attach -file ${XLSTODAY} attach -file ${ANALYZECOUNTRY} attach -file ${COMPARE1DAY}" > mailcmd.sh

# if today is Friday, will add compare-1week:
if [ ${DOWTODAY} = ${WEEKCOMPAREDAY} ]
then
  SENDEMAILTODAY="YES"
  REPORTWEEKAGO="${CSVREPORTSFOLDER}/report-${WEEKAGO}.csv"
  echo "Today is ${DOWTODAY}; adding ${COMPARE1WEEK}"
  ./compare-csv9.py ${REPORTWEEKAGO} ${REPORTTODAY} > ${COMPARE1WEEK}
  zip -9 --junk-paths ${ZIPTOSEND} ${COMPARE1WEEK}
  echo -n " attach -file ${COMPARE1WEEK}" >> mailcmd.sh
fi

if [ ${DOMTODAY} = "01" ]
then
  SENDEMAILTODAY="YES"
  MD=`date +"%m%d"`
  DAYAGO=`date --date="yesterday" +"%Y%m%d"`
  DANDMAGO=`date --date="1 day ago 1 month ago" +"%Y%m%d"`
  echo "${MD}: Today is the first day of the month; adding ${COMPARE1MON}, between ${DANDMAGO} and ${DAYAGO}"
  REPORTDAYAGO="${CSVREPORTSFOLDER}/report-${DAYAGO}.csv"
  REPORTDANDMAGO="${CSVREPORTSFOLDER}/report-${DANDMAGO}.csv"
  ./compare-csv9.py ${REPORTDANDMAGO} ${REPORTDAYAGO} > ${COMPARE1MON}
  zip -9 --junk-paths ${ZIPTOSEND} ${COMPARE1MON}
  echo -n " attach -file ${COMPARE1MON}" >> mailcmd.sh

  if [ "${MD}" = "0101" -o "${MD}" = "0401" -o "${MD}" = "0701" -o "${MD}" = "1001" ]
  then
    DANDQTAGO=`date --date="1 day ago 3 month ago" +"%Y%m%d"`
    REPORTDANDQTAGO="${CSVREPORTSFOLDER}/report-${DANDQTAGO}.csv"
    echo "${MD}: Today is the first day of the quarter; adding ${COMPARE1QT}, between ${DANDQTAGO} and ${DAYAGO}"
    ./compare-csv9.py ${REPORTDANDQTAGO} ${REPORTDAYAGO} > ${COMPARE1QT}
    zip -9 --junk-paths ${ZIPTOSEND} ${COMPARE1QT}
    echo -n " attach -file ${COMPARE1QT}" >> mailcmd.sh
  fi
fi

echo "" >> mailcmd.sh
#echo "mailcmd:"
#cat mailcmd.sh

if [ ${SENDEMAILTODAY} = "YES" ]
then
  /bin/sh mailcmd.sh
fi

#------------------------------------------------------------------------


# removing files:

rm -f mailcmd.sh

mv ${ZIPTOSEND} ${ZIPREPORTSFOLDER}

zip -9 --junk-paths ${BIGJSONFILE}.zip ${BIGJSONFILE}
mv ${BIGJSONFILE}.zip ${JSONSFOLDER}
zip -9 --junk-paths ${REDUCEDJSONFILE}.zip ${REDUCEDJSONFILE}
mv ${REDUCEDJSONFILE}.zip ${JSONSFOLDER}
zip -9 --junk-paths ${BIGAPPSJSONFILE}.zip ${BIGAPPSJSONFILE}
mv ${BIGAPPSJSONFILE}.zip ${APPSFOLDER}
zip -9 --junk-paths ${BIGAPPINSJSONFILE}.zip ${BIGAPPINSJSONFILE}
mv ${BIGAPPINSJSONFILE}.zip ${APPSFOLDER}

rm -f ${XLSTODAY}
rm -f ${ANALYZECOUNTRY}
rm -f ${COMPARE1DAY}
rm -f ${BIGJSONFILE}
rm -f ${REDUCEDJSONFILE}
rm -f ${BIGAPPSJSONFILE}
rm -f ${BIGAPPINSJSONFILE}
if [ -e ${COMPARE1WEEK} ]
then
  rm -f ${COMPARE1WEEK}
fi
if [ -e ${COMPARE1MON} ]
then
  rm -f ${COMPARE1MON}
fi
if [ -e ${COMPARE1QT} ]
then
  rm -f ${COMPARE1QT}
fi

mv ${REPORTTODAY} ${CSVREPORTSFOLDER}


#------------------------------------------------------------------------
CURDATETIME=`date +%Y%m%d%H%M%S`
echo "== Finishing fetch-big-json-with-all-work at ${CURDATETIME}."
echo "=============================================="
