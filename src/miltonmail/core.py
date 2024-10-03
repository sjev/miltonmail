import imaplib
import email
from email.header import decode_header
from typing import List


def login_to_imap(
    server: str, username: str, password: str, port: int = 993
) -> imaplib.IMAP4_SSL:
    try:
        connection = imaplib.IMAP4_SSL(server, port)
        connection.login(username, password)
        return connection
    except imaplib.IMAP4.error as e:
        raise ConnectionError(f"Failed to login to IMAP server: {e}") from e


def list_folders(connection: imaplib.IMAP4_SSL) -> List[str]:
    status, folders = connection.list()
    if status != "OK":
        raise RuntimeError("Failed to list folders")

    folder_list = []
    for folder in folders:
        if isinstance(folder, bytes):
            folder_name = folder.decode().split(' "/" ')[-1]
            folder_list.append(folder_name)

    return folder_list


def get_messages_from_folder(
    connection: imaplib.IMAP4_SSL, folder: str, limit: int = 10
) -> List:
    status, messages = connection.select(folder)  # pylint: disable=unused-variable
    if status != "OK":
        raise RuntimeError(f"Failed to select folder: {folder}")

    status, message_ids = connection.search(None, "ALL")
    if status != "OK":
        raise RuntimeError(f"Failed to fetch message list from folder: {folder}")

    message_ids = message_ids[0].split()

    messages_list = []
    for message_id in message_ids[-limit:]:
        status, msg_data = connection.fetch(message_id, "(RFC822)")
        if status != "OK":
            raise RuntimeError(f"Failed to fetch message with ID: {message_id}")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                from_ = msg.get("From")

                messages_list.append((subject, from_))

    return messages_list
