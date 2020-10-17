# from __future__ import division
from bottle import run, route, request, response
from threading import Thread
from neopixel import *
import random
import time
import json
import string
import subprocess
# LED strip configuration:
LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0
LED_STRIP      = ws.WS2812_STRIP

# management variables
sections = None
settings = {
    "brightnessChangeMode": "default",
    "colorChangeMode": "swipe",
    "fadeDuration": 300,
    "swipeSpeed": 50
}
if not sections:
    print "no sections loaded"
    sections = {
        '0': {
            'begin': 0,
            'end': LED_COUNT-1,
            'uid': 'abcdef',
            'dynamicFunction': False
        }
    }
activeThreads = {}
# global brightness_percent
brightness_percent = 80
brightness = 204
previousBrightness = brightness
savedBrightness = brightness
timerSeconds = 0
timerActive = False
def runBottle():
    @route('/setSection', method=['OPTIONS', 'POST'])
    def setSection():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'setSection() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            newSectionBegin, newSectionEnd = receivedJSON['newSection']
            print newSectionBegin, newSectionEnd
            deleteAfterIteration = []
            sectionsToAdd = []
            # collision detection
            for name in sections:
                print 'old:', sections[name]['uid'], sections[name]['begin'], '-', str(sections[name]['end'])+'; new:', newSectionBegin, '-', newSectionEnd
                # print type(sections[name]['begin']), type(sections[name]['end']), type(newSectionBegin), type(newSectionEnd)
                if newSectionBegin == sections[name]['begin']: # begin is the same
                    if newSectionEnd == sections[name]['end']: # sections are identical
                        deleteAfterIteration.append(name)
                    elif newSectionEnd < sections[name]['end']: # existing section now begins where new section ends
                        sections[name]['begin'] = newSectionEnd+1
                    elif newSectionEnd > sections[name]['end']: # existing section will be removed
                        deleteAfterIteration.append(name)
                    else:
                        print 'this should not happen (newSectionBegin == sections[name][\'begin\'])'
                elif newSectionEnd == sections[name]['end']: # end is the same
                    if newSectionBegin == sections[name]['begin']: # sections are identical
                        deleteAfterIteration.append(name)
                    elif newSectionBegin > sections[name]['begin']: # existing section now ends where new section begins
                        sections[name]['end'] = newSectionBegin-1
                    elif newSectionBegin < sections[name]['begin']: # existing section will be removed
                        deleteAfterIteration.append(name)
                    else:
                        print 'this should not happen (newSectionEnd == sections[name][\'end\'])'
                elif newSectionBegin < sections[name]['begin']: # if new section begins before existing section begins
                    if newSectionEnd < sections[name]['begin']: # if new section also ends before before existing section begins
                        continue
                    elif newSectionEnd > sections[name]['end']: # if new section overwrites existing section, remove existing section
                        deleteAfterIteration.append(name)
                    elif newSectionEnd >= sections[name]['begin']: # if new section only cuts into existing section, truncate existing section
                        sections[name]['begin'] = newSectionEnd+1
                    else:
                        print 'this should not happen (newSectionBegin < sections[name][\'begin\'])'
                elif newSectionBegin > sections[name]['begin']: # if new section begins after existing section begins
                    if newSectionBegin > sections[name]['end']: # if new section only begins after existing section ends
                        continue
                    elif newSectionEnd > sections[name]['end']: # if new section ends after existing section ends, truncate existing section
                        sections[name]['end'] = newSectionBegin-1
                    elif newSectionEnd < sections[name]['end']: # if new section ends before existing section ends, truncate existing section and make new section from second part
                        uid = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                        sectionsToAdd.append({
                            'begin': newSectionEnd+1,
                            'end': sections[name]['end'],
                            'uid': uid,
                            'dynamicFunction': False
                        })
                        sections[name]['end'] = newSectionBegin-1
                    else:
                        print 'this should not happen (newSectionBegin > sections[name][\'begin\'])'
                else:
                    print 'this should not happen at all!'
                    
            uid = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            sectionsToAdd.append({
                'begin': newSectionBegin,
                'end': newSectionEnd,
                'uid': uid,
                'dynamicFunction': False
            }) # finally add new section after all existing sections have been built around it
            clearNewSection(newSectionBegin, newSectionEnd)
            for key in deleteAfterIteration:
                print 'deleting sections["'+key+'"]'
                if key in activeThreads:
                    print 'active threads:', activeThreads
                    print 'stopping thread for', key
                    # activeThreads[key].stop()
                del sections[key]
            print 'active threads:', activeThreads
            deleteAfterIteration = [] # reset

            for section in sectionsToAdd:
                for x in range(LED_COUNT):
                    if not str(x) in sections:
                        sections[str(x)] = section
                        break
            sectionsToAdd = [] # reset
            exportData(sections, 'sections.json')
        return sections
    
    @route('/removeSection', method=['OPTIONS', 'POST'])
    def removeSection():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'removeSection() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            print sections[str(receivedJSON['deleteSection'])]
            clearNewSection(sections[str(receivedJSON['deleteSection'])]['begin'], sections[str(receivedJSON['deleteSection'])]['end'])
            del sections[str(receivedJSON['deleteSection'])]
            exportData(sections, 'sections.json')
        return sections

    @route('/getSections', method=['OPTIONS','GET'])
    def getSection():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        return sections
    
    @route('/getLedCount', method=['OPTIONS','GET'])
    def getLedCount():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        return {'ledCount': LED_COUNT}
    
    @route('/getCpuTemp', method=['OPTIONS','GET'])
    def getCpuTemp():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        cpuTemp = float(subprocess.check_output(['cat','/sys/class/thermal/thermal_zone0/temp'])[:-1])/1000
        print cpuTemp
        return {'cpuTemp': cpuTemp}
    
    @route('/getSettings', method=['OPTIONS', 'GET'])
    def getSettings():
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        return settings

    @route('/setSettings', method=['OPTIONS', 'POST'])
    def setSettings():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'setSettings() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            for x in receivedJSON:
                settings[x] = receivedJSON[x]
            print settings
        return settings

    @route('/assignFunction', method=['OPTIONS', 'POST'])
    def assignFunction():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'assignFunction() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            if len(receivedJSON)>1:
                print "more than one function assignment at a time"
            for functionAssignment in receivedJSON:
                print "functionAssignment", functionAssignment
                if functionAssignment['functionType'] == 'dynamic':
                    ledFunctionThread = dynamicLedFunction(functionAssignment)
                    ledFunctionThread.setDaemon(True)
                    activeThreads[functionAssignment['section']] = ledFunctionThread
                    ledFunctionThread.start()
                elif functionAssignment['functionType'] == 'static':
                    staticLedFunction(functionAssignment)
                else:
                    print 'something went wrong'
                    return {"success": False}
            return {"success": True}

    @route('/setColorSimple', method=['OPTIONS', 'POST'])
    def setColorSimple():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'setColorSimple() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            print receivedJSON
            fillColorRGB(0, LED_COUNT, *receivedJSON["setColorSimple"])            
        return {"success": True}

    @route('/setColorGradient', method=['OPTIONS', 'POST'])
    def setColorGradient():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'setColorGradient() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            print receivedJSON
            # fillColorRGB(0, LED_COUNT, *receivedJSON["setColorGradient"][0])
            print receivedJSON["setColorGradient"]
            fillGradientColorRGB(0, LED_COUNT, receivedJSON["setColorGradient"])          
        return {"success": True}

    @route('/setBrightness', method=['OPTIONS', 'POST'])
    def setBrightness():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print 'setBrightness() called, received', request.content_type
        receivedJSON = request.json
        if receivedJSON:
            print receivedJSON
            global brightness_percent 
            global brightness
            global previousBrightness
            brightness_percent = float(receivedJSON['brightness'])
            brightness = int(brightness_percent/100*255)
            if brightness > 255:
                brightness = 255
            print brightness_percent
            print brightness
            brightnessSet()
            return {"brightness": brightness}

    @route('/getBrightness', method=['OPTIONS', 'GET'])
    def getBrightness():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        print brightness_percent
        return {"brightness": brightness_percent}

    @route('/powerState', method=['OPTIONS', 'POST'])
    def powerState():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        receivedJSON = request.json
        if receivedJSON:
            global brightness
            global previousBrightness
            global savedBrightness
            global brightness_percent
            if receivedJSON['on']:
                brightness = savedBrightness
                brightnessSet()
                brightness_percent = int(brightness/255)
                return {'on': True}
            else:
                savedBrightness = brightness
                brightness = 0
                brightness_percent = 0
                brightnessSet()
                return {'on': False}

    @route('/sleepTimer', method=['OPTIONS', 'POST'])
    def sleepTimer():
        global timerSeconds
        global timerActive
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        receivedJSON = request.json
        if receivedJSON:
            timerActive = (receivedJSON["active"] == True)
            print timerActive
            if "seconds" in receivedJSON:
                timerSeconds = int(receivedJSON["seconds"])
                print timerSeconds
            return {
                "seconds": timerSeconds,
                "active": timerActive
            }

    @route('/getSleepTimer', method=['OPTIONS', 'GET'])
    def sleepTimerGet():
        response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        return {
                "seconds": timerSeconds,
                "active": timerActive
            }
            
        
    run(host='0.0.0.0',port=8080,debug=True)

