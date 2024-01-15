# kindleInfoDisplay
https://wiki.fhem.de/wiki/Kindle_Display
## on Raspberrypi:
```
crontab -e
```
add line at end of file and save
```
*/20 * * * * /usr/bin/python /home/pi/kindleInfoDisplay/getWeather.py
```
and run
```
sudo crontab -e
```
add line at end of file and save
```
*/5 * * * * /usr/bin/convert /home/pi/kindleInfoDisplay/output.png -colorspace Gray /var/www/html/kindle.png
```
