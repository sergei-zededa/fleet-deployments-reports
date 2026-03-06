#!/usr/bin/python3

import json
import csv
import os
import sys
import requests
from datetime import datetime
from ipaddress import ip_network, ip_address
from requests.utils import default_user_agent
from configobj import ConfigObj


# possible arg - filename of big json
# cloud, token and ExtraColumns defined in the config-file



#============================================================================


# Function to detect position of IPv4 address in ['netStatusList']
def detect_ipv4_position(data):
    for item in data:
        if 'ipAddrs' in item:
            iparray = data.get('ipAddrs')
            for oneip in iparray:
                if '.' in oneip:
                    position = iparray.index(oneip)
                    #print(iparray, position)
                    return position
    return None  # Return None if no IPv4 address found


# Function to reduce size of big json
def clean_dict(data):
    new_data = {}
    new_data['name'] = data.get('name')
    new_data['id'] = data.get('id')
    new_data['runState'] = data.get('runState')
    new_data['adminState'] = data.get('adminState')
    new_data['appInstCount'] = data.get('appInstCount')
    new_data['projectName'] = data.get('projectName')
    new_data['__imageVersion'] = data.get('__imageVersion')
    netStatusList = data.get('netStatusList', [{}])
    if netStatusList:
        new_data['netStatusList'] = []
        for item in netStatusList:
            ipv4_position = detect_ipv4_position(item)
            if ipv4_position is not None:
                # IPv4 address exists, add item to new_data
                new_data['netStatusList'].append({
                    'up': item['up'],
                    'ifName': item['ifName'],
                    'ipAddrs': item['ipAddrs'],
                    'location': {
                        'underlayIP': item['location']['underlayIP'],
                        'city': item['location'].get('city', ''),
                        'country': item['location'].get('country', '')
                    },
                    'uplink': item['uplink']
                })

    else:
        new_data['location'] = {'underlayIP': None, 'country': None}
        new_data['ipAddrs'] = None
        new_data['ifName'] = None
        new_data['uplink'] = None
    return new_data

#-----

# Check if file exists and not zero-sized
def file_exists(pathtofile):
  fileok = False
  if (os.path.isfile(pathtofile)) and (os.path.getsize(pathtofile) != 0):
    fileok = True
  return fileok

#-----

# Function to check if an IP belongs to a list of networks
def ip_in_networks(ip, networks):
    for network in networks:
        if ip_address(ip) in network:
            return True
    return False

#-----

def get_node_description(nodeid, cloud, token, ua):
  endpoint='api/v1/devices/id'
  url=f'https://{cloud}/{endpoint}/{nodeid}'
  description=""

  #callresults = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token), 'User-Agent': ua}, timeout=apicalltimeout)
  try:
    callresults = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token), 'User-Agent': ua}, timeout=apicalltimeout)
    onenode=callresults.json()
    descriptionfield = onenode['description']
    if descriptionfield:
      description=descriptionfield

  except requests.exceptions.RequestException as exc:
    print("Request failed:", exc)

  return description

#-----

def get_node_config(nodeid, cloud, token, ua):
  endpoint='api/v1/devices/id'
  url=f'https://{cloud}/{endpoint}/{nodeid}/config'
  brand=""
  model=""
  created=""

  try:
    callresults = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token), 'User-Agent': ua}, timeout=apicalltimeout)
    onenodeconf = callresults.json()
    brand       = onenodeconf['config']['manufacturer']
    model       = onenodeconf['config']['productName']
    created     = onenodeconf['createdAt']

  except requests.exceptions.RequestException as exc:
    print("Request failed:", exc)

  return [brand,model,created]

#-----

def get_node_status(nodeid, cloud, token, ua):
  endpoint='api/v1/devices/id'
  url=f'https://{cloud}/{endpoint}/{nodeid}/status'
  lastUpdate=""
  bootTime=""
  dataSecInfoStatus=""
  devErrorDescription=""

  try:
    callresults = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token), 'User-Agent': ua}, timeout=apicalltimeout)
    onenodestatus         = callresults.json()
    #with open("onenodestatus.json", "w", encoding="utf-8") as f:
    #  json.dump(onenodestatus, f, indent=4, ensure_ascii=False)
    lastUpdate            = onenodestatus['lastUpdate']
    bootTime              = onenodestatus['bootTime']
    title                 = onenodestatus['title']
    if len(onenodestatus['dataSecInfo']) > 0:
      dataSecInfoStatus   = onenodestatus['dataSecInfo'][0]['status']
    if len(onenodestatus['devError']) > 0:
      devErrorDescription = onenodestatus['devError'][0]['description']

  except requests.exceptions.RequestException as exc:
    print("Request failed:", exc)

  return [lastUpdate, bootTime, title, dataSecInfoStatus, devErrorDescription]



#============================================================================


# Extract variables
variables_file = "fetch-big-json-with-all-work-config.sh"
config         = ConfigObj(variables_file)
tokenfile      = config["TOKENFILE"]
cloud          = config["SERVER"]
extra_columns  = config["EXTRACOLUMNS"]

