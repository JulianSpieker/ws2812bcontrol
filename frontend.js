var brightness;
var sections;
var settings;
var timerSet = false;
var seconds;
var ip = '192.168.2.144';
document.addEventListener('DOMContentLoaded',
async function() {
    advancedMode = (getCookie('advancedMode') == 'true');
    if (advancedMode) {
        advancedModeOn();
        console.log("advancedModeOn");;
    } else {
        console.log("advanced mode is off");
        advancedModeOff();
    }
    darkTheme = (getCookie('darkTheme') == 'true');
    if (darkTheme) {
        console.log("dark theme activated");
        changeTheme("dark");
    }
    ledCountJson = await XHRget('getLedCount');
    brightnessJson = await XHRget('getBrightness');
    settings = await XHRget('getSettings');
    var ledCount = ledCountJson['ledCount'];
    brightness = brightnessJson['brightness'];
    sleepTimerStatus = await XHRget('getSleepTimer');
    sleepTimerStatus["active"];
    if (sleepTimerStatus["active"] === true) {
        console.log("shutdown timer active");
        startCountdown(sleepTimerStatus["seconds"]);
        timerSet = true;
        updateButtonState(sleepTimerStatus);
        document.getElementById('sleepTimerDisplayInput').disabled = true;
    } else {
        console.log("shutdown timer inactive");
    }
    // console.log(settings);
    // if (settings) {
    //     for (key in Object.keys(settings)) {
    //         console.log(key, settings[key]);
    //         document.getElementById(key).value = settings[key];
    //     }
    // }
    setBrightnessIndicator(brightness);
    console.log(brightness);
    ledStripContainer = document.getElementById('ledStripContainer');
    hnode = document.createElement('h1');
    hnode.innerHTML = 'LED Visualisation';
    ledStripContainer.appendChild(hnode);
    for (let i=0; i<ledCount; i++) {
        ledNode = document.createElement('div');
        ledNode.id = 'led'+i;
        ledNode.className = 'ledElement';
        ledNode.setAttribute('onclick','stripSelection('+i+')');
        idNode = document.createElement('div');
        idNode.className = 'textNode idNode'
        idNode.innerHTML = i;
        ledNode.appendChild(idNode);
        ledStripContainer.appendChild(ledNode);
    }
    sections = await XHRget('getSections');
    updateSectionContainer();
    updateButtonState();
})

function advancedModeOff() {
    advancedMode = false;
    document.cookie = 'advancedMode=false';
    console.log('Advanced mode off');
    document.getElementById('rcContainer').style.display = "block";
    document.getElementById('buttonContainer').style.display = 'none';
    document.getElementById('sectionsContainer').style.display = 'none';
    document.getElementById('sleepTimerContainer').style.display = 'none';
    document.getElementById('ledStripContainer').style.display = 'none';
}

function advancedModeOn() {
    advancedMode = true;
    document.cookie = 'advancedMode=true';
    console.log('Advanced mode on');
    document.getElementById('rcContainer').style.display = "block";
    document.getElementById('buttonContainer').style.display = "block";
    document.getElementById('sectionsContainer').style.display = "block";
    document.getElementById('sleepTimerContainer').style.display = "block";
    document.getElementById('ledStripContainer').style.display = "block";
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
        c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
        }
    }
    return "";
}

async function saveSettings() {
    var formElements = document.getElementById("settingsForm").elements;
    // let settings = {}
    for (var i = 0; i < formElements.length; i++) {
        settings[formElements[i].name] = formElements[i].value;
    }
    console.log(settings);
    ip = settings["ipAdress"];
    response = await setSettings();
    console.log(response);
    if (response["brightnessChangeMode"]) {
        alert("Settings saved!");
    }
}

async function setSettings() {
    console.log('Sending content:\n', settings);
    response = await XHRpost('setSettings', JSON.stringify(settings));
    console.log(response);
    return response;
}

