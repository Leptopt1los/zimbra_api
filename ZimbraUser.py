class ZimbraUser:
    def __init__(
        self, email: str, password: str, name: str, patronymic: str, surname: str
    ) -> None:
        self.SetEmail(email)
        self.SetPassword(password)
        self.SetName(name)
        self.SetPatronymic(patronymic)
        self.SetSurname(surname)

    def SetEmail(self, email: str) -> None:
        self.__email = email

    def SetPassword(self, password: str) -> None:
        self.__password = password

    def SetName(self, name: str) -> None:
        self.__name = name.encode("ascii", errors="xmlcharrefreplace").decode()

    def SetSurname(self, surname: str) -> None:
        self.__surname = surname.encode("ascii", errors="xmlcharrefreplace").decode()

    def SetPatronymic(self, patronymic: str) -> None:
        self.__patronymic = patronymic.encode(
            "ascii", errors="xmlcharrefreplace"
        ).decode()

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
