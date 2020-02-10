from time import sleep,time
from random import choice,random
from re import findall
import signal
import csv
from getchar import _Getch
from math import floor
import pickle
import decimal

SAVE_FILE = 'player.save'

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
ERASE = '\x1b[1A\x1b[2K'

MENU = [('p','Player stats','check all the players stats'),
		('s','Strength training','upgrade strength value'),
		('f','Focus training','upgrade focus value'),
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

CSV_DIR = 'csv/'

# Input functions -----------------------------------

def alarm_handler(signum,frame):
	'''Raise a timeout error'''
	raise ValueError

def input_with_timeout(timeout,inkey,single=True,moveset=None):
	'''Input with timeout'''
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(timeout)
	try:
		if single:
			c,n = inkey(),0
			while is_prefix(moveset,n,c):
				if c in moveset: return c
				c += inkey()
				n += 1
		else:
			ret = []
			while True:
				ret.append(inkey())
	finally:
		signal.alarm(0)
		if not single: return ''.join(ret)

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

		if enough_fast(player,enemy[4]):

			inkey = _Getch()
			print('A new Boss appeared..'); sleep(2); print(BOLD+FAIL+enemy[0].upper()+ENDC); sleep(2); print('FIGHT!',end='\n\n')
			enemy_hp_left = enemy[2]
			enemy_velocity = int(floor(player['stats']['focus']) - enemy[4] + 1)
			while enemy_hp_left > 0 and player['hp_left'] > 0:
				print(versus_step(player,enemy,enemy_hp_left))
				bm = rand_move(enemy[5])
				try:
					sleep(random())
					print('Enemy does',get_name(fighters_moveset,bm,1),end='\n')
					pm = input_with_timeout(enemy_velocity,inkey,moveset=get_shortcut(fighters_moveset[0]))
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
				return 0
			else:
				print(enemy[0],OKGREEN+'DEFEATED'+ENDC+'!!!')
				player['level'] += 1
				print('You reach level '+WARNING+str(player['level']+1)+ENDC+'!\n') 
				player['stats']['stamina'] -= 1
				return 1
		else:
			print('You\'ll die instantly, be careful!')
			print('You don\'t have enough focus to counter this Boss\' velocity ['+WARNING+'train focus'+ENDC+']\n')
			return 0
	
	else: return 0


def strength_training(player):
	'''Training: improves strength'''
	remove_menu()
	print(set_title('Strength training'))

	if can_do_action(player):

		if is_trainable(player,'strength'):

			inkey = _Getch()
			d = select_difficulty(inkey,[(1,'Easy'),(2,'Hard')])
			pattern = 'a'*(d+1)+'l'*(d+1)
			print(); print('Repeat the pattern',BOLD+WARNING+pattern.upper()+ENDC,'as fast as you can for 5 seconds'); input('When you\'re ready, press ENTER '); print('GO!')
			try:
				train = input_with_timeout(5,inkey,False)
			except ValueError: pass
			
			n = len(findall(pattern,train))
			improve = n*2**(d+1) / 7 * d
			print('\n| {3} |\nPattern executed {1}{0}{2} times.'.format(n,WARNING,ENDC,train.upper()))
			update_stats(player,'strength',improve)
			player['stats']['stamina'] -= 1

def focus_training(player):
	'''Training: improves focus'''
	remove_menu()
	print(set_title('Focus training'))

	if can_do_action(player):

		if is_trainable(player,'focus'):

			inkey = _Getch()
			d = select_difficulty(inkey,[(1,'Easy'),(2,'Hard'),(3,'Insane')])
			times = 5+((d-1)*2)
			pattern = ''.join([chr(choice(range(97,123))) for _ in range(times)])
			print('\n> 3',end='\r'); sleep(1); print('> 2',end='\r'); sleep(1); print('> 1',end='\r'); sleep(1); print('> GO!\n')
			print('Insert the pattern',BOLD+WARNING+pattern.upper()+ENDC,'in the next 3 seconds!');
			try:
				train = input_with_timeout(3,inkey,False)
			except ValueError: pass
			
			print('\n| {} |'.format(train.upper()))
			if pattern == train:
				improve = 2**d / 10
				update_stats(player,'focus',improve)
				player['stats']['stamina'] -= 1
			else:
				print('Fai schifo!')


def dojo(movesets):
	'''Dojo: train moveset'''
	moveset_p,moveset_b = movesets[0],movesets[1]
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
	print('{15:<11}{11}{10}{14}{12}\n{6:<11}{11}{10}{2}{12} / {1}\n{7:<11}{11}{10}{3:.2f}{12} / {17}\n{8:<11}{11}{10}{4:.2f}{12} / {18}\n{9:<11}{11}{10}{5}{12} / {16}\n'.format(player['name'],player['hp'],player['hp_left'],player['stats']['strength'],player['stats']['focus'],player['stats']['stamina'],'HP','Strength','Focus','Stamina',BOLD,WARNING,ENDC,UNDERLINE,player['level']+1,'Level',player['max_stats']['stamina'],player['max_stats']['strength'],player['max_stats']['focus']))

def rest(player):
	'''Resting: TODO'''
	remove_menu()
	print(set_title('Resting'))
	player['hp_left'] = player['hp']
	player['stats']['stamina'] = 3
	player['stats']['strength'] *= 0.95
	player['stats']['focus'] *= 0.95
	print(OKGREEN+'Rest completed!\n'+ENDC)

def help():
	'''Print: menu with help'''
	remove_menu()
	print(get_menu('MENU [Help]',True))
	
# Other functions -----------------------------------

def select_difficulty(inkey,list_diff):
	'''Menu: difficulty selector'''
	print('Choose the difficulty:')
	print('\n'.join(['{} - {}'.format(v,l) for v,l in list_diff]))
	d = input('Choice: ')
	while not possible_choice(d,range(1,len(list_diff)+1),int):
		print(ERASE,end='\r')
		d = input('Choice: ')
	return int(d)

def update_stats(player,stat,improve):
	'''After complete a train upgrade stats'''
	new_value = player['stats'][stat] + improve
	old = player['stats'][stat]
	player['stats'][stat] = new_value if new_value < player['max_stats'][stat] else player['max_stats'][stat]
	print('Strength upgrade: {0:.2f} -> {2}{1:.2f}{3}'.format(old,player['stats'][stat],OKGREEN,ENDC)); print(OKGREEN+'Training complete!\n'+ENDC)
	

def is_prefix(moveset,n,c):
	'''Check if input is prefix of more complex move'''
	return c in [x[:n+1] for x in moveset]

def new_movesets(level):
	'''Reload movesets base on level'''
	return load_moveset(CSV_DIR+'moveset_player.csv',level),load_moveset(CSV_DIR+'moveset_bosses.csv',level)

def is_alive(player):
	'''Check if alive'''
	return player['hp_left'] > 0

def enough_stamina(player):
	'''Check if enough stamina'''
	return player['stats']['stamina'] > 0

def enough_fast(player,enemy_velocity):
	'''Check if enough focus'''
	return player['stats']['focus'] > enemy_velocity

def is_trainable(player,stats):
	'''Check if stats is maxed'''
	if player['stats'][stats] < player['max_stats'][stats]: return 1
	else: 
		print('You already reach the '+WARNING+'maximum'+ENDC+' value in '+WARNING+stats+ENDC+' for this level.\nIt\'s time to beat the boss!\n')
		return 0

def load_moveset(filename,level):
	'''Load moveset base on player level'''
	csv_moveset = read_csv_moveset(filename)
	return [(s,n) for l,s,n in csv_moveset if l <= level]

def get_shortcut(moveset):
	'''Return list with actions shortcut'''
	return [s for s,n in moveset]

def load_vs_matrix(movesets,total_matrix):
	'''Get partial table'''
	return [[x for x in row[:len(movesets[1])]] for row in total_matrix[:len(movesets[0])]]

def possible_choice(choice,choice_list,type_choice):
	'''Possible choice from menu'''
	try:
		c = type_choice(choice)
		return c in choice_list
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

def get_max_stats(filename,level):
	'''Read csv: max stats'''
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file,delimiter=',')
		return [{'strength':int(s),'focus':int(f),'stamina':int(t)} for s,f,t in [row for row in csv_reader][1:]][level]

