import asyncio
from kivy import Logger
from datasource import Datasource
from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datasource = None
        self.map_view = None
        self.map_layer = None
        self.car_marker = None
        self.pothole_markers = []
        self.bump_markers = []

    def on_start(self):
        """
        Запускається при старті додатку: ініціалізує datasource та планує оновлення мапи
        """
        self.datasource = Datasource(1)
        Logger.debug("Datasource started")
        Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        """
        Викликається регулярно для отримання нових точок і оновлення мапи
        """
        Logger.debug("update() called")
        points = self.datasource.get_new_points()
        Logger.debug(f"Got {len(points)} points")
        if not points:
            return

        for lon, lat, state in points:
            self.map_layer.add_point((lat, lon, state))
            if state == 'pothole':
                self.set_pothole_marker((lat, lon))
            elif state == 'bump':
                self.set_bump_marker((lat, lon))

        last_lon, last_lat, _ = points[-1]
        self.update_car_marker((last_lat, last_lon))

    def update_car_marker(self, point):
        """
        Оновлює позицію маркера машини
        :param point: (lat, lon)
        """
        lat, lon = point
        Logger.debug(f"Updating car marker to ({lat}, {lon})")
        # Видалити старий маркер
        try:
            self.map_view.remove_marker(self.car_marker)
        except Exception:
            pass
        # Оновити координати
        self.car_marker.lat = lat
        self.car_marker.lon = lon
        # Додати назад
        self.map_view.add_marker(self.car_marker)

    def set_pothole_marker(self, point):
        lat, lon = point
        marker = MapMarker(lat=lat, lon=lon, source="images/pothole.png")
        self.map_view.add_marker(marker)
        self.pothole_markers.append(marker)
        Logger.debug(f"Pothole marker added at ({lat}, {lon})")

    def set_bump_marker(self, point):
        lat, lon = point
        marker = MapMarker(lat=lat, lon=lon, source="images/bump.png")
        self.map_view.add_marker(marker)
        self.bump_markers.append(marker)
        Logger.debug(f"Bump marker added at ({lat}, {lon})")

    def build(self):
        """
        Ініціалізує MapView з базовим маршрутом та маркерами
        """
        self.map_layer = LineMapLayer()
        self.map_view = MapView(
            zoom=15,
            lat=50.4501,
            lon=30.5234,
        )
        self.map_view.add_layer(self.map_layer, mode="scatter")

        # Початковий маркер машини
        self.car_marker = MapMarker(
            lat=50.45034509664691,
            lon=30.5246114730835,
            source="images/car.png"
        )
        self.map_view.add_marker(self.car_marker)
        return self.map_view


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MapViewApp().async_run(async_lib="asyncio"))
    loop.close()
