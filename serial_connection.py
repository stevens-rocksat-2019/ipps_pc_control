from comm import comm_pb2 as comm
import serial
from serial.tools import list_ports
from cobs import cobs
from typing import Callable


class Controller:

    def __init__(self, data_callback: Callable):
        self.data_callback = data_callback
        # self.connection = SerialConnection()
        # self.connection.connect()

        pass

    @staticmethod
    def output(rx: comm.RxMicro):
        print(rx)

    def control_rail(self, rail_number, state: int):
        message = comm.RxMicro()
        message.powerControl.powerRail = rail_number
        message.powerControl.powerState = state
        self.output(message)

    def input(self, tx: comm.TxMicro):
        if tx.HasField("powerRailInfo"):
            voltage_data = [None] * 8
            current_data = [None] * 8
            for powerRailInfo in tx.powerRailInfo:
                voltage_data[powerRailInfo.powerRail] = powerRailInfo.voltage
                current_data[powerRailInfo.powerRail] = powerRailInfo.current

            voltage_data[0] = 0
            for i in voltage_data[1:]:
                voltage_data[0] += i

            current_data[0] = 0
            for i in current_data[1:]:
                current_data[0] += i

            self.data_callback(voltage_data, current_data)

        if tx.HasField("powerEvent"):
            # TODO: add some kind of dialog in the future
            print(tx.powerEvent)

    def read_loop(self):
        while True:
            pass
            # self.input(self.connection.read_packet())

def get_serial_port():
    return "TEST SERIAL PORT"
    # return list(list_ports.grep("USB"))[0].device

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


if __name__ == '__main__':
    sc = SerialConnection()
    sc.connect()
    a = comm.RxMicro()
    a.powerControl.powerRail = 1
    sc.send_packet(a)
