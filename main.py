# main.py
import os
import sys
import argparse


import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box 
from datetime import datetime, timezone

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

console = Console()

def fetch_current_weather(city: str, units: str = "metric"):
    if not API_KEY:
        console.print("[bold red]ERROR:[/bold red] OPENWEATHER_API_KEY not set in .env")
        sys.exit(1)

    params = {"q": city, "appid": API_KEY, "units": units}
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        try:
            err = resp.json().get("message", "Unknown HTTP error")
        except Exception:
            err = "Unknown HTTP error"
        console.print(f"[bold red]API error:[/bold red] {err}")
        return None
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Network error:[/bold red] {e}")
        return None

    return resp.json()

def format_time(ts, tz_offset):
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(ts + tz_offset, timezone.utc).strftime("%Y-%m-%d %H:%M")


def pretty_render(data: dict, units: str):
    if not data:
        return

    name = data.get("name", "Unknown")
    sysinfo = data.get("sys", {})
    country = sysinfo.get("country", "")
    weather_desc = data.get("weather", [{}])[0].get("description", "N/A").title()

    main = data.get("main", {})
    temp = main.get("temp", "N/A")
    feels = main.get("feels_like", "N/A")
    humidity = main.get("humidity", "N/A")

    wind = data.get("wind", {})
    wind_speed = wind.get("speed", "N/A")

    tz_offset = data.get("timezone", 0)
    dt = data.get("dt", 0)
    sunrise = sysinfo.get("sunrise")
    sunset = sysinfo.get("sunset")

    # header panel
    title = Text(f" Weather — {name}, {country} ", style="bold white on blue")
    time_text = Text(f" Local time (approx): {format_time(dt, tz_offset)} ", style="dim")
    header = Panel(Align.center(Text.assemble(title, "\n", time_text)),
                   expand=False, box=box.ROUNDED)  
    console.print(header)

    # big condition line
    condition_style = "bold magenta" if "cloud" in weather_desc.lower() else "bold yellow" if "clear" in weather_desc.lower() else "bold cyan"
    condition = Text(weather_desc, style=condition_style)
    temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"

    console.print(Align.center(condition, vertical="middle"))
    console.print()

    # table of details
    table = Table(box=None, show_edge=False, show_header=False, pad_edge=False)
    table.add_column("name", style="bold")
    table.add_column("value", overflow="fold")

    table.add_row("Temperature", f"{temp} {temp_unit} (Feels like {feels}{temp_unit})")
    table.add_row("Humidity", f"{humidity}%")
    table.add_row("Wind Speed", f"{wind_speed} {'m/s' if units!='imperial' else 'mph'}")
    table.add_row("Sunrise", format_time(sunrise, tz_offset))
    table.add_row("Sunset", format_time(sunset, tz_offset))

    console.print(table)
    console.print("\n")

def main():
    parser = argparse.ArgumentParser(description="Weather CLI (rich output)")
    parser.add_argument("city", nargs="+", help="City name, e.g. 'Bengaluru' or 'New York,US'")
    parser.add_argument("-u", "--units", choices=["metric", "imperial", "standard"], default="metric",
                        help="Units: metric (C), imperial (F), standard (K)")
    parser.add_argument("-k", "--apikey", help="OpenWeatherMap API key (optional override)")
    args = parser.parse_args()

    city = " ".join(args.city)
    global API_KEY
    if args.apikey:
        API_KEY = args.apikey

    data = fetch_current_weather(city, units=args.units)
    if data:
        pretty_render(data, args.units)

if __name__ == "__main__":
    main()
