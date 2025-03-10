#!/usr/bin/env python3
# coding: utf-8

# Modified Code for using the TLV320ADC6140 on the eval board in a PONE Acoustic Test Module
# Modifications are made with the intent of ease of use in the testing environment

import tempfile
import sys
from math import ceil

import pyaudio
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

import subprocess as sp
import time
import configparser
import mutagen

import os
import psutil

import TLV320ADC

def setup_adc(adc, again,dgain,pregain, channel_list):

    #again and dgain are lists with up to 4 elements, one for each channel

    adc.shutdown()
    adc.startup()
    
    adc.set_wake()
    adc.set_power_config()

    adc.set_communication(samplerate=192) # 48, 96, 192, 384 kHz sample rate
    adc.set_output_type(protocol="I2S", word_length=24, compatibility= True)  # 32 bit word length default
    for index, channel in enumerate(channel_list):
        if channel % 2 == 0:
            side = "RIGHT"
        else:
            side = "LEFT"
        adc.set_output_slot(channel=channel, slot_side=side, slot_num=0)
        adc.set_analog_gain(channel, analog_gain_db=again[index])
        adc.set_input(channel=channel, in_type="LINE", config="DIFF", coupling="DC", impedance=10, dynamic_range_processing="OFF")

    #Set any coefficients and mixer settings here
    adc.set_summer(sum_type = "NONE")
    adc.set_dynamic_range_enhancer(trigger_threshold_db = -54, max_gain_db=24, enable_dre=True )

    #Turn on ADC
    adc.set_input_power(channel_list, power="ON", enable = True)
    adc.set_output_enable(channel_list=channel_list, enable=True)
    adc.set_adc_power(mic_bias="OFF", vref_volt=2.75, mic_bias_volt="1.096VREF", change_input_pwr_while_recording=False)

    # Below items can be changed while running

    for index, channel in enumerate(channel_list):
        adc.set_digital_gain_calibration(channel, calibration_db = 0.0)
        adc.set_phase_calibration(channel, calibration_cycles = 0.0)
        adc.set_digital_gain(channel=channel, digital_gain_db = dgain[index], muted=False, soft_step=True, ganged=False)
        adc.set_pre_input_gain(channel=channel,pre_input_gain_db = pregain[index])
        
    print('--- STATUS ---')
    adc.i2cread('ADCX140_SLEEP_CFG')
    adc.i2cread('ADCX140_DEV_STS0')
    adc.i2cread('ADCX140_DEV_STS1')
    print("ADC is ready")

    return



def cputemp():
    with open("/sys/class/thermal/thermal_zone0/temp", 'r') as f:
        return float(f.read().strip()) / 1000


def encoding_command(filename,enc, date_string,title_string,artist_string,album_string,genre_string, channels = 1, bitrate=96, samplerate=48000):
    
    if enc == 'flac':
        outfile = filename+'.flac'
        command = ['flac',
                   '--silent',
                   '--force',
                   '--compression-level-5',
                   '--endian','little',
                   '--channels',str(channels),
                   '--bps','24',
                   '--sample-rate',f"{samplerate}",
                   '--sign',"signed",
                   '-T','date='+date_string,
                   '-T','title='+title_string,
                   '-T','artist='+artist_string,
                   '-T','album='+album_string,
                   '-T','genre='+genre_string,
                   '-',
                   '-o', str(outfile)]

    elif enc == 'opus':
        outfile = filename+'.opus'
        command = ['opusenc',
                   '--bitrate', str(bitrate),
                   '--comp', '10',
                   '--framesize', '20',
                   '--date', date_string,
                   '--title', title_string,
                   '--artist', artist_string,
                   '--album',album_string,
                   '--genre',genre_string,
                   '--raw',
                   '--raw-bits', '24',
                   '--raw-rate', r'{samplerate}',
                   '--raw-chan', str(channels),
                   '--raw-endianness', '0',
                   '--quiet',
                   '-',str(outfile) ]
    elif enc == 'ogg':
        outfile = filename+'.ogg'
        command = ['oggenc',
                   '--quiet',
                   '--raw',
                   '--raw-bits', '24',
                   '--raw-chan', str(channels),
                   '--raw-rate', '192000',
                   '--raw-endianness', '0',
                   '--bitrate', str(bitrate),
                   '--date',date_string,
                   '--title',title_string,
                   '--album',album_string,
                   '--artist',artist_string,
                   '--genre',genre_string,
                   '--output', str(outfile),
                   '-']
        
    return command,outfile

