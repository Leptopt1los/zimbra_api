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
        self, accountName: str, password: str, name: str, surname: str, patronymic: str
    ) -> ResponseData:
        name = name.encode("ascii", errors="xmlcharrefreplace").decode()
        surname = surname.encode("ascii", errors="xmlcharrefreplace").decode()
        patronymic = patronymic.encode("ascii", errors="xmlcharrefreplace").decode()

        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()
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

        if CreateAccountResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(CreateAccountResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def DeleteAccount(self, accountID: str = "", accountName: str = "") -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        if accountID == "":
            accInfo = self.GetAccountInfo(accountName=accountName)
            if accInfo.IsError():
                return accInfo
            if not accInfo.GetData()["exists"]:
                result.SetErrorCode("NO_SUCH_MAILBOX")
                return result
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

    def GetAccountInfo(
        self, accountID: str = "", accountName: str = ""
    ) -> ResponseData:
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

        jsonResponseData = json.loads(AccountInfoResponse.text)["Body"]

        data = {}
        try:
            tempDataArray = jsonResponseData["BatchResponse"]["GetAccountResponse"]
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

        return result

    def GetAccountMembership(
        self, accountID: str = "", accountName: str = ""
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        requestStr = ""
        if accountName == "":
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
            if "dl" in jsonResponseData["GetAccountMembershipResponse"]:
                for distrList in jsonResponseData["GetAccountMembershipResponse"]["dl"]:
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

            data = {"messages": []}
            if "m" in jsonResponseData:
                data["count"] = len(jsonResponseData["m"])
                for message in jsonResponseData["m"][:10]:
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
            result.SetErrorText(GetMessagesResponse.text)
            if GetMessagesResponse.status_code == 404:
                result.SetErrorCode("NO_SUCH_MAILBOX")
            else:
                result.SetErrorCode("UNEXPECTED_ERROR")

        return result

    def GetPreauthLink(
        self, accountID: str = "", accountName: str = ""
    ) -> ResponseData:
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

        PreauthResponse = requests.post(
            self.__AdminHost + "/service/admin/soap/DelegateAuthRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        jsonResponseData = json.loads(PreauthResponse.text)["Body"]

        if PreauthResponse.status_code == 200:
            preauthToken = jsonResponseData["DelegateAuthResponse"]["authToken"][0][
                "_content"
            ]
            result.SetData(
                {
                    "url": self.__Host
                    + f"/service/preauth?authtoken={preauthToken}&isredirect=1"
                }
            )
        else:
            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    ################################################## DISTRIBUTION LIST MANAGEMENT ##################################################

    def CreateDistributionList(
        self,
        name: str,
        displayName: str,
        description: str = "",
        subscriptionPolicy: str = "APPROVAL",
        unsubscriptionPolicy: str = "ACCEPT",
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

        displayName = displayName.encode("ascii", errors="xmlcharrefreplace").decode()
        description = description.encode("ascii", errors="xmlcharrefreplace").decode()

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

        jsonResponseData = json.loads(CreateDistrListResponse.text)["Body"]

        if CreateDistrListResponse.status_code == 200:
            id = jsonResponseData["CreateDistributionListResponse"]["dl"][0]["id"]
            result.SetData({"id": id})
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

        if DeleteDistrListResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(DeleteDistrListResponse.text)["Body"]

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

            data["name"] = jsonResponseData["GetDistributionListResponse"]["dl"]["name"]
            data["id"] = jsonResponseData["GetDistributionListResponse"]["dl"]["id"]

            members = dict()

            if "dlm" in jsonResponseData["GetDistributionListResponse"]["dl"]:
                for member in jsonResponseData["GetDistributionListResponse"]["dl"][
                    "dlm"
                ]:
                    members[member["_content"]] = "member"

            data["members"] = members

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

        jsonResponseData = json.loads(GetDistrListsResponse.text)["Body"]

        if GetDistrListsResponse.status_code == 200:
            data = dict()
            if "dl" in jsonResponseData["SearchDirectoryResponse"]:
                for distrList in jsonResponseData["SearchDirectoryResponse"]["dl"]:
                    bDistrList = {}
                    bDistrList["id"] = distrList["id"]
                    for attr in distrList["a"]:
                        bDistrList[attr["n"]] = attr["_content"]
                    if "owners" in distrList:
                        bDistrList["owner"] = distrList["owners"][0]["owner"][0]
                    data[distrList["name"]] = bDistrList

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
            if "dl" in jsonResponseData["GetDistributionListMembershipResponse"]:
                for distrList in jsonResponseData[
                    "GetDistributionListMembershipResponse"
                ]["dl"]:
                    item = dict()
                    item["id"] = distrList["id"]
                    item["via"] = distrList["via"] if "via" in distrList else "DIRECT"
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
            self.__AdminHost + "/service/admin/soap/AddDistributionListMemberRequest",
            data=RequestData,
            cookies=self.__GetCookies(),
            verify=False,
        )

        if AddDistrListMembersResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(AddDistrListMembersResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def RemoveDistributionListMembers(
        self, distrListID: str, usersEmail: list
    ) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

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

        if AddDistrListMembersResponse.status_code == 200:
            result.SetData({"success": True})
        else:
            jsonResponseData = json.loads(AddDistrListMembersResponse.text)["Body"]

            result.SetErrorText(jsonResponseData["Fault"]["Reason"]["Text"])
            result.SetErrorCode(jsonResponseData["Fault"]["Detail"]["Error"]["Code"])

        return result

    def __RenameDistributionList(self, distrListID: str, newName: str) -> ResponseData:
        UpdateAuthDataStatus = self.__UpdateAuthData()
        if UpdateAuthDataStatus.IsError():
            return UpdateAuthDataStatus

        result = ResponseData()

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

        jsonResponseData = json.loads(CreateDistrListResponse.text)["Body"]

        if CreateDistrListResponse.status_code == 200:
            id = jsonResponseData["CreateDistributionListResponse"]["dl"][0]["id"]
            result.SetData({"id": id})
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