function updateSectionContainer() {
    document.getElementById('sectionsContainer').innerHTML = '';
    hnode = document.createElement('h1');
    hnode.innerHTML = 'Sections';
    document.getElementById('sectionsContainer').appendChild(hnode);
    divnode = document.createElement('div');
    document.getElementById('sectionsContainer').appendChild(divnode);
    document.querySelectorAll('.sectionIdNode').forEach(function(a) {
        a.remove();
    });
    var ledElements = document.getElementsByClassName('ledElement');
    for (i=0; i < ledElements.length; i++) {
        ledElements[i].style.boxShadow = ''
    }
    for (key in sections) {
        //marks first Led Element in a given section with the section ID
        ledElement = document.getElementById('led'+sections[key]['begin']);
        sectionIdNode = document.createElement('div');
        sectionIdNode.className = 'textNode sectionIdNode';
        sectionIdNode.innerHTML = key;
        ledElement.appendChild(sectionIdNode);
        
        sectionNodeParent = document.createElement('div');
        sectionNodeParent.className = 'sectionElementParent';
        
        //make section node
        sectionNode = document.createElement('table');
        sectionNode.id = key;
        sectionNode.className = 'sectionElement';
        sectionNode.setAttribute('onclick','initiateSectionAssignment('+key+')');
        row1 = document.createElement('tr');
        idNode = document.createElement('th');
        idNode.innerHTML = key;
        row1.appendChild(idNode);
        crossNode = document.createElement('th');
        crossNode.innerHTML = "<span style='color: red;'>&#10006;</span>";
        crossNode.setAttribute('onclick','deleteSection('+key+')');
        row1.appendChild(crossNode);
        sectionNode.appendChild(row1);
        row2 = document.createElement('tr');
        rangeNode = document.createElement('div');
        rangeNode.innerHTML = sections[key]['begin']+' - '+sections[key]['end'];
        row2.appendChild(rangeNode);
        checkNode = document.createElement('th');
        checkNode.id = 'check'+key;
        checkNode.innerHTML = "<span style='color: transparent;'>&#10004;</span>";
        row2.appendChild(checkNode);
        sectionNode.appendChild(row2);

        sectionNodeParent.appendChild(sectionNode);
        divnode.appendChild(sectionNodeParent);
        function random_rgb() {
            var o = Math.round, r = Math.random, s = 255;
            return 'rgb(' + o(r()*s) + ',' + o(r()*s) + ',' + o(r()*s) + ')';
        }
        boxShadow = '4px 4px 2px 0px '+random_rgb() ;
        for (let i=sections[key]['begin']; i<=sections[key]['end']; i++) {
            ledNode = document.getElementById('led'+i);
            ledNode.style.boxShadow = boxShadow;
        }
        sectionNode.style.boxShadow = boxShadow;
    }
}

