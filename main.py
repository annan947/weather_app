import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
)


# Find files relative to main.py, regardless of where you run it.
APP_FOLDER = Path(__file__).resolve().parent
HISTORY_FILE = APP_FOLDER / "recent_cities.json"

load_dotenv(APP_FOLDER / ".env")


class WeatherWorker(QThread):
    """Fetch weather in the background. Never modify widgets here."""

    weather_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, city, api_key, parent=None):
        super().__init__(parent)
        self.city = city
        self.api_key = api_key

    def run(self):
        url = "https://api.openweathermap.org/data/2.5/weather"

        # Requests handles encoding spaces and special characters.
        params = {
            "q": self.city,
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=(5, 10),
            )
            response.raise_for_status()
            data = response.json()

            # Validate the fields used by the interface.
            float(data["main"]["temp"])
            float(data["main"]["feels_like"])
            float(data["wind"]["speed"])
            int(data["main"]["humidity"])
            int(data["main"]["pressure"])
            int(data["weather"][0]["id"])
            str(data["weather"][0]["description"])
            int(data["dt"])
            int(data["timezone"])

            self.weather_ready.emit(data)

        except requests.exceptions.HTTPError as error:
            status = error.response.status_code

            messages = {
                400: "Please check the city name.",
                401: "Invalid or inactive API key. Check your .env file.",
                403: "Access denied by the weather service.",
                404: "City not found. Try a name like London,GB.",
                429: "Too many requests. Please wait and try again.",
            }

            if status >= 500:
                message = "The weather service is unavailable. Try again later."
            else:
                message = messages.get(
                    status, f"Weather request failed (HTTP {status})."
                )

            self.error_occurred.emit(message)

        except requests.exceptions.Timeout:
            self.error_occurred.emit(
                "The request timed out. Please try again."
            )

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(
                "Unable to connect. Check your internet connection."
            )

        except requests.exceptions.RequestException:
            # Avoid displaying exception URLs containing the API key.
            self.error_occurred.emit(
                "The weather request failed. Please try again."
            )

        except (ValueError, KeyError, IndexError, TypeError, OverflowError):
            self.error_occurred.emit(
                "The weather service returned unexpected data."
            )


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()

        self.weather_data = None
        self.worker = None
        self.closing = False
        self.searched_city = ""
        self.recent_cities = self.load_history()

        self.initUI()
        self.update_history_menu()

    def initUI(self):
        self.setWindowTitle("Weather App")
        self.resize(480, 650)
        self.setMinimumWidth(380)

        title = QLabel("Weather")
        title.setObjectName("title")

        subtitle = QLabel("Search a city to see current conditions.")
        subtitle.setObjectName("subtitle")

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("City name, e.g. New York,US")
        self.city_input.setClearButtonEnabled(True)

        self.get_weather_button = QPushButton("Get Weather")
        self.get_weather_button.setObjectName("searchButton")

        search_row = QHBoxLayout()
        search_row.addWidget(self.city_input, 1)
        search_row.addWidget(self.get_weather_button)

        self.recent_combo = QComboBox()
        self.recent_combo.setMinimumWidth(160)

        self.units_combo = QComboBox()
        self.units_combo.addItems(["°F", "°C"])

        options_row = QHBoxLayout()
        options_row.addWidget(self.recent_combo, 1)
        options_row.addWidget(QLabel("Units:"))
        options_row.addWidget(self.units_combo)

        self.location_label = QLabel("Choose a city")
        self.location_label.setObjectName("location")

        self.emoji_label = QLabel("🌤️")
        self.emoji_label.setObjectName("emoji")

        self.temperature_label = QLabel("—")
        self.temperature_label.setObjectName("temperature")

        self.description_label = QLabel("")
        self.description_label.setObjectName("description")

        self.details_label = QLabel("")
        self.details_label.setObjectName("details")

        self.updated_label = QLabel("")
        self.updated_label.setObjectName("subtitle")

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")

        self.result_labels = [
            self.location_label,
            self.emoji_label,
            self.temperature_label,
            self.description_label,
            self.details_label,
            self.updated_label,
        ]

        for label in [title, subtitle, *self.result_labels, self.status_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(search_row)
        layout.addLayout(options_row)
        layout.addStretch()

        for label in self.result_labels:
            layout.addWidget(label)

        layout.addStretch()
        layout.addWidget(self.status_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #111827;
                color: #f3f4f6;
                font-family: Segoe UI;
                font-size: 15px;
            }

            QLabel#title {
                font-size: 34px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #9ca3af;
                font-size: 13px;
            }

            QLabel#location {
                font-size: 25px;
                font-weight: bold;
            }

            QLabel#emoji {
                font-family: Segoe UI Emoji;
                font-size: 72px;
            }

            QLabel#temperature {
                font-size: 70px;
                font-weight: bold;
            }

            QLabel#description {
                font-size: 23px;
                color: #93c5fd;
            }

            QLabel#details {
                font-size: 17px;
                color: #d1d5db;
            }

            QLabel#status {
                font-size: 13px;
                color: #9ca3af;
            }

            QLineEdit, QComboBox {
                background-color: #1f2937;
                border: 1px solid #4b5563;
                border-radius: 8px;
                padding: 10px;
            }

            QLineEdit:focus {
                border: 1px solid #60a5fa;
            }

            QPushButton {
                background-color: #2563eb;
                border: none;
                border-radius: 8px;
                padding: 11px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #374151;
                color: #9ca3af;
            }

            QComboBox QAbstractItemView {
                background-color: #1f2937;
                color: #f3f4f6;
                selection-background-color: #2563eb;
            }
        """)

        self.get_weather_button.clicked.connect(self.get_weather)
        self.city_input.returnPressed.connect(self.get_weather)
        self.units_combo.currentIndexChanged.connect(self.display_weather)
        self.recent_combo.activated[int].connect(self.search_recent_city)

    def get_weather(self):
        # Prevent overlapping requests.
        if self.worker is not None:
            return

        city = self.city_input.text().strip()

        if not city:
            self.set_status("Please enter a city name.", error=True)
            self.city_input.setFocus()
            return

        api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()

        if not api_key:
            self.set_status(
                "Missing API key. Add it to your .env file and restart.",
                error=True,
            )
            return

        self.searched_city = city
        self.weather_data = None

        for label in self.result_labels:
            label.clear()

        self.location_label.setText(city)
        self.temperature_label.setText("—")

        self.set_loading(True)
        self.set_status(f"Loading weather for {city}...")

        self.worker = WeatherWorker(city, api_key, self)
        self.worker.weather_ready.connect(self.receive_weather)
        self.worker.error_occurred.connect(self.display_error)
        self.worker.finished.connect(self.request_finished)
        self.worker.start()

    def receive_weather(self, data):
        if self.closing:
            return

        self.weather_data = data
        self.display_weather()

        saved = self.save_city(self.searched_city)

        if saved:
            self.set_status("Weather updated.")
        else:
            self.set_status(
                "Weather updated, but recent searches could not be saved."
            )

    def display_weather(self, _index=None):
        if self.weather_data is None:
            return

        data = self.weather_data
        main = data["main"]
        weather = data["weather"][0]

        use_fahrenheit = self.units_combo.currentText() == "°F"
        unit = "°F" if use_fahrenheit else "°C"

        temperature = float(main["temp"])
        feels_like = float(main["feels_like"])
        wind = float(data["wind"]["speed"])

        # The API always returns metric data; convert locally.
        if use_fahrenheit:
            temperature = temperature * 9 / 5 + 32
            feels_like = feels_like * 9 / 5 + 32
            wind *= 2.23694
            wind_unit = "mph"
        else:
            wind *= 3.6
            wind_unit = "km/h"

        city = data.get("name") or self.searched_city
        country = data.get("sys", {}).get("country", "")
        location = f"{city}, {country}" if country else city

        self.location_label.setText(location)
        self.temperature_label.setText(f"{temperature:.0f}{unit}")
        self.description_label.setText(
            str(weather["description"]).capitalize()
        )

        self.emoji_label.setText(
            self.get_weather_emoji(
                int(weather["id"]),
                str(weather.get("icon", "")).endswith("n"),
            )
        )

        self.details_label.setText(
            f"Feels like: {feels_like:.0f}{unit}\n"
            f"Humidity: {int(main['humidity'])}%\n"
            f"Wind: {wind:.1f} {wind_unit}\n"
            f"Pressure: {int(main['pressure'])} hPa"
        )

        # Show the observation time in the searched city's timezone.
        try:
            city_timezone = timezone(
                timedelta(seconds=int(data["timezone"]))
            )
            observed = datetime.fromtimestamp(
                int(data["dt"]), tz=city_timezone
            )
            self.updated_label.setText(
                f"Observed: {observed:%b %d, %I:%M %p} (city time)"
            )
        except (ValueError, OverflowError, OSError):
            self.updated_label.clear()

    def display_error(self, message):
        if self.closing:
            return

        self.weather_data = None

        for label in self.result_labels:
            label.clear()

        self.location_label.setText("Weather unavailable")
        self.temperature_label.setText("—")
        self.set_status(message, error=True)

    def set_status(self, message, error=False):
        self.status_label.setText(message)
        color = "#fca5a5" if error else "#9ca3af"
        self.status_label.setStyleSheet(f"color: {color};")

    def set_loading(self, loading):
        self.get_weather_button.setEnabled(not loading)
        self.city_input.setEnabled(not loading)
        self.recent_combo.setEnabled(not loading)
        self.get_weather_button.setText(
            "Loading..." if loading else "Get Weather"
        )

    def request_finished(self):
        finished_worker = self.worker
        self.worker = None

        if finished_worker is not None:
            finished_worker.deleteLater()

        if self.closing:
            self.close()
        else:
            self.set_loading(False)

    def search_recent_city(self, index):
        if index > 0:
            self.city_input.setText(self.recent_combo.itemText(index))
            self.get_weather()

    def update_history_menu(self):
        self.recent_combo.clear()
        self.recent_combo.addItem("Recent searches")
        self.recent_combo.addItems(self.recent_cities)

    @staticmethod
    def load_history():
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

            if not isinstance(data, list):
                return []

            return [
                city.strip()
                for city in data
                if isinstance(city, str) and city.strip()
            ][:5]

        except (OSError, ValueError):
            return []

    def save_city(self, city):
        # Move the latest successful search to the top.
        self.recent_cities = [
            previous
            for previous in self.recent_cities
            if previous.casefold() != city.casefold()
        ]
        self.recent_cities.insert(0, city)
        self.recent_cities = self.recent_cities[:5]
        self.update_history_menu()

        try:
            HISTORY_FILE.write_text(
                json.dumps(self.recent_cities, indent=2),
                encoding="utf-8",
            )
            return True
        except OSError:
            return False

    @staticmethod
    def get_weather_emoji(weather_id, is_night=False):
        if 200 <= weather_id <= 232:
            return "⛈️"
        elif 300 <= weather_id <= 321:
            return "🌦️"
        elif 500 <= weather_id <= 531:
            return "🌧️"
        elif 600 <= weather_id <= 622:
            return "❄️"
        elif weather_id in (701, 711, 721, 731, 741, 751, 761):
            return "🌫️"
        elif weather_id == 762:
            return "🌋"
        elif weather_id == 771:
            return "💨"
        elif weather_id == 781:
            return "🌪️"
        elif weather_id == 800:
            return "🌙" if is_night else "☀️"
        elif 801 <= weather_id <= 804:
            return "☁️"
        return "🌡️"

    def closeEvent(self, event):
        # Allow a running request to finish before destroying its thread.
        if self.worker is not None:
            self.closing = True
            self.set_status("Closing after the current request finishes...")
            self.setEnabled(False)
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())