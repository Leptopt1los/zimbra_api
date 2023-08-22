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