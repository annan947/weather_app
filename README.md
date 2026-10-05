# Python Weather App

A desktop weather application built with Python, PyQt5, and the OpenWeather API. Search for a city to view current weather conditions.

## Project Background

I built the original version by following Bro Code’s Python weather app tutorial to learn how to connect a PyQt5 interface to a weather API.

After completing the tutorial, I used AI assistance to expand the application with additional features, improve the interface, and handle requests in the background. This project is part of my ongoing practice with Python, APIs, and desktop application development.

## How The App Looks
<img width="474" height="760" alt="image" src="https://github.com/user-attachments/assets/3932d2af-d63e-460e-b29d-e333db74eddf" />



## Features

- Search for current weather by city name
- Switch between Fahrenheit and Celsius without another API request
- Display feels-like temperature, humidity, wind speed, and pressure
- Show weather emojis, including a nighttime clear-sky icon
- Save the five most recent successful searches locally
- Search by pressing Enter or clicking Get Weather
- Keep the interface responsive with background API requests
- Display loading states and helpful error messages
- Load the API key from a local `.env` file

## Technologies

- Python
- PyQt5
- Requests
- python-dotenv
- OpenWeather API
- JSON for local search history

## Setup

1. Download or clone this repository and open its folder.

2. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Obtain an API key from [https://openweathermap.org/](https://openweathermap.org/).

4. Create a file named `.env` in the same folder as `main.py`:

   ```dotenv
   OPENWEATHER_API_KEY=your_api_key_here
   ```

   You can also copy `.env.example` and rename the copy to `.env`.

5. Start the application:

   ```bash
   python main.py
   ```

## Usage

Enter a city, such as `New York,US` or `London,GB`, and click **Get Weather**.

Use the units menu to switch between °F and °C. Select a previous search from the recent searches menu to fetch its current weather again.

## Local Files

- `.env` stores your API key and is excluded from Git.
- `recent_cities.json` is created automatically to save recent searches and is excluded from Git.

Each person running the app supplies their own API key.

## What I Practiced

- Creating a desktop interface with PyQt5
- Making HTTP requests and reading JSON responses
- Connecting buttons and keyboard events to Python methods
- Handling input errors and network failures
- Working with environment variables
- Using AI-assisted code to explore background threads and local persistence

## Credits

- Bro Code: original Python weather app tutorial
- OpenWeather: weather data
- AI assistance: feature expansion, interface improvements, and debugging
