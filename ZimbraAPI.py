# %%
import requests
import json
import config
import re
from ZimbraUser import ZimbraUser
from ResponseData import ResponseData
from AuthData import AuthData


class ZimbraAPI:
    def __init__(self, host, adminUsername, adminPassword) -> None:
        self.__Host = host
        self.__AdminHost = self.__Host + ":7071"
        self.__AuthData = AuthData(self.__AdminHost, adminUsername, adminPassword)
        self.__CreateAccountURL = (
            self.__AdminHost + "/service/admin/soap/CreateAccountRequest"
        )
        self.__DeleteAccountURL = (
            self.__AdminHost + "/service/admin/soap/DeleteAccountRequest"
        )
        self.__BatchRequestURL = self.__AdminHost + "/service/admin/soap/BatchRequest"
        self.__DelegateAuthURL = (
            self.__AdminHost + "/service/admin/soap/DelegateAuthRequest"
        )

    def __UpdateAuthData(self) -> ResponseData:
        return self.__AuthData.UpdateAuthData()

    def __GetCSRFToken(self) -> str:
        return self.__AuthData.GetCSRFToken()

    def __GetCookies(self) -> dict:
        return self.__AuthData.GetCookies()

    def CreateAccount(self, AccountData: ZimbraUser) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><format type="js"/><csrfToken>{self.__GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><CreateAccountRequest xmlns="urn:zimbraAdmin"><name>{AccountData.GetEmail()}</name><password>{AccountData.GetPassword()}</password><a n="zimbraAccountStatus">active</a><a n="displayName">{AccountData.GetSurname()} {AccountData.GetName()} {AccountData.GetPatronymic()}</a><a n="givenName">{AccountData.GetName()}</a><a n="initials">{AccountData.GetPatronymic()}</a><a n="sn">{AccountData.GetSurname()}</a><a n="zimbraPasswordMustChange">FALSE</a></CreateAccountRequest></soap:Body></soap:Envelope>'
            CreateAccountResponse = requests.post(
                self.__CreateAccountURL,
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            if CreateAccountResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(CreateAccountResponse.text)["Body"]["Fault"]["Reason"][
                        "Text"
                    ]
                )
                result.SetErrorCode(
                    json.loads(CreateAccountResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
            result.SetStatusCode(CreateAccountResponse.status_code)
        else:
            result = UpdateAuthDataStatus

        return result

    def __DeleteAccountByID(self, AccountID: str) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><format type="js"/><csrfToken>{self.__GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><DeleteAccountRequest xmlns="urn:zimbraAdmin"><id>{AccountID}</id></DeleteAccountRequest></soap:Body></soap:Envelope>'
            DeleteAccountResponse = requests.post(
                self.__DeleteAccountURL,
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(DeleteAccountResponse.status_code)
            if DeleteAccountResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(DeleteAccountResponse.text)["Body"]["Fault"]["Reason"][
                        "Text"
                    ]
                )
                result.SetErrorCode(
                    json.loads(DeleteAccountResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
        else:
            result = UpdateAuthDataStatus

        return result

    def DeleteAccountByName(self, AccountName: str) -> ResponseData:
        x = self.GetAccountInfoByName(AccountName)
        result = ResponseData()
        if x.IsError():
            result = x
        else:
            result = self.__DeleteAccountByID(x.GetData()["id"])
        return result

    def GetAccountInfoByName(self, AccountName: str) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        result = ResponseData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><format type="js"/><csrfToken>{self.__GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><BatchRequest xmlns="urn:zimbra" onerror="continue"><GetAccountRequest xmlns="urn:zimbraAdmin" applyCos="0"><account by="name">{AccountName}</account></GetAccountRequest></BatchRequest></soap:Body></soap:Envelope>'
            AccountInfoResponse = requests.post(
                self.__BatchRequestURL,
                RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(AccountInfoResponse.status_code)
            jsonResponseData = json.loads(AccountInfoResponse.text)
            data = {}
            try:
                tempDataArray = jsonResponseData["Body"]["BatchResponse"][
                    "GetAccountResponse"
                ]
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
                    if d["n"] == "zimbraIsAdminAccount":
                        data["isAdmin"] = d["_content"]
                data["exists"] = True
                result.SetData(data)
            except:
                data["exists"] = False
                result.SetData(data)
        else:
            result = UpdateAuthDataStatus

        return result

    def GetMessages(self, email: str, unreadOnly: bool = True) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            requestPath = (
                self.__AdminHost
                + f"/home/{email}/inbox?fmt=json"
                + ("&query=is:unread" if unreadOnly else "")
            )
            GetMessagesResponse = requests.get(
                requestPath, cookies=self.__GetCookies(), verify=False
            )
            result.SetStatusCode(GetMessagesResponse.status_code)
            if GetMessagesResponse.status_code != 200:
                result.SetErrorText(GetMessagesResponse.text)
                if GetMessagesResponse.status_code == 404:
                    result.SetErrorCode("NO_SUCH_MAILBOX")
                else:
                    result.SetErrorCode("UNEXPECTED_ERROR")
            else:
                response = json.loads(GetMessagesResponse.text)
                data = {'messages':[]}
                if "m" in response:
                    data["count"] = len(response['m'])
                    for message in response["m"][:10]:
                        parsedMessage = {}
                        parsedMessage["date"] = message["d"] // 1000
                        if "p" in message["e"][1]:
                            parsedMessage["sender_name"] = message["e"][1]["p"]
                        else:
                            parsedMessage["sender_name"] = message["e"][1]["d"]
                        parsedMessage["sender_email"] = message["e"][1]["a"]
                        parsedMessage["subject"] = message["su"]
                        parsedMessage["message"] = message["fr"]
                        data["messages"].append(parsedMessage)
                else:
                    data['count'] = 0
                result.SetData(data)
        else:
            result = UpdateAuthDataStatus

        return result

    def GetPreauthLink(self, email: str) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC111 (Win)"/><session id="350"/><format type="js"/><csrfToken>{self.__GetCSRFToken()}</csrfToken></context></soap:Header><soap:Body><DelegateAuthRequest xmlns="urn:zimbraAdmin"><account by="name">{email}</account></DelegateAuthRequest></soap:Body></soap:Envelope>'
            PreauthResponse = requests.post(
                self.__AdminHost + "/service/admin/soap/DelegateAuthRequest",
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(PreauthResponse.status_code)
            if PreauthResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(PreauthResponse.text)["Body"]["Fault"]["Reason"]["Text"]
                )
                result.SetErrorText(
                    json.loads(PreauthResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
            else:
                preauthToken = json.loads(PreauthResponse.text)["Body"][
                    "DelegateAuthResponse"
                ]["authToken"][0]["_content"]
                result.SetData(
                    {
                        "url": self.__Host
                        + f"/service/preauth?authtoken={preauthToken}&isredirect=1"
                    }
                )
        else:
            result = UpdateAuthDataStatus
        return result

    def ExecuteCustomRequest(
        self, URL: str, Request: str
    ) -> ResponseData:  # DEBUG METHOD
        UpdateAuthDataStatus = self.__UpdateAuthData()
        Request = re.sub(
            r"(?<=<csrfToken>)(.*?)(?=<\/csrfToken>)", self.__GetCSRFToken(), Request
        )
        Response = requests.post(
            self.__AdminHost + URL, Request, cookies=self.__GetCookies()
        )

        result = ResponseData()
        result.SetData(Response.text)
        return result
