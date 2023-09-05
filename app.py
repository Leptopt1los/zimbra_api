# %%
from flask import Flask, request
from ZimbraAPI import ZimbraAPI, ResponseData
from config import host, adminUsername, adminPassword, hmac_key
from time import time
import hmac, hashlib


def check_HMAC(timestamp: str, data: list, hmac_sign: str) -> bool:
    current_timestamp = int(time())
    if abs(current_timestamp - int(timestamp)) > 30:
        return False
    return (
        str(
            hmac.new(
                hmac_key,
                f'{timestamp}{"".join(data)}'.encode("utf-8"),
                hashlib.sha3_512,
            ).hexdigest()
        )
        == hmac_sign
    )


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

Zimbra = ZimbraAPI(host, adminUsername, adminPassword)


@app.route("/createAccount", methods=["POST"])
def CreateAccount():
    accountName: str = request.form.get("accountName")
    password: str = request.form.get("password")
    name: str = request.form.get("name")
    surname: str = request.form.get("surname")
    patronymic: str = request.form.get("patronymic")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if None in [accountName, password, name, surname, patronymic, timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(
        timestamp, [accountName, password, name, surname, patronymic], hmac_sign
    ):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.CreateAccount(
        accountName, password, name, patronymic, surname
    ).asdict()
    return result


@app.route("/deleteAccount", methods=["POST"])
def DeleteAccount():
    accountID: str = request.form.get("accountID", "")
    accountName: str = request.form.get("accountName", "")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if (None in [accountID, accountName, timestamp, hmac_sign]) or (
        accountID == accountName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(timestamp, [accountID, accountName], hmac_sign):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.DeleteAccount(accountID, accountName).asdict()
    return result


@app.route("/getAccountInfo", methods=["POST"])
def GetAccountInfo():
    accountName: str = request.form.get("accountName")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if None in [accountName, timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(timestamp, [accountName], hmac_sign):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetAccountInfoByName(accountName).asdict()
    return result


@app.route("/getMessages", methods=["POST"])
def GetMessages():
    accountName: str = request.form.get("accountName")
    unreadOnly: str = str(request.form.get("unreadOnly", default=""))

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if None in [accountName, timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(timestamp, [accountName, unreadOnly], hmac_sign):
        return ResponseData.GetHMACError().asdict()

    unreadOnly = False if unreadOnly.lower() in ["false", "0"] else True

    result = Zimbra.GetMessages(accountName, unreadOnly).asdict()
    return result


@app.route("/getPreauthLink", methods=["POST"])
def GetPreauthLink():
    accountName: str = request.form.get("accountName")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if None in [accountName, timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(timestamp, [accountName], hmac_sign):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetPreauthLink(accountName).asdict()
    return result


@app.route("/getDistributionLists", methods=["POST"])
def GetDistributionLists():
    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if None in [timestamp, hmac_sign]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(timestamp, [""], hmac_sign):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.GetDistributionLists().asdict()
    return result


@app.route("/createDistributionList", methods=["POST"])
def CreateDistributionList():
    name: str = request.form.get("name")
    displayName: str = request.form.get("displayName")
    description: str = request.form.get("description", default="")
    subscriptionPolicy: str = request.form.get("subscriptionPolicy", default="")
    unsubscriptionPolicy: str = request.form.get("unsubscriptionPolicy", default="")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if None in [
        name,
        displayName,
        description,
        subscriptionPolicy,
        unsubscriptionPolicy,
        timestamp,
        hmac_sign,
    ]:
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(
        timestamp,
        [name, displayName, description, subscriptionPolicy, unsubscriptionPolicy],
        hmac_sign,
    ):
        return ResponseData.GetHMACError().asdict()

    subscriptionPolicy = "APPROVAL" if subscriptionPolicy == "" else subscriptionPolicy
    unsubscriptionPolicy = (
        "ACCEPT" if unsubscriptionPolicy == "" else unsubscriptionPolicy
    )

    result = Zimbra.CreateDistributionList(
        name, displayName, description, subscriptionPolicy, unsubscriptionPolicy
    ).asdict()
    return result


@app.route("/deleteDistributionList", methods=["POST"])
def DeleteDistributionListByID():
    distrListID: str = request.form.get("distrListID", "")
    distrListName: str = request.form.get("distrListName", "")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if (None in [distrListID, distrListName, timestamp, hmac_sign]) or (
        distrListID == distrListName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(timestamp, [distrListID, distrListName], hmac_sign):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.DeleteDistributionList(distrListID, distrListName).asdict()
    return result


@app.route("/addDistributionListMembers", methods=["POST"])
def AddDistributionListMembers():
    distrListID: str = request.form.get("distrListID", "")
    distrListName: str = request.form.get("distrListName", "")
    userEmails: list = request.form.get("userEmails")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if (None in [distrListID, "".join(userEmails), timestamp, hmac_sign]) or (
        distrListID == distrListName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(
        timestamp, [distrListID, distrListName, "".join(userEmails)], hmac_sign
    ):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.AddDistributionListMembers(
        userEmails, distrListID, distrListName
    ).asdict()
    return result


@app.route("/removeDistributionListMembers", methods=["POST"])
def RemoveDistributionListMembers():
    distrListID: str = request.form.get("distrListID", "")
    distrListName: str = request.form.get("distrListName", "")
    userEmails: list = request.form.get("userEmails")

    timestamp: str = request.form.get("timestamp")
    hmac_sign: str = request.form.get("hmac_sign")

    if (None in [distrListID, "".join(userEmails), timestamp, hmac_sign]) or (
        distrListID == distrListName == ""
    ):
        return ResponseData.GetMissingDataError().asdict()

    if not check_HMAC(
        timestamp, [distrListID, distrListName, "".join(userEmails)], hmac_sign
    ):
        return ResponseData.GetHMACError().asdict()

    result = Zimbra.AddDistributionListMembers(
        userEmails, distrListID, distrListName
    ).asdict()
    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0")
