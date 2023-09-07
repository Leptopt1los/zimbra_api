import requests
import json
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
        RequestData = (
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
                "<soap:Header>"
                    '<context xmlns="urn:zimbra">'
                        '<authTokenControl voidOnExpired="1"/>'
                        '<format type="js"/>'
                    "</context>"
                "</soap:Header>"
                "<soap:Body>"
                    '<AuthRequest xmlns="urn:zimbraAdmin">'
                        f"<name>{self.__Username}</name>"
                        f"<password>{self.__Password}</password>"
                        "<csrfTokenSecured>1</csrfTokenSecured>"
                    "</AuthRequest>"
                "</soap:Body>"
            "</soap:Envelope>"
        )

        try:
            AuthResponse = requests.post(self.__AuthURL, data=RequestData, verify=False)
        except requests.exceptions.RequestException as e:
            result.SetErrorCode(str(type(e)))
            result.SetErrorText(str(e))
            return result

        self.__AuthToken = AuthResponse.cookies.get("ZM_ADMIN_AUTH_TOKEN")
        self.__CSRFToken = AuthResponse.headers.get("X-Zimbra-Csrf-Token")

        if None in (self.__AuthToken, self.__CSRFToken):
            jsonResponseData = json.loads(AuthResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def GetAuthToken(self) -> str:
        return self.__AuthToken

    def GetCSRFToken(self) -> str:
        return self.__CSRFToken

    def GetCookies(self) -> dict:
        return {"ZM_ADMIN_AUTH_TOKEN": self.GetAuthToken()}
