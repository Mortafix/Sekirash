from time import sleep
from random import choice,random
from re import findall
import signal
import csv

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
ERASE = '\x1b[1A\x1b[2K'

PLAYER_MOVE = {'n':'nothing','j':'jump','d':'dodge','a':'attack','mck':'mikiri counter'}
BOSS_MOVE = {'s':'swipe','g':'grab','m':'mikiri','n':'nothing'}
FIGHTERS = [PLAYER_MOVE,BOSS_MOVE]
VS_MATRIX = [[-1,-1,-1,0],
			 [0,-1,-1,0],
			 [-1,0,0,0],
			 [-1,-1,-1,1],
			 [-1,-1,1,0]]

# Input functions -----------------------------------

def alarm_handler(signum, frame):
	'''Raise a timeout error'''
	raise ValueError

def input_with_timeout(prompt, timeout):
	'''Input with timeout'''
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(timeout)
	try:
		return input(prompt)
	finally:
		signal.alarm(0)

# Move functions ------------------------------------

def damage_vs(player_move,enemy_move):
	'''Return damage after versus: 0 -> no damage, 1 -> enemy takes damage and -1 player takes damage'''
	return VS_MATRIX[list(PLAYER_MOVE.keys()).index(player_move)][list(BOSS_MOVE.keys()).index(enemy_move)]

def possible_move(move):
	'''1 if possible move, 0 instead'''
	return move in PLAYER_MOVE.keys()

def rand_move(moveset):
	'''Generate a random move for the enemy'''
	return choice(moveset)

# Printing functions --------------------------------

def get_name(move,who):
	'''Printing: move name'''
	return FIGHTERS[who][move]
 
def hp_bar(hp_total,hp_left):
	'''Printing: HP bar'''
	if hp_left <= 0: return '['+BOLD+FAIL+'XXXXXXXXXXXXXXX'+ENDC+']'+' {:.1f} %'.format(0)
	else: return '['+BOLD+OKBLUE+''.join(['#' if x < round(hp_left * 15 / hp_total) else ENDC+'_' for x in range(15)])+ENDC+']'+' {:.1f} %'.format(hp_left/hp_total*100)

def versus_step(player,enemy,enemy_hp_left):
	'''Printing: versus step'''
	max_string = max(len(player[0]),len(enemy[0]))
	return '{5}{0:<{4}}{6} {1}\n{5}{2:>{4}}{6} {3}'.format(player[0],hp_bar(player[1],player[2]),enemy[0],hp_bar(enemy[1],enemy_hp_left),max_string,BOLD,ENDC)

def print_title(string):
	print(BOLD+UNDERLINE+string+ENDC)

# Actions functions --------------------------------

def battle(player,enemy):
	'''Battle: enemy'''
	remove_menu()
	print_title('Boss battle'); sleep(1)

	if player[3][2] == 0:
		print('Seems you\'re out of '+FAIL+'stamina'+ENDC+' (0/3) [check '+WARNING+'stats'+ENDC+']\nBefore doing stuff, you need to restore the stamina ['+WARNING+'rest'+ENDC+']\n')
		return -1
	else: player[3][2] -= 1

	print('A new Boss appeared..'); sleep(2); print(BOLD+FAIL+enemy[0].upper()+ENDC); sleep(2); print('FIGHT!',end='\n\n')
	enemy_hp_left = enemy[2]
	while enemy_hp_left > 0 and player[2] > 0:
		print(versus_step(player,enemy,enemy_hp_left))
		bm = rand_move(enemy[5])
		try:
			print('Enemy does ',end='')
			sleep(random())
			pm = input_with_timeout(get_name(bm,1)+' > ',enemy[4])
			if possible_move(pm):
				dmg = damage_vs(pm,bm)
			else:
				dmg = damage_vs('n',bm)
		except ValueError:
			dmg = damage_vs('n',bm)
			print('nothing..')
		finally:
			if dmg == 1:
				print('Boss takes '+OKGREEN+'DAMAGE'+ENDC)
				enemy_hp_left -= player[3][0]
			if dmg == -1:
				print('Player takes '+FAIL+'DAMAGE'+ENDC)
				player[2] -= enemy[3]
			if dmg == 0:
				print('Nothing happens..')
			sleep(1)
			print(ERASE+ERASE+ERASE+ERASE,end='')
	print(versus_step(player,enemy,enemy_hp_left),end='\n\n')
	if player[2] <= 0: print('Player dies...'); player[2] = 0
	else: print(enemy[0],FAIL+'DEFEATED'+ENDC+'!!!') 

