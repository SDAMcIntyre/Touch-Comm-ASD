from psychopy import visual, core, event, data, gui
import numpy as np
import random, os, pygame, copy
from touchcomm import *


# -- GET INPUT FROM THE EXPERIMENTER --

exptInfo = {'Experiment name':'TC-ASD-comm',
            'Participant Code':'test',
            'Number of trials per cue':10,
            'Press to continue':True,
            'Participant screen':1,
            'Experimenter screen':0,
            'Participant screen resolution':'800,600', #'1920, 1200',
            'Experimenter screen resolution':'400,300', #'1280,720',
            'Folder for saving data':'data'}


dlg = gui.DlgFromDict(exptInfo, title='Experiment details', 
                    order = ['Experiment name',
                    'Participant Code',
                    'Number of trials per cue',
                    'Press to continue',
                    'Participant screen',
                    'Experimenter screen',
                    'Participant screen resolution',
                    'Experimenter screen resolution',
                    'Folder for saving data'])

if dlg.OK:
    pass ## continue
else:
    core.quit() ## the user hit cancel so exit

# ----

# -- PROMPT PARTICIPANT FOR LANGUAGE --
languageLabels = ['svenska', 'english']
languagePrompt = ButtonInterface(fullscr = True,
                                screen = exptInfo['Participant screen'],
                                size = [int(i) for i in exptInfo['Participant screen resolution'].split(',')],
                                message = '',
                                nCol = len(languageLabels), nRow = 1, 
                                buttonLabels = languageLabels)

languagePrompt.showButtons(languageLabels)
(responseN, t) = languagePrompt.getButtonClick(core.Clock())
languagePrompt.hideButtons()
if responseN < 0:
    core.quit() ## the user hit cancel so exit
else:
    exptInfo['language'] = ['sv','en'][responseN]

# ----

# -- SET UP THE EXPERIMENT --

exptInfo['Date and time']= data.getDateStr(format='%Y-%m-%d_%H-%M-%S') ##add the current time

exptInfo['Inter-stimulus interval (sec)'] = 6

# text displayed to experimenter and participant
displayText = dict((line.strip().split('\t') for line in open('./text/display-text-' + exptInfo['language'] + '.txt')))
languagePrompt.updateMessage(displayText['waitMessage'])

# ----

# -- SETUP STIMULUS RANDOMISATION AND CONTROL --

stimLabels = ['attention','gratitude','love','sadness','happiness','calming']
receiverCueText = dict((line.strip().split('\t') for line in open('./text/receiver-cues-' + exptInfo['language'] + '.txt')))
toucherCueText = dict((line.strip().split('\t') for line in open('./text/toucher-cues.txt')))
soundDurations = dict((line.strip().split('\t') for line in open('./sounds/durations.txt')))

stimList = []
for stim in stimLabels: 
    stimList.append({'stim':stim,
                    'toucherCueText':toucherCueText[stim],
                    'receiverCueText':receiverCueText[stim],
                    'cueSound':'./sounds/{} - short.wav' .format(stim),
                    'cueSoundDuration':float(soundDurations[stim])})
trials = data.TrialHandler(stimList, exptInfo['Number of trials per cue'])

# ----

# -- MAKE FOLDER/FILES TO SAVE DATA --

saveFiles = DataFileCollection(foldername = exptInfo['Folder for saving data'],
                filename = exptInfo['Experiment name'] + '_' + exptInfo['Date and time'] +'_P' + exptInfo['Participant Code'],
                headers = ['trial','cued','response'],
                dlgInput = exptInfo)

# ----

# -- SETUP VISUAL INTERFACE --

toucher = DisplayInterface(False,
                        exptInfo['Experimenter screen'],
                        [int(i) for i in exptInfo['Experimenter screen resolution'].split(',')], ## convert text input to numbers
                        displayText['startMessage'])

receiverStimLabels = stimLabels + ['other']
receiver = ButtonInterface(fullscr = True,
                                screen = exptInfo['Participant screen'],
                                size = [int(i) for i in exptInfo['Participant screen resolution'].split(',')],
                                message = displayText['waitMessage'],
                                nCol = 2, nRow = 4, 
                                buttonLabels = [receiverCueText[i] for i in receiverStimLabels])

# -----

# -- SETUP AUDIO --

pygame.mixer.pre_init() 
pygame.mixer.init()
goStopSound = pygame.mixer.Sound('./sounds/go-stop.wav')

# ----


# -- RUN THE EXPERIMENT --

# display starting screens
languagePrompt.win.close()
exptClock=core.Clock()
exptClock.reset()
isiCountdown = core.CountdownTimer(0)
receiver.startScreen(displayText['waitMessage'])
toucher.startScreen(displayText['startMessage'])

# wait for start trigger
for (key,keyTime) in event.waitKeys(keyList=['space','escape'], timeStamped=exptClock):
    if key in ['escape']:
        saveFiles.logAbort(keyTime)
        core.quit()
    if key in ['space']:
        exptClock.add(keyTime)
        saveFiles.logEvent(0,'experiment started')


# communication task loop
for thisTrial in trials:
    
    event.clearEvents()
    
    if trials.thisN == 0: 
        isiCountdown.reset(exptInfo['Inter-stimulus interval (sec)'])
    
    present_stimulus(thisTrial,
                    exptInfo,displayText,
                    receiver,toucher,
                    saveFiles,
                    exptClock,isiCountdown,
                    goStopSound)
    
    response = get_button_response(stimLabels,receiverCueText,
                    thisTrial,
                    displayText,
                    receiver,toucher,
                    saveFiles,
                    exptClock)
    
    saveFiles.writeTrialData([trials.thisN+1,
                            thisTrial['stim'],
                            response])
    
    saveFiles.logEvent(exptClock.getTime(),
        '{} of {} complete' .format(trials.thisN+1, trials.nTotal))

# -----

# prompt at the end of the experiment
event.clearEvents()
receiver.updateMessage(displayText['finishedMessage'])
toucher.updateMessage(displayText['finishedMessage'])

saveFiles.logEvent(exptClock.getTime(),'experiment finished')
saveFiles.closeFiles()
core.wait(2)
receiver.win.close()
toucher.win.close()
core.quit()