def directory_check(file_path):
    if not os.path.exists(file_path):
        os.mkdir(file_path)
        return 0
    return 0

    
def editmeta_command(outfile,tracknumber,tracktotal,comment, location):
    command = ['./aux/editmeta.py',
               '--tracknumber', str(tracknumber),
               '--tracktotal', str(tracktotal),
               '--location', location,
               '--comment', comment,
               outfile]
    return command
    

def start_temp():
    cmd = ['cat',
           '/sys/bus/w1/devices/28-00000bf3efa6/w1_slave',
           './divider.txt',
           '/sys/bus/w1/devices/28-00000bf3fc08/w1_slave']

    proc = sp.Popen(cmd, stdin=sp.PIPE,stdout=sp.PIPE,stderr=sp.PIPE,universal_newlines=True)
    

    return(proc)

def get_temp(proc):
    
    
    rc = proc.wait()
    out,err = proc.communicate()
    out = out.split('---\n\n')
    
    
    try:
        out1 = out[0].split('\n')
        t1 = out1[1].split('t=')[-1]
        t1 = float(t1)/1000.0
    except:
        t1 = None
    
    try:
        out2 = out[1].split('\n')
        t2 = out2[1].split('t=')[-1]
        t2 = float(t2)/1000.0       
    except:
        t2 = None
    

    return(t1,t2)