def brightnessSet():
    global previousBrightness
    global brightness
    print "change from",previousBrightness,"to",brightness
    print "mode:", settings["brightnessChangeMode"]
    if settings["brightnessChangeMode"] == "fade":
        duration = float(settings["fadeDuration"])/1000
        if brightness >= previousBrightness:
            steps = brightness - previousBrightness
            if steps > 0:
                interval = duration/steps 
                for i in range(2,steps):
                    strip.setBrightness(previousBrightness + i-1)
                    if i%2 == 0:
                        strip.show()
                    time.sleep(interval)                    
        if brightness <= previousBrightness:
            steps = previousBrightness - brightness
            if steps > 0:
                interval = duration/steps 
                for i in range(2,steps):
                    strip.setBrightness(previousBrightness - i-1)
                    if i%2 == 0:
                        strip.show()
                    time.sleep(interval)
        strip.show()
        previousBrightness = brightness
    else:
        strip.setBrightness(brightness)
        strip.show()

def exportData(data,filename):
    try:
        with open(filename,'w') as file:
            print("exported data")
            json.dump(data,file,indent=4)
    except Exception:
        print "Exception exporting data"

def clearNewSection(begin, end):
    print 'clearing section from', begin, 'to', end
    for i in range(begin, end+1):
        strip.setPixelColorRGB(i, 0, 0, 0)
    strip.show()

