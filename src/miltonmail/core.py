import logging
import imaplib
import email
from email.header import decode_header
from email.message import Message
from typing import List
from pathlib import Path
import re
from datetime import datetime

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


def select_folder(connection: imaplib.IMAP4_SSL, folder: str) -> None:
    """
    Selects the folder, handling spaces and special characters by quoting the folder name.
    """
    folder = f'"{folder}"' if " " in folder or "/" in folder else folder
    status, messages = connection.select(folder)  # pylint: disable=unused-variable
    if status != "OK":
        raise RuntimeError(f"Failed to select folder: {folder}")
    log.info(f"Successfully selected folder: {folder}")


def get_messages_from_folder(
    connection: imaplib.IMAP4_SSL, folder: str, limit: int = 10
) -> List:
    select_folder(connection, folder)

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


def format_filename_with_date(message: Message, filename: str) -> str:
    """
    Formats the filename by prepending the date and replacing spaces with underscores.
    """
    date = email.utils.parsedate_to_datetime(message["Date"]).strftime("%Y%m%d")

    filename = filename.replace(" ", "_")
    formatted_filename = f"{date}_{filename}"

    formatted_filename = re.sub(r"[^A-Za-z0-9_.-]", "", formatted_filename)

    return formatted_filename


def save_attachments_from_message(message: Message, output_dir: Path) -> None:
    """
    Save attachments from an email message to the specified directory.
    Skip the attachment if it already exists in the folder.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            if filename:
                filename = decode_mime_words(filename)
                filename = format_filename_with_date(message, filename)

                filepath = output_dir / filename

                if filepath.exists():
                    log.info(f"Attachment already exists: {filename}, skipping...")
                    continue

                with open(filepath, "wb") as f:
                    payload = part.get_payload(decode=True)
                    if payload:
                        f.write(payload)

                log.info(f"Saved attachment: {filename} to {output_dir}")


def download_attachments_from_folder(
    connection: imaplib.IMAP4_SSL,
    folder: str,
    output_dir: Path,
    cutoff_date: str = "20220101",
) -> None:
    """
    Download attachments from emails in the specified folder that are newer than the given cutoff date.

    Parameters
    ----------
    connection : imaplib.IMAP4_SSL
        The IMAP connection object.
    folder : str
        The folder to download attachments from (e.g., "INBOX").
    output_dir : Path
        The directory where attachments should be saved.
    cutoff_date : str
        The cutoff date in 'YYYYMMDD' format. Only messages after this date will be processed.
    """
    log.info(f"Downloading attachments from {folder} to {output_dir}")

    # Select the folder, handle folder names with spaces
    select_folder(connection, folder)

    cutoff_datetime = datetime.strptime(cutoff_date, "%Y%m%d")
    imap_cutoff_date = cutoff_datetime.strftime("%d-%b-%Y")

    search_query = f"SINCE {imap_cutoff_date}"
    status, message_ids = connection.search(None, search_query)
    if status != "OK":
        raise RuntimeError(f"Failed to search for messages in {folder}")

    message_ids = message_ids[0].split()

    if not message_ids:
        log.info(f"No messages found after {cutoff_date}.")
        return

    log.info(
        f"Found {len(message_ids)} messages after {cutoff_date} in folder: {folder}"
    )

    message_ids.reverse()

    for message_id in message_ids:
        status, msg_data = connection.fetch(message_id, "(RFC822)")
        if status != "OK":
            raise RuntimeError(f"Failed to fetch message with ID: {message_id}")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                save_attachments_from_message(message, output_dir)
