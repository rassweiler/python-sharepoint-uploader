# python-sharepoint-uploader
Will collect files from remote pi-networked-counters and upload them to a sharepoint site.

## Setup
- create a key on the server running the sharepoint uploader using ssh-keygen
- add the generated public key to each counter pi in the ~/.ssh/authorized_keys file
