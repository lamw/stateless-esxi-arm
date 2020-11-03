#!/bin/sh
# William Lam
# www.virtuallyghetto.com

# Enable & start SSH (useful for debugging)
TEXT="Enabling and Starting SSH"
/bin/logger "[STATELESS-DEBUG] ${TEXT}"
esxcfg-init --set-boot-progress-text "${TEXT} ..."
vim-cmd hostsvc/enable_ssh
vim-cmd hostsvc/start_ssh

# Enable & start ESXi Shell (useful for debugging)
TEXT="Enabling and Starting ESXi-Arm Shell"
/bin/logger "[STATELESS-DEBUG] ${TEXT}"
esxcfg-init --set-boot-progress-text "${TEXT} ..."
vim-cmd hostsvc/enable_esx_shell
vim-cmd hostsvc/start_esx_shell

# Enable HTTP Client
TEXT="Enabling httpClient on ESXi-Arm Firewall"
/bin/logger "[STATELESS-DEBUG] ${TEXT}"
esxcfg-init --set-boot-progress-text "${TEXT} ..."
esxcli network firewall ruleset set -e true -r httpClient

# Process boot options from ESXi-Arm
TEXT="Processing ESXi-Arm Boot Options"
/bin/logger "[STATELESS-DEBUG] ${TEXT}"
esxcfg-init --set-boot-progress-text "${TEXT} ..."
CONFIG_SERVER=$(/bin/bootOption -o | awk -F 'configServer=' '{print $2}' | awk '{print $1}')
JOIN_VC=$(/bin/bootOption -o | awk -F 'joinVC=' '{print $2}' | awk '{print $1}')
RUN_EXTRA_CONFIG=$(/bin/bootOption -o | awk -F 'runExtraConfig=' '{print $2}' | awk '{print $1}')

# Download ESXi-Arm Configuration
TEXT="Downloading ESXi-Arm Configuration File"
/bin/logger "[STATELESS-DEBUG] ${TEXT}"
esxcfg-init --set-boot-progress-text "${TEXT} ..."
wget http://${CONFIG_SERVER}/esxi-arm-config.json -O /tmp/esxi-arm-config.json

# Configure NTP
TEXT="Configuring NTP"
/bin/logger "[STATELESS-DEBUG] ${TEXT}"
esxcfg-init --set-boot-progress-text "${TEXT} ..."
NTP_SERVER=$(cat /tmp/esxi-arm-config.json | python -m json.tool | python -c 'import sys, json; print(json.load(sys.stdin)["ntp_server"])')
esxcli system ntp set -e true -s ${NTP_SERVER}
sleep 5

if [ "${RUN_EXTRA_CONFIG}" == "true" ]; then
    # Download ESXi-Arm Extra Custom Configuration
    TEXT="Downloading ESXi-Arm Extra Configuration Script"
    /bin/logger "[STATELESS-DEBUG] ${TEXT}"
    esxcfg-init --set-boot-progress-text "${TEXT} ..."
    wget http://${CONFIG_SERVER}/esxi-arm-extra-config.sh -O /tmp/esxi-arm-extra-config.sh

    # Run ESXi-Arm Extra Configuration Script
    TEXT="Running esxi-arm-extra-config.sh"
    /bin/logger "[STATELESS-DEBUG] ${TEXT}"
    esxcfg-init --set-boot-progress-text "${TEXT} ..."
    sh /tmp/esxi-arm-extra-config.sh
fi

# Join vCenter Server
if [ "${JOIN_VC}" == "true" ]; then
    TEXT="Running join-vcenter.py"
    /bin/logger "[STATELESS-DEBUG] ${TEXT}"
    esxcfg-init --set-boot-progress-text "${TEXT} ..."
    python /etc/rc.local.d/join-vcenter.py -j /tmp/esxi-arm-config.json
fi

exit 0