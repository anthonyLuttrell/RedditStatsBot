from ftplib import FTP
from configparser import ConfigParser

config = ConfigParser()
config.read("ftp.ini")
SERVER_ADDRESS = config["ftp"]["server_address"]
USERNAME = config["ftp"]["username"]
PASSWORD = config["ftp"]["password"]


def send_file(file_to_send: str):
    with FTP(SERVER_ADDRESS, USERNAME, PASSWORD) as ftp, open(file_to_send, 'rb') as file:
        ftp.storbinary(f"stor {file_to_send}", file)
