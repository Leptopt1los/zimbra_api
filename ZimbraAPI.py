# %%
import requests
import json
import config
import re

class ZimbraUser:
    def __init__(self, email:str, password:str, name:str, patronymic:str, surname:str) -> None:
        self.SetEmail(email)
        self.SetPassword(password)
        self.SetName(name)
        self.SetPatronymic(patronymic)
        self.SetSurname(surname)
    
    def SetEmail(self, email:str) -> None:
        self.__email = email

    def SetPassword(self, password:str) -> None:
        self.__password = password

    def SetName(self, name:str) -> None:
        self.__name = name.encode('ascii', errors='xmlcharrefreplace').decode()

    def SetSurname(self, surname:str) -> None:
        self.__surname = surname.encode('ascii', errors='xmlcharrefreplace').decode()

    def SetPatronymic(self, patronymic:str) -> None:
        self.__patronymic = patronymic.encode('ascii', errors='xmlcharrefreplace').decode()

    def GetEmail(self) -> str:
        return self.__email

    def GetPassword(self) -> str:
        return self.__password

    def GetName(self) -> str:
        return self.__name

    def GetPatronymic(self) -> str:
        return self.__patronymic

    def GetSurname(self) -> str:
        return self.__surname
    
class ResponseData:
    def __init__(self) -> None:
        self.__StatusCode = 200
        self.__ErrorText = None
        self.__ErrorCode = None
        self.__IsError = False
        self.__Data = None
    
    def SetStatusCode(self, code: int) -> None:
        self.__StatusCode = code

    def SetErrorText(self, errorText: str) -> None:
        self.__ErrorText = errorText
        self.__IsError = True

    def SetErrorCode(self, errorCode: str) -> None:
        self.__ErrorCode = errorCode
        self.__IsError = True

    def SetData (self, data: dict) -> None:
        self.__Data = data

    def GetStatusCode(self) -> int:
        return self.__StatusCode
    
    def IsError(self) -> bool:
        return self.__IsError
    
    def GetErrorText(self) -> str:
        return self.__ErrorText
    
    def GetData(self) -> dict:
        return self.__Data
    
    def Get_HMAC_Error() -> dict:
        return {'statuscode': 500, 'errorcode':"HMAC_ERROR", 'iserror':True, 'data':"" ,'errortext': "incorrect hmac or timestamp"}
    
    def asdict(self) -> dict:
        return {'statuscode': self.__StatusCode, 'errorcode':self.__ErrorCode, 'iserror':self.__IsError, 'data':self.__Data ,'errortext': self.__ErrorText}

    
class ZimbraAuthData:
    def __init__(self, Username: str, Password: str) -> None:
        self.__AuthURL = config.AuthURL
        self.__Username = Username
        self.__Password = Password
        self.__CSRFToken = ''
        self.__AuthToken = ''

    def UpdateAuthData(self) -> ResponseData:
        result = ResponseData()
        RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><session/><authTokenControl voidOnExpired="1"/><format type="js"/></context></soap:Header><soap:Body><AuthRequest xmlns="urn:zimbraAdmin"><name>{self.__Username}</name><password>{self.__Password}</password><virtualHost>mail.amursu.ru</virtualHost><csrfTokenSecured>1</csrfTokenSecured></AuthRequest></soap:Body></soap:Envelope>'
        AuthResponse = requests.post(self.__AuthURL, data=RequestData, verify = False)
        try:
            self.__AuthToken = AuthResponse.cookies["ZM_ADMIN_AUTH_TOKEN"]
            self.__CSRFToken = AuthResponse.headers['X-Zimbra-Csrf-Token']
        except:
            x = json.loads(AuthResponse.text)
            print(x)
            result.SetErrorText(x['Body']['Fault']['Reason']['Text'])
            result.SetErrorCode(x['Body']['Fault']['Detail']['Error']['Code'])
        result.SetStatusCode(AuthResponse.status_code)
        return result

    def GetAuthToken(self) -> str:
        return self.__AuthToken

    def GetCSRFToken(self) -> str:
        return self.__CSRFToken

    def GetCookies(self) -> dict:
        return {'ZM_ADMIN_AUTH_TOKEN': self.GetAuthToken()}

