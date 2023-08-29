# Zimbra_api
Python API for Zimbra Web Client

## Description

API for managing mailboxes on Zimbra Web Client. Requires only the administrator login and password, which are specified in the file config.py.
It runs on Flask, uses HMAC based on SHA3_512 signature for the received data

### Routes:
- create (email, password, name, surname, patronymic, timestamp, hmac_sign) `for create a postmail`
- deleteByEmail (email, timestamp, hmac_sign) `for delete postmail`
- getAccountInfoByEmail (email, timestamp, hmac_sign) `to get postmail info`
- getMessages (email, all, timestamp, hmac_sign) `to get messages from postmail. specify all=false to get last 5 messages`

## Usage
```$ pip install -r requirements.txt```

```$ python3 app.py```

or build via docker:

```$ docker build -t zimbra_api .```

```$ docker run -d -p 8080:80 --name zimbra_api zimbra_api:latest```
