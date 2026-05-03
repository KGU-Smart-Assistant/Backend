from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    department_id: str
    department_name: str
    phone_number: str

    @property
    def tel_uri(self) -> str:
        digits = "".join(char for char in self.phone_number if char.isdigit())
        return f"tel:{digits}"

    def to_dict(self) -> dict[str, str]:
        return {
            "department_id": self.department_id,
            "department_name": self.department_name,
            "phone_number": self.phone_number,
            "tel_uri": self.tel_uri,
        }

# 전화번호 수정할 것
CONTACTS = [
    Contact(
        department_id="academic_affairs",
        department_name="학사지원팀",
        phone_number="031-249-0000",
    ),
    Contact(
        department_id="student_support",
        department_name="학생지원팀",
        phone_number="031-249-1111",
    ),
    Contact(
        department_id="admissions",
        department_name="입학관리팀",
        phone_number="031-249-2222",
    ),
]


def list_department_contacts() -> list[dict[str, str]]:
    return [contact.to_dict() for contact in CONTACTS]


def get_department_contact(department_id: str) -> dict[str, str] | None:
    for contact in CONTACTS:
        if contact.department_id == department_id:
            return contact.to_dict()
    return None
