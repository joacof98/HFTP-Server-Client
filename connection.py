# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
from constants import *
from base64 import b64encode
import os

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        # FALTA: Inicializar atributos de Connection
        self.s = socket
        self.dir = directory
        self.buffer = ''
        self.connected = True
        
        self.msjOk = str(CODE_OK) + ' ' + error_messages[CODE_OK]
        self.msjBadEol = str(BAD_EOL) + ' ' + error_messages[BAD_EOL]
        self.msjInv = str(INVALID_COMMAND) + ' ' + error_messages[INVALID_COMMAND]
        self.msjBadArgs = str(INVALID_ARGUMENTS) + ' ' + error_messages[INVALID_ARGUMENTS]
        self.msjBadFile = str(FILE_NOT_FOUND) + ' ' + error_messages[FILE_NOT_FOUND]
        self.msjBadOffset = str(BAD_OFFSET) + ' ' + error_messages[BAD_OFFSET]
        self.msjIntError = str(INTERNAL_ERROR) + ' ' + error_messages[INTERNAL_ERROR]
        self.msjBadReq = str(BAD_REQUEST) + ' ' + error_messages[BAD_REQUEST]

        self.commands = {
            "get_file_listing": self.getFileListing,
            "get_metadata": self.getMetaData,
            "get_slice": self.getSlice,
            "quit": self.endConnection
        }

    def send(self, message):
        message += EOL  # Completar el mensaje con un fin de línea
        try:
            bytes_sent = self.s.send(message.encode("ascii"))
            assert bytes_sent > 0
        except Exception:
            self.connected = False
            self.s.close()
    
    def checkMetadata(self, args):
        path = os.path.abspath(self.dir + '/' + args[1])
        
        if not os.path.exists(path):
            self.send(self.msjBadFile)
            return True

    def checkSlice(self, args):
        path = os.path.abspath(self.dir + '/' + args[1])
        
        if not os.path.exists(path):
            self.send(self.msjBadFile)
            return True

        try:
            size = os.path.getsize(path)
            n1 = int(args[2])
            n2 = int(args[3])

            if n1+n2 > size:
                self.send(self.msjBadOffset)
                return True
            if n1<0 or n2<0:
                self.send(self.msjBadArgs)
                return True
        except ValueError:
            self.send(self.msjBadArgs)
            return True

        return False

    def checkErrors(self, data):
        '''Envia mensajes de error al ejecutar
        comandos de manera incorrecta'''
        
        res = False
        args = data.split()

        if len(data.split('\n')) > 2:
            self.send(self.msjBadEol)
            res = True
        elif args == [] or args[0] not in self.commands:
            self.send(self.msjInv)
            res = True
        elif len(args) == 1:
            if args[0] == 'get_metadata' or args[0] == 'get_slice':
                self.send(self.msjBadArgs)
                res = True
        elif len(args)>1:
            if args[0] == 'quit' or args[0] == 'get_file_listing':
                self.send(self.msjBadArgs)
                res = True 
            elif args[0] == 'get_metadata' and len(args) != 2:
                self.send(self.msjBadArgs)
                res = True
            elif args[0] == 'get_metadata' and len(args)==2:
                res = self.checkMetadata(args)
            elif args[0] == 'get_slice' and len(args) != 4:
                self.send(self.msjBadArgs)
                res = True
            elif args[0] == 'get_slice' and len(args)==4:
                res = self.checkSlice(args)

        return res

    def getFileListing(self):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        files = os.listdir(self.dir)
            
        self.send(self.msjOk)

        for file in files:
            self.send(file)
        self.send('')

    def getMetaData(self, data):
        filename = (data.split())[1]
        filePath = os.path.abspath(self.dir + '/' + filename)
        arc_byte = os.path.getsize(filePath)
        self.send(self.msjOk)      
        self.send(str(arc_byte))        
    
    def getSlice(self, data):
        arr = data.split()
        filename = arr[1]
        offset = arr[2]
        size = arr[3]
        filePath = os.path.abspath(self.dir + '/' + filename)
        file = open(filePath, 'rb')
        file.seek(int(offset))
        fragment = file.read(int(size))
        base64_bytes = b64encode(fragment)      # Base64 Encode the bytes
        base64_fragment = base64_bytes.decode('ascii')    # Decoding the Base64 bytes to string
        self.send(self.msjOk)
        self.send(base64_fragment)
        file.close()

    def endConnection(self):
        self.send(self.msjOk)
        self.connected = False
        self.s.close()

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while(self.connected):
            try:
                data = self.s.recv(4096).decode("ascii")
            except UnicodeDecodeError:
                self.send(self.msjBadReq)
                self.connected = False
                self.s.close()
            except Exception:
                self.connected = False
                self.s.close()
            finally:
                if len(data) == 0:
                    self.send(self.msjIntError)
                    self.connected = False
                    self.s.close()
                else:
                    self.buffer += data
                    commands = self.buffer.split('\r\n')[:-1]
                    self.buffer = self.buffer.split('\r\n')[-1]

                    for command in commands:
                        if not self.checkErrors(command):
                            if command.startswith('get_m'):
                                self.commands['get_metadata'](command)
                            elif command.startswith('get_s'):
                                self.commands['get_slice'](command)
                            elif command == 'quit':
                                self.commands['quit']()
                            elif command == 'get_file_listing':
                                self.commands['get_file_listing']()


                
