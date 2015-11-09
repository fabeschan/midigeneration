def normalizeemission(emission):
	for i in range(len(emission)):
		total=0.0
		for j in range(len(emission[i])):
			total+=emission[i][j][1]
		for j in range(len(emission[i])):
			emission[i][j][1]/=total
	return

def addemission(left, right, weightleft=1.0, weightright=1.0):
	if len(left)==0:
		return [[[field for field in emission] for emission in hiddenstate] for hiddenstate in right]
	elif len(right)==0:
		return [[[field for field in emission] for emission in hiddenstate] for hiddenstate in left]
	if len(left)!=len(right):
		return -1
	sum=[]
	for i in range(len(left)):
		sum+=[[]]
		for j in range(len(left[i])):
			sum[-1]+=[[field for field in left[i][j]]]
			sum[-1][-1][1]*=weightleft
		for j in range(len(right[i])):
			if right[i][j][0] in [emission[0] for emission in sum[-1]]:
				index=[emission[0] for emission in sum[-1]].index(right[i][j][0])
				sum[-1][index][1]+=weightright*right[i][j][1]
			else:
				sum[-1]+=[[field for field in right[i][j]]]
				sum[-1][-1][1]*=weightright
	return sum

def make(statechains, order, numberofhiddenstates):
	overalltransition=[]
	overallemission=[]
	for statechain in statechains:
		#Get a list of unique states
		listofstates=[]
		for state in statechain:
			if state not in listofstates:
				listofstates+=[state]
		#assign hidden states randomly but as equally as possible. Hidden states are represented by integers.
		speed=0.5#Arbitrary for now -- past-present bias (1 means present, 0 means past)
		import random
		hiddenstatechain=[-1]*len(statechain)#-1 means unassigned, hiddenstatechain[i] corresponds to statechain[i]
		nextstatetoassign=0#start at hidden state 0
		while -1 in hiddenstatechain:#while there's an unassigned hidden state
			randomindex=int(random.random()*len(statechain))#get a random spot
			if hiddenstatechain[randomindex]==-1:#make sure it's unassigned
				hiddenstatechain[randomindex]=nextstatetoassign#assign it
				nextstatetoassign=(nextstatetoassign+1)%numberofhiddenstates#change up the hidden state. So, hidden states get picked to be stuck in in a round-robin fashion.
		transition=[]#transition is a list of [[previous],next,frequency], as specified in mm module
		emission=[]#emission is a list of lists of [visible,frequency], the higher list's ith element corresponds to the ith hidden state, which has value i.
		#Set up a uniform distribution for initial emission and transition probabilities
		import mm
		transition=mm.uniform(range(numberofhiddenstates),order)
		for i in range(numberofhiddenstates):#For all hidden states
			emission+=[[]]
			for state in listofstates:#For all visible states
				emission[i]+=[[state,1.0/len(listofstates)]]#Want frequency to add to 1 for each current state
		for iteration in range(20):#Just iterate a bunch of times
			#Find the emission frequency
			emissionnew=[]#empty this so we can accumulate in it
			for i in range(numberofhiddenstates):#for all hidden states
				emissionnew+=[[]]#add a new empty list to be populated shortly.
				for j in range(len(statechain)):#For all states in the statechain
					if hiddenstatechain[j]==i:#If the hidden state is the one we're looking at
						#Get a list of states we've seen come from this hidden state so far
						statessofar=[]
						if len(emissionnew[i]):
							statessofar=[x[0] for x in emissionnew[i]]
						if statechain[j] in statessofar:#If the current visible state is in this list
							emissionnew[i][statessofar.index(statechain[j])][1]+=1#Increment the frequency
						else:#Otherwise, add in a new element with frequency 1.
							emissionnew[i]+=[[statechain[j],1]]
			#Find the transition probability
			transitionnew=mm.make([hiddenstatechain],order,"start","end")#Make a Markov model out of the hidden state transitions.
			#merge past and present emission frequencies
			emission=addemission(emission,emissionnew,1-speed,speed)
			transition=mm.add(transition,transitionnew,1-speed,speed)#merge past and present transition frequencies
			#Redo the hidden state sequence based on the emission and transition probabilities we found
			newhiddenstatechain=[-1]*len(hiddenstatechain)#get a list with same size as hiddenstatechain filled with a value that means "unassigned"
			previous=["start"]*order#Start from "start". Note "start" (or "end") doesn't emit any visible states.
			for i in range(len(statechain)):#for all states in the statechain
				#Find the probability of transitioning to each hidden state
				probabilitybasedontransition=[0]*numberofhiddenstates#Start with 0 probability to transition to each hidden state
				for j in range(numberofhiddenstates):#For all hidden states
					for x in transition:#For all transitions from this hidden state to another
						if x[0]==previous:#If the transition is one from the previous state
							if x[1]==j:#If the transition is to the hidden state we're looking at right now
								probabilitybasedontransition[j]=x[2]#add in that transition frequency
				#Find the probability of the next hidden state being a certain hidden state based on the corresponding visible state
				probabilitybasedonemission=[0]*numberofhiddenstates#Start with 0 chance for each hidden state
				for j in range(numberofhiddenstates):#for each hidden state
					for k in range(len(emission[j])):#for each state emission
						if emission[j][k][0]==statechain[i]:#if the emission in question is produces the hidden state we're looking at right now
							probabilitybasedonemission[j]=emission[j][k][1]#Add that emission frequency
				probability=[]#Find the overall probability of the next hidden state being each hidden state
				for j in range(numberofhiddenstates):#Just multiply the two probabilities we found
					probability+=[probabilitybasedonemission[j]*probabilitybasedontransition[j]]
				newhiddenstatechain[i]=probability.index(max(probability))#The hidden state assigned to this position is the one with maximum probability
				previous=previous[1:]+[newhiddenstatechain[i]]#Update the previous state
			hiddenstatechain=newhiddenstatechain#copy the new findings
		overalltransition=mm.add(overalltransition,transition)
		overallemission=addemission(overallemission,emission)
	import copy
	overalltransition=copy.deepcopy(overalltransition)
	overallemission=copy.deepcopy(overallemission)
	return [overalltransition, overallemission]

