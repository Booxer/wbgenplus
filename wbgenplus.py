# -*- coding: utf-8 -*-
"""
Spyder Editor

This temporary script file is located here:
/home/mkreider/.spyder2/.temp.py
"""
from xml.dom import minidom
import datetime
from textformatting import parseNumeral as str2int
from textformatting import mskWidth as mskWidth 
import os.path
import sys
import getopt
from stringtemplates import sysIfStr as sysStr
from stringtemplates import wbsVhdlStrGeneral
from writeout import writeout
from wbslave import wbslave as wbs

myVersion = "1.1"
myStart   = "15 Dec 2014"
myUpdate  = "10 Jan 2015"
myCreator = "M. Kreider <m.kreider@gsi.de>"

def parseXMLNew(xmlIn, now, unitname):
    xmldoc      = minidom.parse(xmlIn)   

    #defaults
    dictVendId  = {'GSI'       : 0x0000000000000651,
                   'CERN'      : 0x000000000000ce42}    
    
    author      = "unknown_author"
    email       = "unknown_mail"
    version     = "unknown_version"
        
    ifList      = []
    clockList   = []
    genIntD     = dict()
    genMiscD    = dict()
    
    if (len(xmldoc.getElementsByTagName('wbdevice'))==0):
        print "No <wbdevice> tag found"
        sys.exit(2)
        
    author   = xmldoc.getElementsByTagName('wbdevice')[0].getAttribute('author')
    version  = xmldoc.getElementsByTagName('wbdevice')[0].getAttribute('version')
    email    = xmldoc.getElementsByTagName('wbdevice')[0].getAttribute('email')

       
    clocks = xmldoc.getElementsByTagName('clockdomain')
    if(len(clocks) > 0):    
        for clock in clocks:
            if(clock.hasAttribute("name")):
                clockList += [clock.getAttribute("name")]
            else:
                print "Clock must have a name!"
                sys.exit(2)
    else:
        clockList += ["sys"]        
            
    
    generics = xmldoc.getElementsByTagName('generic')
   
    print "Found %u generics\n" % len(generics)   
    for generic in generics:
        genName = generic.getAttribute('name')
        genType = generic.getAttribute('type')
        genVal  = generic.getAttribute('default')
        genDesc = generic.getAttribute('comment')
        #if genTypes.has_key(genType):
        #    genType = genTypes[genType]               
        if(genType == 'natural'):
            aux = str2int(genVal)
            if(aux == None):            
                print "Generic <%s>'s numeric value <%s> is invalid" % (genName, genVal)
            else:        
                genVal = aux
                genIntD[genName] = [ genType , genVal, genDesc ]
        else:
            genMiscD[genName] = [ genType , genVal, genDesc ]    
            #else:
            #    print "%s is not a valid type" % generic.getAttribute('type')
            #    sys.exit(2)
 
        
    slaveIfList = xmldoc.getElementsByTagName('slaveinterface')
    print "Found %u slave interfaces\n" % len(slaveIfList)    
    for slaveIf in slaveIfList:
        
        genericPages = False 
        name    = slaveIf.getAttribute('name')
        ifWidth = str2int(slaveIf.getAttribute('data'))
        print "Slave <%s>: %u Bit wordsize" % (name, ifWidth)
        pages  = slaveIf.getAttribute('pages')
        #check integer generic list
        for genName in genIntD.iterkeys():
            if(pages.find(genName) > -1):
                genericPages = True                
        
        if(not genericPages):        
            aux = str2int(pages)
            if(aux == None):            
                print "Slave <%s>: Pages' numeric value <%s> is invalid. Defaulting to 0" % (name, pages)
                pages = 0
            else:        
                pages = aux
    
        
        #sdb record
        sdb = slaveIf.getElementsByTagName('sdb')
        vendId      = sdb[0].getAttribute('vendorID')
        prodId      = sdb[0].getAttribute('productID')
        #check vendors
        if dictVendId.has_key(vendId):
            print "Slave <%s>: Known Vendor ID <%s> found" % (name, vendId)            
            vendId = dictVendId[vendId]
             
        else:
            aux = str2int(vendId)
            if(aux == None):            
                print "Slave <%s>: Invalid Vendor ID <%s>!" % (name, vendId)
                sys.exit(2)
            else:
                vendId = aux                
                print "Slave <%s>: Unknown Vendor ID <%016x>" % (name, vendId)                
                
        
        aux = str2int(prodId)
        if(aux == None):            
                print "Slave <%s>: Invalid Product ID <%s>!" % (name, prodId)
        else:
            prodId = aux     
                
        sdbname     = sdb[0].getAttribute('name')
        if(len(sdbname) > 19):
            print "Slave <%s>: Sdb name <%s> is too long. It has %u chars, allowed are 19" % (name, sdbname, len(sdbname))
            sys.exit(2)
        
        tmpSlave    = wbs(unitname, version, now, name, 0, '', pages, ifWidth, vendId, prodId, sdbname, clockList, genIntD, genMiscD, 'g_') 
        
        selector = ""
        #name, adr, pages, selector
        #registers
        registerList = slaveIf.getElementsByTagName('reg')
        for reg in registerList:
            if reg.hasAttribute('name'):            
                regname = reg.getAttribute('name')
            else:
                print "Register must have a name!"
                sys.exit(2)
            
            if reg.hasAttribute('comment'):      
                regdesc = reg.getAttribute('comment')
            else:        
                print "Register must have a comment!"
                sys.exit(2)
            
            regadr = None       
            if reg.hasAttribute('address'):            
                regadr = reg.getAttribute('address')            
                aux = str2int(regadr)
                if(aux == None):            
                    print "Slave <%s>: Register <%s>'s supplied address <0x%x> is invalid, defaulting to auto" % (name, regname, regadr)
                regadr = aux            
                print "Slave <%s>: Register <%s> using supplied address <0x%x>, enumerating from there" % (name, regname, regadr)
                
            regflags    = str()
            if reg.hasAttribute('read'):
                if reg.getAttribute('read') == 'yes':            
                    regflags += 'r'    
            if reg.hasAttribute('write'):        
                if reg.getAttribute('write') == 'yes':
                    regflags += 'w'
            if reg.hasAttribute('drive'):        
                if reg.getAttribute('drive') == 'yes':
                    regflags += 'd'        
            if reg.hasAttribute('paged'):
                if reg.getAttribute('paged') == 'yes':
                    regflags += 'm'
            if reg.hasAttribute('access'):
                if reg.getAttribute('access') == 'atomic':
                    regflags += 'a'
            if reg.hasAttribute('flags'):
                if reg.getAttribute('flags') == 'yes':            
                    regflags += 'f'
            if reg.hasAttribute('autostall'):
                if reg.getAttribute('autostall') == 'yes':            
                    regflags += 's'
            if reg.hasAttribute('pulse'):
                if reg.getAttribute('pulse') == 'yes':            
                    regflags += 'p'        
            if reg.hasAttribute('selector'):            
                if reg.getAttribute('selector') == 'yes':            
                    if(selector == ""):            
                        selector = regname
            regclk = clockList[0]                
            if reg.hasAttribute('clock'):
                regclk = reg.getAttribute('clock')
                print "Slave <%s>: Register <%s> is in clockdomain %s and will be synced" % (name, regname, regclk)
                
            if reg.hasAttribute('mask'):      
                regmsk    = reg.getAttribute('mask')
                genericMsk = False
                #check integer generic list
                
                genericMsk = (regmsk in genIntD)

                #check conversion function list
                if(not genericMsk):
                    aux = str2int(regmsk)
                    if(aux == None):
                        aux = 2^ int(ifWidth) -1
                        print "Slave <%s>: Register <%s>'s supplied mask <%s> is invalid, defaulting to %x" % (name, regname, regmsk, aux)
                    elif( (regmsk.find('0x') == 0) or (regmsk.find('0b') == 0) ):
                        #it's a mask. treat as such
                        regmsk = aux
                    else:
                        #it's decimal and therefore the bitwidth. make a bitmask                        
                        regmsk = 2**aux-1
                else:
                     #careful, using generics in register width probably causes more trouble than it's worth
                     print "Slave <%s>: Register <%s>'s using supplied generic width <%s>" % (name, regname, regmsk)
            else:        
                print "Slave <%s>: No mask for Register <%s> supplied, defaulting to 0x%x" % (name, regname, 2**ifWidth-1)
                regmsk = 2**ifWidth-1

            rstvec = None    
            if reg.hasAttribute('reset'):
                          
                    
                aux = reg.getAttribute('reset')

                if(aux in genIntD):
                    (_, val, _) = genIntD[aux]
                    print "Slave <%s>: Register <%s>'s Reset using supplied generic value <%s>" % (name, regname, val)
                    rstvec = aux
                #elif(aux in genMiscD):
                else:    
                    aux = str2int(aux)
                    if(aux != None):
                        rstvec = aux
                        print "Slave <%s>: Register <%s>'s Reset using supplied value <%s>" % (name, regname, aux)
                    
                    else:
                        print "Slave <%s>: Register <%s>'s Reset value <%s> is invalid, defaulting to zereos." % (name, regname, val)
                      
                      
            tmpSlave.addWbReg(regname, regdesc, regmsk, regflags, regclk, rstvec, regadr)
      
            #x.addSimpleReg('NEXT2',     0xfff,  'rm',   "WTF")
            if(isinstance(pages, int)):
                if((selector != '') and (pages > 0)):    
                    print "Slave <%s>: Interface has <%u> memory pages. Selector register is <%s>" % (name, pages, selector)    
                    tmpSlave.selector = selector    
                    tmpSlave.pages      = pages
            elif(selector != ''):
                    print "Slave <%s>: Interface has <%s> memory pages. Selector register is <%s>" % (name, pages, selector)                 
                    tmpSlave.selector = selector    
                    tmpSlave.pages      = pages    
       
        ifList.append(tmpSlave)
    print genIntD        
    return [author, version, email, ifList]


