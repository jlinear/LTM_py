import numpy as np
from itertools import chain


burnin, maxit, sample_step, threshold = 50, 5000, 1, 0.5
alpha= [[100,1000],[50,50]]
beta = [10,10]
sample_size = maxit/sample_step - burnin/sample_step


sid2double, sid2source = {}, {} # double - entity,value, sid mapping source
entity2value2truth, entity2value2sid = {},{}
# read in rawdata and format
fr = open('rawdb.txt','rb')
for line in fr: 
	arr = line.strip('\n').split('\t')
	sid, source = int(arr[3]), arr[2]
	entity,value = arr[0],arr[1]
	# build sid-ev and sid-src
	if sid not in sid2source:
		sid2source[sid]=source
		sid2double[sid]=set() # the operation (x in z) is faster when using set than list.
	sid2double[sid].add((entity,value)) # [] is not hasable while () is.
	# build the initial fact table $entity2value2truth$
	if entity not in entity2value2truth:
		entity2value2truth[entity]={}
	if value not in entity2value2truth[entity]:
		t = np.random.uniform(0,1)
		entity2value2truth[entity][value] = (t >= 0.5)
	# pre-claim table: fact-sid
	if entity not in entity2value2sid:
		entity2value2sid[entity]={}
	if value not in entity2value2sid[entity]:
		entity2value2sid[entity][value]=[]
	entity2value2sid[entity][value].append(sid)
fr.close()

# claim table with o and t
entity2value2sid2ob_t = {}
n_sto = {}
for [entity,value2sid] in entity2value2sid.items():
	sids = entity2value2sid[entity].values()
	for [value,sid] in value2sid.items():
		if entity not in entity2value2sid2ob_t:
			entity2value2sid2ob_t[entity]={}
			# n_sto[entity]={}
		if value not in entity2value2sid2ob_t[entity]:
			entity2value2sid2ob_t[entity][value]={}	
			# n_sto[entity][value]={}
		for s in set(chain(*sids)):
			entity2value2sid2ob_t[entity][value][s] = [0.0,0.0]
			entity2value2sid2ob_t[entity][value][s][0] = ((entity,value) in sid2double[s]) # o
			entity2value2sid2ob_t[entity][value][s][1] = entity2value2truth[entity][value] # initial t
			if s not in n_sto:#fill in the n_sto matrix
				n_sto[s] = [[0, 0], [0, 0]]
			_t = int(entity2value2sid2ob_t[entity][value][s][1])
			_o = int(entity2value2sid2ob_t[entity][value][s][0])
			n_sto[s][_t][_o] += 1


it = 0
p_t = {}
while it < maxit:
	p={}
	it += 1
	for [entity,value2truth] in entity2value2truth.items():
		if entity not in p:
			p[entity] = {}
		if entity not in p_t:
			p_t[entity] = {}
		for [value,truth] in value2truth.items():
			if value not in p[entity]:
				p[entity][value]={}
			if value not in p_t[entity]:
				p_t[entity][value] = 0
			p[entity][value][int(truth)] = beta[int(truth)]
			p[entity][value][int(1-truth)] = beta[int(1-truth)]
			#for c in C_f
			for [sid, ob_t] in entity2value2sid2ob_t[entity][value].items():
				o, t = int(ob_t[0]), int(ob_t[1])
				p[entity][value][int(truth)] *= 1.0 * (n_sto[sid][t][o] - 1 + alpha[t][o]) / \
				(n_sto[sid][t][1] + n_sto[sid][t][0] - 1 + alpha[t][1] + alpha[t][0])
				p[entity][value][int(1-truth)] *= 1.0 * (n_sto[sid][1-t][o] - 1 + alpha[1-t][o]) / \
				(n_sto[sid][1-t][1] + n_sto[sid][1-t][0] - 1 + alpha[1-t][1] + alpha[1-t][0])
			if np.random.uniform(0,1) < 1.0 * (p[entity][value][int(1-truth)]) / (p[entity][value][int(1-truth)] + p[entity][value][int(truth)]):
				entity2value2truth[entity][value] = 1 - truth
				for [sid, ob_t] in entity2value2sid2ob_t[entity][value].items():
					entity2value2sid2ob_t[entity][value][sid][1] = 1 - truth
					o, t = int(ob_t[0]), int(ob_t[1])
					n_sto[sid][1-t][o] -= 1
					n_sto[sid][t][o] += 1
			if it > burnin and it % sample_step == 0:
				p_t[entity][value] += 1.0 * entity2value2truth[entity][value] / sample_size
				# print (str(p_t['HP']['EW'] >= 0.5))

for [entity, value2p] in sorted(p_t.items()):
    for [value, p] in sorted(value2p.items()):
        print (entity + ' ' + value + ' ' + str(p >= threshold))











