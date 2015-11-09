import muse, parsemidi, sys, pickle

# finds all the riffs that are similar in the track with the threshold value 
# specified (currently 0.85) by using parsemidi.similarity
def findRiff(master, start, riffLength, riffCounter):
	accuracies = []
	riff = master[start:riffLength]
	for i in range(start+riffLength, len(master)-riffLength, 1):
		result = parsemidi.similarity(riff, master[i:i+riffLength])
		if result >= 0.85:
			accuracies.append([(i, i+riffLength, result), riffCounter])
	return accuracies

# generates a probability matrix that holds the probabilities of expected
# sequence based on previous sequences. Also generates a dictionary of 
# different transition sections; the key is the note and the values are the
# different sections that it can transition to. This is based on finding the 
# last note in the section and seeing which section follows
def generateProbMatrix(riff, master):
	sequence = []
	pMat = []
	
	# store the sequence from the riff
	for i in range(len(riff)):
		sequence.append(riff[i][-1])
	# create empty matrix to hold probabilities
	for i in range(max(sequence)):
		pMat.append([0] * max(sequence))
	for sec in range(len(sequence)-2):
		pMat[sequence[sec]][sequence[sec+1]] += 1
	for i in range(len(pMat)):
		for j in range(len(pMat[i])):
			if sum(pMat[i]) != 0:
				newSum = float(pMat[i][j]) / float(sum(pMat[i]))
				pMat[i][j] = newSum
	print 'Original sequence:\n', sequence

	#THE BELOW CODE GENERATES A DICT BASED ON TRANSITION POINTS
	#noteDict has the note as a key and the next sections as the value
	noteDict = {}
	for i in range(len(riff) - 1):
		lastNoteInRiff = riff[i][0][1] - 1
		prevNote = master[lastNoteInRiff][0][4] #take first note in chord
		nextSection = riff[i + 1][-1]
		
		if prevNote not in noteDict:
			noteDict[prevNote] = [nextSection]
		else:
			noteDict[prevNote].append(nextSection)
	print noteDict
	return (pMat, noteDict)

# returns the next section based on the probabilities in pMat
# if the next section is not a transition point from the last note in the
# previous section, the pop that sequence and return
def getNextRiff(generatedSeq, pMat, noteDict, listedSong):
	import random
    
	totals = []	
	running_total = 0
	for w in pMat[generatedSeq[-1][1]]:
		running_total += w
		totals.append(running_total)
	rnd = random.random() * running_total
	for i in range(len(totals)):
		total = totals[i]
		if rnd < total:
			generatedSeq.append([1, i])
			lastLastSec = generatedSeq[-2]
			lastNote = listedSong[-1][0][4]

			if lastNote in noteDict:
				pass
				#if i not in noteDict[lastNote]:
					#generatedSeq.pop()
			else:
				generatedSeq.pop()
			break;
	return generatedSeq

def getNextDualRiff(seq, dualDict, listedSong):
	import random
	
	lastNote = listedSong[-1][0][4]
	if lastNote in dualDict:
		i = random.randint(0, len(dualDict[lastNote]) - 1)
		generatedTup = dualDict[lastNote][i]
	        seq.append([generatedTup[0], generatedTup[1]])
	else:
		seq.pop()
	
	return seq

# a helper function for generateNotes
# returns a dictionary of the section number as the key and the different
# sections in the song as values 
def generateRiffDictionary(riff):
	riffChoice = {}
	for i in range(len(riff)):
		if riff[i][-1] not in riffChoice:
			riffChoice[riff[i][-1]] = [(riff[i][0][0], riff[i][0][1])]
		else:
			riffChoice[riff[i][-1]].append((riff[i][0][0], riff[i][0][1]))
	print "Riff Dictionary:"
	print riffChoice
	return riffChoice