#TODO: A lot ...

        
#masterIfList = xmldoc.getElementsByTagName('masterinterface')
#for masterIf in masterIfList:
#    if masterIf.getAttribute('name'):
#        print "Generating WBMF %s" % masterIf.getAttribute('name')
#        entityPortList.append(VhdlStr.masterIf % (masterIf.getAttribute('name'), masterIf.getAttribute('name'))) 
    

        
def main():

    s = sysStr(sys.argv[0], myCreator, myVersion, myStart, myUpdate)             
             
    def usage():
        for line in s.helpText:        
            print line
    
    def manual():
        for line in s.detailedHelpText:        
            print line            
    
    def version():
        for line in s.versionText:        
            print line 
                    
    xmlIn = ""  
    log = False
    quiet = False
    
    if(len(sys.argv) > 1):
        xmlIn = sys.argv[1]
    else:
        usage()
        sys.exit(2)     
    
    if(len(sys.argv) == 2):
        sIdx=1
    else:
        sIdx=2
        
    try:
        opts, args = getopt.getopt(sys.argv[sIdx:], "hlqf", ["help", "log", "quiet", "force", "version"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)    
    
    needFile = True
    force    = False
    optFound = False
    for option, argument in opts:
        if option in ("-h", "-?", "--help"):
            optFound = True        
            needFile = False
            manual()
        elif option in ("--version"):
            optFound = True        
            needFile = False        
            version()
        elif option in ("-f", "--force"):
            optFound = True            
            force = True    
        elif option in ("-q", "--quiet"):
            optFound = True            
            quiet = True
        elif option in ("-l", "--log"):
            optFound = True        
            log = True
        else:
            print "unhandled option %s" % option
            sys.exit(2) 
    
    
    if(needFile):
        if(optFound and len(sys.argv) == 2):
            usage()
            sys.exit(0)
            
        if os.path.isfile(xmlIn):
            mypath, myfile = os.path.split(xmlIn)        
            if not mypath:
                mypath += './'
                
            now = datetime.datetime.now()
            print "f: %s p: %s" % (myfile, mypath)
            
            unitname = os.path.splitext(myfile)[0]        
            #path    = os.path.dirname(os.path.abspath(xmlIn)) + "/"
            
            print "input/output dir: %s" % mypath
            print "Trying to parse:  %s" % myfile
            print "Unit:             %s" % unitname
            print "\n%s" % ('*' * 80)
                        
            [author, version, email, slaves] = parseXMLNew(xmlIn, now, unitname)
            wo = writeout(unitname, myfile, mypath, author, email, version, now)
            
            print slaves            
            
            for slave in slaves:
                wo.writeMainVhd(slave)
                wo.writePkgVhd(slave)
                wo.writeStubVhd(slave, True)
                wo.writePythonDict(slave)
                #tmp = slave.getAddressListPython()
                #for line in tmp:
                #    print line
            #writeHdrC(fileHdrC)
            #writeStubVhd(fileStubVhd)
            #writeStubPkgVhd(fileStubPkgVhd)
            #writeTbVhd(fileTbVhd)
            print "\n%s" % ('*' * 80) 
            print "\nDone!"
        else:
            print "\nFile not found: %s" % xmlIn
    
    


if __name__ == "__main__":
    main()



