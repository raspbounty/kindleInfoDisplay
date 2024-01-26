import requests
import json
import platform
import os
import arrow
from ics import Calendar

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
from datetime import timedelta, datetime, timezone
import svglue

def degrees_to_cardinal(d):
    dirs = ['N', 'NNO', 'NO', 'ONO', 'O', 'OSO', 'SO', 'SSO', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def intToString(value):
    return str(int(round(value,0)))

def getCalDateString(event):
    if(event.all_day):
        if(event.duration.days > 1):
            out = event.begin.format("DD.MM.") + " bis "  + event.end.format("DD.MM.")
        else:
            out = event.begin.format("DD.MM.")
    else:
        beginTime = datetime.fromtimestamp(event.begin.timestamp())
        endTime = datetime.fromtimestamp(event.end.timestamp())
        out=  beginTime.strftime("%d.%m. von %H:%M") + " bis "  + endTime.strftime("%H:%M")
    return out

urlNow = "https://api.openweathermap.org/data/2.5/weather"
urlFore = "https://api.openweathermap.org/data/2.5/forecast"
outputsvg = "output.svg"
outputpng = "output.png"
weatherFile = "weatherData.json"
calendarFile = "calendar.ics"
oneday = timedelta(days=1)
halfhour = timedelta(seconds=1800)

with open("parameter.json", "r") as f:
    params = json.load(f)
owmParams = params["owm"]
calUrl = params["gcalendar"]

current_time = datetime.now()

'''weather Data'''
try:
    with open(weatherFile, "r") as f:
        localData = json.load(f)
    lastWeatherRequest = datetime.fromtimestamp(localData["now"]["dt"])
    timeDiff = current_time - lastWeatherRequest
except:
    #set to timedelta more than 1 day ago
    timeDiffCal = timedelta.max

#check if data is more than 30 min old
weatherError = None
if timeDiff > halfhour:
    #pull new Data   
    try:
        response = requests.get(urlNow, params = owmParams)
        nowWeather = response.json()
        response = requests.get(urlFore, params = owmParams)
        foreWeather = response.json()

        weather = {}
        weather["now"] = nowWeather
        weather["forecast"] = foreWeather

        #save new data
        with open(weatherFile, "w") as f:
            json.dump(weather, f)
    except Exception as e:
        weatherError = e
else:
    weather = localData

tpl = svglue.load(file="template.svg")

if weatherError == None:
    with open("iconsMapping.json", "r") as f:
        iconMap = json.load(f)

    currentTemp = intToString(weather["now"]["main"]["temp"])
    currentFeels = intToString(weather["now"]["main"]["feels_like"])
    currentIcon = "icons/160/"+ str(iconMap[weather["now"]["weather"][0]["icon"]])
    currentWind = intToString(weather["now"]["wind"]["speed"]) + "m/s"
    currentDeg = degrees_to_cardinal(weather["now"]["wind"]["deg"])
    currentGust = intToString(weather["now"]["wind"]["gust"]) + "m/s"
    currentRain = intToString(weather["now"]["rain"]["1h"]) + "mm"

    tpl.set_text("currentTemp", currentTemp)
    tpl.set_text("currentFeelTemp", currentFeels)
    tpl.set_text("currentRain", currentRain)
    tpl.set_text("currentWindDir", currentDeg)
    tpl.set_text("currentWindSpeed", currentWind)
    tpl.set_text("currentWindGust", currentGust)
    tpl.set_svg("curIcon", file=currentIcon)

    forecasts = weather["forecast"]["list"]
    for i in range(5):
        time = forecasts[i]["dt"]
        temp = forecasts[i]["main"]["feels_like"]
        icon = forecasts[i]["weather"][0]["icon"]
        
        timestr = str(datetime.fromtimestamp(timestamp=time, tz=timezone.utc).strftime('%H:%M'))
        temp = str(int(round(temp, 0))) + "C"
        iconName = "icons/80/"+ str(iconMap[icon])

        tpl.set_text("foreTime" + str(i), timestr)
        tpl.set_text("foreTemp" + str(i), temp)
        tpl.set_svg("foreIcon" + str(i), file=iconName)
else:
    tpl.set_text("weatherError", weatherError)


'''Calendar Data'''
calendarError = None
try:
    lastCalendarRequest = datetime.fromtimestamp(os.path.getmtime(calendarFile))
    timeDiffCal = current_time - lastCalendarRequest
except:
    #set to timedelta more than 1 day ago
    timeDiffCal = timedelta.max

if(timeDiffCal > oneday):
    try:
        calendar = requests.get(calUrl).text
        with open(calendarFile, 'w') as calFile:
            calFile.write(calendar)
    except Exception as e:
        calendarError = e

else:
    with open(calendarFile, 'r') as calFile:
        calendar = calFile.read()

if calendarError == None:
    c = Calendar(calendar)
    eventsList = list(c.timeline.now()) + list(c.timeline.start_after(arrow.now()))
    for i in range(3):
        tpl.set_text("calendarEventDesc" + str(i), eventsList[i].name)
        tpl.set_text("calendarEventDate" + str(i), getCalDateString(eventsList[i]))

else:
    tpl.set_text("calendarError", weatherError)

tpl.set_text("updateTime", "last updated: " + current_time.strftime("%H:%M"))

src = tpl.__str__().decode()
with open(outputsvg, 'w') as svgout:
    svgout.write(src)
cairosvg.svg2png(url=outputsvg, write_to=outputpng)