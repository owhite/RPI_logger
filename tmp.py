#!/usr/bin/env python3

import sys
import os
import time
import logging
import HostMessages
import time, math, colorsys

import GoogleHandler

import matplotlib
matplotlib.use('Qt5Agg')  # This chooses the appropriate backend for the RPI 

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QMainWindow, QSizePolicy, QLabel, QLineEdit, QTextEdit, QTabWidget
from PyQt5.QtCore import Qt, QEvent, QTimer, pyqtSignal
from PyQt5.QtGui import QTextCursor, QPixmap, QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# remove this later
import re
import plotMESC
from datetime import datetime
import Payload

from PyQt5 import QtCore
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

# the goal of this code is to basically handle all the UI elements, while
#   cutting over the other serial stuff and logging stuff to other code
#   python classes. No idea how well that worked here. 

class TopApplication(QMainWindow):
    def __init__(self):
        super().__init__()

        self.output_data_file = 'MESC_logdata.txt'
        self.output_plot_file = 'MESC_plt.png'

        self.button_w = 600 - 20
        self.button_h = 80

        self.setGeometry(1, 1, self.button_w + 20, 350)
        self.setWindowTitle('MESC logger')

        # self.msgs = HostMessages.Log_Handler(self)
        self.msgs = Log_Handler(self)

        # Create a QTabWidget to hold the tabs
        self.tabs = QTabWidget()

        # Create the tabs for the application
        self.serialOutTab = SerialOutTab()

        new_handler2 = self.serialOutTab
        self.msgs.serial_msgs.addHandler(new_handler2)

        # Add each tab to the QTabWidget
        self.tabs.addTab(self.serialOutTab, "SER")

        self.setCentralWidget(self.tabs)

        # Install event filter to handle key events
        self.installEventFilter(self)

        ##############################
        if sys.platform.startswith('darwin'):
            self.msgs.logger.info("macOS detected")
            self.portName = '/dev/tty.usbmodem3552356B32321'
            account_file = "/Users/owhite/mesc-data-logging-ae144bcc6287.json"
        elif sys.platform.startswith('linux'):
            account_file = "/home/pi/mesc-data-logging-083b86e157cf.json"
            self.portName = '/dev/ttyACM0'
            self.msgs.logger.info("linux detected")
        else:
            self.msgs.logger.info("Unknown operating system")
            sys.exit()

        self.msgs.openPort(self.portName)

        # sometimes it's streaming so shut it off
        self.msgs.sendToPort('status stop')

        # manage the uploader
        self.drive = GoogleHandler.handler(self.msgs.logger, account_file)
        self.msgs.logger.info("GoogleHandler initiated")


    def keyPressEvent(self, event):
        key = event.key()
        # print(f"Key Pressed in Main Window: {key}")

# the HostMessaging class creates system logs and opens the serial to talk to controller
#  this tab takes output from the serial log
class SerialOutTab(QMainWindow, logging.Handler):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Log Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)

        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.ping)
        # self.timer.start(50)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Set initial buffer size
        self.max_buffer_size = 100
        self.current_buffer_size = 0
        self.counter = 0

    def append_text(self, text):
        self.text_edit.append(text)
        self.current_buffer_size += len(text)
        if self.current_buffer_size > self.max_buffer_size:
            current_text = self.text_edit.toPlainText()
            excess_text = self.current_buffer_size - self.max_buffer_size
            trim_index = 0
            for i, c in enumerate(current_text):
                excess_text -= sys.getsizeof(c.encode())
                if excess_text <= 0:
                    trim_index = i
                    break
            trimmed_text = current_text[trim_index:]
            self.text_edit.setPlainText(trimmed_text)
            self.current_buffer_size = len(trimmed_text)