def staticLedFunction(arguments):
    sectionId = arguments['section']
    functionName = arguments['functionName']
    parameters = arguments['arguments']
    begin, end = sections[str(sectionId)]['begin'], sections[str(sectionId)]['end']
    if functionName == 'singleColor':
        fillColorRGB(begin, end, *parameters)
    elif functionName == 'gradientColor':
        fillGradientColorRGB(begin, end, parameters)
    else:
        print 'function', functionName, 'is not known'

def fillColorRGB(begin, end, r, g, b):
    print 'singleColor', begin, end
    if settings["colorChangeMode"] == "swipe":
        interval = 1.0/int(settings["swipeSpeed"])
        print interval
        start = time.time()
        for i in range(begin, end):
            strip.setPixelColorRGB(i, r, g, b)
            if i%2 == 0:
                strip.show()
            time.sleep(interval)
        end = time.time()
        print "time elapsed:", end-start
    elif settings["colorChangeMode"] == "fade":
        prevColors = []
        for i in range(begin, end):
            RGBint = strip.getPixelColor(i)
            prevColors.append([RGBint & 255, (RGBint >> 8) & 255, (RGBint >> 16) & 255])
        print len(prevColors)
        # transition from prev colors to current colors
    else:
        for i in range(begin, end):
            strip.setPixelColorRGB(i, r, g, b)
        strip.show()

def fillGradientColorRGB(begin, end, gradient):
    target = {}
    r1 = gradient[0][0]
    g1 = gradient[0][1]
    b1 = gradient[0][2]
    r2 = gradient[1][0]
    g2 = gradient[1][1]
    b2 = gradient[1][2]
    print begin, end
    for i in range(end-begin+1):
        target[begin+i] = [
            r1 + (r2-r1) * i / (end-begin+1),
            g1 + (g2-g1) * i / (end-begin+1),
            b1 + (b2-b1) * i / (end-begin+1)
        ]

    if settings["colorChangeMode"] == "swipe":
        interval = 1.0/int(settings["swipeSpeed"])
        print interval
        start = time.time()
        for i in range(end-begin+1):
            print begin+i, target[begin+i]
            strip.setPixelColorRGB(begin+i, *target[begin+i])
            if i%2 == 0:
                strip.show()
            time.sleep(interval)
        end = time.time()
        strip.show()
        print "time elapsed:", end-start
    elif settings["colorChangeMode"] == "fade":
        prevColors = []
        for i in range(end-begin+1):
            RGBint = strip.getPixelColorRGB(begin+i, *target[i])
            prevColors.append([RGBint & 255, (RGBint >> 8) & 255, (RGBint >> 16) & 255])
        print len(prevColors)
        # transition from prev colors to current colors
    else:
        for i in range(begin, end):
            strip.setPixelColorRGB(i, *target[i])
        strip.show()

