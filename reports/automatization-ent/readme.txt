fleet-deployments-reports

The set of scripts that can be run daily to track the fleet deployment process.
The script needs Ubuntu Linux, python and docker.

The main script is fetch-big-json-with-all-work9.sh,
it invokes the state of the fleet using zcli docker container and then analyzes the fetched data.
For that, there are several python sub-scripts are invoked from the main script:
gen-report19.py - creates a CSV-table with deployed edge-nodes and some of their parameters and makes a conclusing about devices' readiness (marking it as Green/Yellow/Orange/Red),
gen-report-excel10.py - creates an excel-variant of the table,
analyze-countries7.py - analyzes the distribution over the World,
compare-csv9.py - compares the CSV-tables between today and yesterday, and 1 week ago, and 1 month ago, and 1 quarter ago.

Produced files are sent via smtp to recipients' email addresses.

This set of scripts requires the mailsend-go binary and several python modules to be deployed. The details are in the requirements-ubuntu22.txt.

The main script and gen-report19.py need the config
fetch-big-json-with-all-work-config.sh and token.txt files.
There are examples of fetch-big-json-with-all-work-config.sh.example and 
token.txt.example
The auth token should be obtained in Zedcloud UI from the user's properties.
The script tested only with CONTAINERTAG="zededa/zcli:9.11.0"
If EXTRACOLUMNS set to "YES", the script makes 3 additional API calls to Zedcloud API for each node (adding 3 secs of time per each node) to fetch additional info such as EVE versions, nodes' descriptions, and so on.

Possible statuses of nodes' readiness in the produced reports:
Green - online, not at factory, with at least 2 deployed app-instances,
Yellow -  online, at factory (defined by the list of CIDRs in the file fabric-ip-ranges.txt)
Orange -  online, not at factory, with less than 2 deployed app-instances,
Red - offline, not onboarded, and other nonfunctional states.

The script can be run regularly by cron from the working directory.

