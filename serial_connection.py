import comm_pb2 as comm
import serial
from serial.tools import list_ports
from cobs import cobs
from typing import Callable


class Controller:

    def __init__(self, data_callback: Callable):
        self.data_callback = data_callback
        self.connection = SerialConnection()
        self.connection.connect()

        pass

    def output(self, rx: comm.RxMicro):
        print(rx)
        self.connection.send_packet(rx)

    def control_rail(self, rail_number, state: int):
        message = comm.RxMicro()
        message.powerControl.powerRail = rail_number
        message.powerControl.powerState = state
        self.output(message)

    def input(self, tx: comm.TxMicro):

        voltage_data = [None] * (len(tx.powerRailInfo)+1)
        current_data = [None] * (len(tx.powerRailInfo)+1)
        for powerRailInfo in tx.powerRailInfo:
            voltage_data[powerRailInfo.powerRail] = powerRailInfo.voltage
            current_data[powerRailInfo.powerRail] = powerRailInfo.current

        voltage_data[0] = 0
        for i in voltage_data[1:]:
            voltage_data[0] += i

        current_data[0] = 0
        for i in current_data[1:]:
            current_data[0] += i

        temp_hum = [tx.envEvent.temp, tx.envEvent.humidity] if tx.HasField("envEvent") else None

        self.data_callback(voltage_data, current_data, temp_hum)

        if tx.HasField("powerEvent"):
            # TODO: add some kind of dialog in the future
            print(tx.powerEvent)

    def read_loop(self):
        while True:
            self.input(self.connection.read_packet())


def get_serial_port():
    #return list(list_ports.grep("USB"))[0].device
    return list(list_ports.grep("usbmodem"))[0].device

class SerialConnection:

    def __init__(self, serial_port=get_serial_port(), baud=115200):
        self.ser: serial.Serial = None
        self.serial_port = serial_port
        self.baud = baud

    def connect(self):
        self.ser = serial.Serial(self.serial_port, self.baud)

    def close(self):
        self.ser.close()

    def read_packet(self) -> comm.TxMicro:
        byte = self.ser.read()
        result = b''
        while byte != b'\x00':
            result += byte
            byte = self.ser.read()
        tx = comm.TxMicro()
        tx.ParseFromString(cobs.decode(result))
        return tx

    def send_packet(self, rx: comm.RxMicro):
        return self.ser.write(cobs.encode(rx.SerializeToString()) + b'\x00')




def serial_test():
    sc = SerialConnection()
    sc.connect()
    while True:
        print(sc.read_packet())

def controller_test():
    def callback_test(*kwargs):
        print(kwargs)

    c = Controller(callback_test)
    c.read_loop()


if __name__ == '__main__':
    controller_test()
