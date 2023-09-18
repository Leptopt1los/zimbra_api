# %%
from flask import Flask, request
from ZimbraAPI import ZimbraAPI, ResponseData
from config import host, adminUsername, adminPassword, hmac_key
from time import time
import hmac, hashlib
import json


def check_HMAC(data: dict) -> bool:
    hmac_sign = data.pop("hmac_sign")
    datastr = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    current_timestamp = int(time())
    if abs(current_timestamp - data["timestamp"]) > 30:
        return False

    calculated_hmac = str(
        hmac.new(
            hmac_key,
            datastr.encode("utf-8"),
            hashlib.sha3_512,
        ).hexdigest()
    )
    return calculated_hmac == hmac_sign


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

Zimbra = ZimbraAPI(host, adminUsername, adminPassword)


################################################## ACCOUNT MANAGEMENT ##################################################


@app.route("/createAccount", methods=["POST"])
def CreateAccount():
    data = request.json

    accountName: str = data.get("accountName")
    password: str = data.get("password")
    name: str = data.get("name")
    surname: str = data.get("surname")
    patronymic: str = data.get("patronymic", "")
    params: dict = data.get(
        "params",
        {
            "zimbraAccountStatus": "active",
            "zimbraFeatureCalendarEnabled": "FALSE",
            "zimbraFeatureTasksEnabled": "FALSE",
            "zimbraFeatureBriefcasesEnabled": "FALSE",
            "zimbraFeatureOptionsEnabled": "FALSE",
            "zimbraFeatureSharingEnabled": "FALSE",
            "zimbraFeatureManageZimlets": "FALSE",
            "zimbraFeatureGalEnabled": "FALSE",
            "zimbraFeatureGalAutoCompleteEnabled": "FALSE",
            "zimbraPrefGalAutoCompleteEnabled": "FALSE",
            "zimbraFeatureChangePasswordEnabled": "FALSE",
            "zimbraMailForwardingAddressMaxNumAddrs": 5,
            "zimbraMailQuota": 524288000,
        },
    )

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if None in [accountName, password, name, surname, timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.CreateAccount(
        accountName, password, name, surname, patronymic, params
    ).asdict()
    return result


@app.route("/deleteAccount", methods=["POST"])
def DeleteAccount():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [timestamp, hmac_sign]) or (accountID == accountName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.DeleteAccount(accountID, accountName).asdict()
    return result


@app.route("/modifyAccount", methods=["POST"])
def ModifyAccount():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")
    params: dict = data.get("params")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [params, timestamp, hmac_sign]) or (accountID == accountName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.ModifyAccount(params, accountID, accountName).asdict()
    return result


@app.route("/renameAccount", methods=["POST"])
def RenameAccount():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")
    newName: str = data.get("newName")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [newName, timestamp, hmac_sign]) or (accountID == accountName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.RenameAccount(newName, accountID, accountName).asdict()
    return result


@app.route("/setPassword", methods=["POST"])
def SetPassword():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")
    newPassword: str = data.get("newPassword")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [newPassword, timestamp, hmac_sign]) or (
        accountID == accountName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.SetPassword(newPassword, accountID, accountName).asdict()
    return result


@app.route("/getAccount", methods=["POST"])
def GetAccount():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [timestamp, hmac_sign]) or (accountID == accountName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetAccount(accountID, accountName).asdict()
    return result


@app.route("/getAccounts", methods=["POST"])
def GetAccounts():
    data = request.json

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if None in [timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetAccounts().asdict()
    return result


@app.route("/getAccountMembership", methods=["POST"])
def GetAccountMembership():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [timestamp, hmac_sign]) or (accountID == accountName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetAccountMembership(accountID, accountName).asdict()
    return result


################################################## MAILBOX MANAGEMENT ##################################################


@app.route("/getMessages", methods=["POST"])
def GetMessages():
    data = request.json

    accountName: str = data.get("accountName")
    unreadOnly: bool = data.get("unreadOnly", True)

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if None in [accountName, timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetMessages(accountName, unreadOnly).asdict()
    return result


@app.route("/getPreauthLink", methods=["POST"])
def GetPreauthLink():
    data = request.json

    accountID: str = data.get("accountID", "")
    accountName: str = data.get("accountName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [accountName, timestamp, hmac_sign]) or (
        accountID == accountName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetPreauthLink(accountID, accountName).asdict()
    return result


################################################## DISTRIBUTION LIST MANAGEMENT ##################################################


@app.route("/getDistributionLists", methods=["POST"])
def GetDistributionLists():
    data = request.json

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if None in [timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetDistributionLists().asdict()
    return result


@app.route("/getDistributionList", methods=["POST"])
def GetDistributionList():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [timestamp, hmac_sign]) and (distrListID == distrListName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetDistributionList(distrListID, distrListName).asdict()
    return result


@app.route("/getDistributionListMembership", methods=["POST"])
def GetDistributionListMembership():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [timestamp, hmac_sign]) or (distrListID == distrListName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetDistributionListMembership(distrListID, distrListName).asdict()
    return result


@app.route("/createDistributionList", methods=["POST"])
def CreateDistributionList():
    data = request.json

    name: str = data.get("name")
    displayName: str = data.get("displayName", "")
    params: dict = data.get(
        "params",
        {
            "zimbraMailStatus": "enabled",
            "zimbraDistributionListSubscriptionPolicy": "REJECT",
            "zimbraDistributionListUnsubscriptionPolicy": "REJECT",
        },
    )

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if None in [
        name,
        timestamp,
        hmac_sign,
    ]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.CreateDistributionList(name, displayName, params).asdict()
    return result


@app.route("/deleteDistributionList", methods=["POST"])
def DeleteDistributionList():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [timestamp, hmac_sign]) or (distrListID == distrListName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.DeleteDistributionList(distrListID, distrListName).asdict()
    return result


@app.route("/modifyDistributionList", methods=["POST"])
def ModifyDistributionList():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")
    params: dict = data.get("params")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [params, timestamp, hmac_sign]) or (distrListID == distrListName == ""):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.ModifyDistributionList(params, distrListID, distrListName).asdict()
    return result


@app.route("/renameDistributionList", methods=["POST"])
def RenameDistributionList():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")
    newName: str = data.get("newName")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [newName, timestamp, hmac_sign]) or (
        distrListID == distrListName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.RenameDistributionList(newName, distrListID, distrListName).asdict()
    return result


@app.route("/addDistributionListMembers", methods=["POST"])
def AddDistributionListMembers():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")
    userEmails: list = data.get("userEmails")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [userEmails, timestamp, hmac_sign]) or (
        distrListID == distrListName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.AddDistributionListMembers(
        userEmails, distrListID, distrListName
    ).asdict()
    return result


@app.route("/removeDistributionListMembers", methods=["POST"])
def RemoveDistributionListMembers():
    data = request.json

    distrListID: str = data.get("distrListID", "")
    distrListName: str = data.get("distrListName", "")
    userEmails: list = data.get("userEmails")

    timestamp: str = data.get("timestamp")
    hmac_sign: str = data.get("hmac_sign")

    if (None in [userEmails, timestamp, hmac_sign]) or (
        distrListID == distrListName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(data):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.RemoveDistributionListMembers(
        userEmails, distrListID, distrListName
    ).asdict()
    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0")
