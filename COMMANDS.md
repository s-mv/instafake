- Find IP Subnet
`ip addr show` copy first IP subnet under wlp4s0
Example `192.168.29.175/24`
- Use nmap to find Raspberry Pi's address
`nmap -sn 192.168.29.175/24`
- Connect to Raspberry Pi
`ssh smv@<IP>`
- prometheus
`sudo systemctl start prometheus`
- webmin
`sudo systemctl start webmin`
- nginx
`sudo systemctl start nginx`
- minio
`sudo minio server ~/storage --console-address ":9001"`

---

In case SSH isn't working:
`cd /run/media/smv`
`cd bootfs`
`touch ssh`
