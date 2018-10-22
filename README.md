Ansible Module Utils
====================
These are custom libraries and module_utils for Ansible to work with libvirtd with different storage backends (ZFS)

## Python modules
```
pip install -r vutils/requirements.txt
pip install -r module_utils/requirements.txt
```

## Symlinks for Ansible testing
```
sudo ln -s ~/ansible_vutils/vutils /usr/lib/python2.7/dist-packages/ansible/modules/cloud/misc/.
sudo ln -s ~/ansible_vutils/module_utils/virt_utils.py /usr/lib/python2.7/dist-packages/ansible/module_utils/.
