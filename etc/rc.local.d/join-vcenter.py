#!/bin/python
# William Lam
# www.virtuallyghetto.com

import atexit
import argparse
import getpass
import json
import os
import sys
import ssl

sys.path.append('/lib64/python3.5/site-packages/') # Required to reference existing PyVim libraries
from pyVim.task import WaitForTask
from pyVim import invt
from pyVmomi import Vim
from pyVim.connect import SmartConnect, Disconnect

def GetArgs():
    """
    Supports the command-line arguments listed below.
    """

    parser = argparse.ArgumentParser(
        description='Process args for joining stateless ESXi-Arm to vCenter Server')
    parser.add_argument('-j', '--json', dest='jsonConfig', required=True, action='store',
                        help='Path to ESXi-Arm Configuration JSON')
    args = parser.parse_args()
    return args

def main():
    args = GetArgs()

    jsonConfig = args.jsonConfig
    if not os.path.exists(jsonConfig):
        os.system("/bin/logger '[STATELESS-DEBUG] Unable to find JSON Config File '" + jsonConfig)
        return

    # Process JSON
    with open(jsonConfig) as f:
        jsonData = json.load(f)

    os.system("/bin/logger '[STATELESS-DEBUG] jsonConfigData='" + json.dumps(jsonData))

    vcenterServer = jsonData["vcenter_server"]
    vcenterUser = jsonData["vcenter_user"]
    vcenterPass = jsonData["vcenter_pass"]
    datacenterName=jsonData["vcenter_datacenter"]
    clusterName=jsonData["vcenter_cluster"]
    esxUsername="root"
    esxPassword=""
    esxPort = 443

    # For python 2.7.9 and later, the defaul SSL conext has more strict
    # connection handshaking rule. We may need turn of the hostname checking
    # and client side cert verification
    context = None
    if sys.version_info[:3] > (2, 7, 8):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    si = SmartConnect(host=vcenterServer,
            user=vcenterUser,
            pwd=vcenterPass,
            port=443,
            sslContext=context)

    atexit.register(Disconnect, si)

    # Retrieve ESXi SSL Thumbprint
    cmd = "echo -n | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -fingerprint -sha1 | awk -F \'=\' \'{print $2}\'"
    tmp = os.popen(cmd)
    sslThumbprint = (tmp.readline()).strip()
    tmp.close()

    # Retrieve ESXi IP Address
    cmd = "grep HostIPAddr /etc/vmware/esx.conf | awk \'{print $3}\'"
    tmp = os.popen(cmd)
    esxHostname = (tmp.readline()).strip().replace('"','')
    tmp.close()

    # Check to see if previous ESXi-Arm instance was added, remove prior to adding again
    try:
        hostRef, hostPath = invt.findHost('', esxHostname, si)[0]
        os.system("/bin/logger '[STATELESS-DEBUG] Removing previous ESXi-Arm instance '" + esxHostname)
        task = hostRef.Destroy()
        if WaitForTask(task) == "error":
            raise task.info.error
        else:
            task.info.result
    except:
        os.system("/bin/logger '[STATELESS-DEBUG] Creating AddHost Spec'")

    # Create AddHost Spec
    hostAddSpec = Vim.Host.ConnectSpec()
    hostAddSpec.SetHostName(esxHostname)
    hostAddSpec.SetPort(esxPort)
    hostAddSpec.SetUserName(esxUsername)
    hostAddSpec.SetPassword(esxPassword)
    hostAddSpec.SetForce(True)
    hostAddSpec.SetSslThumbprint(sslThumbprint)

    # Add Host
    cluster = invt.GetCluster(datacenterName, clusterName, si)
    os.system("/bin/logger '[STATELESS-DEBUG] hostAddSpec='" + json.dumps(hostAddSpec.__dict__))
    os.system("/bin/logger '[STATELESS-DEBUG] Joining vCenter Server'")
    os.system("esxcfg-init --set-boot-progress-text \"Joining vCenter Server ...\"")
    task = cluster.AddHost(hostAddSpec, True, None)

    if WaitForTask(task) == "error":
        raise task.info.error
    else:
        return task.info.result

if __name__ == "__main__":
    main()