def record_sounds(adc, enc,file_path, file_count,  channel_list, title="Sound Recording",
                  location = "Test", artist_string="Me",
                  genre_string = "Nature", file_size_minutes = 15,
                  overflow_exception=True, logfile=None) :
    errorfile =  None
    res_bits = 24
    res_format = pyaudio.paInt24 # 24-bit resolution
    channels = len(channel_list) # 2 channel
    one, two = channel_list
    samplerate = 192000 #48000 # 48kHz sampling rate
    chunk = 9600 # Even multiple for buffer
    record_secs = file_size_minutes * 60 # seconds to record

    bitrate = 256 #kbits per second encoding

    #debug
    soundcard = "ADCX140"
    #soundcard = "VIA"

    tproc = start_temp() # start getting the temps

    audio = pyaudio.PyAudio()
        
    dev_index=None
    
    logfile.write("Audio Cards/n")
    for ii in range(audio.get_device_count()):
        device_name = audio.get_device_info_by_index(ii).get('name')
        logfile.write(str(ii)+"->"+device_name+"\n")
        if soundcard in device_name:
            dev_index = ii

    if dev_index is None:
        logfile.write("Audio card "+soundcard+" is not found!"+"\n")
        dev_index = 0
        #return 0
    
    logfile.write("Full Device Info:"+str(audio.get_device_info_by_index(dev_index))+"\n")
    
    afs = audio.is_format_supported(rate=samplerate, input_device=dev_index, input_channels=channels,
                             input_format=res_format)
    logfile.write("is format supported? "+str(afs)+"\n")
    
    t_out,t_in = get_temp(tproc) # get tempuratures

    logfile.write("Temps  In="+str(t_in)+" Out="+str(t_out)+'\n')
    print("Temps  In="+str(t_in)+" Out="+str(t_out)+'\n')
    
    date_string = time.strftime("%Y-%m-%d")
    album_string = title + " at " + location
    logfile.write("Creating Album: "+ album_string+" on " +
          time.strftime("%Y-%m-%d")+time.strftime(" %I:%M:%S %p")+"\n")

    logfile.flush()
    print("Creating Album: "+ album_string+" on " +
          time.strftime("%Y-%m-%d")+time.strftime(" %I:%M:%S %p")+"\n")
    

    # ping-pong between two processes for continuous processing
    ping = 0
    
    p = [0,0]
    
    # create pyaudio stream
    stream = audio.open(format = res_format,rate = samplerate,channels = channels,
                        input_device_index = dev_index,input = True,
                        frames_per_buffer=chunk)
    
    for file_num in range(1,1+file_count):


        tproc = start_temp() # start getting the temps
        
        date_time_string = time.strftime("%Y%m%d_%H%M%S")

        ch_string = 'ch' + str(one) + '-ch' + str(two)

        title_string = title + "_" + ch_string + "_" + str(file_num) + "_" + date_time_string

        filename = file_path + title_string 

        date_string = time.strftime("%Y-%m-%d")

        #debug
        #comment_string = "Test Comment"
        comment_string = "Total Gain: "+str(adc.total_gain())+" dB"


        command,outfile = encoding_command(filename,enc, date_string,title_string,artist_string,
                                           album_string,genre_string, channels, bitrate, samplerate)

        logfile.write("CPU Temp="+str(cputemp())+"\n")

        p[ping] = sp.Popen(command, bufsize = 4*samplerate*2, stdin=sp.PIPE)  # bufsize = 4*48000*2
        
        logfile.write("recording file:"+outfile+"\n")
        logfile.flush()


        # loop through stream and append audio chunks to frame array
        for ii in range(0, ceil((samplerate/chunk)*record_secs)):
            data = stream.read(chunk, exception_on_overflow=overflow_exception)
            p[ping].stdin.write(data)

        p[ping].stdin.close()
        
        
        metadata_command = editmeta_command(outfile,tracknumber=file_num,tracktotal=file_count,
                                            comment=comment_string, location=location)
        p_meta = sp.Popen(metadata_command)
        
        ping = (ping + 1) & 1  # return zero or one
        if p[ping] != 0:
            p[ping].wait()
            
            
        t_out,t_in = get_temp(tproc) # get temperatures
        
        logfile.write("Temps  In="+str(t_in)+" Out="+str(t_out)+'\n')

        logfile.write("finished recording"+"\n")


    # stop the stream, close it, and terminate the pyaudio instantiation
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # clean up
    ping = (ping + 1) & 1  # return zero or one
    p[ping].wait()
    
        
    success_flag = 1
    
    return success_flag


def init_arecord():
    command = "arecord -L"
    sp.run(command.split())
    return



def shutdown():
    command = '/usr/bin/sudo /usr/sbin/shutdown -h now'
    process = sp.Popen(command.split(),stdout=sp.PIPE)
    #output = process.communicate()[0]
    #print(output)
    #return output

def wireless(state):

    if state:
        command = '/usr/bin/sudo /usr/sbin/ifconfig wlan0 up'
    else:
        command = '/usr/bin/wall "Warning WiFi going down in 120 seconds" && /usr/bin/sleep 120 && /usr/bin/sudo /usr/sbin/ifconfig wlan0 down'
        #command = "/usr/bin/sudo /usr/sbin/ifconfig wlan0 down"
    process = sp.Popen(command,shell=True) #using shell, but command is fixed

def parse_gain_string(st):
	stl = st.split("/")
	gain = [float(x) for x in stl]
	if len(gain) == 1:
		gain.append(gain[0])
	return gain
	
#Main code

init_arecord()

config = configparser.ConfigParser()
configfilename = '/home/bukavac/Desktop/Audio_Software/audio-recording-firmware-raspi-tlv320adc6140/aux/config.ini'

config.read(configfilename)
print(configfilename)