if extra_columns.upper()=="YES":
  WithExtraDetails = True
  print(f"ExtraColumns = Yes")
else:
  WithExtraDetails = False


fabipfile = 'fabric-ip-ranges.txt'

uaaddon   = "-SergeiReportExtra/0.1"
custom_ua = default_user_agent() + uaaddon
apicalltimeout = 120

default_input_file = 'all.json'
input_file = sys.argv[1] if len(sys.argv) > 1 else default_input_file

current_date     = datetime.now().strftime("%Y%m%d")
current_datetime = datetime.now().strftime("%Y%m%d%H%M")
output_file = f'all-reduced-{current_date}.json'
csv_file    = f'report-{current_date}.csv'


for ff in [fabipfile,input_file,tokenfile]:
  if not file_exists(ff):
    print(f"The file {ff} isn't exist or empty. Please put a non-empty file in the current directory.")
    exit()


# Load the list of IP ranges:
with open(fabipfile, 'r') as file:
    ip_ranges = [ip_network(line.strip()) for line in file]


with open(tokenfile, 'r') as file:
    apitoken = file.readline().strip('\n')


with open(input_file, 'r') as file:
    data = json.load(file)
    cleaned_list = [clean_dict(item) for item in data['list']]
    data['list'] = cleaned_list

with open(output_file, 'w') as file:
    json.dump(data, file, indent=4)



# Prepare data for CSV
devices_total = data['summaryByState']['total']
devices_online = data['summaryByState']['values']['Online']
devices_suspect = data['summaryByState']['values']['Suspect']
devices_provisioned = data['summaryByState']['values']['Provisioned']
devices_with_2_apps = data['summaryByAppInstanceCount']['values']['DEVICE_SUMMARY_APP_INSTANCE_COUNT_2_PLUS']


# Write data to CSV
with open(csv_file, 'w', newline='') as file:
    csvwriter = csv.writer(file, quoting=csv.QUOTE_MINIMAL)

    # Header:
    csvwriter.writerow(['Datetime:', current_datetime])
    csvwriter.writerow(['Devices Created Total:', devices_total, '100%'])
    csvwriter.writerow(['Devices Online:', devices_online, '{:.2f}%'.format(100*devices_online/devices_total)])
    csvwriter.writerow(['Devices Suspect:', devices_suspect, '{:.2f}%'.format(100*devices_suspect/devices_total)])
    csvwriter.writerow(['Devices Provisioned:', devices_provisioned, '{:.2f}%'.format(100*devices_provisioned/devices_total)])
    csvwriter.writerow(['Devices With 2 Apps:', devices_with_2_apps, '{:.2f}%'.format(100*devices_with_2_apps/devices_total)])

    # Body:
    # Columns:
    if WithExtraDetails:
        csvwriter.writerow(['Name', 'RunState', 'AdminState', 'AppInstCount', 'UnderlayIP', 'Country', 'Valuation', 'ProjectName','SwVersion', 'Description', 'Brand', 'Model', 'ConfigCreatedAt', 'LastUpdateTime', 'LastBootTime', 'Title', 'DataSecInfoStatus', 'DevErrorDescription'])
    else:
        csvwriter.writerow(['Name', 'RunState', 'AppInstCount', 'UnderlayIP', 'Country', 'Valuation'])

    # Rows:
    for item in cleaned_list:
        run_state   = item['runState']
        appscount   = item['appInstCount']
        if 'netStatusList' in item and item['netStatusList']:
          underlay_ip = item['netStatusList'][0]['location']['underlayIP']
          country     = item['netStatusList'][0]['location']['country']
          ifname      = item['netStatusList'][0]['ifName']
          localip     = item['netStatusList'][0]['ipAddrs'][0]
        else:
          underlay_ip = ""
          country     = ""
          ifname      = ""
          localip     = ""
 
        if WithExtraDetails:
            admin_state    = item['adminState']
            projectname    = item['projectName']
            swversion      = item['__imageVersion']
            nodeid         = item['id']
            descr          = get_node_description(nodeid, cloud , apitoken, custom_ua)
            [brand, model, created] = get_node_config(nodeid, cloud, apitoken, custom_ua)
            [lastUpdate, bootTime, title, dataSecInfoStatus, devErrorDescription] = get_node_status(nodeid, cloud, apitoken, custom_ua)

        valuation   = "Red"       # device unfunctional
        if (run_state == 'RUN_STATE_ONLINE'):
          if (int(appscount) >= 2):
            valuation = "Green"   # device is functional, i.e. online, not at factory, and has more than 1 app-instance deployed
          else:
            valuation = "Orange"  # device is online, not at factory, and has too few app-instance deployed
          if underlay_ip and ip_in_networks(underlay_ip, ip_ranges):
            valuation = "Yellow"  # device is still at factory

        if WithExtraDetails:
            csvwriter.writerow([item['name'], run_state, admin_state, appscount, underlay_ip, country, valuation, projectname, swversion, descr, brand, model, created, lastUpdate, bootTime, title, dataSecInfoStatus, devErrorDescription])
        else:
            csvwriter.writerow([item['name'], run_state, appscount, underlay_ip, country, valuation])