def traverse(transition, emission, table, starttoken="start", endtoken="end"):
	hiddenstatechain=[]
	statechain=[]
	hiddencurrent=["start"]*len(transition[0][0])
	current=[starttoken]*len(table[0][0])
	import random
	import copy
	while True:
		choices=0
		for transitionchoice in transition:
			if transitionchoice[0]==hiddencurrent:
				choices+=transitionchoice[2]
		choice=random.random()*choices
		choicemade=False
		for transitionchoice in transition:
			if transitionchoice[0]==hiddencurrent:
				choice-=transitionchoice[2]
				if choice<choices/1000.0:
					hiddencurrent=hiddencurrent[1:]+[transitionchoice[1]]
					choicemade=True
					break
		if not choicemade:
			print choice
			print hiddencurrent
			return -1
		if hiddencurrent[-1]=="end":
			break
		hiddenstatechain+=[hiddencurrent[-1]]
		probability=[]
		for transitionchoice in table:
			if transitionchoice[0]==current:
				if transitionchoice[1] in [entry[0] for entry in emission[hiddenstatechain[-1]]]:
					probability+=[copy.deepcopy(transitionchoice)]
					probability[-1][2]=transitionchoice[2]*emission[hiddenstatechain[-1]][[entry[0] for entry in emission[hiddenstatechain[-1]]].index(transitionchoice[1])][1]
		choices=0
		for transitionchoice in probability:
			if transitionchoice[0]==current:
				choices+=transitionchoice[2]
		choice=random.random()*choices
		choicemade=False
		for transitionchoice in probability:
			if transitionchoice[0]==current:
				choice-=transitionchoice[2]
				if choice<choices/1000.0:
					current=current[1:]+[transitionchoice[1]]
					choicemade=True
					break
		if not choicemade:
			print choice
			print current
			return -1
		if current[-1]==endtoken:
			break
		statechain+=[current[-1]]
	statechain=copy.deepcopy(statechain)
	return statechain
