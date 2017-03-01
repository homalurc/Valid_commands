"""
Handles the work of validating and processing command input.
"""
import os
import subprocess
import time
from db import session, engine
from base import Command
import math

def get_valid_commands(queue, fi, fd):
    # TODO: efficiently evaluate commands
	list_val  = 0
	# for storing commands that have to evaluated
	commands = []
	# for storing given valid commands
	valid_commands = []
	# if file data is given directly
	if(not fd==None):
		# read commands.txt file line by line 
		lines = fd.split('\n')
		for line in lines:
			if('[COMMAND LIST]' in line):
				list_val = 1
			elif('[VALID COMMANDS]' in line):
				list_val = 2
			else:
				if (list_val == 1):
					commands.append(line)
				if(list_val == 2):
					valid_commands.append(line)

	# if file name is given 
	else:
		with open('commands.txt','r') as commandsFile:
			for line in commandsFile:
				if('[COMMAND LIST]' in line):
					list_val = 1
				elif('[VALID COMMANDS]' in line):
					list_val = 2
				else:
					if (list_val == 1):
						commands.append(line)
					if(list_val == 2):
						valid_commands.append(line)
	# check for all commands whether it is a valid command
	for command in commands:
		command = command.strip()
		if(command in valid_commands):
			queue.put(command)
			print command, 'is valid'
		else:
			print command, 'is not valid'  
	

    


def process_command_output(queue):
    # TODO: run the command and put its data in the db
    while(not queue.empty()):
		command = queue.get()
		# create a temp file that does not exist already
		file = open('test_'+str(os.getpid())+'.sh','w')
		file.write(command)
		file.close()
		
		start = time.time()
		p = subprocess.Popen(['sh','test_'+str(os.getpid())+'.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		
		out=''
		
		# poll the subprocess created until the returncode is not None or until the time is over 60 seconds
		while(p.returncode == None and time.time()-start<60):
			p.poll()
			#read from stdout and store it in out
			out = out + p.stdout.readline()
		t = time.time()-start

		# if return code of the process is still None kill the process
		if(p.returncode == None):
			p.kill()
		
		# if time taken to run the command is over 60 seconds then assign the time taken as 0
		if( t>60):
			t = 0.0
		
		# create an object of the table 
		c = Command(command, len(command), math.ceil(t), out)
		# check whether the same command exists in the table and if it does do not the command again to the database
		command_db = session.query(Command).filter_by(command_string = command).first()
		if(command_db is None):
			session.add(c)
			session.commit()
		#remove the temporary file that was created
		os.remove('test_'+str(os.getpid())+'.sh')


