# Joulie-16-LCD
buildroot config for a Battery info screen with web ui for the Raspberry Pi
reworked to utilise the UDP Multicast protocoll enabled via DIP Switch 8 since version 1.14 of the JouLie-16 

## Required HW:

× Raspberry Pi

× 20x4 I2C LCD

× 3.3V to 5V Level shifter

× Class 10 Micro SD Card with at least 1GB


## Instructions for building:

* Get the latest stable Buildroot release from (https://buildroot.org/downloads/buildroot-2019.08.tar.gz)
* Unpack the buildroot tar
* Clone this repo
* Move the overlay dir into the unpacked buildroot dir
* Move the config file into the buildroot dir and rename it to .config
* Open a Terminal in the buildroot dir
* Run `make menuconfig` and check the `Target options` to make sure the config was loaded
  - Target Architecture (ARM (little endian))
  - Target Binary Format (ELF)
  - Target Architecture Variant (arm1176jzf-s)
* Quit the menuconfig by hitting *ESC* until you return to the Terminal
* Run `make` to start building your image. This requires an active internet connection to download all the packages. This will take a couple of hours depending on your system.
* Once finished, navigate your file browser to the **output/images** dir where you will find a **sdcard.img** file. This is your SD card image.
* Alternatively you can download a prebuilt Image here: (https://drive.google.com/file/d/1jDVkfmO4_kC0xCqfQeMeR_219UbtfRNR/view?usp=sharing)
* Write that image file to your SD card either using dd on Linux systems or using https://etcher.download
* Unmount the SD Card and plug it into your Pi
* Connect the I2C LCD to the Pi according to the instructions below. Most LCD's will run off of 3.3V with usable but not good contrast, so a level shifter is recommended.

LCD SCL → Shift 1 → Pi Pin 5

LCD SDA → Shift 2 → Pi Pin 3

LCD GND → Shift GND → Pi Pin 6

LCD Vcc → Pi Pin 2

Shift HV → Pi Pin 4

Shift LV → Pi Pin 1

* When directly connecting the LCD to the Pi, power the LCD from Pin 1 instead of Pin 2 from the Pi
* Connect the Pi to the same network as the BMS. This can be through a switch as long as they're in the same network and the Pi can receive the UDP Multicast packets
* Power up the Pi
* The Pi should boot within ~2 minutes
* You should now see the battery status on the LCD
* Now you can open up a browser and go to (http://autarctech-bms/) to view the web interface.
* If you are directly connected to the BMS then call up this address: http://10.214.161.1
* Debugging via SSH:
  - Username: root
  - Password: AutarcTech

### To Do:
- [ ] Proper interactive Web Interface
- [ ] CANBUS Mode
- [ ] Cloud?
- [ ] Better local screen. Maybe a TFT? Or a HDMI Screen?
