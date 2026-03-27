#!/bin/sh


#-----------------------------------------------------------
#reading variables:
VARFILE="./versions-distribution-config.sh"
if [ ! -f "$VARFILE" ]; then
    echo "Config file $VARFILE missing. Exiting right away."
    exit 1
fi
echo "Reading variables from ${VARFILE}"
. ${VARFILE}
#-----------------------------------------------------------


curdate=`date +%Y%m%d`
curtime=`date +%H:%M`
zipfile="${curdate}.zip"
logfile="versions-distribution-${curdate}.txt"
DOWTODAY=`date +%a`


echo "Versions distribution" > ${logfile}
echo "at the moment ${curdate} ${curtime}" >> ${logfile}
echo "" >> ${logfile}

for ict in "os" "atelios" "vaps"
do
  echo "" >> ${logfile}
  echo "======================" >> ${logfile}
  echo "${ict}:" >> ${logfile}
  echo "---------------" >> ${logfile}
  ./eve-vers-info.sh ../../reports/automatization-${ict} >> ${logfile}
  echo "---------------" >> ${logfile}
  echo "Fortigate:" >> ${logfile}
  ./app-inst-vers-info-fortigate.sh ../../reports/automatization-${ict} >> ${logfile}
  echo "---------------" >> ${logfile}
  echo "k3s:" >> ${logfile}
  ./app-inst-vers-info-k3s.sh ../../reports/automatization-${ict} >> ${logfile}
  echo "======================" >> ${logfile}
  echo "" >> ${logfile}
done


# if today a Senday of week we send the report via email:
if [ ${DOWTODAY} = ${SENDDAY} ]
then
  subj="Versions distribution at VW, ${curdate}"
  message="Hi! Here is the versions distribution at VW."
  uuid=`uuidgen`
  echo -n "/usr/local/bin/mailsend-go -smtp ${SMTPSERVER} -port ${SMTPPORT} -t ${TO} -cc ${CC} -bcc ${BCC} -f ${FROM} -fname \"${ROBOTNAME}\" -sub \"${subj}\" body -msg \"${message}\" auth -user ${SMTPUSER} -pass ${SMTPPASS} header -name Message-ID -value \"<${uuid}@${MESSIDDOMAIN}\" -log mailsend.log attach -file ${logfile}" > mailcmd.sh
  /bin/sh mailcmd.sh
  rm -f mailcmd.sh
fi


zip -9 --junk-paths ${zipfile} ${logfile} > /dev/null
mv -f ${zipfile} ${producedfolder}
rm -f ${logfile}
