# kindleInfoDisplay
https://wiki.fhem.de/wiki/Kindle_Display
## on Raspberrypi:
```
crontab -e
```
add line at end of file and save
```
*/20 * * * * /usr/bin/python /home/pi/kindle/getWeather.py
```
and run
```
sudo crontab -e
```
add line at end of file and save
```
*/10 * * * * /usr/bin/convert /home/pi/kindle/output.png -colorspace Gray /var/www/html/kindle.png
```
