import requests
import json
import config
from ResponseData import ResponseData


class AuthData:
    def __init__(self, AdminHost: str, Username: str, Password: str) -> None:
        self.__AuthURL = AdminHost + "/service/admin/soap/AuthRequest"
        self.__Username = Username
        self.__Password = Password
        self.__CSRFToken = ""
        self.__AuthToken = ""

    def UpdateAuthData(self) -> ResponseData:
        result = ResponseData()
        RequestData = f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra"><userAgent name="ZimbraWebClient - GC107 (Win)"/><session/><authTokenControl voidOnExpired="1"/><format type="js"/></context></soap:Header><soap:Body><AuthRequest xmlns="urn:zimbraAdmin"><name>{self.__Username}</name><password>{self.__Password}</password><virtualHost>mail.amursu.ru</virtualHost><csrfTokenSecured>1</csrfTokenSecured></AuthRequest></soap:Body></soap:Envelope>'
        AuthResponse = requests.post(self.__AuthURL, data=RequestData, verify=False)
        try:
            self.__AuthToken = AuthResponse.cookies["ZM_ADMIN_AUTH_TOKEN"]
            self.__CSRFToken = AuthResponse.headers["X-Zimbra-Csrf-Token"]
        except:
            x = json.loads(AuthResponse.text)
            print(x)
            result.SetErrorText(x["Body"]["Fault"]["Reason"]["Text"])
            result.SetErrorCode(x["Body"]["Fault"]["Detail"]["Error"]["Code"])
        result.SetStatusCode(AuthResponse.status_code)
        return result

    def GetAuthToken(self) -> str:
        return self.__AuthToken

    def GetCSRFToken(self) -> str:
        return self.__CSRFToken

    def GetCookies(self) -> dict:
        return {"ZM_ADMIN_AUTH_TOKEN": self.GetAuthToken()}
