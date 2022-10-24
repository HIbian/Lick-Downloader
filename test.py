import sys

outputfile = open('log2', 'a')
sys.stdout = outputfile
print('123')
print('321')
outputfile.close()
