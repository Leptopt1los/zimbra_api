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

    def CreateAccount(self, accountName:str, password:str, name:str, surname:str, patronymic:str) -> ResponseData:
        name = name.encode("ascii", errors="xmlcharrefreplace").decode()
        surname = surname.encode("ascii", errors="xmlcharrefreplace").decode()
        patronymic = patronymic.encode("ascii", errors="xmlcharrefreplace").decode()
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = self.__WrapInSoapTemplate(
                [
                    (
                        '<CreateAccountRequest xmlns="urn:zimbraAdmin">'
                            f"<name>{accountName}</name>"
                            f"<password>{password}</password>"
                            '<a n="zimbraAccountStatus">active</a>'
                            f'<a n="displayName">{surname} {name} {patronymic}</a>'
                            f'<a n="givenName">{name}</a>'
                            f'<a n="initials">{patronymic}</a>'
                            f'<a n="sn">{surname}</a>'
                            '<a n="zimbraPasswordMustChange">FALSE</a>'
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
            result.SetData({"success": True})
        else:
            result = UpdateAuthDataStatus

        return result

    def DeleteAccount(self, accountID: str = "", accountName: str = "") -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            if accountID == "":
                accInfo = self.GetAccountInfoByName(accountName)
                if accInfo.IsError():
                    return accInfo
                if not accInfo.GetData()["exists"]:
                    result.SetErrorCode("NO_SUCH_MAILBOX")
                    return result
                accountID = accInfo.GetData()['id']

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
                result.SetData({"success": True})
        else:
            result = UpdateAuthDataStatus

        return result

    def GetAccountInfoByName(self, accountName: str) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        result = ResponseData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = self.__WrapInSoapTemplate(
                [
                    (
                        '<BatchRequest xmlns="urn:zimbra" onerror="continue">'
                            '<GetAccountRequest xmlns="urn:zimbraAdmin" applyCos="0">'
                                f'<account by="name">{accountName}</account>'
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
                data = {"messages": []}
                if "m" in response:
                    data["count"] = len(response["m"])
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
                    data["count"] = 0
                result.SetData(data)
        else:
            result = UpdateAuthDataStatus

        return result

    def GetPreauthLink(self, email: str) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = self.__WrapInSoapTemplate(
                [
                    (
                        '<DelegateAuthRequest xmlns="urn:zimbraAdmin">'
                            f'<account by="name">{email}</account>'
                        "</DelegateAuthRequest>"
                    )
                ]
            )
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
                result.SetErrorCode(
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

    def CreateDistributionList(
        self,
        name: str,
        displayName: str,
        description: str = "",
        subscriptionPolicy: str = "APPROVAL",
        unsubscriptionPolicy: str = "ACCEPT",
    ) -> ResponseData:
        result = ResponseData()
        displayName = displayName.encode("ascii", errors="xmlcharrefreplace").decode()
        description = description.encode("ascii", errors="xmlcharrefreplace").decode()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = self.__WrapInSoapTemplate(
                [
                    (
                        '<CreateDistributionListRequest xmlns="urn:zimbraAdmin">'
                            f"<name>{name}</name>"
                            '<a n="zimbraMailStatus">enabled</a>'
                            f'<a n="displayName">{displayName}</a>'
                            f'<a n="description">{description}</a>'
                            f'<a n="zimbraDistributionListSubscriptionPolicy">{subscriptionPolicy}</a>'
                            f'<a n="zimbraDistributionListUnsubscriptionPolicy">{unsubscriptionPolicy}</a>'
                        "</CreateDistributionListRequest>"
                    )
                ]
            )
            CreateDistrListResponse = requests.post(
                self.__AdminHost + "/service/admin/soap/CreateDistributionListRequest",
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(CreateDistrListResponse.status_code)
            if CreateDistrListResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(CreateDistrListResponse.text)["Body"]["Fault"]["Reason"][
                        "Text"
                    ]
                )
                result.SetErrorCode(
                    json.loads(CreateDistrListResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
            else:
                id = json.loads(CreateDistrListResponse.text)["Body"][
                    "CreateDistributionListResponse"
                ]["dl"][0]["id"]
                result.SetData({"id": id})
        else:
            result = UpdateAuthDataStatus
        return result

    def DeleteDistributionList(
        self, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            if distrListID == "":
                distrListID = self.GetDistributionLists().GetData()[distrListName]["id"]

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
            result.SetStatusCode(DeleteDistrListResponse.status_code)
            if DeleteDistrListResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(DeleteDistrListResponse.text)["Body"]["Fault"]["Reason"][
                        "Text"
                    ]
                )
                result.SetErrorCode(
                    json.loads(DeleteDistrListResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
            else:
                result.SetData({"success": True})
        else:
            result = UpdateAuthDataStatus
        return result

    def GetDistributionLists(self) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            RequestData = self.__WrapInSoapTemplate(
                [
                    (
                        '<SearchDirectoryRequest xmlns="urn:zimbraAdmin" offset="0" sortBy="name" sortAscending="1" applyCos="false" applyConfig="false" attrs="displayName,uid,description" types="distributionlists,dynamicgroups">'
                            "<query>(&amp;(!(zimbraIsSystemAccount=TRUE)))</query>"
                        "</SearchDirectoryRequest>"
                    )
                ]
            )
            GetDistrListsResponse = requests.post(
                self.__AdminHost + "/service/admin/soap/SearchDirectoryRequest",
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(GetDistrListsResponse.status_code)
            if GetDistrListsResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(GetDistrListsResponse.text)["Body"]["Fault"]["Reason"][
                        "Text"
                    ]
                )
                result.SetErrorCode(
                    json.loads(GetDistrListsResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
            else:
                data = dict()
                try:
                    jsonResp = json.loads(GetDistrListsResponse.text)["Body"][
                        "SearchDirectoryResponse"
                    ]["dl"]
                    for distrList in jsonResp:
                        bDistrList = {}
                        bDistrList["id"] = distrList["id"]
                        for attr in distrList["a"]:
                            bDistrList[attr["n"]] = attr["_content"]
                        if "owners" in distrList:
                            bDistrList["owner"] = distrList["owners"][0]["owner"][0]
                        data[distrList["name"]] = bDistrList
                except:
                    pass
                result.SetData(data)
        else:
            result = UpdateAuthDataStatus
        return result

    def AddDistributionListMembers(
        self, userEmails: list, distrListID: str = "", distrListName: str = ""
    ) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            if distrListID == "":
                distrListID = self.GetDistributionLists().GetData()[distrListName]["id"]

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
            AddDistrListMembersResponse = requests.post(
                self.__AdminHost
                + "/service/admin/soap/AddDistributionListMemberRequest",
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(AddDistrListMembersResponse.status_code)
            if AddDistrListMembersResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(AddDistrListMembersResponse.text)["Body"]["Fault"][
                        "Reason"
                    ]["Text"]
                )
                result.SetErrorCode(
                    json.loads(AddDistrListMembersResponse.text)["Body"]["Fault"][
                        "Detail"
                    ]["Error"]["Code"]
                )
            else:
                result.SetData({"success": True})
        else:
            result = UpdateAuthDataStatus
        return result

    def RemoveDistributionListMembers(
        self, distrListID: str, usersEmail: list
    ) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
            usersRequestStr = ""
            for user in usersEmail:
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
            AddDistrListMembersResponse = requests.post(
                self.__AdminHost
                + "/service/admin/soap/RemoveDistributionListMemberRequest",
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(AddDistrListMembersResponse.status_code)
            if AddDistrListMembersResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(AddDistrListMembersResponse.text)["Body"]["Fault"][
                        "Reason"
                    ]["Text"]
                )
                result.SetErrorCode(
                    json.loads(AddDistrListMembersResponse.text)["Body"]["Fault"][
                        "Detail"
                    ]["Error"]["Code"]
                )
            else:
                result.SetData({"success": True})
        else:
            result = UpdateAuthDataStatus
        return result

    def __RenameDistributionList(self, distrListID: str, newName: str) -> ResponseData:
        result = ResponseData()
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if not UpdateAuthDataStatus.IsError():
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
            CreateDistrListResponse = requests.post(
                self.__AdminHost + "/service/admin/soap/RenameDistributionListRequest",
                data=RequestData,
                cookies=self.__GetCookies(),
                verify=False,
            )
            result.SetStatusCode(CreateDistrListResponse.status_code)
            if CreateDistrListResponse.status_code != 200:
                result.SetErrorText(
                    json.loads(CreateDistrListResponse.text)["Body"]["Fault"]["Reason"][
                        "Text"
                    ]
                )
                result.SetErrorCode(
                    json.loads(CreateDistrListResponse.text)["Body"]["Fault"]["Detail"][
                        "Error"
                    ]["Code"]
                )
            else:
                id = json.loads(CreateDistrListResponse.text)["Body"][
                    "CreateDistributionListResponse"
                ]["dl"][0]["id"]
                result.SetData({"id": id})
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
