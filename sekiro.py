from time import sleep
from random import choice,random
from re import findall
import signal
import csv
from getchar import _Getch

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
ERASE = '\x1b[1A\x1b[2K'

MENU = [('s','Player stats','check all the players stats'),
		('t','Strength training','upgrade strength value'),
		('b','Boss battle','start a boss fight'),
		('d','Dojo','learn the moveset'),
		('r','Rest','restore stamina'),
		('h','Help','display menu with help'),
		('q','Save and quit','save progress and quit the game')]

VS_MATRIX = [[0,-1,-1,-1],
			 [0,0,-1,-1],
			 [0,-1,0,0],
			 [1,-1,-1,-1],
			 [0,-1,-1,1]]

# Input functions -----------------------------------

def alarm_handler(signum,frame):
	'''Raise a timeout error'''
	raise ValueError

def input_with_timeout(timeout,inkey,single=True):
	'''Input with timeout'''
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(timeout)
	try:
		if single:
			return inkey()
		else:
			ret = []
			while True:
				ret.append(inkey())
	finally:
		if single: signal.alarm(0)
		else: return ''.join(ret)

# Move functions ------------------------------------

def damage_vs(movesets,player_move,enemy_move):
	'''Return damage after versus: 0 -> no damage, 1 -> enemy takes damage and -1 player takes damage'''
	return VS_MATRIX[get_shortcut(movesets[0]).index(player_move)][get_shortcut(movesets[1]).index(enemy_move)]

def possible_move(moveset,move):
	'''1 if possible move, 0 instead'''
	return move in get_shortcut(moveset)

def rand_move(moveset):
	'''Generate a random move for the enemy'''
	return choice(moveset)

# Printing functions --------------------------------

def get_name(fighters,move,who):
	'''Printing: move name'''
	return [n for s,n in fighters[who] if s == move][0]
 
def hp_bar(hp_total,hp_left):
	'''Printing: HP bar'''
	if hp_left <= 0: return '['+BOLD+FAIL+'XXXXXXXXXXXXXXX'+ENDC+']'+' {:.1f} %'.format(0)
	else: return '['+BOLD+OKBLUE+''.join(['#' if x < round(hp_left * 15 / hp_total) else ENDC+'_' for x in range(15)])+ENDC+']'+' {:.1f} %'.format(hp_left/hp_total*100)

def versus_step(player,enemy,enemy_hp_left):
	'''Printing: versus step'''
	max_string = max(len(player['name']),len(enemy[0]))
	return '{5}{0:<{4}}{6} {1}\n{5}{2:>{4}}{6} {3}'.format(player['name'],hp_bar(player['hp'],player['hp_left']),enemy[0],hp_bar(enemy[1],enemy_hp_left),max_string,BOLD,ENDC)

def set_title(string):
	'''Printing: action title'''
	return BOLD+UNDERLINE+string+ENDC

def get_menu(title,hlp=False):
	'''Printing: menu (w or w/o help)'''
	print(set_title(title))
	return '\n'.join(['{0} - {1} [{3}{2}{4}]'.format(s,w,h,UNDERLINE,ENDC) if hlp else '{} - {}'.format(s,w) for s,w,h in MENU])

def can_do_action(player):
	'''Check if alive and if enough stamina'''
	if not is_alive(player):
		print('Seems you\'re '+FAIL+'dead'+ENDC+' [check '+WARNING+'stats'+ENDC+']\nTo resurrect, you need to restore the HP ['+WARNING+'rest'+ENDC+']\n')
		return False
	elif not enough_stamina(player):
		print('Seems you\'re out of '+FAIL+'stamina'+ENDC+' (0/3) [check '+WARNING+'stats'+ENDC+']\nBefore doing stuff, you need to restore the stamina ['+WARNING+'rest'+ENDC+']\n')
		return False
	else: return True

# Actions functions --------------------------------

