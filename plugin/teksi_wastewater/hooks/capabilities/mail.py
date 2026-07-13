from dataclasses import dataclass


@dataclass(slots=True)
class MailCapability:

    def send(
        self,
        receiver: str,
        subject: str,
        body: str,
    ):
        pass