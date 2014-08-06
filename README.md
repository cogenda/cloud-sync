     ____    ___                       __      ____                              
    /\  _`\ /\_ \                     /\ \    /\  _`\                            
    \ \ \/\_\//\ \     ___   __  __   \_\ \   \ \,\L\_\  __  __    ___     ___   
     \ \ \/_/_\ \ \   / __`\/\ \/\ \  /'_` \   \/_\__ \ /\ \/\ \ /' _ `\  /'___\ 
      \ \ \L\ \\_\ \_/\ \L\ \ \ \_\ \/\ \L\ \    /\ \L\ \ \ \_\ \/\ \/\ \/\ \__/ 
       \ \____//\____\ \____/\ \____/\ \___,_\   \ `\____\/`____ \ \_\ \_\ \____\
        \/___/ \/____/\/___/  \/___/  \/__,_ /    \/_____/`/___/> \/_/\/_/\/____/
                                                             /\___/              

[![Build Status](https://travis-ci.org/cogenda/cloud-sync.svg)](https://travis-ci.org/cogenda/cloud-sync)

-----

Cloud sync tool for AWS S3 & AliYun OSS.

- Monitoring system file operations. (CREATE/DELETE/MODIFY)
- Auto sync monitored file to AWS S3 & AliYun OSS.
- Invoke web services once sync file succeed. (with HMAC based authentication)
- Recording synced files into SQLite DB & synced file status verification.
- Auto deploy with Travis CI & Fabric.

### Preparation

    $ ./setenv
    $ source venv/bin/activate

## Serving public files

    $ make run

### Verify uploaded files

    $ make verify

## Stop Serving

    $ make stop

> Please dig into cloud_sync.yml to specify your customized configuration.