def strength_training(player):
	'''Battle: improves strenght'''
	remove_menu()
	print_title('Strength training'); sleep(1)

	if player[3][2] == 0:
		print('Seems you\'re out of '+FAIL+'stamina'+ENDC+' (0/3) [check '+WARNING+'stats'+ENDC+']\nBefore doing stuff, you need to restore the stamina ['+WARNING+'rest'+ENDC+']\n')
		return -1
	else: player[3][2] -= 1

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
		train = input_with_timeout('> ',l)
		n = len(findall(pattern,train))
		improves = n*2**(d+1)
		print('\nPattern executed {1}{0}{2} times.'.format(n,WARNING,ENDC)); print('Strength upgrade: {0} -> {2}{1}{3}'.format(player[3][0],player[3][0]+improves,OKGREEN,ENDC)); print(OKGREEN+'Training complete!\n'+ENDC);
		player[3][0] += improves
	except ValueError:
		print(OKGREEN+'\nYou fool!'+ENDC+' (press ENTER before timeout)\n')

def stats(player):
	'''Print: stats'''
	remove_menu()
	print_title(player[0]+' stats')
	print('{6:<11}{11}{10}{2}{12} / {1}\n{7:<11}{11}{10}{3}{12}\n{8:<11}{11}{10}{4}{12}\n{9:<11}{11}{10}{5}{12} / 3\n'.format(player[0],player[1],player[2],player[3][0],player[3][1],player[3][2],'HP','Strength','Focus','Stamina',BOLD,WARNING,ENDC,UNDERLINE))

def rest(player):
	'''Resting: TODO'''
	remove_menu()
	print_title('Resting')
	player[2] = player[1]
	player[3][2] = 3
	print(OKGREEN+'Rest completed!\n'+ENDC)

def help():
	'''Print: menu with help'''
	remove_menu()
	print_title('MENU [Help]')
	return input('s - Player stats ['+UNDERLINE+'check all the players stats'+ENDC+']\nt - Strength training ['+UNDERLINE+'upgrade strenght value'+ENDC+']\nb - Boss battle ['+UNDERLINE+'start a boss fight'+ENDC+']\nr - Rest ['+UNDERLINE+'restore stamina'+ENDC+']\nh - Help ['+UNDERLINE+'print menu with help'+ENDC+']\nq - Save and quit ['+UNDERLINE+'save progress and quit the game'+ENDC+']\nChoise: ')

# Other functions -----------------------------------

def possible_choise(choise,choise_list,type_choise):
	'''Possible choice from menu'''
	try:
		c = type_choise(choise)
		return c in choise_list
	except ValueError:
		return False

def remove_menu():
	n_rows = 8
	print(ERASE*n_rows,end='\r')

def read_csv(filename):
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		return [(str(n),int(h),int(hl),int(d),int(v),str(m)) for n,h,hl,d,v,m in [row for row in csv_reader][1:]]

# ---------------------------------------------------

if __name__ == '__main__':
	p_stats = [1,0.1,0]
	p_hp = 401
	player = ['Mortafix',p_hp,1,p_stats,0]
	enemies = read_csv('bosses.csv')
	print(enemies)
	menu = BOLD+UNDERLINE+'MENU'+ENDC+'\ns - Player stats\nt - Strength training\nb - Boss battle\nr - Rest\nh - Help\nq - Save and quit\nChoise: '
	# MENU -----------------------------------
	while True:
		m = input(menu)
		while not possible_choise(m,['s','t','b','q','r','h'],str):
			remove_menu()
			m = input(menu)
		while m == 'h' or not possible_choise(m,['s','t','b','q','r','h'],str):
			m = help()
		if m == 's':
			stats(player)
		elif m == 't':
			strength_training(player)
		elif m == 'b':
			battle(player,enemies[player[4]])
		elif m == 'r':
			rest(player)
		elif m == 'q':
			print(WARNING+'Game saved.'+ENDC)
			break

	

