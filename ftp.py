import ftplib
from ftplib import FTP
from configparser import ConfigParser

config = ConfigParser()
config.read("ftp.ini")
SERVER_ADDRESS = config["ftp"]["server_address"]
USERNAME = config["ftp"]["username"]
PASSWORD = config["ftp"]["password"]


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
        with FTP(SERVER_ADDRESS, USERNAME, PASSWORD) as ftp, open(file_to_send, 'rb') as file:
            ftp.cwd("public_html/json")
            return ftp.storbinary(f"STOR {file_to_send}", file)
    except (FileNotFoundError, ftplib.error_perm) as e:
        print(f"{e}: Unable to upload file {file_to_send}")

