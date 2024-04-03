"""
SFTP Server with Paramiko

Author: Charles THOMAS
Date: 03/04/2024

Description:
This script implements a simple SFTP (SSH File Transfer Protocol) server using Paramiko, a Python library for SSH protocol implementation. It allows clients to connect and perform various file operations such as listing directories, creating directories, removing files, etc. The server runs on the specified host and port, handling multiple client connections concurrently. Each client connection is managed in a separate thread. 

Credits:
- Paramiko: https://www.paramiko.org/
"""

import paramiko
from logger import Logger
from paramiko import SFTPError, Transport, SFTPServer, ServerInterface, SFTPHandle
from paramiko.common import AUTH_SUCCESSFUL, OPEN_SUCCEEDED
from paramiko.sftp_attr import SFTPAttributes
from paramiko.sftp_si import SFTPServerInterface
import os, socket, time, threading


HOST = "127.0.0.1"
KEY_DIR = "host_key.key"
PORT = 2222
MAX_CLIENTS = 5


class OpenHandle(SFTPHandle):

    def __init__(self, flags):
        super(OpenHandle, self).__init__(flags)

    def stat(self):
        print("stat")
        try:
            return SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)


class StubServer(ServerInterface):
    def check_auth_password(self, username, password):
        return AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        return OPEN_SUCCEEDED


class StubSFTPServer(SFTPServerInterface):

    ROOT = os.getcwd() + "/home"

    def _realpath(self, path):
        """Fonction utilitaire permettant d'obtenir le chemin réél"""
        return self.ROOT + self.canonicalize(path)

    def __init__(self, *args, **kwargs):
        super(StubSFTPServer, self).__init__(*args, **kwargs)
        self.current_path = self.ROOT

    def session_started(self):
        Logger.log(f"Session started")
        return super().session_started()

    def session_ended(self):
        Logger.log(f"Session ended")
        return super().session_ended()

    def list_folder(self, path):
        """Liste les fichiers sur le path"""

        Logger.log(f"ls command executed")
        path = self._realpath(path)

        try:
            out = []
            flist = os.listdir(path)
            for fname in flist:
                attr = SFTPAttributes.from_stat(os.stat(os.path.join(path, fname)))
                attr.filename = fname
                out.append(attr)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

        return out

    def stat(self, path):
        Logger.log(f"cd command executed")
        path = self._realpath(path)
        try:
            return SFTPAttributes.from_stat(os.stat(path))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def lstat(self, path):
        path = self._realpath(path)
        try:
            return SFTPAttributes.from_stat(os.lstat(path))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def open(self, path, flags, attr):
        Logger.log(f"Open command - path={path}")

        # Overture du fichier et lecture des permission
        try:
            binary_flag = getattr(os, "O_BINARY", 0)
            flags |= binary_flag
            mode = getattr(attr, "st_mode", None)
            fd = os.open(
                self._realpath(path), flags, mode if mode is not None else 0o666
            )
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

        # Gestion des permissions
        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            SFTPServer.set_file_attr(path, attr)
        if flags & os.O_WRONLY:
            fstr = "ab" if flags & os.O_APPEND else "wb"
        elif flags & os.O_RDWR:
            fstr = "a+b" if flags & os.O_APPEND else "r+b"
        else:
            fstr = "rb"

        try:
            file = os.fdopen(fd, fstr)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

        # Création du handler pour les opération sftp
        handler = OpenHandle(flags)
        handler.filename = path
        handler.readfile = file
        handler.writefile = file
        return handler

    def mkdir(self, path, attr):
        """Créer un dossier sur le seveur"""

        Logger.log(f"mkdir command executed - path={path}")
        path = self._realpath(path)

        try:
            os.mkdir(path, attr.st_mode)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def rmdir(self, path):
        """Supprimme un dossier sur le serveur"""

        Logger.log(f"rmdir command executed - path={path}")
        path = self._realpath(path)

        try:
            os.rmdir(path)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def remove(self, path):
        Logger.log(f"remove command executed - path={path}")
        path = self._realpath(path)

        try:
            os.remove(path)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)


def handle_client(conn, addr):
    """Fonction permettant la gestion des connections"""

    Logger.log(f"Connection from {addr[0]}:{addr[1]}")

    host_key = paramiko.RSAKey.from_private_key_file(KEY_DIR)

    try:
        transport = Transport(conn)
        transport.add_server_key(host_key)
        transport.set_subsystem_handler("sftp", SFTPServer, StubSFTPServer)

        server = StubServer()
        transport.start_server(server=server)

        channel = transport.accept()

        while transport.is_active():
            time.sleep(1)
    except Exception as e:
        Logger.log(f"Error: {e}")
    finally:
        conn.close()


def start_server():
    """Créer les sous processus à chaque nouvelle connection"""

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_CLIENTS)

    Logger.log(f"Socket created, waiting for connection")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
