#%%
from flask import Flask, request
from ZimbraAPI import ZimbraAPI, ZimbraUser, ResponseData
from config import hmac_key
from time import time
import hmac, hashlib

def check_HMAC(timestamp:str, data:list, hmac_sign:str) -> bool:
    current_timestamp = int(time())
    if abs(current_timestamp-int(timestamp)) > 30: return False
    return (str(hmac.new(hmac_key, f'{timestamp}{"".join(data)}'.encode('utf-8'), hashlib.sha3_512).hexdigest()) == hmac_sign)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

Zimbra = ZimbraAPI()

@app.route('/create', methods=['POST'])
def create():
    email:str = request.form.get('email')
    password:str = request.form.get('password')
    name:str = request.form.get('name')
    surname:str = request.form.get('surname')
    patronymic:str = request.form.get('patronymic')
    timestamp:str = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(timestamp, [email,password,name,surname,patronymic], hmac_sign)):
        return ResponseData.Get_HMAC_Error()

    newUser = ZimbraUser(email, password, name, patronymic, surname)

    result = Zimbra.CreateAccount(newUser).asdict()
    return result

@app.route('/deleteByEmail', methods=['POST'])
def delete():
    email:str = request.form.get('email')
    timestamp:int = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(timestamp, [email], hmac_sign)):
        return ResponseData.Get_HMAC_Error()

    result = Zimbra.DeleteAccountByName(email).asdict()
    return result

@app.route('/getAccountInfoByEmail', methods=['POST'])
def getInfo():
    email:str = request.form.get('email')
    timestamp:str = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(timestamp, [email], hmac_sign)):
        return ResponseData.Get_HMAC_Error()

    result = Zimbra.GetAccountInfoByName(email).asdict()
    return result

@app.route('/ping', methods=['POST'])
def hello():
    return "hello world"

@app.route('/getMessages', methods=['POST'])
def getMessages():
    email:str = request.form.get('email')
    allMessages:str = str(request.form.get('all'))
    timestamp:str = request.form.get('timestamp')
    hmac_sign:str = request.form.get('hmac_sign')
    data = ''.join(str(x) for x in [email,allMessages] if not x=="None")

    if (timestamp is None) or (hmac_sign is None) or (not check_HMAC(timestamp, data, hmac_sign)):
        return ResponseData.Get_HMAC_Error()

    allMessages = False if allMessages.lower() in ["false", "0", "none"] else True

    result = Zimbra.GetMessages(email, allMessages).asdict()
    return result

if __name__ == '__main__':
    app.run(host = "0.0.0.0")