class dynamicLedFunction(Thread):
    def __init__(self, arguments):
        super(dynamicLedFunction, self).__init__()
        self.sectionId = arguments['section']
        self.functionName = arguments['functionName']
        sections[str(self.sectionId)]['dynamicFunction'] = True
    def run(self):
        print 'Running thread for', self.sectionId, 'with function', self.functionName
        exec(self.functionName+'('+str(self.sectionId)+')')

def flash(sectionId):
    dynamicFunction = sections[str(sectionId)]['dynamicFunction']
    uid = sections[str(sectionId)]['uid']
    begin = sections[str(sectionId)]['begin']
    end = sections[str(sectionId)]['end']
    clearNewSection(begin, end)
    initialUid = uid
    initiallyDynamicFunction = dynamicFunction
    i = begin
    while uid == initialUid and dynamicFunction == initiallyDynamicFunction:
        dynamicFunction = sections[str(sectionId)]['dynamicFunction']
        uid = sections[str(sectionId)]['uid']
        begin = sections[str(sectionId)]['begin']
        end = sections[str(sectionId)]['end']
        # print begin, end, uid, dynamicFunction
        # if uid != initialUid or :
        #     print 'function not in use'
        #     break
        # else:
        strip.setPixelColor(i, Color(0,0,100))
        strip.show()
        time.sleep(1)
        strip.setPixelColor(i, Color(0,0,0))
        strip.show()
        i += 1
        if i > end:
            i = begin

def flashingStars(sectionId):
    dynamicFunction = sections[str(sectionId)]['dynamicFunction']
    uid = sections[str(sectionId)]['uid']
    begin = sections[str(sectionId)]['begin']
    end = sections[str(sectionId)]['end']
    clearNewSection(begin, end)
    initialUid = uid
    initiallyDynamicFunction = dynamicFunction
    while uid == initialUid and dynamicFunction == initiallyDynamicFunction:
        dynamicFunction = sections[str(sectionId)]['dynamicFunction']
        uid = sections[str(sectionId)]['uid']
        begin = sections[str(sectionId)]['begin']
        end = sections[str(sectionId)]['end']
           

def rainbow(sectionId):
    dynamicFunction = sections[str(sectionId)]['dynamicFunction']
    uid = sections[str(sectionId)]['uid']
    begin = sections[str(sectionId)]['begin']
    end = sections[str(sectionId)]['end']
    clearNewSection(begin, end)
    initialUid = uid
    initiallyDynamicFunction = dynamicFunction
    i = begin
    while uid == initialUid and dynamicFunction == initiallyDynamicFunction:
        dynamicFunction = sections[str(sectionId)]['dynamicFunction']
        uid = sections[str(sectionId)]['uid']
        begin = sections[str(sectionId)]['begin']
        end = sections[str(sectionId)]['end']

        pass

        i += 1
        if i > end:
            i = begin

class timerBackgroundThread(object):
    def __init__(self):
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        global timerSeconds
        global timerActive
        global savedBrightness
        global brightness
        while True:
            while timerActive:
                timerSeconds -= 1
                print timerSeconds
                if timerSeconds < 1:
                    timerActive = False
                    savedBrightness = brightness
                    brightness = 0
                    brightnessSet()
                time.sleep(1)

if __name__ == "__main__":
    try:
        strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
        strip.begin()
        try:
            with open('sections.json','r') as file:
                sections = json.load(file)
        except Exception:
            print "sections.json not found"
        try:
            with open('settings.json','r') as file:
                settings = json.load(file)
        except Exception:
            print "settings.json not found"
        timerThread = timerBackgroundThread()
        runBottle()
    except KeyboardInterrupt:
        print "exit"
        exit()