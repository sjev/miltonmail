import logging
import imaplib
import email
from email.header import decode_header
from email.message import Message  # Correct import
from typing import List
from pathlib import Path


log = logging.getLogger(__name__)


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
        log.debug(f"{folder=}")
        if isinstance(folder, bytes):
            folder_name = folder.decode().split(" ")[-1]
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


def decode_mime_words(text: str) -> str:
    """Decodes MIME encoded words (=?UTF-8?B?....?=) into a readable string."""
    decoded_fragments = []
    for fragment, encoding in decode_header(text):
        if isinstance(fragment, bytes):
            fragment = fragment.decode(encoding if encoding else "utf-8")
        decoded_fragments.append(fragment)
    return "".join(decoded_fragments)


def save_attachments_from_message(message: Message, output_dir: Path) -> None:
    """
    Save attachments from an email message to the specified directory.
    Skip the attachment if it already exists in the folder.

    :param message: The email message object.
    :param output_dir: The directory to save attachments.
    """
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure output directory exists

    for part in message.walk():
        # Check if the part is an attachment
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            if filename:
                # Decode the filename if it's MIME-encoded
                filename = decode_mime_words(filename)

                filepath = output_dir / filename

                # Check if the file already exists
                if filepath.exists():
                    log.info(f"Attachment already exists: {filename}, skipping...")
                    continue

                # Save the attachment
                with open(filepath, "wb") as f:
                    payload = part.get_payload(decode=True)
                    if payload is not None:
                        f.write(payload)

                log.info(f"Saved attachment: {filename} to {output_dir}")


def download_attachments_from_folder(
    connection: imaplib.IMAP4_SSL, folder: str, output_dir: Path
) -> None:
    """
    Download attachments from the specified folder.
    """
    log.info(f"Downloading attachments from {folder} to {output_dir}")
    status, messages = connection.select(folder)  # pylint: disable=unused-variable
    if status != "OK":
        raise RuntimeError(f"Failed to select folder: {folder}")

    status, message_ids = connection.search(None, "ALL")
    if status != "OK":
        raise RuntimeError(f"Failed to fetch message list from folder: {folder}")

    message_ids = message_ids[0].split()

    log.info(f"Found {len(message_ids)} messages in folder: {folder}")

    for message_id in message_ids:
        status, msg_data = connection.fetch(message_id, "(RFC822)")
        if status != "OK":
            raise RuntimeError(f"Failed to fetch message with ID: {message_id}")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                save_attachments_from_message(message, output_dir)