class Log_Handler():
    def __init__(self, parent):
        self.parent = parent

        self.port = QSerialPort()
        self.serialPayload = Payload.Payload()
        self.serialPayload.startTimer()

        self.serial = None

        # serial_msgs handles sending the serial data that is not sent to disk, but goes to the UI
        self.serial_msgs = logging.getLogger('serial_msgs')
        self.serial_msgs.setLevel(logging.INFO)
        # data_logger handles sending serial data to disk, gets created later
        self.data_logger = None

        # dont confuse the service log, which just gets information from the program
        #  and sends it to serial_service.log, with the collection that is done by 
        #  initDataLogging() which actually collects data from the controller
        self.service_log_file = 'serial_service.log'
        self.logger = logging.getLogger('serial_service_log')
        self.logger.setLevel(logging.INFO)
        serial_service_handler = logging.FileHandler(self.service_log_file)
        stdout_handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        serial_service_handler.setFormatter(formatter)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(serial_service_handler)
        self.logger.addHandler(stdout_handler)

        self.term_collect_str = ''
        self.term_collect_flag = False

        self.json_collect_str = ''
        self.json_collect_flag = False

    def closePort(self):
        if self.serial:
            self.serial.close()

    def openPort(self, name):
        self.portName = name
        if not self.port.isOpen():
            self.port.setBaudRate( 115200 ) 
            self.port.setPortName( self.portName )
            self.port.setDataBits( 8 )
            self.port.setParity( 0 ) 
            self.port.setStopBits( 0 ) 
            self.port.setFlowControl( 0 ) 
            r = self.port.open(QtCore.QIODevice.ReadWrite)
            if not r:
                self.logger.info("Log Handler port: %s not open", self.portName)
                # self.statusText.setText('Port open: error')
            else:
                self.logger.info("Log Handler opened for port: %s", self.portName)
                # self.statusText.setText('Port opened')
                self.port.readyRead.connect(self.parseStream)
        else:
            self.port.close()
            # self.statusText.setText('Port closed')

    def sendToPort(self, text):
        if not self.port.isOpen():
            self.logger.info("cant send cmd: {0} port not open".format(text))
        else:
            self.logger.info("sending cmd: {0}".format(text))
            text = text + '\r\n'
            self.serialPayload.resetString()
            self.port.write( text.encode() )

    def parseStream(self):
        data = self.port.readAll().data().decode()

        # strip vt100 chars
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        data = ansi_escape.sub('', data)
        data = re.sub('\\| ', '\t', data)

        # get current buffer, add the data
        r = self.serialPayload.reportString() + data
        
        # Extract json strings from input buffer
        text_inside_braces = ''
        pattern = r'(\{[^}]+\}\r\n)'            # find text between "{.*}\r\n"
        matches = re.findall(pattern, r)        # get all matches
        text_inside_braces = ''.join(matches)   # concatenate all matches
        remaining_text = re.sub(pattern, '', r) # remove these
        pattern = r'(\r)'                       # more purification
        remaining_text = re.sub(pattern, '', remaining_text)

        if len(text_inside_braces) > 0:
            t = text_inside_braces.replace('\r', '').replace('\n', '')
            # here is where the stream gets split to either go to self.data_logger or self.serial_msgs
            if self.data_logger:
                # t = text_inside_braces.replace('\r', '').replace('\n', '')
                if self.json_collect_flag:
                    self.data_logger.info("[JSON BLOCK]")
                    self.json_collect_flag = False
                self.data_logger.info(f"{t}")
            else:
                # self.serial_msgs.info(f"{t}")
                pass

            self.serialPayload.resetTimer() 

        # hoping this means we have a complete block from terminal
        if remaining_text.endswith("@MESC>"):
            s = self.serialPayload.reportString()
            cmd = s.split("\n")

            # also where the stream gets split
            if self.data_logger:
                if len(cmd) > 2:
                    self.data_logger.info("[{0}]\n{1}".format(cmd[0],"\n".join(cmd[1:])))
                else:
                    self.data_logger.info("[{0}]\n{1}".format(cmd[0],self.serialPayload.reportString()))
            else:
                t = ''
                for line in self.serialPayload.reportString().split('\n'):
                    if line.count('\t') == 4:
                        l = line.split('\t')
                        w = l[0]
                        t = t + w[:10] + '\t' + l[1] + '\n'
                    else:
                        t = t + line + '\n'

                print("PRINT SOMETHING OUT", t)
                # self.serial_msgs.info(f"t")

            self.serialPayload.resetString()
            r = ''
            data = ''
            remaining_text = ''
            
        self.serialPayload.setString(remaining_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TopApplication()
    window.show()
    sys.exit(app.exec_())

