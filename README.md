# Stateless ESXi-Arm

This is the custom `extra.tgz` payload which is included as part of the ESXi-Arm boot process and handles the logic of automatically adding an ESXi-Arm host to a vCenter Server and performs any post-boot customizations. These scripts have been designed to be generic and retrieves the actual configurations from a remote endpoint which is hosted on a web server.

Here is the expected structure of the files when it is extracted onto the ESXi-Arm filesystem:

```console
etc
└── rc.local.d
    ├── join-vcenter.py
    └── local.sh
```

To create the exta.tgz, run the following command:

```console
# tar -czvf extra.tgz etc/
# chmod 655 extra.tgz
```

You can download the pre-packaged `extra.tgz` or you can manually create your own. Just make sure you are using GNU tar when creating the payload.

When `/etc/rc.local.d/local.sh` runs, it will process the kernel boot options which will tell it where to find both the `esxi-arm-config.json` and `esxi-arm-extra-config.sh` configuration files.

```console
/var/www/html/
├── esxi-arm-config.json
├── esxi-arm-extra-config.sh
```

Here is an example of the `esxi-arm-config.json` which tells the ESXi-Arm host which vCenter Server to join along with NTP configuration as this is required prior to joining. This is completely optional and is controlled by the `joinVC=true` kernel boot option

```
{
	"vcenter_server": "192.168.30.200",
	"vcenter_user": "vc-join@vsphere.local",
	"vcenter_pass": "VMware1!",
	"vcenter_datacenter": "Arm-Datacenter",
	"vcenter_cluster": "Arm-Cluster",
	"ntp_server": "pool.ntp.org"
}
```
Here is an example of the `esxi-arm-extra-config.sh` which is nothing more than basic shell script that contains commands that would be executed on the ESXi-Arm Shell for additional configurations. This is completely optional and is controlled by the `runExtraConfig=true` kernel boot option

```
#!/bin/sh

# Suppress UI Warnings
esxcli system settings advanced set -o /UserVars/SuppressShellWarning -i 1
esxcli system settings advanced set -o /UserVars/SuppressCoredumpWarning -i 1
```