def battle(player,enemy,fighters_moveset):
	'''Battle: enemy'''
	remove_menu()
	print(set_title('Boss battle')); sleep(1)

	if can_do_action(player):

		inkey = _Getch()
		print('A new Boss appeared..'); sleep(2); print(BOLD+FAIL+enemy[0].upper()+ENDC); sleep(2); print('FIGHT!',end='\n\n')
		enemy_hp_left = enemy[2]
		enemy_velocity = int(enemy[4] / 10000 * player['stats']['focus'])
		while enemy_hp_left > 0 and player['hp_left'] > 0:
			print(versus_step(player,enemy,enemy_hp_left))
			bm = rand_move(enemy[5])
			try:
				sleep(random())
				print('Enemy does',get_name(fighters_moveset,bm,1),end='\n')
				pm = input_with_timeout(enemy_velocity,inkey)
				if possible_move(fighters_moveset[0],pm):
					dmg = damage_vs(fighters_moveset,pm,bm)
				else:
					dmg = damage_vs(fighters_moveset,'n',bm)
			except ValueError:
				dmg = damage_vs(fighters_moveset,'n',bm)
			finally:
				space_cancel=' '*15
				if dmg == 1:
					print('Boss takes '+OKGREEN+'DAMAGE'+ENDC+space_cancel)
					enemy_hp_left -= player['stats']['strength']
				if dmg == -1:
					print('Player takes '+FAIL+'DAMAGE'+ENDC+space_cancel)
					player['hp_left'] -= enemy[3]
				if dmg == 0:
					print('Nothing happens..'+space_cancel)
				sleep(1)
				print(ERASE+ERASE+ERASE+ERASE,end='')
		print(versus_step(player,enemy,enemy_hp_left),end='\n\n')
		if player['hp_left'] <= 0: 
			print('Player dies...\n'); player['hp_left'] = 0
		else:
			print(enemy[0],OKGREEN+'DEFEATED'+ENDC+'!!!')
			player['level'] += 1
			print('You reach level '+WARNING+str(player['level']+1)+ENDC+'!\n') 
		player['stats']['stamina'] -= 1

def strength_training(player):
	'''Battle: improves strength'''
	remove_menu()
	print(set_title('Strength training'))

	if can_do_action(player):

		inkey = _Getch()
		d = input('Choose the difficulty:\n1 - Easy\n2 - Medium\n3 - Hard\n4 - Extreme\nChoise: ')
		while not possible_choise(d,range(1,4),int):
			print(ERASE+ERASE+ERASE+ERASE+ERASE+ERASE,end='\r')
			d = input('Choose the difficulty (from 1 to 4):\n1 - Easy\n2 - Medium\n3 - Hard\n4 - Extreme\nChoise: ')
		l = input('Choose the lenght (from 1 to 10 seconds): ')
		while not possible_choise(l,range(1,10),int):
			print(ERASE,end='\r')
			l = input('Choose the lenght (from 1 to 10 seconds): ')
		d,l = int(d),int(l)
		pattern = 'a'*d+'s'*d
		print(); print('Repeat the pattern',BOLD+WARNING+pattern.upper()+ENDC,'as fast and as long as you can for '+str(l)+' seconds and press ENTER'); input('When you\'re ready, press ENTER '); print('GO!')
		try:
			train = input_with_timeout(l,inkey,False)
			n = len(findall(pattern,train))
			improves = n*2**(d+1)
			print('\nPattern executed {1}{0}{2} times.[{3}]'.format(n,WARNING,ENDC,train)); print('Strength upgrade: {0} -> {2}{1}{3}'.format(player['stats']['strength'],player['stats']['strength']+improves,OKGREEN,ENDC)); print(OKGREEN+'Training complete!\n'+ENDC);
			player['stats']['strength'] += improves
		except ValueError:
			n = len(findall(pattern,train))
			improves = n*2**(d+1)
			print('\nPattern executed {1}{0}{2} times.[{3}]'.format(n,WARNING,ENDC,train)); print('Strength upgrade: {0} -> {2}{1}{3}'.format(player['stats']['strength'],player['stats']['strength']+improves,OKGREEN,ENDC)); print(OKGREEN+'Training complete!\n'+ENDC);
			player['stats']['strength'] += improves

		player['stats']['stamina'] -= 1

def dojo(moveset_p,moveset_b):
	'''Dojo: train moveset'''
	remove_menu()
	print(set_title('Dojo'))
	print(WARNING+'Player moveset'+ENDC)
	print('\n'.join(['  {0:<12} {1}'.format(UNDERLINE+k+ENDC,v) for k,v in moveset_p]))
	print(WARNING+'Boss moveset'+ENDC)
	print('\n'.join(['  {0:<12} {1}'.format(UNDERLINE+k+ENDC,v) for k,v in moveset_b]))
	print()
	print('\\'+WARNING+'B'+ENDC+'   '+' '.join(['{:<11}'.format(UNDERLINE+move+ENDC) for move in get_shortcut(moveset_b)]))
	print(WARNING+'P'+ENDC)
	print('\n'.join(['{:<13}'.format(UNDERLINE+get_shortcut(moveset_p)[i]+ENDC)+'   '.join([replace_dmg(v) for v in row]) for i,row in enumerate(PARTIAL_MATRIX)]))
	print()

