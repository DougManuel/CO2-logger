## CO2 data logger with a temperature, pressure and altimer sensor

import time
import board
import busio
import digitalio
import adafruit_scd30 #CO2 sensor
import adafruit_bmp280 #Temperature, pressure and altimeter sensor
import adafruit_pcf8523 #Realtime clock (RTC)
import adafruit_sdcard #data storage
import storage
import neopixel #light

# define constant variables
days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

# CO2 warning levels (ppm)
poor = 2000 
fair = 1000
good = 700

# pin for SPI chip select line to wake up SD card. You'll need to change this pin if name or niumber you aren't using D10 on your controller.
sd_cs = board.D10

# set up the SPI and I2C communicaations protocols
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(sd_cs)
i2c = busio.I2C(board.SCL, board.SDA)

# set up the sensors and data logger
scd = adafruit_scd30.SCD30(i2c) #0x61 address
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c) # 0x77
bmp280.sea_level_pressure = 1013.25 # calibrate the pressure

rtc = adafruit_pcf8523.PCF8523(i2c)  # 0x68
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)

# mount the SD card to save files in the /sd folder
storage.mount(vfs, "/sd")

# setup the neopixel. This code will need to be changed if you 
# use a microcontroller other than an Adafruit feather 
pixels = neopixel.NeoPixel(board.NEOPIXEL, n=1, brightness=0.05, auto_write=False)

# Create a CSV data loger file. The file name includes the date, hour and min in the name.
# i.e If we started logging on April 14, 2021 at 8:30 am the file would be saved in: co2log_2021_04_14-08-30.csv 

# record the current date and time.
t = rtc.datetime  

# create the name of the csv file that will log the data
filename = "co2log_" + f"{t.tm_year}-{t.tm_mon:02d}-{t.tm_mday:02d}_{t.tm_hour:02d}-{t.tm_min:02d}" + ".csv"

# print out the file name to the serial port, for testing on your computer.
print("logging to: ", filename)

# create for the csv file with a header with the names for all the variables. 
with open("/sd/" + filename, "w") as f:
    f.write("date, time, altitude, CO2, humidity, pressure, temperature\n")

# take measurements from the sensors. Write the values to the monitor and add to the data logger 
while True:

    pixels.fill((0, 0, 255)) # Blue light indicator when writing to the SD card. Don't unplug if the blue light is on!
    pixels.show()

    # record the date and time.
    t = rtc.datetime

    # check if data is available
    if scd.data_available:
        
        # save data to SD card
        with open("/sd/" + filename, "a") as f:
            f.write(f"{t.tm_year}-{t.tm_mon:02d}-{t.tm_mday:02d},") # year
            f.write(f"{t.tm_hour:02d}-{t.tm_min:02d}-{t.tm_sec:02d},") # month
            f.write(f"{bmp280.altitude:1f},{scd.CO2:1f},{scd.relative_humidity:1f},{bmp280.pressure:1f},{bmp280.temperature:1f}\n")
            
        # print to serial monitor (if connected)
        print("%s %d/%d/%d %02d:%02d:%02d" % (days[t.tm_wday], t.tm_mday, t.tm_mon, t.tm_year, t.tm_hour, t.tm_min, t.tm_sec))
        print("Altitude: %0.1f meters" % bmp280.altitude)
        print("CO2: %0.1f ppm" % scd.CO2)
        print("Humidity: %0.1f %%rH" % scd.relative_humidity)
        print("Pressure: %0.1f hPa" % bmp280.pressure)
        print("Temperature: %0.1f C" % bmp280.temperature)
        print("")
    
    time.sleep(1)

    # CO2 color warnings for Dotpixel
    if scd.CO2 > poor:
        pixels.fill((255, 0, 0)) # red. Yikes! 
    elif scd.CO2 > fair:
        pixels.fill((255, 126, 0)) # orange
    elif scd.CO2 > good:
        pixels.fill((255, 255, 0)) # yellow
    else: # very good
        pixels.fill((0, 255, 0)) # green
    pixels.show()

    time.sleep(4)