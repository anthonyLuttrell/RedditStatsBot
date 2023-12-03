import ftplib
import os.path
from ftplib import FTP
from configparser import ConfigParser

config = ConfigParser()
config.read("ftp.ini")
SERVER_ADDRESS = config["ftp"]["server_address"]
USERNAME = config["ftp"]["username"]
PASSWORD = config["ftp"]["password"]
SERVER_JSON_DIR = "public_html/json"
LOCAL_JSON_DIR = "json/"
SESSION_STORAGE_FILE_DICT = {}
SESSION_STORAGE_LIMIT = 5242880  # 5 MiB (mebibyte)


def exceeded_session_storage(file_to_send: str) -> bool:
    # make sure we do not exceed the session storage limit before sending the files
    try:
        size = os.path.getsize(LOCAL_JSON_DIR + file_to_send)
    except OSError as e:
        print(f"{e}: Unable to check file size, sending file anyway.")
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
        "226 0.027 seconds (measured here), 449.62 bytes per second"
        "530 Login authentication failed"
    """
    try:
        with FTP(SERVER_ADDRESS, USERNAME, PASSWORD) as ftp, open(LOCAL_JSON_DIR + file_to_send, 'rb') as file:
            if not exceeded_session_storage(file_to_send):
                ftp.cwd(SERVER_JSON_DIR)
                return ftp.storbinary(f"STOR {file_to_send}", file)
            else:
                raise ftplib.error_perm("Exceeded browser session storage limit")
    except (FileNotFoundError, ftplib.error_perm) as e:
        print(f"{e}: Unable to upload file {file_to_send}")