def replace_dmg(v):
	'''Symbol for dojo table'''
	if v == 1: return OKGREEN+'O'+ENDC
	elif v == -1: return FAIL+'X'+ENDC
	else: return '-' 

def new_level(player):
	return get_max_stats(CSV_DIR+'stats.csv',player['level']),new_movesets(player['level'])

# Save / Load Functions --------------------------------------

def save_data(player):
	'''Save data on file'''
	with open(SAVE_FILE, 'wb') as f:
		pickle.dump(player,f, protocol=2)

def load_data():
	'''Load data from file'''
	try:
		with open(SAVE_FILE, 'rb') as f:
			player = pickle.load(f)
		return player
	except FileNotFoundError:
		return None		

def new_player(usr):
	'''Creating new player'''
	p_stats = {'strength':1,'focus':1,'stamina':2}
	max_stats = get_max_stats(CSV_DIR+'stats.csv',0)
	player = {'name':usr,'level':0,'hp':401,'hp_left':1,'stats':p_stats,'max_stats':max_stats}
	save_data(player)
	return player

# ---------------------------------------------------

if __name__ == '__main__':
	# INITIAL SETTINGS ------------------------------
	player = load_data()
	if player:
		print('Welcome back {1}{0}{2}!\n'.format(player['name'],WARNING,ENDC))
	else:
		print('I\'ve never seen this noob before, I think you\'re new down here.')
		usr = input('What\'s your name? ')
		print('{1}{0}{3}? Kinda stupid name, but whatever.. Welcome on {2}SEKIRASH{3}!\n'.format(usr,WARNING,UNDERLINE,ENDC))
		player = new_player(usr)
	# SET UP BOSS AND MOVESET -----------------------
	enemies = read_csv_bosses(CSV_DIR+'bosses.csv')
	PLAYER_MOVES,BOSS_MOVES = new_movesets(player['level'])
	FIGHTERS_MOVESET = [PLAYER_MOVES,BOSS_MOVES]
	PARTIAL_MATRIX = load_vs_matrix(FIGHTERS_MOVESET,VS_MATRIX)
	# GAME ------------------------------------------
	while True:
		print(get_menu('MENU'))
		m = input('Choice: ')
		while not possible_choice(m,[s for s,w,h in MENU],str):
			remove_menu()
			print(get_menu('MENU'))
			m = input('Choice: ')
		while m == 'h' or not possible_choice(m,[s for s,w,h in MENU],str):
			help()
			m = input('Choice: ')
		if m == 'p':
			stats(player)
		elif m == 's':
			strength_training(player)
			save_data(player)
		elif m == 'f':
			focus_training(player)
			save_data(player)
		elif m == 'b':
			win = battle(player,enemies[player['level']],FIGHTERS_MOVESET)
			if win:
				player['max_stats'],FIGHTERS_MOVESET = new_level(player)
				PARTIAL_MATRIX = load_vs_matrix(FIGHTERS_MOVESET,VS_MATRIX)
			save_data(player)
		elif m == 'r':
			rest(player)
			save_data(player)
		elif m == 'd':
			dojo(FIGHTERS_MOVESET)
		elif m == 'q':
			save_data(player)
			print(WARNING+'Game saved.'+ENDC)
			break