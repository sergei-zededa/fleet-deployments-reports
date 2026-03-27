
versions-distribution


The script versions-distribution-4.sh reads its config from versions-distribution-config.sh
and runs series of scripts that additionally analyze the fleet information
collected with fleet-deployments-reports (https://github.com/sergei-zededa/fleet-deployments-reports/tree/main/reports/automatization-ent)
Additional analyzis creates a table of versons of interesting edge-apps and EVE-OS on the fleet.
versions-distribution-4.sh
invokes several sub-scripts with path to data-folders as argument:
app-inst-vers-info-fortigate.sh
app-inst-vers-info-k3s.sh
in this two scripts the edge-applications templates should be specified:
apptpl="global-fortigate"
apptpl1ver="global-fortigate-7.2.10"
and
eve-vers-info.sh
in this script the eve-version template should be specified:
apptpl="global-fortigate"
apptpl1ver="global-fortigate-7.2.10"
eve1ver="11.0.12"

For daily run from cron the script versions-distribution.sh is used

Requirements:
zip (apt install zip)
mailsend-go (https://github.com/muquit/mailsend-go)

