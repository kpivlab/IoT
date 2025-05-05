from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking
from domain.aggregated_data import AggregatedData
import config


class FileDatasource:
    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
        parking_filename: str,
    ) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.parking_filename = parking_filename
        self.accelerometer_file = None
        self.gps_file = None
        self.parking_file = None

    def read(self) -> AggregatedData:
        """Метод повертає дані отримані з датчиків"""
        
        accelerometer_data = None
        gps_data = None
        parking_data = None

        if self.accelerometer_file:
            accelerometer_reader = reader(self.accelerometer_file)
            for row in accelerometer_reader:
                try:
                    accelerometer_data = Accelerometer(*map(int, row))
                    break
                except ValueError:
                    continue

        if self.gps_file:
            gps_reader = reader(self.gps_file)
            for row in gps_reader:
                try:
                    gps_data = Gps(*map(float, row))
                    break
                except ValueError:
                    continue

        if self.parking_file:
            parking_reader = reader(self.parking_file)
            for row in parking_reader:
                try:
                    parking_data = Parking( empty_count=int(row[0]), gps=Gps(*map(float, row[1:])) )
                    break
                except ValueError:
                    continue

        return AggregatedData(
            accelerometer_data,
            gps_data,
            parking_data,
            datetime.now(),
            config.USER_ID
        )

    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""
        self.accelerometer_file = open(self.accelerometer_filename, 'r')
        self.gps_file = open(self.gps_filename, 'r')
        self.parking_file = open(self.parking_filename, 'r')

    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""
        if self.accelerometer_file:
            self.accelerometer_file.close()
            self.accelerometer_file = None
        if self.gps_file:
            self.gps_file.close()
            self.gps_file = None
        if self.parking_file:
            self.parking_file.close()
            self.parking_file = None