class ZimbraAPIUsage:   
    def __init__(self) -> None:
        self.Host = config.Host
        self.CreateAccountURL = config.CreateAccountURL
        self.AuthURL = config.AuthURL
        self.DeleteAccountURL = config.DeleteAccountURL
        self.BatchRequestURL = config.BatchRequestURL
        self.EmailDomain = config.EmailDomain
        self.__AuthData = ZimbraAuthData(config.adminUsername, config.adminPassword)

    def UpdateAuthData(self) -> ResponseData:
        return self.__AuthData.UpdateAuthData()
    
    def GetAuthToken(self) -> str:
        return self.__AuthData.GetAuthToken()

    def GetCSRFToken(self) -> str:
        return self.__AuthData.GetCSRFToken()

    def GetCookies(self) -> dict:
        return self.__AuthData.GetCookies()

    def CreateAccount(self, AccountData: ZimbraUser) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.UpdateAuthData()
        if (not UpdateAuthDataStatus.IsError()):
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><format type="js"/><csrfToken>{self.GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><CreateAccountRequest xmlns="urn:zimbraAdmin"><name>{AccountData.GetEmail()}</name><password>{AccountData.GetPassword()}</password><a n="zimbraAccountStatus">active</a><a n="displayName">{AccountData.GetSurname()} {AccountData.GetName()} {AccountData.GetPatronymic()}</a><a n="givenName">{AccountData.GetName()}</a><a n="initials">{AccountData.GetPatronymic()}</a><a n="sn">{AccountData.GetSurname()}</a><a n="zimbraPasswordMustChange">FALSE</a></CreateAccountRequest></soap:Body></soap:Envelope>'
            CreateAccountResponse = requests.post(self.CreateAccountURL, data = RequestData, cookies=self.GetCookies(), verify = False)
            if (CreateAccountResponse.status_code != 200):
                result.SetErrorText(json.loads(CreateAccountResponse.text)['Body']['Fault']['Reason']['Text'])
                result.SetErrorCode(json.loads(CreateAccountResponse.text)['Body']['Fault']['Detail']['Error']['Code'])
            result.SetStatusCode(CreateAccountResponse.status_code)
        else:
            result = UpdateAuthDataStatus

        return result
        

    def DeleteAccountByID(self, AccountID: str) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.UpdateAuthData()
        if (not UpdateAuthDataStatus.IsError()):
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><format type="js"/><csrfToken>{self.GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><DeleteAccountRequest xmlns="urn:zimbraAdmin"><id>{AccountID}</id></DeleteAccountRequest></soap:Body></soap:Envelope>'
            DeleteAccountResponse = requests.post(self.DeleteAccountURL, data = RequestData, cookies=self.GetCookies(), verify = False)
            result.SetStatusCode(DeleteAccountResponse.status_code)
            if (DeleteAccountResponse.status_code != 200):
                result.SetErrorText(json.loads(DeleteAccountResponse.text)['Body']['Fault']['Reason']['Text'])
                result.SetErrorText(json.loads(DeleteAccountResponse.text)['Body']['Fault']['Detail']['Error']['Code'])
        else:
            result = UpdateAuthDataStatus
        
        return result

    def DeleteAccountByName(self, AccountName: str) -> ResponseData:
        x = self.GetAccountInfoByName(AccountName)
        result = ResponseData()
        if x.IsError():
            result = x
        else: #НЕ РАБОТАЕТ БЕЗ ELSE???????????????
            result = self.DeleteAccountByID(x.GetData()['id'])
        return result

    def GetAccountInfoByName(self, AccountName: str) -> ResponseData:
        UpdateAuthDataStatus = self.UpdateAuthData()
        result = ResponseData()
        if (not UpdateAuthDataStatus.IsError()):
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><format type="js"/><csrfToken>{self.GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><BatchRequest xmlns="urn:zimbra" onerror="continue"><GetAccountRequest xmlns="urn:zimbraAdmin" applyCos="0"><account by="name">{AccountName}</account></GetAccountRequest></BatchRequest></soap:Body></soap:Envelope>'
            AccountInfoResponse = requests.post(self.BatchRequestURL, RequestData, cookies=self.GetCookies(), verify = False)
            result.SetStatusCode(AccountInfoResponse.status_code)
            jsonResponseData = json.loads(AccountInfoResponse.text)
            data = {}
            try:
                tempDataArray = jsonResponseData['Body']['BatchResponse']['GetAccountResponse']
                for i in tempDataArray:
                    if "account" in i:
                        tempDataArray = i["account"]
                        break 
                for i in tempDataArray:
                    if "name" in i:
                        data["name"] = i["name"]
                        break
                for i in tempDataArray:
                    if "id" in i:
                        data["id"] = i["id"]
                        break
                for i in tempDataArray:
                    if "a" in i:
                        tempDataArray = i["a"]
                        break
                for d in tempDataArray:
                    if d['n']=='zimbraIsAdminAccount':
                        data['isAdmin'] = d['_content']
                result.SetData(data)
            except:
                result.SetStatusCode(500)
                result.SetErrorCode(jsonResponseData["Body"]["BatchResponse"]["Fault"][0]["Detail"]["Error"]["Code"])
                result.SetErrorText(jsonResponseData['Body']['BatchResponse']['Fault'][0]['Reason']['Text'])
        else:
            result = UpdateAuthDataStatus

        return result

    def ExecuteCustomRequest(self, URL:str, Request: str) -> ResponseData:   #DEBUG METHOD
        UpdateAuthDataStatus = self.UpdateAuthData()
        Request = re.sub(r'(?<=<csrfToken>)(.*?)(?=<\/csrfToken>)', self.GetCSRFToken(), Request)
        Response = requests.post(self.Host+URL, Request, cookies=self.GetCookies())
        
        return f'STATUS CODE: {UpdateAuthDataStatus}\n' + Response.text

    def GetMessages(self, email:str) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.UpdateAuthData()
        if (not UpdateAuthDataStatus.IsError()):
            GetMessagesResponse = requests.get(self.Host+f"/home/{email}/inbox?fmt=json", cookies=self.GetCookies(), verify = False)
            result.SetStatusCode(GetMessagesResponse.status_code)
            if (GetMessagesResponse.status_code != 200):
                result.SetErrorText(GetMessagesResponse.text)
            else:
                result.SetData(GetMessagesResponse.text)
        else:
            result = UpdateAuthDataStatus
        
        return result