if config.sections() == []:
    # write out a config file
    config['audio_files']={}
    config['state']['run'] = "record complete"
    config['audio_files']['title'] = "Title"
    config['audio_files']['location'] = "Location"
    config['audio_files']['artist'] = "Artist"
    config['audio_files']['genre'] = "Nature"
    config['audio_files']['encoding'] = 'opus'  # 'opus', 'flac', 'ogg'
    config['audio_files']['filePath'] = "/media/pi/LINUXUSB/recordings/"

    config['settings']={}
    config['settings']["hours"] = "12.0"
    config['settings']["analoggain"] = "30"
    config['settings']["digitalgain"] = "20"
    config['settings']["turnoff"] = "No"
    config['settings']["wifi_on_during_recording"] = "Yes"
    config['settings']["fileminutes"] = "30"
    config['settings']["logfile"] = "logfile.txt"
    print("Writing out a new 'config.ini' file")
    with open('configfilename','w') as cfile:
        config.write(cfile)

elif config['state']['run'] == "record":

#    config['state']['run'] = 'record started'

    #read config
    title = config['audio_files']['title']
    location = config['audio_files']['location']
    artist = config['audio_files']['artist']
    genre = config['audio_files']['genre']
    enc = config['audio_files']['encoding']
    file_path = config['audio_files']['filepath']

    again = parse_gain_string(config['settings']["analoggain"])
    dgain = parse_gain_string(config['settings']["digitalgain"])
    
    pregain = parse_gain_string(config.get('settings','pregain', fallback='0.0'))

    channel_list_aux = config['settings']["channel_list"].split(',')
    channel_list = [int(i) for i in channel_list_aux]
       
    hours = float(config['settings']["Hours"])
    fileminutes = float(config['settings']["fileminutes"])
    turnoff = config['settings']["turnOff"]
    wifi_on = config['settings']["wifi_on_during_recording"]
    logfile = open(config['settings']['logfile'], "a")
    logfile.write("\n"+"*+*"+"*"*30+"\n")

    logfile.write("Starting Run at"+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")

    file_count = int(hours*60.0/fileminutes)
    logfile.write(" Run will produce "+str(file_count)+" files each of "+str(fileminutes)+" minutes."+"\n")

    #print("Delay until startup completes to load AlSA, etc")

    #for d in range(1,30):
    #    print(d, end=',')
    #    time.sleep(1)

    #print("done.")


    with open(configfilename,'w') as cfile:
        config.write(cfile)

    logfile.write("Path:"+file_path+"\n")

    #debug
    #adc1 = DUMMYADC()
    adc1 = TLV320ADC.TLV320ADC()

    #debug
    setup_adc(adc1,again=again,dgain=dgain,pregain=pregain, channel_list=channel_list)

    status = adc1.get_status()
    if status:
        logfile.write("Error in status of ADC")
        logfile.close()
        print("Error in status of ADC")
        sys.exit()

    print("Wifi flag = ",wifi_on)

    if wifi_on == "No":
        wireless(False)
        logfile.write("Wifi will be shut down during recording"+"\n")
        logfile.flush()

    directory_check(file_path = file_path)

    record_sounds(adc=adc1,enc=enc,file_path=file_path,file_count=file_count,
                  title=title, location = location, artist_string= artist,
                  genre_string = genre, file_size_minutes = fileminutes, channel_list = channel_list,
                  overflow_exception = False,
                  logfile=logfile)

    # Sleep after having done a run
    adc1.set_sleep()
    adc1.shutdown()

    
#    config['state']['run'] = 'record complete'
    with open(configfilename,'w') as cfile:
        config.write(cfile)
    logfile.write("Finished recording at "+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")


    if wifi_on == "No":
        wireless(True)
        logfile.write("Wifi turned back on at "+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")
    
    
    if turnoff == "Yes":
        logfile.write("Shutting down at "+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")
        logfile.close()
        shutdown()
else:
    logfile = open(config['settings']['logfile'], "a")
    logfile.write("Config file shows this is already recorded\n")

logfile.close()
