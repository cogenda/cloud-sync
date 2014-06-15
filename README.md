Cloud Sync tool to upload AWS S3 & AliYun

-----

Auto upload tool for AWS S3 & AliYun OSS.

- Auto monitor system file operations (CREATE/DELETE/MODIFY)
- Auto transport monitored file to AWS S3 & AliYun OSS.
- Record synced files into SQLite DB.

## Preparation

    $ ./setenv
    $ source venv/bin/activate

> Specify user cutomized settings in cloud_sync_setting.py.

## Serving

    $ make run

## Stop Serving

    $ cat /tmp/cloud_sync.pid|xargs kill -9
