# auto-ddns

DDNS scripts for tencent cloud

# Author

[Jasecharloote](https://github.com/Jasecharloote)

# Goal

update DNS record automatically from the server. The record is updated every minute.

Combined with the restart policy of docker, the script keeps running as long as the docker service is active.

# Tencent Cloud API version
1. [Signature API version is V3](https://cloud.tencent.com/document/product/639/41437)
2. [DNSPod version is 2021-03-23](https://cloud.tencent.com/document/product/1427/56193)

# Requirements

1. Container runtime(docker, podman, etc.)
2. An existing DNS record corresponding to the subdomain in this context(for example, in `www.google.com`, the DOMAIN is `google.com`, the SUBDOMAIN is `www`)
3. Active secret id and secret key that has the correct permission

# Usage

For a first-time user with a domain already purchased, do the following:

1. create a sub-user with Read/Write permission of all the Web resources and get the secret ID and secret key.
2. run `signature.py` with the `TC3_DNSPOD_DOMAIN`, `TC3_DNSPOD_SUB_DOMAIN`, `TC3_SECRET_ID`, `TC3_SECRET_KEY` set through the env variables

# Environment variables
- `TC3_SECRET_ID` is secret id, <span style="color:red">*required*</span>, from [cam user detail](https://console.cloud.tencent.com/cam)
- `TC3_SECRET_KEY` is secret key, <span style="color:red">*required*</span>, from [cam user detail](https://console.cloud.tencent.com/cam)
- `TC3_DNSPOD_DOMAIN` is your domain(for example, in `www.google.com`, the DOMAIN is `google.com`, the SUBDOMAIN is `www`), <span style="color:red">*required*</span>, 
- `TC3_DNSPOD_SUB_DOMAIN` is your subdomain(for example, in `www.google.com`, the DOMAIN is `google.com`, the SUBDOMAIN is `www`), <span style="color:red">*required*</span>, 
- `ENABLE_PROXY` is the flag to enable http proxy, and default value is `False`, ***optional***, 
- `HTTP_PROXY` is http proxy url configuration, when `ENABLE_PROXY` is `False`, this configuration will be ignored, ***optional***
- `HTTPS_PROXY` is https proxy url configuration, when `ENABLE_PROXY` is `False`, this configuration will be ignored, ***optional***
- `AUTO_ADD_SUB_DOMAIN` is the flag to enable auto add record when SUBDOMAIN not exists, default value is `True`, ***optional***
- `SLEEP_SECS` is the interval parameter, unit is second, default value is `60`, ***optional***

# Command
The following steps must be run every time this container is manually started:

`docker run -e TC3_DNSPOD_DOMAIN=<TC3_DNSPOD_SUB_DOMAIN> -e TC3_DNSPOD_SUB_DOMAIN=<TC3_DNSPOD_SUB_DOMAIN> -e TC3_SECRET_ID=<TC3_SECRET_ID> -e TC3_SECRET_KEY=<TC3_SECRET_KEY> -d --restart always --name auto-ddns jasecharloote/auto-ddns:latest`
