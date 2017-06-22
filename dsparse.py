#!/usr/bin/python3

'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

'''
Usage:
Select the section of the datasheet that you want to parse. Copy. Run. Paste.
For example, from the STM32L4 Technical Reference Manual, I'd select this
part, between the double quotes:
"
40.8.1  Control register 1 (USART_CR1)
Address offset: 0x00
Reset value: 0x00
<register info>
Bits 31:29 Reserved,
blah blah blah...
"
40.8.2.........

Copy that to the clipboard and then run the software.  It will:
- Read the text from the clipboard
- Try to parse it
- Save the output to your clipboard (as well as print it).

Then you:
- Paste it into your code
- Select the next section
- Rinse and repeat
'''


# This is tuned for ST datasheets, specifically for the TRM for the STM32L4.  YMMV.

import re
import sys
import math
import time
import pyperclip


sectionSeparatorRE = r'^\d+\.\d+\.\d+'

scriptName = 'dsparse'
scriptVer = 'v1.0'

#infilename = "/tmp/cr1b.txt"

# These lengths determine how many tabs to use
tabWidth = 8
shortLen = (5*tabWidth)
longLen = (8*tabWidth)

intext = pyperclip.paste()
outtext = ''

def output(text=''):
  global outtext
  outtext += text+'\n'
  print(text)
  

def processSection(lines):
  linesDone = 0
  
  if len(lines) < 5:
    print("ERROR: Are you sure you copied the text?")
    sys.exit(1)
    
  registerbase = None
  for linesStart in range(5):
    registerbase = re.search(r'\((\w+)\)', lines[linesStart])
    linesDone += 1
    if registerbase is None:
      continue
    else:
      break
      
  if registerbase is None:
      print("ERROR: Couldn't find register name in input")
      sys.exit(1)
    
  registerbase = registerbase.group(1)
  output('/* --- '+registerbase+' values ----------------------------------------------------- */')
  output('/* --- ('+scriptName+' '+scriptVer+' at '+time.strftime('%c')+') --- */')
  output()
  
  inSection = False
  
  for line in lines[linesStart+1:]:
    
    if inSection:
      if re.search(sectionSeparatorRE, line) is not None:
        # Start of next section, so bail
        return linesDone
    
    inSection = True
    
    linesDone += 1
    if line.startswith('Bit'):
      tokens = line.split(' ')
      isRange = False
      if line.startswith('Bits'):
        isRange = True
        name = tokens[2].split('[')[0].strip(',').strip(':')
        if 'Reserved' in name:
          continue
        nameBits = re.search(r'\w+\[(\d+):(\d+)\]', tokens[2])
        nameBits = [nameBits.group(1), nameBits.group(2)]
        bit = tokens[1].split(':')
        rangeLength = 1 + int(bit[0]) - int(bit[1])
        rangeMask = '0x{:X}'.format((2 ** rangeLength) - 1)
      else:
        bit = tokens[1]
        name = tokens[2].strip(',').strip(':')

      if 'Reserved' in name:
        continue
        
      description = line.split(':')[-1].strip()
      
      startLine = '#define '+registerbase+'_'+name
      
      if isRange:
        startLine += '_MASK'
        comment = '/* '+name+'['+nameBits[0]+':'+nameBits[1]+']: '+description+' */'
        endLine = '('+rangeMask+' << '+bit[1]+')'
      else:
        comment = '/* '+name+': '+description+' */'
        endLine = '(1 << '+bit+')'
        
      if len(startLine) < shortLen:
        tabs = '\t' * math.ceil((shortLen - len(startLine))/tabWidth)
      elif len(startLine) < longLen:
        tabs = '\t' * math.ceil((longLen - len(startLine))/tabWidth)
      else:
        tabs = '\t'
      
      output(comment)
      output(startLine+tabs+endLine)
      output()
  
  return linesDone
  
def processSections(lines):
  linesTodo = len(lines)
  linesStart = 0
  while (linesStart < linesTodo):
    linesDone = processSection(lines[linesStart:])
    linesStart += linesDone

lines = intext.split('\n')

processSections(lines)

print("ALL DONE")
pyperclip.copy(outtext)


