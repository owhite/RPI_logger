#! /usr/bin/env python3

# This is called HostMessages but in the context of it running
#   with python-flask it is basically the server backend. 
# note that it handles two forms of logging:
#  1) it opens up system logs that sit on the host computer
#  2) it also handles various serial operations like opening/closing the port

import logging
import re
import sys, os
import threading

import time
import serial
import plotMESC
import Payload


class LogHandler():
    def __init__(self, parent):
        self.parent = parent
        self.image_directory = self.parent.image_directory
        self.log_directory = self.parent.log_directory

        self.serialPayload = Payload.Payload()
        self.serialPayload.startTimer()
        self.port = None

        # serial_msgs handles sending the serial data that is not sent to disk, but goes to the UI
        self.serial_msgs = logging.getLogger('serial_msgs')
        self.serial_msgs.setLevel(logging.INFO)
        # data_logger handles sending serial data to disk, gets created later
        self.data_logger = None

        # dont confuse the service log, which just gets information from the program
        #  and sends it to serial_service.log, with the collection that is done by 
        #  initDataLogging() which actually collects data from the controller
        self.service_log_file = os.path.join(self.log_directory, 'serial_service.log')
        self.logger = logging.getLogger('serial_service_log')
        self.logger.setLevel(logging.INFO)
        serial_service_handler = logging.FileHandler(self.service_log_file, mode='w')
        stdout_handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        serial_service_handler.setFormatter(formatter)
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(serial_service_handler)
        self.logger.addHandler(stdout_handler)

        self.dataBuffer = bytearray()
        # alias this so it looks like QT version
        Mutex = threading.Lock
        self.is_running = True
        self.mutex = Mutex()
        self.process_thread = threading.Thread(target=self.process_loop)
        self.process_thread.start()
        
        self.json_collect_str = ''
        self.json_collect_flag = False
        self.hostStatusText = None

        self.log_is_on = False

    def process_loop(self):
        while self.is_running:
            if self.port and self.port.is_open:
                try:
                    if self.port.in_waiting > 0:
                        self.processData()
                except OSError as e:
                    if e.errno == 6:
                        # Handle the specific error
                        self.logger.info("Device not configured. Please check the connection.")
                        self.is_running = False  # Optionally, stop the loop
                    else:
                        # Handle other potential OS errors
                        self.logger.info(f"An unexpected OS error occurred: {e}")
                except Exception as e:
                    # Handle any other exceptions
                    self.logger.info(f"An unexpected error occurred: {e}")
        time.sleep(0.01)


    # this function is called periodically and chows self.dataBuffer
    def processData(self):
        if not self.port or not self.port.is_open:
            return

        with self.mutex:
            try:
                data = self.port.readline()
                if data:
                    self.dataBuffer.extend(data)
                    data = self.dataBuffer.copy()
                    self.dataBuffer.clear()
                    data = data.decode()
            except serial.SerialException as e:
                self.logger.error(f"Error reading from serial port: {e}")

        # strip vt100 chars
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        data = ansi_escape.sub('', data)
        data = re.sub('\\| ', '\t', data)

        
        # get current buffer, add the data
        self.serialPayload.concatString(data)

        remaining_text = ''
        s = self.serialPayload.reportString()

        json_text = ''
        if re.search("{.*}", s):
            s = s.replace('\r', '')
            s = s.replace("\x00", '')
            pattern = r'\{(.*?)\}\n'
            pattern = r'(\{.*\})\n'
            matches = re.findall(pattern, s, re.DOTALL)
            remaining_text = re.sub(pattern, '', s)
            json_text = ''.join(matches)
            json_text = json_text.replace('\r', '').replace('\n', '')
            json_text = json_text.replace("}{", "}\n{") 
            self.serialPayload.setString(remaining_text)

        if len(json_text) > 0:
            # split json to go to self.data_logger or self.serial_msgs
            if self.data_logger:
                if self.json_collect_flag:
                    self.data_logger.info("[JSON BLOCK]")
                    self.json_collect_flag = False
                self.data_logger.info(f"{json_text}")
            else:
                self.serial_msgs.info(f"{json_text}")

            self.serialPayload.resetTimer() 

        token = "usb@MESC>"
        s = self.serialPayload.reportString()
        s = s.replace('\r', '')

        # mulitple blocks may occur, so they get processed in the while loop, or
        #   once it breaks out of loop. 
        result, first_block, second_block = self.chow_block(s, token)
        while(result):    
            self.serial_msgs.info(first_block)
            # the only time you log this is if it is get command and it is long
            if self.data_logger and token + 'get' in first_block and len(first_block) > 2000:
                    self.data_logger.info("[GET]")
                    self.data_logger.info(first_block)
                    self.json_collect_flag = True
                    self.sendToPort('status json')

            else:
                self.serial_msgs.info(first_block)

            result, first_block, second_block = self.chow_block(second_block, token)

        if len(first_block)!= 0:
            # the only time you log this is if it is get command and it is long
            if self.data_logger and token + 'get' in first_block and len(first_block) > 2000:
                    self.data_logger.info("[GET]")
                    self.data_logger.info(first_block)

                    self.json_collect_flag = True
                    self.sendToPort('status json')

            else:
                self.serial_msgs.info(first_block)

        self.serialPayload.setString(second_block)


    def initHostStatusLabel(self, label):
        if isinstance(label, QLabel):
            self.hostStatusText = label

    def openPort(self, name):
        self.portName = name
        try:
            self.port = serial.Serial(port=self.portName, baudrate=115200, timeout=1)
            self.logger.info(f"Log Handler opened for port: {self.portName}")
            self.setStatusText('Port opened')
            self.sendToPort('su -g')  # Example: sending commands to port
            self.sendToPort('status stop')

        except serial.SerialException as e:
            self.logger.info(f"Error opening or using serial port: {e}")
            self.setStatusText(f'Port open error: {e}')

    def setStatusText(self, text):
        if self.hostStatusText and isinstance(self.hostStatusText, QLabel):
            self.hostStatusText.setText(text)

    def closePort(self):
        if self.serial:
            self.serial.close()

        
    def sendToPort_BROKEN(self, text):
        if not self.port.isOpen():
            self.logger.info("Port not open. Attempting to reopen.")
            # self.port = serial.Serial(port=self.portName, baudrate=115200, timeout=1)
            # self.logger.info(f"Log Handler opened for port: {self.portName}")
            # self.setStatusText('Port opened')
            try:
                self.logger.info("Port reopened successfully.")
            except serial.SerialException as e:
                self.logger.error(f"Failed to reopen port: {e}")
                self.logger.info(f"Cant send cmd: {text} port not open")

                return

        try:
            self.logger.info(f"Sending cmd: {text}")
            text = text + '\r\n'
            self.port.write(text.encode())
        except Exception as e:
            self.logger.error(f"Failed to send cmd: {text} due to: {e}")

    def sendToPort(self, text):
        if not self.port.isOpen():
            self.logger.info("Cant send cmd: {0} port not open".format(text))
        else:
            self.logger.info("sending cmd: {0}".format(text))
            text = text + '\r\n'
            self.port.write( text.encode() )

    def chow_block(self, text, token):
        flag = False

        t = text
        # not really intuitive but remove the token if at beginning of string
        #  the idea is the remainder will get save for the next round of parsing
        if text.startswith(token):
            t = text.replace(token, '', 1)

        if len(t) == 0: # you get this if string was empty or was just a prompt
            return False, t, t

        l = t.split(token)
        payload = ''
        remainder = ''
        if len(l) == 1: # no token, everything goes in remainder
            remainder = l[0]
        elif len(l) == 2:
            payload = l[0]
        elif len(l) > 2:
            flag = True
            payload = l[0]
            remainder = token.join(l[1:])
        else:
            print("chow_block: unforseen parsing condition")
            payload = "chow_block: unforseen parsing condition"

        # fakes the user out by showing the prompt at the beginning of the payload
        if len(payload) > 0:
            payload = token + payload

        return flag, payload, remainder

    def logIsOn(self):
        return self.log_is_on

    def setDataLogFile(self, file_name):
        self.datafile_name = file_name

    def initDataLogging(self):
        self.logger.info(F"Initiate data logging: {self.datafile_name}")

        if self.data_logger:
            for handler in self.data_logger.handlers[:]:
                self.data_logger.removeHandler(handler)
                print("Deleted logger 'output_log'.")
                handler.close()
            self.data_logger = None

        # Create a new logger for output.log (overwriting the file each time)
        self.data_logger = logging.getLogger('output_log')
        self.data_logger.setLevel(logging.INFO)

        print(F"LOGGER: {self.data_logger}")

        formatter = logging.Formatter('%(message)s')
        file_handler = logging.FileHandler(self.datafile_name, mode="w") 
        file_handler.setFormatter(formatter)

        self.data_logger.addHandler(file_handler)
        self.logger.info(f"Created new output file log: {self.datafile_name}")

        self.serialPayload.resetTimer() 
        self.sendToPort('get')


    def setPlotFile(self, file_name):
        self.plot_file = file_name

    def getPlotFile(self):
        return self.plot_file

    def endDataLogging(self):
        self.sendToPort('status stop')

        if self.data_logger:
            for handler in self.data_logger.handlers[:]:
                self.data_logger.removeHandler(handler)
                handler.close()
            self.data_logger = None
            self.logger.info("Finished logging")
            self.setStatusText("Finished logging")

            datatypes = ('ehz', 'phaseA', 'iqreq', 'vbus')
            p = plotMESC.PlotMESCOutput()
            (plt, fig) = p.generatePlot(self.datafile_name, datatypes)

            if plt is not None and fig is not None:
                self.logger.info(F"Created plot: {self.plot_file}")
                self.setStatusText("Created plot file")
                plt.savefig(self.plot_file)
            else:
                self.setStatusText("No plot saved")
                self.logger.info(F"No plot saved")

def main():
    pass

if __name__ == "__main__":
    main()