def generateNotes(riff, master, pMat, noteDict, model, filename, dualInput=False, riff2=None, master2=None, pMat2=None, noteDict2=None):
	
	from random import choice
	#generate dictionary of all possible riffs
	riffChoice = generateRiffDictionary(riff)
	if dualInput:
		riffChoice2 = generateRiffDictionary(riff2)
		# merge note dictionaries, keys are the last note
		# values are a list of tuples of (model, section)
		# eg: 72:[(1, 3), (2, 0)] refers to note 72 can be followed by
		# model 1 section 3 or model 2 section 0
		dualDict = {}
		for key in noteDict:
			if key not in dualDict:
				dualDict[key] = []
			for val in noteDict[key]:
				dualDict[key].append((1, val))
		for key in noteDict2:
			if key not in dualDict:
				dualDict[key] = []
			for val in noteDict2[key]:
				dualDict[key].append((2, val))
	
	#from the dictionary of riffs, get a random one for the sequence
	noteOn = 0
	song = []
	listedSong = []
	listedTimes = []
	temp = []
	seq = [[1, 0]]	
	#choose a random sequence from the dictionary and put the chorded notes
	# in listedSong

	while (seq[-1][0] == 1 and seq[-1][1] != (len(pMat) - 1)) or seq[-1][0] == 2 and seq[-1][1] != (len(pMat2) - 1):
		if seq[-1][0] == 2:
			selectedRiff = choice(riffChoice2[seq[-1][1]])
			riffNotes = master2[selectedRiff[0]:selectedRiff[1]+1]
		else:
			selectedRiff = choice(riffChoice[seq[-1][1]])
			riffNotes = master[selectedRiff[0]:selectedRiff[1]+1]	

		if riffNotes == []:
			continue
		# subtracts first note from the noteOn value in order to set relative duration
		duration = riffNotes[0][0][1] - noteOn
		for k in range(len(riffNotes)):
			currentChord = []
			#adjusts duration from riff to be relative to new placement
			for j in range(len(riffNotes[k])):
				currentNote = ['note', riffNotes[k][j][1] - duration]
				currentNote.append(riffNotes[k][j][2] - riffNotes[k][j][1])
				currentNote.append(riffNotes[k][j][3])
				currentNote.append(riffNotes[k][j][4])
				currentChord.append(currentNote)
				# this finds the correct placement of the next note
				noteOn = currentNote[1] + currentNote[2]
				#noteOn = currentNote[1]
			listedSong.append(currentChord)
	
		prevseq = seq

		if dualInput:
			seq = getNextDualRiff(seq, dualDict, listedSong)
		else:
			seq = getNextRiff(seq, pMat, noteDict, listedSong)

		# Attempt to not have repeated sections
		#if len(seq) > 2 and seq[-1] == seq[-2]:
			#seq.pop()
			#seq = getNextRiff(seq, pMat, noteDict, listedSong)
		#if len(seq) == len(prevseq):
			#listedSong.pop()

	print 'New Sequence:', seq
		
	# append final riff
	selectedRiff = choice(riffChoice[len(pMat)])
	riffNotes = master[selectedRiff[0]:selectedRiff[1]]
	duration = riffNotes[0][0][1] - noteOn
	for k in range(len(riffNotes)):
		currentChord = []
		#adjusts duration from riff to be relative to new placement
		for j in range(len(riffNotes[k])):
			currentNote = ['note', riffNotes[k][j][1] - duration]
			currentNote.append(riffNotes[k][j][2] - riffNotes[k][j][1])
			currentNote.append(riffNotes[k][j][3])
			currentNote.append(riffNotes[k][j][4])
			currentChord.append(currentNote)
		listedSong.append(currentChord)

	#notes are ['note', noteon, duration, track, noteval]
	#right now the master track has the ['note', noteon, noteoff, track, noteval, duration]

	#remove the notes from the embedded list
	for i in range(len(listedSong)):
		for j in range(len(listedSong[i])):
			temp += [listedSong[i][j]]

	#sort the notes by track
	temp.sort(key=lambda x: int(x[3]))
	tracks = []
	#create empty arrays for the tracks
	for i in range(temp[-1][3] + 1):
		tracks.append([])
	#insert the notes into the right tracks
	for i in range(len(temp)):
		tracks[temp[i][3]].append(temp[i])
	#insert the tracks into the song
	for i in range(len(tracks)):
		song.append(tracks[i])
	#insert the header
	song.insert(0, [["ticks",0,256],["time",0,model[0][1][2],model[0][1][3]]])
	import midi
	midi.write(filename, song)
	return

def unpickle(model):
	readmodel = open(model, "r")
	
	# We want to read the file in order of:
	# riff, master, pMat, noteDict, midiFile(model)
	
	# retrieve riff
	line = readmodel.readline() # first line contains header
	line = readmodel.readline() # start of riff info
	command = ''
	while not line.startswith('---'):
		command += line
		line = readmodel.readline()
		#print line
	riff = pickle.loads(command)

	# retrieve master
	line = readmodel.readline()
	command = ''
	while not line.startswith('---'):
		command += line
		line = readmodel.readline()
	master = pickle.loads(command)

	# retrieve pMat
	line = readmodel.readline()
	command = ''
	while not line.startswith('---'):
		command += line
		line = readmodel.readline()
	pMat = pickle.loads(command)

	# retrieve noteDict
	line = readmodel.readline()
	command = ''
	while not line.startswith('---'):
		command += line
		line = readmodel.readline()
	noteDict = pickle.loads(command)

	# retrieve midiFile(model)
	midiFile = pickle.loads(readmodel.read()) #reamainder of file

	readmodel.close()
	
	return(riff, master, pMat, noteDict, midiFile)

if __name__ == '__main__':
	if len(sys.argv) != 1:
		raise ValueError("Usage is: python generateSong.py")
	
	model = raw_input('Enter model to generate from: ')
	model2 = raw_input('Enter model to generate from or DONE to generate: ')
	songname = raw_input('Enter the output song name: ')
	
	# unpickle the model to get the variables
	dualInput = False
	(riff, master, pMat, noteDict, midiFile) = unpickle(model)

	if model2 != 'DONE':
		dualInput = True
		(riff2, master2, pMat2, noteDict2, midiFile2) = unpickle(model2)
	

	if dualInput:
		generateNotes(riff, master, pMat, noteDict, midiFile, songname, dualInput, riff2, master2, pMat2, noteDict2)
	else:
		generateNotes(riff, master, pMat, noteDict, midiFile, songname)