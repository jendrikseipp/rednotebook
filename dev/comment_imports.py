import os

keepnote_dir = '../rednotebook/gui/keepnote/'

whitelist = ['richtext', 'gui', 'LinkedTreeNode', 'get_resource', 'UndoStack', 'Listeners']

def comment_out_imports(file):
	next_line_is_comment = False
	line_whitelisted = False
	
	lines = open(file).readlines()
	
	for lineIndex in range(len(lines)):
		line = lines[lineIndex]
		
		if line.strip().startswith('#'):
			continue
		
		for item in whitelist:
			if item in line:
				line_whitelisted = True
				
		if line_whitelisted:
			continue
		
		if ('import ' in line and 'keepnote' in line) or next_line_is_comment:
			next_line_is_comment = False
			line_whitelisted = False
			print line
			lines[lineIndex] = '##' + line
			print lines[lineIndex]
			if line.strip().endswith('\\'):
				next_line_is_comment = True
			
	open(file, 'w').writelines(lines)
	

for dirpath, dirnames, filenames in os.walk(keepnote_dir):
	for filename in filenames:
		file = os.path.join(dirpath, filename)
		
		if '.svn' not in file and file.endswith('.py'):
			comment_out_imports(file)