function XHRpost(endpoint, content) {
    let xhr = new XMLHttpRequest();
    return new Promise(function (resolve, reject) {
        xhr.open('POST', 'http://'+ip+':8080/'+endpoint, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.responseType = 'json';
        xhr.onload = function () {
            console.log('XHRpost', endpoint, xhr.status);
            if (xhr.status === 200) {
                resolve(this.response);
            } else {
                reject();
            };
        };
        xhr.onerror = function () {
            console.log('XHRpost Error occured!');
        }
        xhr.send(content);
    });
}

function XHRget(endpoint) {
    let xhr = new XMLHttpRequest();
    return new Promise(function (resolve, reject) {
    xhr.open('GET', 'http://'+ip+':8080/'+endpoint, true);
    xhr.responseType = 'json';
    xhr.onload = function () {
        console.log('XHRget', endpoint, xhr.status);
        if (xhr.status === 200) {
            resolve(this.response);
        } else {
            reject();
        };
    };
    xhr.onerror = function () {
        console.log('XHRget Error occured!');
    }
    xhr.send();
    });
}

var sectionAssignmentStatus = 0;
var sectionAssignmentSectionIds = {};
function initiateSectionAssignment(section) {
    sectionAssignmentStatus = 1;
    if (!sectionAssignmentSectionIds[section]) {
        console.log("section assignment now active for",section);
        sectionAssignmentSectionIds[section] = true;
        document.getElementById('check'+section).childNodes[0].style.color = '#2196f3'
        // console.log(document.getElementById(section).style.boxShadow);
    } else {
        console.log("section assignment now inactive for",section);
        sectionAssignmentSectionIds[section] = false;
        document.getElementById('check'+section).childNodes[0].style.color = 'transparent'
        // console.log(document.getElementById(section).style.boxShadow);
    }
    // console.log('Initiating section assignment, section id', section);
    console.log(sectionAssignmentSectionIds);
}

async function assignFunction(functionName) {
    if (sectionAssignmentStatus === 1 && sectionAssignmentSectionIds != null) {
        let content = [];
        for (id in sectionAssignmentSectionIds) {
            if (sectionAssignmentSectionIds[id]) {
                console.log('assigning function', functionName, 'to section', id);
                functionAssignment = {
                    'section': id,
                    'functionType': 'dynamic',
                    'functionName': functionName,
                    'arguments': null
                };
                content.push(functionAssignment);
            }
        }
        console.log('Sending content:\n', content);
        response = await XHRpost('assignFunction', JSON.stringify(content));
        console.log(response);
    }
}

async function setColorFromButton(r, g, b) {
    switch (colorGradientSelection) {
        case 1:
            colorGradientSelectionValues.push([r, g, b]);
            document.getElementById('gradientComboButtonLeft').style.backgroundColor = 'rgb('+r+','+g+','+b+')'
            colorGradientSelection = 2; //starts phase 2, next setColorFromButton is the final color for the color gradient
            break;
        case 2:
            colorGradientSelectionValues.push([r, g, b]);
            document.getElementById('gradientComboButtonRight').style.backgroundColor = 'rgb('+r+','+g+','+b+')'
            if (!advancedMode) {
                let content = {"setColorGradient": colorGradientSelectionValues};
                await XHRpost("setColorGradient", JSON.stringify(content));
                colorGradientSelectionValues = []
                // TODO visual
            } else {
                if (sectionAssignmentStatus === 1 && sectionAssignmentSectionIds != null) {
                    // console.log('assigning single color to section', sectionAssignmentSectionIds);
                    let content = [];
                    for (id in sectionAssignmentSectionIds) {
                        if (sections[id]) { //check if section mentioned in sectionAssignmentID still exists
                            if (sectionAssignmentSectionIds[id]) {
                                console.log('assigning gradient color from',sectionAssignmentSectionIds[0],'to', sectionAssignmentSectionIds[1],' section', id);
                                functionAssignment = {
                                    'section': id,
                                    'functionType': 'static',
                                    'functionName': 'gradientColor',
                                    'arguments': colorGradientSelectionValues
                                };
                                content.push(functionAssignment);
                            }
                        } else {
                            console.log("section",id,"doesn't exist anymore");
                            delete sectionAssignmentSectionIds[id]
                        }
                    }
                    if (content.length > 0) {
                        response = await XHRpost('assignFunction', JSON.stringify(content));
                        console.log(response);
                    } else {
                        console.log("No section selected");
                    }
                    colorGradientSelectionValues = [];
                    colorGradientSelection = 0;
                }
            }
            break;
        default:
            if (!advancedMode) {
                let content = {"setColorSimple": [r, g, b]};
                await XHRpost('setColorSimple', JSON.stringify(content));
                // TODO
                // visual color representation
                // for (var x=0; x<ledCount; x++) {
                //     backgroundColor = 'rgb('+r+','+g+','+b+')';
                //     document.getElementById('led'+x).style.backgroundColor = backgroundColor
                // }
            } else {
                if (sectionAssignmentStatus === 1 && sectionAssignmentSectionIds != null) {
                    // console.log('assigning single color to section', sectionAssignmentSectionIds);
                    let content = [];
                    for (id in sectionAssignmentSectionIds) {
                        if (sections[id]) { //check if section mentioned in sectionAssignmentID still exists
                            if (sectionAssignmentSectionIds[id]) {
                                console.log('assigning single color',r,g,b,'to section', id);
                                functionAssignment = {
                                    'section': id,
                                    'functionType': 'static',
                                    'functionName': 'singleColor',
                                    'arguments': [r, g, b]
                                };
                                content.push(functionAssignment);
                            }
                        } else {
                            console.log("section",id,"doesn't exist anymore");
                            delete sectionAssignmentSectionIds[id]
                        }
                    }
                    if (content.length > 0) {
                        response = await XHRpost('assignFunction', JSON.stringify(content));
                        console.log(response);
                    } else {
                        console.log("No section selected");
                    }
                }
            }
    }
}

var newSectionSelectionStatus = 0;
async function initiateNewSectionSelection() {    
    sections = await XHRget('getSections');
    updateSectionContainer();
    newSectionSelectionStatus = 1;
    console.log('Initiating new section selection');
}

async function sendNewSection() {
    let content = {'newSection' : newSectionPosition};
    console.log('Sending content:\n', content);
    sections = await XHRpost('setSection', JSON.stringify(content));
    updateSectionContainer();
}

async function deleteSection(section) {
    let content = {'deleteSection' : section};
    console.log('Sending contrent:\n', content);
    sections = await XHRpost('removeSection', JSON.stringify(content));
    updateSectionContainer();
}

var newSectionPosition = [null, null];
function stripSelection(id) {
    if (newSectionSelectionStatus === 1) {
        newSectionPosition[0] = id;
        newSectionSelectionStatus = 2;
    } else if (newSectionSelectionStatus === 2) {
        newSectionPosition[1] = id;
        newSectionSelectionStatus = 0;
        newSectionPosition = [Math.min(... newSectionPosition), Math.max(... newSectionPosition)];
        sendNewSection();
    }
}

async function increaseBrightness() {
    if (brightness < 5) {
        brightness += 1;
    } else if (brightness < 20) {
        brightness += 5; //increment by 5 if between 5 and 20
    } else if (brightness < 100) {
        brightness += 20; 
    } else if (brightness > 100) {
        brightness = 100;
    }
    response = await XHRpost('setBrightness', JSON.stringify({brightness: brightness}))
    setBrightnessIndicator(brightness);
}

async function decreaseBrightness() {
    if (brightness > 20) {
        brightness -= 20; //increment by 5 if between 5 and 20
    } else if (brightness > 5) {
        brightness -= 5; 
    } else if (brightness > 1) {
        brightness -= 1;
    }
    response = await XHRpost('setBrightness', JSON.stringify({brightness: brightness}))
    setBrightnessIndicator(brightness);
}

function setBrightnessIndicator(brightness) {
    document.getElementById('brightnessIndicatorText').innerHTML = brightness+'%';
    document.getElementById('brightnessIndicatorInnnerPart').style.height = brightness+'%'; //set height to x% of parent height
}

async function on(on) {
    response = await XHRpost('powerState', JSON.stringify({'on': on}))
    if (on === true) {
        setBrightnessIndicator(brightness);
    } else if (on === false) {
        setBrightnessIndicator(0);
    }
    console.log(response);
}

var colorGradientSelection = 0;
var colorGradientSelectionValues = [];
function startColorGradientSelection() {
    colorGradientSelection = 1; //starts gradient color selection process, next setColorFromButton is the initial color for colorGradient
    document.getElementById('gradientComboButtonLeft').style.backgroundColor = 'lightgrey'
    document.getElementById('gradientComboButtonRight').style.backgroundColor = 'lightgrey'
}

//UI

function toggleMenu() {
    var menu = document.getElementById('verticalMenu');
    if (menu.style.width == "200px") {
        menu.style.width = "0px";
        menu.style.boxShadow = "none";
    } else {
        menu.style.width = "200px";
        menu.style.boxShadow = "var(--menuBoxShadow)";
    }
    var settingsButtons = document.getElementsByClassName('menuSettingsButton');
    for (i=0; i < settingsButtons.length; i++) {
        if(settingsButtons[i].style.left == "0px") {
            settingsButtons[i].style.left = "-100px";
        } else {
            settingsButtons[i].style.left = "0px";
        }
        
    }
}

function menuButton(id) {
    var settingsButtons = document.getElementsByClassName('menuSettingsButton');
    for (var i=0; i < settingsButtons.length; i++) {
        settingsButtons[i].style.color = "var(--textColor)";
    }
    document.getElementById(id).style.color = "var(--blueTextColor)";
    var divs = document.getElementsByClassName('toggle');
    for (var i=0; i < divs.length; i++) {
        divs[i].style.display = "none";
    }
    switch(id) {
        case "simpleModeMenu":
            advancedModeOff();
            break
        case "advancedModeMenu":
            advancedModeOn();
            break
        case "settingsMenu":
            document.getElementById('settingsContainer').style.display = "block";
            console.log("settingsmenu");
            break
    }
    toggleMenu();
}

function changeTheme(theme) {
    root = document.documentElement;
    if (!darkTheme || theme == "dark") {
        console.log("set dark theme");
        root.style.setProperty('--backgroundColorSecondary','#181818');
        root.style.setProperty('--backgroundColorPrimary','#353535');
        root.style.setProperty('--textColor','#ffffff');
        root.style.setProperty('--blueTextColor','#56c0ff');
        root.style.setProperty('--menuBoxShadow', '0 0 15px 0px #000000');
        root.style.setProperty('--containerBoxShadow', '0 2px 5px 0 #000000');
        darkTheme = true;
        document.cookie = 'darkTheme=true';
        document.getElementById('themeText').innerHTML = 'Light Theme';
    } else if (darkTheme || theme == "light") {
        console.log("set light theme");
        root.style.setProperty('--backgroundColorSecondary','#eeeeee');
        root.style.setProperty('--backgroundColorPrimary','#ffffff');
        root.style.setProperty('--blueTextColor','#007BC3');
        root.style.setProperty('--textColor','#0000000');
        root.style.setProperty('--menuBoxShadow', '0 0 15px 0px #7f7f7f');
        root.style.setProperty('--containerBoxShadow', '0 2px 5px 0 rgba(0,0,0,.3)');
        darkTheme = false;
        document.cookie = 'darkTheme=false';
        document.getElementById('themeText').innerHTML = 'Dark Theme'
    }
}

async function sleepTimer(id) {
    switch (id) {
        case "start":
            console.log(id);
            document.getElementById('sleepTimerDisplayInput').disabled = true;

            let hm = document.getElementById('sleepTimerDisplayInput').value;
            let times =  hm.split(':');
            if (times.length === 3) {
                seconds = parseInt(times[0])*60*60 + parseInt(times[1])*60 + parseInt(times[2]); //2:30:30 -> h:m:s
            } else if (times.length === 2) {
                seconds = parseInt(times[0])*60*60 + parseInt(times[1])*60; //2:30 -> h:m
            } else if (times.length === 1) {
                seconds = parseInt(times[0]*60); //30 -> m
            }
            // alert('timer set to '+seconds+' seconds!');

            // seconds = parseInt(document.getElementById('sleepTimerDisplayInput').value);
            timerSet = true;
            timerData = {
                "seconds": seconds,
                "active": true
            };
            console.log(timerData);
            response = await XHRpost('sleepTimer', JSON.stringify(timerData));            
            updateButtonState(response);
            console.log(response);
            document.cookie = 'initialTimerValue='+seconds;
            startCountdown(seconds);
            break;
        case "stop":
            console.log(id);
            timerSet = false;
            timerData = {
                // "seconds": seconds,
                "active": false
            };
            response = await XHRpost('sleepTimer', JSON.stringify(timerData));            
            updateButtonState(response);
            break;
        case "reset":
            console.log(id);
            timerSet = false;
            console.log(getCookie('initialTimerValue'));
            if (getCookie('initialTimerValue')) {
                seconds = getCookie('initialTimerValue');
            } else {
                seconds = 60*60*30;
            }
            timerData = {
                "seconds": seconds,
                "active": false
            };
            document.getElementById('sleepTimerDisplayInput').value = hmsFromSec(seconds);
            document.getElementById('sleepTimerDisplayInput').disabled = false;
            response = await XHRpost('sleepTimer', JSON.stringify(timerData));            
            updateButtonState(response);
            console.log(response);
            break;
        case "displayPress":
            // console.log(id);
            // console.log(document.getElementById('sleepTimerDisplayInput').disabled);
            // if (document.getElementById('sleepTimerDisplayInput').disabled === false) {
            //     console.log("input is enabled");
            //     document.getElementById('sleepTimerDisplayInput').disabled = true
            //     console.log(document.getElementById('sleepTimerDisplayInput').disabled);
            // } else if (document.getElementById('sleepTimerDisplayInput').disabled === true) {
            //     console.log("input is disabled");
            //     document.getElementById('sleepTimerDisplayInput').disabled = false;
            //     document.getElementById('sleepTimerDisplayInput').focus();
            //     console.log(document.getElementById('sleepTimerDisplayInput').disabled);
            // } 
            break;
    }
}

async function startCountdown(seconds) {
    timeleft = seconds - 1;
    display = document.getElementById('sleepTimerDisplayInput');
    var timer = setInterval(function() {
        if (timeleft <= 0 || !timerSet) {
            clearInterval(timer);
            sleepTimer('reset');
        } else {
            display.value = hmsFromSec(timeleft);
        }
        timeleft -= 1;
    }, 1000)
}

function updateButtonState(response) {
    // timerSet = (getCookie('timerSet') == 'true');
    if (response) {
        document.getElementById('sleepTimerDisplayInput').value = hmsFromSec(response["seconds"])
    }
    if (timerSet) {
        document.getElementById('sleepTimerStartButton').style.backgroundColor = '#dbdbdb';
        document.getElementById('sleepTimerStartButton').style.color = 'rgba(0,0,0,0.5)';
        document.getElementById('sleepTimerStopButton').style.backgroundColor = '#fafafa';
        document.getElementById('sleepTimerStopButton').style.color = 'rgb(0,0,0)';
    } else {
        document.getElementById('sleepTimerStopButton').style.backgroundColor = '#dbdbdb';
        document.getElementById('sleepTimerStopButton').style.color = 'rgba(0,0,0,0.5)';
        document.getElementById('sleepTimerStartButton').style.backgroundColor = '#fafafa';
        document.getElementById('sleepTimerStartButton').style.color = 'rgb(0,0,0)';                
    }
}

function hmsFromSec(seconds) {
    return (new Date(seconds * 1000)).toUTCString().match(/(\d\d:\d\d:\d\d)/)[0];
  }