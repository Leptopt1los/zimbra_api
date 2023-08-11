#%%
from flask import Flask, request, jsonify
from ZimbraAPI import ZimbraAPIUsage, ZimbraUser, ResponseData
from config import hmac_key
import logging
from logging.handlers import RotatingFileHandler
from time import time, strftime, localtime
import hmac, hashlib

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def get_HMAC(data:list) -> dict:
    timestamp = int(time()*1000)
    return {'hmac':hmac.new(hmac_key, f'{timestamp}{"".join(data)}'.encode('utf-8'), hashlib.sha3_512).hexdigest(), 'timestamp':timestamp}

def check_HMAC(timestamp:str, data:list, hmac_sign:str) -> bool:
    current_timestamp = int(time())
    if abs(current_timestamp-int(timestamp)) > 30: return False
    return (str(hmac.new(hmac_key, f'{timestamp}{"".join(data)}'.encode('utf-8'), hashlib.sha3_512).hexdigest()) == hmac_sign)



Zimbra = ZimbraAPIUsage()



@app.route('/create', methods=['POST'])
def create():
    email:str = request.form.get('email')
    password:str = request.form.get('password')
    name:str = request.form.get('name')
    surname:str = request.form.get('surname')
    patronymic:str = request.form.get('patronymic')
    timestamp:int = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')

    logging.info(f"From IP: {request.remote_addr}. Route: {request.path}. Email: {email}")

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(request.form.get('timestamp'), [email,password,name,surname,patronymic], request.form.get('hmac_sign'))):
        logging.warning(f"HMAC error from IP: {request.remote_addr}. Route: {request.path}. Data = {request.form}")
        return ResponseData.Get_HMAC_Error()
    
    newUser = ZimbraUser(email, password, name, patronymic, surname)

    result = Zimbra.CreateAccount(newUser).asdict()

    logging.info(f"Response to IP: {request.remote_addr}. IsError: {result['iserror']}. ErrorCode: {result['errorcode']}. Route: {request.path}. Email: {email}")

    return result

@app.route('/deleteByEmail', methods=['POST'])
def delete(): 
    email:str = request.form.get('email')
    timestamp:int = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')

    logging.info(f"From IP: {request.remote_addr}. Route: {request.path}. Email: {email}")

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(request.form.get('timestamp'), [email], request.form.get('hmac_sign'))):
        logging.warning(f"HMAC error from IP: {request.remote_addr}. Route: {request.path}. Data = {request.form}")
        return ResponseData.Get_HMAC_Error()
    
    result = Zimbra.DeleteAccountByName(email).asdict()

    logging.info(f"Response to IP: {request.remote_addr}. IsError: {result['iserror']}. ErrorCode: {result['errorcode']}. Route: {request.path}. Email: {email}")
    
    return result

@app.route('/getAccountInfoByEmail', methods=['POST'])
def getInfo():  
    email:str = request.form.get('email')
    timestamp:int = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(request.form.get('timestamp'), [email], request.form.get('hmac_sign'))):
        logging.warning(f"HMAC error from IP: {request.remote_addr}. Route: {request.path}. Data = {request.form}")
        return ResponseData.Get_HMAC_Error()
    
    result = Zimbra.GetAccountInfoByName(email).asdict()
    
    logging.info(f"Response to IP: {request.remote_addr}. IsError: {result['iserror']}. ErrorCode: {result['errorcode']}. Route: {request.path}. Email: {email}")

    return result

@app.route('/ping', methods=['POST'])
def hello(): 
    logging.warning(f"Ping from IP: {request.remote_addr}. Route: {request.path}. Data: {request.form}")

    return "hello world"

@app.route('/getMessages', methods=['POST'])
def getMessages():
    email = request.form.get('email')
    allMessages = str(request.form.get('all'))
    timestamp = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')
    data = ''.join(str(x) for x in [email,allMessages] if not x=="None")

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(request.form.get('timestamp'), data, request.form.get('hmac_sign'))):
        logging.warning(f"HMAC error from IP: {request.remote_addr}. Route: {request.path}. Data = {request.form}")
        return ResponseData.Get_HMAC_Error()
    
    allMessages = False if allMessages.lower() in ["false", "0", "none"] else True

    result = Zimbra.GetMessages(email,allMessages).asdict()

    logging.info(f"Response to IP: {request.remote_addr}. IsError: {result['iserror']}. ErrorCode: {result['errorcode']}. Route: {request.path}. Email: {email}")

    return result

if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler('ZimbraAPI.log', maxBytes=5000000000, backupCount=2)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)


    app.run(host = "0.0.0.0")

