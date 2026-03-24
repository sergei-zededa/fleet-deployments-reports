#!/usr/bin/python3

import subprocess
import datetime
import os
import docker
import sys
import zipfile


#docker run -id --rm -v ${PWD}:/in --name ${CONTAINERNAME} -e ZENTERPRISE=${ENT} zededa/zcli:9.11.0
#docker exec -i ${CONTAINERNAME} zcli configure -T "${TOKEN}" --user="${AUTHEMAIL}" --server="${SERVER}" --output=json
#docker exec -i ${CONTAINERNAME} zcli login
#docker exec -i ${CONTAINERNAME} zcli -o json edge-node show > ${BIGJSONFILE}


# Function to load variables from a file
def load_variables(file_path):
    variables = {}
    try:
        with open(file_path, "r") as file:
            for line in file:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    variables[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading variables file: {e}")
        exit(1)
    return variables


def safe_decode(output):
    if output is None:
        return ""
    return output.decode('utf-8')


def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        print(f"Error initializing Docker client: {e}")
        exit(1)


# Function to read the auth token from the file
def read_token(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading token file: {e}")
        exit(1)


# Function to start the Docker container
def start_container1(image, container, voldir, envvars):
    try:
        result = subprocess.run([
            "docker", "run", "-id", "--rm", f"--volume {voldir}:/in", f"-e{envvars}", "--name", container, image
        ], check=True)
        print(f"Docker container '{container}' started successfully.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}: {e.stderr}")
        exit(1)
#"docker", "run", "-d", "--name", container, image


def start_container2(image, container, voldir, envvars):
    shcommand = f"docker stop {container}"
    try:
        result = subprocess.run(shcommand, shell=True, capture_output=True, text=True, check=True)
        print(f"Docker container '{container}' stopped preventivly.")
        #return result.stdout
    except subprocess.CalledProcessError as e:
        estderr=e.stderr
    shcommand = f"docker run -id --rm -v {voldir}:/in --name {container} -e {envvars} {image}"
    try:
        result = subprocess.run(shcommand, shell=True, capture_output=True, text=True, check=True)
        print(f"Docker container '{container}' started successfully.")
        #return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}: {e.stderr}")
        exit(1)


# Function to execute a command inside the Docker container
def exec_in_container1(container, command):
    try:
        result = subprocess.run([
            "docker", "exec", "-i", container, command
        ], capture_output=True, text=True, check=True)
        print(f"Command output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}: {e.stderr}")
        exit(1)


def exec_in_container2(client, container, command):
    try:
        container_obj = client.containers.get(container)
        result = container_obj.exec_run(command, demux=True, stream=False)
        #result = container_obj.exec_run(command, stream=False, demux=False)
        stdout, stderr = result.output
        if stderr:
            #safeoutput = safe_decode(result.output)
            print(f"Command error: {stderr}")
            #print(f"Command error: {safeoutput}")
            exit(1)
        #safeoutput = safe_decode(result.output)
        return stdout
    except docker.errors.APIError as e:
        print(f"Error executing command in container: {e}")
        exit(1)


def exec_in_container3(container, command):
    shcommand = f"docker exec -i {container} {command}"
    try:
        result = subprocess.run(shcommand, shell=True, capture_output=True, text=True, check=True)
        #print("Command output:")
        #print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}: Error output: {e.stderr}")
        return f"Command failed with return code {e.returncode}: Error output: {e.stderr}"



# Function to stop the Docker container
def stop_container(container):
    try:
        subprocess.run([
            "docker", "stop", container
        ], check=True)
        print(f"Docker container '{container}' stopped successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error stapping Docker container: {e.stderr}")
        exit(1)



# ====== body of the script ======

# Parse CLI arguments for the variables file
if len(sys.argv) < 2:
    script_name = os.path.basename(sys.argv[0])
    default_variables_file = f"{os.path.splitext(script_name)[0]}-configvars.txt"
    print(f"No variables file specified, using default: {default_variables_file}")
    variables_file = default_variables_file
else:
    variables_file = sys.argv[1]


# Extract variables
config = load_variables(variables_file)
token_file        = config.get("token_file")
docker_image      = config.get("docker_image")
docker_container  = config.get("docker_container")
voldir            = config.get("d")
envs              = config.get("envs")
zedcloudserver    = config.get("zedcloudserver")
authemail         = config.get("authemail")
eventstemplate    = config.get("eventstemplate")
collected_file    = config.get("collected_file")
AddDateToFileName = config.get("AddDateToFileName", "True").lower() == "true"
start_date        = config.get("start_date", "")
end_date          = config.get("end_date", "")
YesterdayOnly     = config.get("YesterdayOnly", "False").lower() == "true"
SortNeeded        = config.get("SortNeeded", "True").lower() == "true"
ZipNeeded         = config.get("ZipNeeded", "True").lower() == "true"


# Adjust start_date and end_date if YesterdayOnly is True
if YesterdayOnly:
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = yesterday
    end_date = yesterday

if AddDateToFileName:
    collected_file_name, collected_file_ext = os.path.splitext(collected_file)
    collected_file = f"{collected_file_name}-{end_date}{collected_file_ext}"


# get current dir:
#vol_folder = os.getcwd()
#vol_folder = "/root/vw/test/events/d"
vol_folder = os.getcwd()+"/d"
#vol_folder = "./d"
#print(vol_folder)

print("")
print("=== Gathering events ===")
print(envs)
print(f"start_date = {start_date}")
print(f"end_date   = {end_date}")
print(f"template   = {eventstemplate}")


# Start zcli container
#start_result=start_container1(docker_image, docker_container, vol_folder, envs)
start_result=start_container2(docker_image, docker_container, vol_folder, envs)
#print(start_result)


client = get_docker_client()



# Read the auth token
auth_token = read_token(token_file)


# zcli configure
auth_command = f'zcli configure --token={auth_token} --user={authemail} --server={zedcloudserver} --output=json'
#auth_command = f'cat .config/zededa/zcli.json'
#print("zcli configure...")
#print(auth_command)
#auth_result = exec_in_container1(docker_container, auth_command)
auth_result = exec_in_container2(client, docker_container, auth_command)
#print("Authentication successful.")
#print(auth_result)


# zcli login
zcli_command = f'zcli login'
#print("zcli login...")
zcli_result = exec_in_container3(docker_container, zcli_command)
if zcli_result == "":
  print("zcli login is not successfull !")
print(f"zcli login result= {zcli_result}")



# Prepare to collect events
print("Collecting events...")

daypos = datetime.datetime.strptime(start_date, "%Y-%m-%d")
dayend = datetime.datetime.strptime(end_date,   "%Y-%m-%d")

collected_lines = []

# zcli events show --filter-edge-app-instance="*fortigate-1" --filter-resource=EdgeAppInstance --filter-event-type=EdgeAppInstance_Created --starts="2024-06-01 00:00:00" --ends="2025-01-06 23:59:59" > /in/events-EdgeAppInstance-Created-fortigate.txt
# zcli events show --filter-edge-app-instance="*fortigate-1" --filter-resource=EdgeAppInstance --filter-event-type=EdgeAppInstance_Deleted --starts="2024-06-01 00:00:00" --ends="2025-01-06 23:59:59" > /in/events-EdgeAppInstance-Deleted-fortigate.txt

while daypos <= dayend:
    moment1 = daypos.strftime("%Y-%m-%d 00:00:00")
    moment2 = daypos.strftime("%Y-%m-%d 23:59:59")
    #events_command = f'zcli -o text events show --filter-edge-app-instance="*fortigate-1" --filter-resource=EdgeAppInstance --filter-event-type=EdgeAppInstance_Created --starts="{moment1}" --ends="{moment2}"'
    events_command = f'zcli -o text events show {eventstemplate} --starts="{moment1}" --ends="{moment2}"'
    #logs = exec_in_container2(client, docker_container, events_command)
    #result = exec_in_container2(client, docker_container, events_command)
    #print(events_command)
    result = exec_in_container3(docker_container, events_command)
    #print(type(result))
    #print(result)
    collected_lines.append(result)
    daypos += datetime.timedelta(days=1)

#exit(0)



# Sort lines by timestamp
#collected_lines.sort(key=lambda x: x.split()[0])


# Write collected lines to the output file

try:
    with open(collected_file, "w") as file:
    #with open(collected_file, "wb") as file:
        for line in collected_lines:
            file.write(line)  # Add newline
            #file.write(line + b"\n")  # Add newline as bytes
    print(f"Events collected and saved to {collected_file}")
except Exception as e:
    print(f"Error writing to collected file: {e}")


if SortNeeded:
    sorted_file = f"{collected_file}-sorted"
    try:
        # Read and sort
        with open(collected_file, 'r') as input_file:
            lines = input_file.readlines()
            sorted_lines = sorted(lines)
        # Write to temporary file
        with open(sorted_file, 'w') as output_file:
            output_file.writelines(sorted_lines)
        # Replace original with sorted
        os.remove(collected_file)
        os.rename(sorted_file, collected_file)
    except Exception as e:
        print(f"Error sorting file {collected_file}: {e}")

if ZipNeeded:
    collected_file_name, collected_file_ext = os.path.splitext(collected_file)
    collected_zipfile = f"{collected_file_name}.zip"
    with zipfile.ZipFile(collected_zipfile, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(collected_file, arcname=os.path.basename(collected_file))
    os.remove(collected_file)

# Stop zcli container
print(f"Stopping container {docker_container}")
stop_container(docker_container)

print("=========done.==========")
print("")

