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
import datetime
import svglue

def degrees_to_cardinal(d):
    dirs = ['N', 'NNO', 'NO', 'ONO', 'O', 'OSO', 'SO', 'SSO', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def getCalDateString(event):
    if(event.all_day):
        if(event.duration.days > 1):
            out = event.begin.format("DD.MM.") + " bis "  + event.end.format("DD.MM.")
        else:
            out = event.begin.format("DD.MM.")
    else:
        beginTime = datetime.datetime.fromtimestamp(event.begin.timestamp())
        endTime = datetime.datetime.fromtimestamp(event.end.timestamp())
        out=  beginTime.strftime("%d.%m. von %H:%M") + " bis "  + endTime.strftime("%H:%M")
    return out

urlNow = "https://api.openweathermap.org/data/2.5/weather"
urlFore = "https://api.openweathermap.org/data/2.5/forecast"
outputsvg = "output.svg"
outputpng = "output.png"
weatherFile = "weatherData.json"
calendarFile = "calendar.ics"

with open("parameter.json", "r") as f:
    params = json.load(f)
owmParams = params["owm"]
calUrl = params["gcalendar"]

current_time = datetime.datetime.now()

'''weather Data'''
try:
    with open(weatherFile, "r") as f:
        localData = json.load(f)
    lastWeatherRequest = datetime.datetime.fromtimestamp(localData["now"]["dt"])
except:
    #set to random timestamp more than 30 min ago
    lastWeatherRequest = datetime.datetime.fromtimestamp(1326244364)

#check if data is more than 30 min old
timeDiff = current_time - lastWeatherRequest
weatherError = None
if timeDiff.seconds > 1800:
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

    currentTemp = str(int(round(weather["now"]["main"]["temp"], 0))) + "C fuehlt sich an wie " + str(int(round(weather["now"]["main"]["feels_like"], 0))) + "C"
    currentIcon = "icons/"+ str(iconMap[weather["now"]["weather"][0]["icon"]])
    currentWind = str(weather["now"]["wind"]["speed"]) + "m/s von " + degrees_to_cardinal(weather["now"]["wind"]["deg"])

    tpl.set_text("curTemp", currentTemp)
    tpl.set_text("curWind", currentWind)
    tpl.set_svg("curIcon", file=currentIcon)

    forecasts = weather["forecast"]["list"]
    for i in range(5):
        time = forecasts[i]["dt"]
        temp = forecasts[i]["main"]["feels_like"]
        icon = forecasts[i]["weather"][0]["icon"]
        
        timestr = str(datetime.datetime.fromtimestamp(timestamp=time, tz=datetime.timezone.utc).strftime('%H:%M'))
        temp = str(int(round(temp, 0))) + "C"
        iconName = "icons/"+ str(iconMap[icon])

        tpl.set_text("foreTime" + str(i), timestr)
        tpl.set_text("foreTemp" + str(i), temp)
        tpl.set_svg("foreIcon" + str(i), file=iconName)
else:
    tpl.set_text("weatherError", weatherError)


'''Calendar Data'''
calendarError = None
try:
    lastCalendarRequest = datetime.datetime.fromtimestamp(os.path.getmtime(calendarFile))
except:
    #set to random timestamp more than 1 day ago
    lastCalendarRequest = datetime.datetime.fromtimestamp(1326244364)
timeDiffCal = current_time - lastCalendarRequest

if(timeDiffCal.days > 1):
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
    eventsList = list(c.timeline.start_after(arrow.now()))
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