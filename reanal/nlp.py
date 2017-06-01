import sys

if __name__ == '__main__':
	argc = len(sys.argv)
	if argc <= 3:
		print 'Usage: python nlp.py features/sentiment TASK [BiggerPockets, activerain]'
		exit()
	if argc > 3:
		urls = sys.argv[3:]
	else:
		urls = ['BiggerPockets', 'activerain']
		
	analysis, task = sys.argv[1:3]
	
