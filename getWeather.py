import requests
import json
import platform
import os

if platform.system() == 'Windows':
    #needed for cairosvg to work under windows
    gtkbin = r'C:\Program Files\GTK3-Runtime Win64\bin'
    add_dll_dir = getattr(os, 'add_dll_directory', None)
    if callable(add_dll_dir):
        add_dll_dir(gtkbin)
    else:
        os.environ['PATH'] = os.pathsep.join((gtkbin, os.environ['PATH']))
else:
    os.chdir('/home/pi/kindleInfoDisplay')

import cairosvg
import datetime
import svglue

def degrees_to_cardinal(d):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

urlNow = "https://api.openweathermap.org/data/2.5/weather"
urlFore = "https://api.openweathermap.org/data/2.5/forecast"
outputsvg = "output.svg"
outputpng = "output.png"

try:
    with open("weatherData.json", "r") as f:
        localData = json.load(f)
    lastRequest = datetime.datetime.fromtimestamp(localData["now"]["dt"])
except:
    #set to random timestamp more than 30 min ago
    lastRequest = datetime.datetime.fromtimestamp(1326244364)

#check if data is more than 30 min old
current_time = datetime.datetime.now()
timeDiff = current_time - lastRequest
weatherError = None
if timeDiff.seconds > 1800:
    #pull new Data
    with open("parameter.json", "r") as f:
        params = json.load(f)
    
    try:
        response = requests.get(urlNow, params = params)
        nowWeather = response.json()
        response = requests.get(urlFore, params = params)
        foreWeather = response.json()

        weather = {}
        weather["now"] = nowWeather
        weather["forecast"] = foreWeather

        #save new data
        with open("weatherData.json", "w") as f:
            json.dump(weather, f)
    except Exception as e:
        weatherError = e
else:
    weather = localData

tpl = svglue.load(file="template.svg")

if weatherError == None:
    with open("iconsMapping.json", "r") as f:
        iconMap = json.load(f)

    currentTemp = str(round(weather["now"]["main"]["temp"], 0)) + "C and feels like " + str(round(weather["now"]["main"]["feels_like"], 0))
    currentIcon = "icons/"+ str(iconMap[weather["now"]["weather"][0]["icon"]])
    currentWind = str(weather["now"]["wind"]["speed"]) + "m/s from " + degrees_to_cardinal(weather["now"]["wind"]["deg"])

    tpl.set_text("curTemp", currentTemp)
    tpl.set_text("curWind", currentWind)
    tpl.set_svg("curIcon", file=currentIcon)

    forecasts = weather["forecast"]["list"]
    for i in range(5):
        time = forecasts[i]["dt"]
        temp = forecasts[i]["main"]["feels_like"]
        icon = forecasts[i]["weather"][0]["icon"]
        
        timestr = str(datetime.datetime.fromtimestamp(timestamp=time, tz=datetime.timezone.utc).strftime('%H:%M'))
        temp = str(round(temp, 0)) + "C"
        iconName = "icons/"+ str(iconMap[icon])

        tpl.set_text("foreTime" + str(i), timestr)
        tpl.set_text("foreTemp" + str(i), temp)
        tpl.set_svg("foreIcon" + str(i), file=iconName)
else:
    tpl.set_text("weatherError", weatherError)

tpl.set_text("updateTime", "last updated: " + current_time.strftime("%H:%M"))

src = tpl.__str__().decode()
with open(outputsvg, 'w') as svgout:
    svgout.write(src)
cairosvg.svg2png(url=outputsvg, write_to=outputpng)