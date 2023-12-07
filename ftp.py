import ftplib
import os.path
import log
from ftplib import FTP
from configparser import ConfigParser

config = ConfigParser()
config.read("ftp.ini")
SERVER_ADDRESS = config["ftp"]["server_address"]
USERNAME = config["ftp"]["username"]
PASSWORD = config["ftp"]["password"]
FTP_JSON_DIR = "public_html/json"
FTP_POLL_DIR = "public_html/poll"
FTP_POLL_FILE = "scanner_requests.csv"  # this doesn't NEED to be a .csv
LOCAL_JSON_DIR = "json/"
SESSION_STORAGE_FILE_DICT = {}
SESSION_STORAGE_LIMIT = 5242880  # 5 MiB (mebibyte)


def exceeded_session_storage(file_to_send: str) -> bool:
    # make sure we do not exceed the session storage limit before sending the files
    try:
        size = os.path.getsize(LOCAL_JSON_DIR + file_to_send)
    except OSError as e:
        log.warn(str(e), ": Unable to check file size, sending file anyway.")
        return True
    SESSION_STORAGE_FILE_DICT[file_to_send] = size
    return SESSION_STORAGE_LIMIT < sum(SESSION_STORAGE_FILE_DICT.values())


def send_file(file_to_send: str) -> str:
    """Sends a file to our FTP server.

    Calling code should ensure the file exists in the same directory and that it is formatted correctly for JSON syntax.

    Args:
        file_to_send: A string that is the file name with the extension. Example: "Cooking.json".

    Returns:
        A string that is the status of the upload. Examples:
        "226-File successfully transferred"
        "530 Login authentication failed"
    """
    try:
        with FTP(SERVER_ADDRESS, USERNAME, PASSWORD) as ftp, open(LOCAL_JSON_DIR + file_to_send, 'rb') as file:
            if not exceeded_session_storage(file_to_send):
                ftp.cwd(FTP_JSON_DIR)
                return ftp.storbinary(f"STOR {file_to_send}", file)
            else:
                raise ftplib.error_perm("Exceeded browser session storage limit")
    except (FileNotFoundError, ftplib.error_perm) as e:
        log.error(str(e), ": Unable to upload file ", file_to_send, "\"")


def get_requested_scanners() -> list:
    """Reads the contents of a file on the FTP server

    A user on the website can request a subreddit to be added to the scanner queue. Those requests are saved to a file,
    and this function retrieves that list. Each string should be a valid subreddit name and the JavaScript should
    perform all input validation and sanitization. The Python code will assume it has a string that is a valid subreddit
    name.

    Returns:
        A list of strings that is each line of the file.
    """
    try:
        with FTP(SERVER_ADDRESS, USERNAME, PASSWORD) as ftp:
            requested_scanners = []
            ftp.cwd(FTP_POLL_DIR)
            ftp.retrlines(f"RETR {FTP_POLL_FILE}", requested_scanners.append)
        return requested_scanners
    except (FileNotFoundError, ftplib.error_perm, ftplib.error_reply) as e:
        log.error(f"{e}: Check directory {FTP_POLL_DIR}")
