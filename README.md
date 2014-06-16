     ____    ___                       __      ____                              
    /\  _`\ /\_ \                     /\ \    /\  _`\                            
    \ \ \/\_\//\ \     ___   __  __   \_\ \   \ \,\L\_\  __  __    ___     ___   
     \ \ \/_/_\ \ \   / __`\/\ \/\ \  /'_` \   \/_\__ \ /\ \/\ \ /' _ `\  /'___\ 
      \ \ \L\ \\_\ \_/\ \L\ \ \ \_\ \/\ \L\ \    /\ \L\ \ \ \_\ \/\ \/\ \/\ \__/ 
       \ \____//\____\ \____/\ \____/\ \___,_\   \ `\____\/`____ \ \_\ \_\ \____\
        \/___/ \/____/\/___/  \/___/  \/__,_ /    \/_____/`/___/> \/_/\/_/\/____/
                                                             /\___/              

-----

Auto upload tool for AWS S3 & AliYun OSS.

- Auto monitor system file operations (CREATE/DELETE/MODIFY)
- Auto transport monitored file to AWS S3 & AliYun OSS.
- Record synced files into SQLite DB.

## Preparation

    $ ./setenv
    $ source venv/bin/activate

> Specify user cutomized settings in cloud_sync_setting.py.

## Verify Uploaded files

    $make verify

## Serving

    $ make run

## Stop Serving

    $ cat /tmp/cloud_sync.pid|xargs kill -9