def stats(player):
	'''Print: stats'''
	remove_menu()
	print(set_title(player['name']+' stats'))
	print('{15:<11}{11}{10}{14}{12}\n{6:<11}{11}{10}{2}{12} / {1}\n{7:<11}{11}{10}{3}{12}\n{8:<11}{11}{10}{4}{12}\n{9:<11}{11}{10}{5}{12} / 3\n'.format(player['name'],player['hp'],player['hp_left'],player['stats']['strength'],player['stats']['focus'],player['stats']['stamina'],'HP','Strength','Focus','Stamina',BOLD,WARNING,ENDC,UNDERLINE,player['level']+1,'Level'))

def rest(player):
	'''Resting: TODO'''
	remove_menu()
	print(set_title('Resting'))
	player['hp_left'] = player['hp']
	player['stats']['stamina'] = 3
	print(OKGREEN+'Rest completed!\n'+ENDC)

def help():
	'''Print: menu with help'''
	remove_menu()
	print(get_menu('MENU [Help]',True))
	
# Other functions -----------------------------------

def new_movesets(level):
	'''Reload movesets base on level'''
	return load_moveset('moveset_player.csv',level),load_moveset('moveset_bosses.csv',level)

def is_alive(player):
	'''Check if alive'''
	return player['hp_left'] > 0

def enough_stamina(player):
	'''Check enough stamina'''
	return player['stats']['stamina'] > 0

def load_moveset(filename,level):
	'''Load moveset base on player level'''
	csv_moveset = read_csv_moveset(filename)
	return [(s,n) for l,s,n in csv_moveset if l <= level]

def get_shortcut(moveset):
	'''Return list with actions shortcut'''
	return [s for s,n in moveset]

def load_vs_matrix(moveset_player,moveset_boss,total_matrix):
	'''Get partial table'''
	return [[x for x in row[:len(moveset_boss)]] for row in total_matrix[:len(moveset_player)]]

def possible_choise(choise,choise_list,type_choise):
	'''Possible choice from menu'''
	try:
		c = type_choise(choise)
		return c in choise_list
	except ValueError:
		return False

def remove_menu():
	'''Remove all the menu rows'''
	n_rows = len(MENU)+2
	print(ERASE*n_rows,end='\r')

def read_csv_moveset(filename):
	'''Read csv: moveset'''
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		return [(int(l),str(s),str(n)) for l,s,n in [row for row in csv_reader][1:]]

def read_csv_bosses(filename):
	'''Read csv: bosses'''
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		return [(str(n),int(h),int(hl),int(d),int(v),str(m)) for n,h,hl,d,v,m in [row for row in csv_reader][1:]]

def replace_dmg(v):
	'''Symbol for dojo table'''
	if v == 1: return OKGREEN+'O'+ENDC
	elif v == -1: return FAIL+'X'+ENDC
	else: return '-' 

# ---------------------------------------------------

if __name__ == '__main__':
	# INITIAL SETTINGS ------------------------------
	p_stats = {'strength':1,'focus':1,'stamina':0}
	player = {'name':'Mortafix','level':0,'hp':401,'hp_left':1,'stats':p_stats}
	enemies = read_csv_bosses('bosses.csv')
	PLAYER_MOVES,BOSS_MOVES = new_movesets(player['level'])
	FIGHTERS_MOVESET = [PLAYER_MOVES,BOSS_MOVES]
	PARTIAL_MATRIX = load_vs_matrix(PLAYER_MOVES,BOSS_MOVES,VS_MATRIX)
	# MENU ------------------------------------------
	while True:
		print(get_menu('MENU'))
		m = input('choice: ')
		while not possible_choise(m,[s for s,w,h in MENU],str):
			remove_menu()
			print(get_menu('MENU'))
			m = input('choice: ')
		while m == 'h' or not possible_choise(m,[s for s,w,h in MENU],str):
			help()
			m = input('choice: ')
		if m == 's':
			stats(player)
		elif m == 't':
			strength_training(player)
		elif m == 'b':
			battle(player,enemies[player['level']],FIGHTERS_MOVESET)
		elif m == 'r':
			rest(player)
		elif m == 'd':
			dojo(PLAYER_MOVES,BOSS_MOVES)
		elif m == 'q':
			print(WARNING+'Game saved.'+ENDC)
			break

	

