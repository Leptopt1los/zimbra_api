# %%
import requests
import json
import re
from ResponseData import ResponseData
from AuthData import AuthData


class ZimbraAPI:
    def __init__(self, host, adminUsername, adminPassword) -> None:
        self.__Host = host
        self.__AdminHost = self.__Host + ":7071"
        self.__AuthData = AuthData(self.__AdminHost, adminUsername, adminPassword)

    def __UpdateAuthData(self) -> ResponseData:
        return self.__AuthData.UpdateAuthData()

    def __GetCSRFToken(self) -> str:
        return self.__AuthData.GetCSRFToken()

    def __GetCookies(self) -> dict:
        return self.__AuthData.GetCookies()

    def __WrapInSoapTemplate(self, data: list) -> str:
        dataStr = "".join(data)
        return (
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
                "<soap:Header>"
                    '<context xmlns="urn:zimbra">'
                        '<format type="js"/>'
                        f"<csrfToken>{self.__GetCSRFToken()}</csrfToken>"
                    "</context>"
                "</soap:Header>"
                "<soap:Body>"
                    f"{dataStr}"
                "</soap:Body>"
            "</soap:Envelope>"
        )

    ################################################## ACCOUNT MANAGEMENT ##################################################

    def CreateAccount(
        self,
        accountName: str,
        password: str,
        name: str,
        surname: str,
        patronymic: str = "",
        extraParams: dict = None,
    ) -> ResponseData:
        name = name.encode("ascii", errors="xmlcharrefreplace").decode()
        surname = surname.encode("ascii", errors="xmlcharrefreplace").decode()
        patronymic = patronymic.encode("ascii", errors="xmlcharrefreplace").decode()

        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        baseParams = {
            "zimbraAccountStatus": "active",
            "givenName": name,
            "sn": surname,
            "initials": patronymic,
            "displayName": f"{surname} {name} {patronymic}",
        }
        params = {**baseParams, **(extraParams if extraParams else {})}

        paramStr = ""
        for key, value in params.items():
            paramStr = paramStr + f'<a n="{key}">{value}</a>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<CreateAccountRequest xmlns="urn:zimbraAdmin">'
                        f"<name>{accountName}</name>"
                        f"<password>{password}</password>"
                        f"{paramStr}"
                    "</CreateAccountRequest>"
                )
            ]
        )

        CreateAccountResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/CreateAccountRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(CreateAccountResponse.text)["Body"]

        if CreateAccountResponse.status_code == 200:
            data = dict()

            accountData = jsonResponseData["CreateAccountResponse"]["account"][0]

            data["name"] = accountData["name"]
            data["id"] = accountData["id"]

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def DeleteAccount(self, accountID: str = "", accountName: str = "") -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if accountID == "":
            accInfo = self.GetAccount(accountName=accountName)
            if accInfo.IsError():
                return accInfo

            accountID = accInfo.GetData()["id"]

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<DeleteAccountRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{accountID}</id>"
                    "</DeleteAccountRequest>"
                )
            ]
        )

        DeleteAccountResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/DeleteAccountRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        if DeleteAccountResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(DeleteAccountResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def ModifyAccount(self, params: dict, accountID: str = "", accountName: str = ""):
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if accountID == "":
            accInfo = self.GetAccount(accountName=accountName)
            if accInfo.IsError():
                return accInfo

            accountID = accInfo.GetData()["id"]

        paramStr = ""
        for key, value in params.items():
            paramStr = paramStr + f'<a n="{key}">{value}</a>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<ModifyAccountRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{accountID}</id>"
                        f"{paramStr}"
                    "</ModifyAccountRequest>"
                )
            ]
        )

        ModifyAccountResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/ModifyAccountRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(ModifyAccountResponse.text)["Body"]

        if ModifyAccountResponse.status_code == 200:
            data = dict()

            accountData = jsonResponseData["ModifyAccountResponse"]["account"][0]

            data["name"] = accountData["name"]
            data["id"] = accountData["id"]

            newParams = dict()

            for param in accountData["a"]:
                paramName = param["n"]
                paramValue = param["_content"]

                newParams[paramName] = paramValue

            data["params"] = newParams
            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def RenameAccount(self, newName: str, accountID: str = "", accountName: str = ""):
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if accountID == "":
            accInfo = self.GetAccount(accountName=accountName)
            if accInfo.IsError():
                return accInfo

            accountID = accInfo.GetData()["id"]

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<RenameAccountRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{accountID}</id>"
                        f"<newName>{newName}</newName>"
                    "</RenameAccountRequest>"
                )
            ]
        )

        RenameAccountResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/RenameAccountRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(RenameAccountResponse.text)["Body"]

        if RenameAccountResponse.status_code == 200:
            data = dict()

            accountData = jsonResponseData["RenameAccountResponse"]["account"][0]

            data["name"] = accountData["name"]
            data["id"] = accountData["id"]

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def SetPassword(self, newPassword: str, accountID: str = "", accountName: str = ""):
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if accountID == "":
            accInfo = self.GetAccount(accountName=accountName)
            if accInfo.IsError():
                return accInfo

            accountID = accInfo.GetData()["id"]

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<SetPasswordRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{accountID}</id>"
                        f"<newPassword>{newPassword}</newPassword>"
                    "</SetPasswordRequest>"
                )
            ]
        )

        SetPasswordResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/SetPasswordRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        if SetPasswordResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(SetPasswordResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def GetAccount(self, accountID: str = "", accountName: str = "") -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestStr = ""
        if accountName == "":
            requestStr = f'<account by="id">{accountID}</account>'
        else:
            requestStr = f'<account by="name">{accountName}</account>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<BatchRequest xmlns="urn:zimbra" onerror="continue">'
                        '<GetAccountRequest xmlns="urn:zimbraAdmin" applyCos="0">'
                            f"{requestStr}"
                        "</GetAccountRequest>"
                    "</BatchRequest>"
                )
            ]
        )

        AccountInfoResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/BatchRequest",
            RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(AccountInfoResponse.text)["Body"]["BatchResponse"]

        if "GetAccountResponse" in jsonResponseData:
            data = dict()

            accountData = jsonResponseData["GetAccountResponse"][0]["account"][0]

            data["name"] = accountData["name"]
            data["id"] = accountData["id"]

            params = dict()
            for param in accountData["a"]:
                paramName = param["n"]
                paramValue = param["_content"]

                params[paramName] = paramValue

            data["params"] = params
            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"][0]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"][0]["Detail"]["Error"]["Code"])

        return result

    def GetAccounts(self):
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<SearchDirectoryRequest xmlns="urn:zimbraAdmin" offset="0" limit="0" sortBy="name" sortAscending="1" applyCos="false" applyConfig="false" attrs="displayName,zimbraAccountStatus,zimbraLastLogonTimestamp,description,zimbraIsAdminAccount,zimbraMailStatus" types="accounts">'
                        "<query>(&amp;(!(zimbraIsSystemAccount=TRUE)))</query>"
                    "</SearchDirectoryRequest>"
                )
            ]
        )

        GetAccountsResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/SearchDirectoryRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(GetAccountsResponse.text)["Body"]

        if GetAccountsResponse.status_code == 200:
            data = dict()

            accountsData = jsonResponseData["SearchDirectoryResponse"]
            if "account" in accountsData:
                for account in accountsData["account"]:
                    item = dict()

                    item["id"] = account["id"]

                    for attr in account["a"]:
                        attrName = attr["n"]
                        attrValue = attr["_content"]

                        item[attrName] = attrValue

                    data[account["name"]] = item

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def GetAccountMembership(
        self, accountID: str = "", accountName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestStr = ""
        if accountID == "":
            requestStr = f'<account by="name">{accountName}</account>'
        else:
            requestStr = f'<account by="id">{accountID}</account>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<GetAccountMembershipRequest xmlns="urn:zimbraAdmin">'
                        f"{requestStr}"
                    "</GetAccountMembershipRequest>"
                )
            ]
        )

        GetAccountMembershipResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/GetAccountMembershipRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(GetAccountMembershipResponse.text)["Body"]

        if GetAccountMembershipResponse.status_code == 200:
            data = dict()

            accountData = jsonResponseData["GetAccountMembershipResponse"]

            if "dl" in accountData:
                for distrList in accountData["dl"]:
                    item = dict()
                    item["id"] = distrList["id"]
                    item["via"] = distrList["via"] if "via" in distrList else "DIRECT"
                    data[distrList["name"]] = item

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    ################################################## MAILBOX MANAGEMENT ##################################################

    def GetMessages(self, accountName: str, unreadOnly: bool = True) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestPath = (
            self.__AdminHost
            + f"/home/{accountName}/inbox?fmt=json"
            + ("&query=is:unread" if unreadOnly else "")
        )

        GetMessagesResponse = requests.get(
            requestPath, cookies=self.__GetCookies(), verify=False
        )

        if GetMessagesResponse.status_code == 200:
            jsonResponseData = json.loads(GetMessagesResponse.text)
            data = dict()

            messages = list()

            if "m" in jsonResponseData:
                data["count"] = len(jsonResponseData["m"])

                for message in jsonResponseData["m"][:10]:
                    parsedMessage = dict()

                    parsedMessage["date"] = message["d"] // 1000

                    sender = message["e"][-1]
                    if "p" in sender:
                        parsedMessage["sender_name"] = sender["p"]
                    elif "d" in sender:
                        parsedMessage["sender_name"] = sender["d"]

                    if "a" in sender:
                        parsedMessage["sender_email"] = sender["a"]

                    if 'su' in message:
                        parsedMessage["subject"] = message["su"]

                    if 'fr' in message:
                        parsedMessage["message"] = message["fr"]

                    messages.append(parsedMessage)
            else:
                data["count"] = 0

            data["messages"] = messages

            result.SetData(data)
        else:
            result.SetErrorText(GetMessagesResponse.text)

            if GetMessagesResponse.status_code == 404:
                result.SetErrorCode("NO_SUCH_MAILBOX")
            else:
                result.SetErrorCode("UNEXPECTED_ERROR")

        return result

    def DelegateAuth(self, accountID: str = "", accountName: str = "") -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestStr = ""
        if accountName == "":
            requestStr = f'<account by="id">{accountID}</account>'
        else:
            requestStr = f'<account by="name">{accountName}</account>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<DelegateAuthRequest xmlns="urn:zimbraAdmin">'
                    f"{requestStr}"
                    "</DelegateAuthRequest>"
                )
            ]
        )

        DelegateAuthResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/DelegateAuthRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(DelegateAuthResponse.text)["Body"]

        if DelegateAuthResponse.status_code == 200:
            delegateAuthResponseData = jsonResponseData["DelegateAuthResponse"]

            authToken = delegateAuthResponseData["authToken"][0]["_content"]
            url = self.__Host + f"/service/preauth?authtoken={authToken}&isredirect=1"

            result.SetData(
                {
                    "authToken": authToken,
                    "url": url,
                }
            )
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def SendMessage(
        self,
        senderAccountName: str,
        receiverAccountName: str,
        subject: str = "",
        content: str = "",
        senderPseudonym: str = "",
        receiverPseudonym: str = "",
    ) -> ResponseData:
        subject = subject.encode("ascii", errors="xmlcharrefreplace").decode()
        content = content.encode("ascii", errors="xmlcharrefreplace").decode()
        senderPseudonym = senderPseudonym.encode("ascii", errors="xmlcharrefreplace").decode()
        receiverPseudonym = receiverPseudonym.encode("ascii", errors="xmlcharrefreplace").decode()
        
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        RequestData = self.__WrapInSoapTemplate(
            [
                '<SendMsgRequest xmlns="urn:zimbraMail">'
                    f'<m su="{subject}">'
                        f'<mp ct="text/plain" content="{content}">'"</mp>"
                        f'<e a="{senderAccountName}" t="f" p="{senderPseudonym}" />'
                        f'<e a="{receiverAccountName}" t="t" p="{receiverPseudonym}" />'
                    "</m>"
                "</SendMsgRequest>"
            ]
        )

        SendMessageResponce = requests.post(
            self.__AdminHost + "/service/admin/soap/SendMsgRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(SendMessageResponce.text)["Body"]

        if SendMessageResponce.status_code == 200:
            result.SetData({"id": jsonResponseData["SendMsgResponse"]["m"][0]["id"]})
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    ################################################## DISTRIBUTION LIST MANAGEMENT ##################################################

    def CreateDistributionList(
        self, name: str, displayName: str = "", extraParams: dict = None
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        displayName = displayName.encode("ascii", errors="xmlcharrefreplace").decode()

        baseParams = {
            "displayName": displayName,
        }
        params = {**baseParams, **(extraParams if extraParams else {})}

        paramStr = ""
        for key, value in params.items():
            paramStr = paramStr + f'<a n="{key}">{value}</a>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<CreateDistributionListRequest xmlns="urn:zimbraAdmin">'
                        f"<name>{name}</name>"
                        f"{paramStr}"
                    "</CreateDistributionListRequest>"
                )
            ]
        )

        CreateDistributionListResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/CreateDistributionListRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(CreateDistributionListResponse.text)["Body"]

        if CreateDistributionListResponse.status_code == 200:
            data = dict()

            dlData = jsonResponseData["CreateDistributionListResponse"]["dl"][0]

            data["name"] = dlData["name"]
            data["id"] = dlData["id"]

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def DeleteDistributionList(
        self, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if distrListID == "":
            distrListData = self.GetDistributionList(distrListName=distrListName)
            if distrListData.IsError():
                return distrListData

            distrListID = distrListData.GetData()["id"]

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<DeleteDistributionListRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{distrListID}</id>"
                    "</DeleteDistributionListRequest>"
                )
            ]
        )

        DeleteDistrListResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/DeleteDistributionListRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        if DeleteDistrListResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(DeleteDistrListResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def ModifyDistributionList(
        self, params: dict, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if distrListID == "":
            distrListData = self.GetDistributionList(distrListName=distrListName)
            if distrListData.IsError():
                return distrListData

            distrListID = distrListData.GetData()["id"]

        paramStr = ""
        for key, value in params.items():
            paramStr = paramStr + f'<a n="{key}">{value}</a>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<ModifyDistributionListRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{distrListID}</id>"
                        f"{paramStr}"
                    "</ModifyDistributionListRequest>"
                )
            ]
        )

        ModifyDistributionListResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/ModifyDistributionListRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(ModifyDistributionListResponse.text)["Body"]

        if ModifyDistributionListResponse.status_code == 200:
            data = dict()

            dlData = jsonResponseData["ModifyDistributionListResponse"]["dl"][0]

            data["name"] = dlData["name"]
            data["id"] = dlData["id"]
            data["dynamic"] = dlData["dynamic"]

            params = dict()
            for param in jsonResponseData["GetDistributionListResponse"]["dl"][0]["a"]:
                paramName = param["n"]
                paramValue = param["_content"]
                params[paramName] = paramValue

            data["params"] = params

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def GetDistributionList(
        self, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestStr = ""
        if distrListID == "":
            requestStr = f'<dl by="name">{distrListName}</dl>'
        else:
            requestStr = f'<dl by="id">{distrListID}</dl>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<GetDistributionListRequest xmlns="urn:zimbraAdmin" limit="0" offset="0">'
                        f"{requestStr}"
                    "</GetDistributionListRequest>"
                )
            ]
        )

        GetDistrListResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/GetDistributionListRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(GetDistrListResponse.text)["Body"]

        if GetDistrListResponse.status_code == 200:
            data = dict()

            dlData = jsonResponseData["GetDistributionListResponse"]["dl"][0]

            data["name"] = dlData["name"]
            data["id"] = dlData["id"]

            members = list()

            if "dlm" in dlData:
                for member in dlData["dlm"]:
                    members.append(member["_content"])

            data["members"] = members

            params = dict()
            for param in dlData["a"]:
                paramName = param["n"]
                paramValue = param["_content"]
                params[paramName] = paramValue

            data["params"] = params

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def GetDistributionLists(self) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<SearchDirectoryRequest xmlns="urn:zimbraAdmin" offset="0" sortBy="name" sortAscending="1" applyCos="false" applyConfig="false" attrs="displayName,uid,zimbraMailStatus" types="distributionlists,dynamicgroups">'
                        "<query>(&amp;(!(zimbraIsSystemAccount=TRUE)))</query>"
                    "</SearchDirectoryRequest>"
                )
            ]
        )

        GetDistributionListsResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/SearchDirectoryRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(GetDistributionListsResponse.text)["Body"]

        if GetDistributionListsResponse.status_code == 200:
            data = dict()

            dlData = jsonResponseData["SearchDirectoryResponse"]
            if "dl" in dlData:
                for distrList in dlData["dl"]:
                    item = dict()

                    item["id"] = distrList["id"]
                    item["dynamic"] = distrList["dynamic"]

                    for attr in distrList["a"]:
                        attrName = attr["n"]
                        attrValue = attr["_content"]

                        item[attrName] = attrValue

                    if "owners" in distrList:
                        item["owner"] = distrList["owners"][0]["owner"][0]

                    data[distrList["name"]] = item

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def GetDistributionListMembership(
        self, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestStr = ""
        if distrListID == "":
            requestStr = f'<dl by="name">{distrListName}</dl>'
        else:
            requestStr = f'<dl by="id">{distrListID}</dl>'

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<GetDistributionListMembershipRequest xmlns="urn:zimbraAdmin">'
                        f"{requestStr}"
                    "</GetDistributionListMembershipRequest>"
                )
            ]
        )

        GetDistributionListMembershipResponse = requests.post(
            self.__AdminHost
            + "/service/admin/soap/GetDistributionListMembershipReques",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(GetDistributionListMembershipResponse.text)[
            "Body"
        ]

        if GetDistributionListMembershipResponse.status_code == 200:
            data = dict()

            dlData = jsonResponseData["GetDistributionListMembershipResponse"]

            if "dl" in dlData:
                for distrList in dlData["dl"]:
                    item = dict()

                    item["id"] = distrList["id"]
                    item["via"] = distrList["via"] if "via" in distrList else "DIRECT"
                    item["dynamic"] = distrList["dynamic"]

                    data[distrList["name"]] = item

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def AddDistributionListMembers(
        self, userEmails: list, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if distrListID == "":
            distrListData = self.GetDistributionList(distrListName=distrListName)
            if distrListData.IsError():
                return distrListData

            distrListID = distrListData.GetData()["id"]

        usersRequestStr = ""
        for user in userEmails:
            usersRequestStr += f"<dlm>{user}</dlm>"

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<AddDistributionListMemberRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{distrListID}</id>"
                        f"{usersRequestStr}"
                    "</AddDistributionListMemberRequest>"
                )
            ]
        )

        AddDistributionListMembersResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/AddDistributionListMemberRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        if AddDistributionListMembersResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(AddDistributionListMembersResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def RemoveDistributionListMembers(
        self, userEmails: list, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if distrListID == "":
            distrListData = self.GetDistributionList(distrListName=distrListName)
            if distrListData.IsError():
                return distrListData

            distrListID = distrListData.GetData()["id"]

        usersRequestStr = ""
        for user in userEmails:
            usersRequestStr += f"<dlm>{user}</dlm>"

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<RemoveDistributionListMemberRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{distrListID}</id>"
                        f"{usersRequestStr}"
                    "</RemoveDistributionListMemberRequest>"
                )
            ]
        )

        RemoveDistributionListMembersResponse = requests.post(
            self.__AdminHost
            + "/service/admin/soap/RemoveDistributionListMemberRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        if RemoveDistributionListMembersResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(RemoveDistributionListMembersResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def RenameDistributionList(
        self, newName: str, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if distrListID == "":
            distrListData = self.GetDistributionList(distrListName=distrListName)
            if distrListData.IsError():
                return distrListData

            distrListID = distrListData.GetData()["id"]

        RequestData = self.__WrapInSoapTemplate(
            [
                (
                    '<RenameDistributionListRequest xmlns="urn:zimbraAdmin">'
                        f"<id>{distrListID}</id>"
                        f"<newName>{newName}</newName>"
                    f"</RenameDistributionListRequest>"
                )
            ]
        )

        RenameDistributionListResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/RenameDistributionListRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(RenameDistributionListResponse.text)["Body"]

        if RenameDistributionListResponse.status_code == 200:
            data = dict()

            dlData = jsonResponseData["RenameDistributionListResponse"]["dl"][0]

            data["name"] = dlData["name"]
            data["id"] = dlData["id"]

            result.SetData(data)
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    ################################################## DEV METHODS ##################################################

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
