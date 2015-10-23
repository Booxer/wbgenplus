# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 16:58:20 2015

@author: mkreider
"""
import datetime


class wbsCStr(object):
   

    def __init__(self, pages, unitname, slaveIfName, sdbVendorID, sdbDeviceID):
        self.unitname     = unitname
        self.slaveIfName  = slaveIfName        
        self.pages        = pages


class gCStr(object):
    def __init__(self, filename, unitname, author, email, version, date):
        self.unitname   = unitname     
        self.author     = author
        self.email      = email
        self.version    = version
        self.date       = date
        self.header         = [] 
        self.hdrfileStart   = ["#ifndef _%s_H_\n"   % unitname.upper(),
                               "#define _%s_H_\n\n" % unitname.upper()]
        self.hdrfileEnd     =  "#endif\n"        


           


class registerVhdlStr(object):
    others             = "(others => '%s')"
    wrModes = {'_GET'  : 'owr',
               '_SET'     : 'set',
               '_CLR'     : 'clr',
               '_OWR'     : 'owr',
               '_RW'     : 'owr'} 
    
    #generate sync signal delcarations if neeeded
    def getSyncSignalDeclaration(self, direction):
        s = []
        if self.wbDomain != self.clockDomain:
            if direction == "out" or direction == "in":
                for line in self.syncSigsTemplate:
                    s.append(line % direction)
        return s
    
    #generate simple or synced (FIFO) port assignment
    def getPortAssignment(self, direction):
        s = []
        
        if self.wbDomain != self.clockDomain:
            matrixPageStr   = ""
            sigInWrapper    = "%s"
            sigOutWrapper   = "%s"
            if self.pages > 0:
                matrixPageStr   = "%s%s * " % self.genPagePrefix, self.pages
                sigInWrapper    = "mflat(%s)"
                sigOutWrapper   = "minfl(%s)"
            syncwidth = "%s%s%s" % (matrixPageStr, self.genWidthPrefix, self.width)
            
            if direction == "out":
                sigin   = sigInWrapper  % self.regname
                sigout  = sigOutWrapper % self.portnameout
                clkin   = wbsVhdlStrGeneral.clkportname % (self.wbDomain, self.wbDomain)
                clkout  = wbsVhdlStrGeneral.clkportname % (self.clockDomain, self.clockDomain)
            elif direction == "in":
                sigin   = sigInWrapper  % self.portnamein
                sigout  = sigOutWrapper % self.portsignamein
                clkin   = wbsVhdlStrGeneral.clkportname % (self.clockDomain, self.clockDomain)
                clkout  = wbsVhdlStrGeneral.clkportname % (self.wbDomain, self.wbDomain)        
            else:
                print "ERROR: Port direction <%s> of Register <%s> is unknown. Choose <in> or <out>" % (direction, self.name)
            
                        
            #construct sync assignments            
            for line in self.syncInstTemplate0_dir2:
                s.append(line % (direction, direction))
            s.append(self.syncInstTemplate1_dir % (direction))
            s.append(self.syncInstTemplate2)
            s.append(self.syncInstTemplate3_sw % syncwidth)
            s += self.syncInstTemplate4
            for line in self.syncInstTemplate5_dir:
                s.append(line % direction)
            s.append(self.syncInstTemplate6_ci % clkin)
            s.append(self.syncInstTemplate7_co % clkout)
            s.append(self.syncInstTemplate8_si % sigin)
            s.append(self.syncInstTemplate9_so % sigout)
                                       
            return s                           
        else:
            if direction == "out":
                s.append(self.portAssignTemplate % (self.portnameout, self.regname))
            elif direction == "in":
                s.append(self.portAssignTemplate % (self.portsignamein, self.portnamein))
            else:
                print "ERROR: Port direction <%s> of Register <%s> is unknown. Choose <in> or <out>" % (direction, self.name)    
        return s        
        
        
        
      
         
        
   
    def __init__(self, wbsStr, name, description, reset, genResetPrefix, width, genWidthPrefix, pages, genPagePrefix, clockDomain, wbDomain):
        self.int2slv    = "std_logic_vector(to_unsigned(%%s, %s))" % (width)
        self.hex2slv    = "std_logic_vector(to_unsigned(16#%%x#, %s))" % (width)    
        print "Resetvec: %s" % reset        
        if reset is None:
            self.resetvector = registerVhdlStr.others % 0
        else: 
           self.resetvector = self.int2slv % (str(genResetPrefix) + str(reset)) 
           if(str(reset).find('0x') > -1):
               self.resetvector = self.hex2slv % reset
          
               
                    
        self.pages          = pages
        self.genPagePrefix  = genPagePrefix
        self.width          = width
        self.genWidthPrefix = genWidthPrefix 
            
        self.clockDomain    = clockDomain
        self.wbDomain       = wbDomain
       
        self.name = name
        self.regname        = "r_" + name
        self.signame        = "s_" + name
        
        #don't bother mentioning the clk domain in the portname if it is not foreign        
        clkdomainSuffix = ""
        if clockDomain != wbDomain:
            clkdomainSuffix = "_" + clockDomain
            
        self.portnamein     = name + clkdomainSuffix + "_i"
        self.portsignamein  = "s_" + name + "_i"
        self.portnameout    = name + clkdomainSuffix + "_o"
        
        # a lot of templates
        self.matrix       = "signal %%s : t_matrix(%s%s-1 downto 0, %s%s-1 downto 0); -- %s\n" % (genPagePrefix, pages, genWidthPrefix, width, description)
        self.slv          = "signal %%s : std_logic_vector(%s%s-1 downto 0); -- %s\n" % (genWidthPrefix, width, description)
        self.sl           = "signal %%s : std_logic; -- %s\n" % (description)
                
        self.portmatrix   = "%%s : %%s t_matrix(%s%s-1 downto 0, %s%s-1 downto 0); -- %s\n" % (genPagePrefix, pages, genWidthPrefix, width, description) 
        self.portslv      = "%%s : %%s std_logic_vector(%s%s-1 downto 0); -- %s\n" % (genWidthPrefix, width, description)          
        self.portsl       = "%%s : %%s std_logic; -- %s\n" % (description)
        
        self.portAssignTemplate = "%s <= %s;\n"
        
        self.syncSigsTemplate  = ["signal s_%s_fifo_%%s_push  : std_logic; -- Sync signals\n" % (self.signame), # in/out
                              "signal s_%s_fifo_%%s_pop   : std_logic;\n"  % (self.signame), # in/out
                              "signal s_%s_fifo_%%s_full  : std_logic;\n"  % (self.signame), # in/out
                              "signal s_%s_fifo_%%s_empty : std_logic;\n"  % (self.signame)] # in/out
         
        #sync instance template. has to be chopped up like this to make fill in easier 
        self.syncInstTemplate0_dir2 = ["  %s_fifo_%%s_pop    <= not %s_fifo_%%s_empty;\n" % (self.signame, self.signame), # in/out
                                       "  %s_fifo_%%s_push   <= not %s_fifo_%%s_full;\n\n" % (self.signame, self.signame)]  # in/out                       
        self.syncInstTemplate1_dir  =  "%s_FIFO_%%s : generic_async_fifo\n" % (self.name) # in/out
        self.syncInstTemplate2      = "generic map(\n"
        self.syncInstTemplate3_sw   = "  g_data_width   => %s,\n"
        self.syncInstTemplate4      = ["  g_size         => %s,\n" % (8),
                                       "  g_show_ahead   => true,\n",
                                       "  g_with_rd_empty   => true,\n",
                                       "  g_with_wr_full    => true)\n",
                                       "port map(\n",
                                       "  rst_n_i  => %s,\n" % wbsVhdlStrGeneral.rstportname % (self.wbDomain)]
        self.syncInstTemplate5_dir  = ["  we_i     => %s_fifo_%%s_push,\n" % (self.signame), # in/out
                                       "  rd_i     => %s_fifo_%%s_pop,\n" % (self.signame), # in/out
                                       "  rd_empty_o  => s_%s_fifo_%%s_empty,\n" % (self.signame), # in/out
                                       "  wr_full_o   => s_%s_fifo_%%s_full,\n" % (self.signame)] # in/out
        self.syncInstTemplate6_ci   = "  clk_wr_i => clk_%s_i,\n" # clkin,                        
        self.syncInstTemplate7_co   = "  clk_rd_i => clk_%s_i,\n" # clkout
        self.syncInstTemplate8_si   = "  d_i      => %s,\n" #sigin
        self.syncInstTemplate9_so   = "  q_o      => %s);\n\n" #sigout
        
       
        # Create all Register Declarations, the reset command, FSM read & write command and pulse generation command  
             
        #if paged, make this a matrix  
        if self.pages > 0:
            self.declarationReg         = self.matrix % (self.regname)
            self.declarationStubIn      = wbsStr.matrixStub % (self.portnamein, genPagePrefix, pages, genWidthPrefix, width, description)
            self.declarationStubOut     = wbsStr.matrixStub % (self.portnameout, genPagePrefix, pages, genWidthPrefix, width, description)
            self.declarationPortSigIn   = self.matrix % (self.portsignamein)
            self.declarationPortIn      = self.portmatrix % (self.portnamein, "in ")
            self.declarationPortOut     = self.portmatrix % (self.portnameout, "out")
            self.reset                  = "%s <= mrst(%s, %s);\n" % (self.regname, self.regname, self.resetvector)
            self.wbRead                 = wbsStr.wbReadMatrix % (self.name, self.regname, "") # Slice
            self.wbWrite                = wbsStr.wbWriteMatrix % (self.name, self.regname, "") # Slice, Slice
            self.wbPulseZero            = "%s <= mrst(%s, %s);\n" % (self.regname, self.regname, (self.int2slv % 0))
        else:
            #default: Slv    
            self.declarationReg         = self.slv % (self.regname)
            self.declarationStubIn      = wbsStr.slvStub % (self.portnamein, genWidthPrefix, width, description)
            self.declarationStubOut     = wbsStr.slvStub % (self.portnameout, genWidthPrefix, width, description)
            self.declarationPortSigIn   = self.slv % (self.portsignamein)
            self.declarationPortIn      = self.portslv % (self.portnamein, "in ")
            self.declarationPortOut     = self.portslv % (self.portnameout, "out")
            self.reset                  = "%s <= %s;\n" % (self.regname, self.resetvector)
            self.wbRead                 = wbsStr.wbRead % (self.name, self.regname, "") # Slice
            self.wbWrite                = wbsStr.wbWrite % (self.name, self.regname, self.regname, "") # Slice, Slice
            self.wbPulseZero            = "%s <= %s;\n" % (self.regname,  (self.others % '0'))
        # derived from wbslave strings
       
        #address constant
        self.vhdlConstRegAdr    = wbsStr.vhdlConstRegAdr % (self.name, description) #address, operation, address, mask
        self.cConstRegAdr       = wbsStr.cConstRegAdr % (self.name, description)
        self.pythonConstRegAdr  = wbsStr.pythonConstRegAdr % (self.name, description)
        
        # Flags
        self.wbRd               = "%s_RD <= \"1\"; -- %s Read enable\n" % (self.regname, self.name)          
        self.wbWe               = "%s_WR <= \"1\"; -- %s Write enable\n" % (self.regname, self.name)
        #Flow control
        self.wbStall            = wbsStr.wbStall
        
        #port assignment, basic or with synchronisation
        self.portAssignOutList      = self.getPortAssignment("out")
        self.portAssignInList       = self.getPortAssignment("in")
        
        self.assignStubOut          = wbsStr.assignStub % (self.portnameout, self.portnameout)
        self.assignStubIn           = wbsStr.assignStub % (self.portnamein, self.portnamein)
        #syncronisation register/signal declaration
        self.declarationSyncInList  = self.getSyncSignalDeclaration("in")
        self.declarationSyncOutList = self.getSyncSignalDeclaration("out")
        
        #assigns the register input port to the register inside the FSM process. Write Arbitration with Wishbone write data, WB wins
        self.readUpdate             = self.portAssignTemplate % (self.regname, self.portsignamein)
        
        
    
class wbsVhdlStrRegister(object):
    

    def __init__(self, slaveIfName):
        self.slaveIfName    = slaveIfName        
        #this is total crap - why can't we have more than two % signs in formatting ?
        self.wbRead             = "when c_" + "%s%%s => " + slaveIfName + "_o.dat(%%s) <= %s%%s; -- %s\n" #regname, #op, #slice, registerName, #slice, description
        self.wbReadMatrix       = "when c_" + "%s%%s => " + slaveIfName + "_o.dat(%%s) <= rget(%%s, v_p)%%%s; -- %%s\n" #regname, #op, #slice, registerName, #slice, description
        self.wbWrite            = "when c_" + "%s%%s => %s%%s <= f_wb_wr(%s%%s, v_d, v_s, \"%%s\"); -- %s\n" #registerName, #op, #slice, registerName, #slice, #opmode, description
        self.wbWriteMatrix      = "when c_" + "%s%%s => %s%%s <= rset(%%s, v_page, f_wb_wr(rget(%%s, v_p)%%s, v_d, v_s, \"%%s\")); -- %%s\n" #registerName, registerName, (set/clr/owr), desc
        self.vhdlConstRegAdr    = "constant c_" + "%s%%s : natural := 16#%%s#; -- %%s 0x%%s, %s\n" #name, adrVal, adrVal, rw, msk, desc
        self.cConstRegAdr       = "#define " + slaveIfName.upper() + "_%s%%s 0x%%s //%%s 0x%%s %s\n" 
        self.pythonConstRegAdr  = "'%s%%s' : 0x%%s, # %%s 0x%%s, %s\n" #name, adrVal, adrVal, rw, msk, desc
        self.slvStub            = "signal s_" + slaveIfName + "_%s : std_logic_vector(%s%s-1 downto 0); -- %s\n"
        self.matrixStub         = "signal s_" + slaveIfName + "_%s : t_matrix(%s%s-1 downto 0, %s%s-1 downto 0); -- %s\n"
        self.assignStub         = "%s => s_" + slaveIfName + "_%s,\n"
        
        self.wbStall            = "r_%s_stall <= \"1\"; --    %s auto stall\n" % (slaveIfName, slaveIfName)
 
        
     
class wbsVhdlStrGeneral(object):
    wbWidth = {8   : '1',
               16  : '3',
               32  : '7', 
               64  : 'f'}  

    hex2slv = "std_logic_vector(to_unsigned(16#%x#, %s))"
    int2slv = "std_logic_vector(to_unsigned(%s, %s))"
    generic = "%s : %s := %s%%s --%s\n"
    clkport = "clk_%s_i : std_logic; -- Clock input for %s domain\n"
    clkportname = "clk_%s_i"
    rstport = "rst_%s_n_i : std_logic; -- Reset input (active low) for %s domain\n"
    rstportname = "rst_%s_n_i"
    assignStub         = "%s => %s,\n"

    def __init__(self, unitname, slaveIfName, dataWidth, vendId, devId, sdbname, clocks, version, now, selector):
        self.unitname       = unitname
        self.slaveIfName    = slaveIfName        
        self.dataWidth      = dataWidth
        self.clocks         = clocks

        #################################################################################        
        #Strings galore
        


        
        self.slaveIf    = ["\n",
                           "%s_i : in  t_wishbone_slave_in;\n" % slaveIfName,
                           "%s_o : out t_wishbone_slave_out\n\n" % slaveIfName]
                           
                           
 
                          
        self.slaveSigs = ["signal s_%s_i : t_wishbone_slave_in;\n" % slaveIfName,
                          "signal s_%s_o : t_wishbone_slave_out;\n" % slaveIfName]
        
        self.slaveInst = ["%s_i => %s_i,\n" % (slaveIfName, slaveIfName),
                          "%s_o => %s_o" % (slaveIfName, slaveIfName)]         
        
        self.wbs0       = ["%s : process(%s)\n" % (slaveIfName, (wbsVhdlStrGeneral.clkportname % clocks[0]) ),
                           "   variable v_d : t_wishbone_data;\n",
                           "   variable v_a  : natural;\n",
                           "   variable v_p  : natural;\n",
                           "   variable v_s  : t_wishbone_byte_select;\n",
                           "   variable v_w  : std_logic;\n",
                           "   variable v_e  : std_logic;\n",
                           "begin\n",
                           "   if rising_edge(%s) then\n" % (wbsVhdlStrGeneral.clkportname % clocks[0]),
                           "      if(%s = '0') then\n" % (wbsVhdlStrGeneral.rstportname % clocks[0])]
       
        self.wbs1_0     = ["else\n",
                           "   -- short names\n",
                           "   v_d := %s_i.dat;\n" % slaveIfName]
        self.wbs1_adr   =  "   v_a := to_integer(unsigned(%s_i.adr(%%u downto %%u)) %%s);\n" % slaveIfName
        self.wbs1_1     = ["   v_s := %s_i.sel;\n" % slaveIfName,
                           "   v_e := %s_i.cyc and %s_i.stb and (not r_%s_stall(0));\n" % (slaveIfName, slaveIfName, slaveIfName),
                           "   v_w := %s_i.we;\n\n" % slaveIfName] 
      
        self.wbs2       = ["if(v_e = '1') then\n",
                           "   %s_o.ack  <= '1';\n" % slaveIfName,
                           "   if(v_w = '1') then\n",
                           "      -- WISHBONE WRITE ACTIONS\n",
                           "      case v_a is\n"]
    
        self.wbs3       = ["   end case;\n",
                           "else\n",
                           "   -- WISHBONE READ ACTIONS\n",
                           "   case v_a is\n"]  

        self.wbs4       = ["               end case;\n",
                           "            end if; -- v_w\n",
                           "         end if; -- v_e\n",
                           "      end if; -- rst\n",
                           "   end if; -- clk edge\n",
                           "end process;\n\n"]
        
                           
        self.wbsPageSelect      = "v_p := to_integer(unsigned(r_%s));\n\n"  % selector #pageSelect Register
                          
                           
        self.wbsStall0   = "%s_o.stall <= r_%s_stall(0);\n" % (slaveIfName, slaveIfName)
        
        self.wbsStall1   = "r_%s_stall <= r_%s_stall and %%s; -- extend stall if requested by outer entity\n" % (slaveIfName, slaveIfName) 
         
     
        self.wbOthers           = ["when others => %s_o.ack <= '0'; %s_o.err <= '1';\n" % (slaveIfName, slaveIfName)]
                             
        self.wbs_reg_o          = "signal r_%s : t_%s_regs_o;\n" % (slaveIfName, slaveIfName)
        self.wbs_reg_i          = "signal s_%s : t_%s_regs_i;\n" % (slaveIfName, slaveIfName)
        
                               
        self.sdb0               = ['constant c_%s_%s_sdb : t_sdb_device := (\n' % (unitname, slaveIfName),
                                   'abi_class     => x"%s", -- %s\n' % ("0000", "undocumented device"),
                                   'abi_ver_major => x"%s",\n' % "01",
                                   'abi_ver_minor => x"%s",\n' % "00",
                                   'wbd_endian    => c_sdb_endian_%s,\n' % "big",
                                   'wbd_width     => x"%s", -- 8/16/32-bit port granularity\n' % self.wbWidth[dataWidth],
                                   'sdb_component => (\n']
        self.sdbAddrFirst        = 'addr_first    => x"%s",\n'
        self.sdbAddrLast         = 'addr_last     => x"%s",\n'
        self.sdb1                = ['product => (\n',
                                   'vendor_id     => x"%016x",\n' % vendId,
                                   'device_id     => x"%08x",\n' % devId,
                                   'version       => x"%s",\n' % '{message:{fill}{align}{width}}'.format(message=version.replace('.', ''), fill='0', align='>', width=8),
                                   'date          => x"%04u%02u%02u",\n' % (now.year, now.month, now.day),
                                   'name          => "%s")));\n' % sdbname.ljust(19)]
        self.sdbReference       = "constant c_%s_%s_sdb : t_sdb_device := work.%s_pkg.c_%s_%s_sdb;\n" % (unitname, slaveIfName, (unitname + '_auto'), unitname, slaveIfName)                            
    
                                 
                                  

  
    codeGen = set(['vhdl', 'C', 'C++'])    

    genTypes = {'u'        : 'unsigned',
            'uint'     : 'natural', 
            'int'      : 'integer', 
            'bool'     : 'boolean',
            'string'   : 'string',
            'sl'       : 'std_logic',
            'slv'      : 'std_logic_vector'}    

class gVhdlStr(object):
   

    def __init__(self, unitname, filename="unknown", author="unknown", email="unknown", version="0.0", date=""):
        self.unitname   = unitname
        self.filename   = filename        
        self.author     = author
        self.version    = version
        self.date       = date
        self.dateStr    = "%02u/%02u/%04u" % (date.day, date.month, date.year)
        
        self.header     = ["--! @file        %s\n" % filename,                 
                           "--  DesignUnit   %s\n" % unitname,                           
                           "--! @author      %s <%s>\n" % (author, email),
                           "--! @date        %s\n" % self.dateStr,
                           "--! @version     %s\n" % version,                     
                           "--! @copyright   %04u GSI Helmholtz Centre for Heavy Ion Research GmbH\n" % (date.year),
                           "--!\n"]

        self.headerLPGL =    ["--------------------------------------------------------------------------------\n" 
                              "--! This library is free software; you can redistribute it and/or\n",
                              "--! modify it under the terms of the GNU Lesser General Public\n",
                              "--! License as published by the Free Software Foundation; either\n",
                              "--! version 3 of the License, or (at your option) any later version.\n",
                              "--!\n",
                              "--! This library is distributed in the hope that it will be useful,\n",
                              "--! but WITHOUT ANY WARRANTY; without even the implied warranty of\n",
                              "--! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU\n",
                              "--! Lesser General Public License for more details.\n",
                              "--!\n",  
                              "--! You should have received a copy of the GNU Lesser General Public\n",
                              "--! License along with this library. If not, see <http://www.gnu.org/licenses/>.\n",
                              "--------------------------------------------------------------------------------\n\n"]                                

        self.headerDetails = []
       
        self.headerWarning =    ["-- ***********************************************************\n",
                                 "-- ** WARNING - THIS IS AUTO-GENERATED CODE! DO NOT MODIFY! **\n",
                                 "-- ***********************************************************\n",
                                 "--\n",
                                 "-- If you want to change the interface,\n"]
                            
        self.headerModify  =    "-- modify %s.xml and re-run 'python wbgenplus.py %s.xml' !\n\n"
                            
        self.libraries  = ["library ieee;\n",
                           "use ieee.std_logic_1164.all;\n",
                           "use ieee.numeric_std.all;\n",
                           "use work.wishbone_pkg.all;\n"]
        self.pkg        =  "use work.%s%%s_pkg.all;\n\n" % unitname                   
           
        self.packageStart       = "package %s_pkg is\n\n" % unitname
        self.componentStart     = "component %s is\n" % unitname
        self.componentMid       = "Port(\n"    
        self.componentEnd       = [");\n",
                                   "end component;\n\n"] 
        self.packageBodyStart   = "package body %s_pkg is\n" % unitname 
        self.packageEnd         = "end %s_pkg;\n" % unitname    
        
        self.entityStart        = "entity %s is\n" % unitname
        self.genStart           = "generic(\n"
        self.genEnd             = ");\n" 
         
        self.entityMid   = "Port(\n"
      
        self.entityEnd   = ");\nend %s;\n\n" % unitname
        
        self.archDecl    = "architecture rtl of %s is\n\n" % unitname
        self.archStart   = "\n\nbegin\n\n"
        self.archEnd     = "end rtl;\n"
        self.generic     = "g_%s : %s := %s%s -- %s\n" #name, type, default
        self.instGenPort    = "%s => %s%s\n" 
        self.instStart      = "INST_%s_auto : %s_auto\n" % (unitname, unitname)
        self.instGenStart   = "generic map (\n"
        self.instGenEnd     = ")\n"
        self.instPortStart  = "port map (\n"
        self.instPortEnd    = ");\n"
  
                   
                   
class sysIfStr(object):                   
    def __init__(self, program, creator, version="0.0", start="", update=""):               
                   
        self.helpText = ["\nUsage: python %s <path-to-wishbone-descriptor.xml>\n" % program, 
                        "-h    --help       Show detailed help. Lots of text, best redirect output to txt file",
                        "-q    --quiet      No console output",
                        "      --version    Shows version information",
                        "-l    --log        Log build output\n"
                        ]
    
             
        self.detailedHelpText = ['%s' % ("*" * 80),
                        '**                                                                            **',                    
                        '**                          wbgenplus Manual V%s                             **' % version,                    
                        ('**' + '%s%s%s' + '**') % ((" " * ((76-len(creator))/2)), creator, (" " * ((76-len(creator))/2 + (76-len(creator))%2))),
                        '%s\n' % ("*" * 80),
                        'wbgenplus autogenerates wishbone devices for FPGAs in VHDL from a single XML file.',
                        'In VHDL, it builds the core logic, a package for register records and SDB entries',
                        'and provides a stub for the outer entity.',
                        'It also creates a C Header file with the address definitions and builds',
                        'documentation via doxygen (not yet implemented).\n',
                        'In order to keep things modular, wbgenplus creates a seperate core for the',
                        'wishbone interface to be instantiated for your design.\n',
                        'Because of this, there are a few design rules which must be obeyed:\n',                    
                        'All registers that are write/read-write on the wishbone side are read-only on the entity side.',
                        'All registers that are read only on the wishbone side will be driven by the entity side.\n',
                        'If you want to use generics, they will be defined as constants in an extra package,',
                        'so they can be imported into the core package. Although VHDL 2008 supports generic packages,',
                        'none of major Synthesizers fully supports VHDL 2008. So there is currently no alternative',
                        'to the workaround. Yes, this sucks.\n\n',
                        'wbgenplus currently supports the following features:\n',
                        '- completely modular wishbone interface core',
                        '- forces comments for all registers in order to produce self-explaining code',                    
                        '- multiple slave interfaces in one core',                       
                        '- auto-generated SDB records',
                        '- automatic clock crossing',
                        '- address offsets can be generated manually, automatically or by a mix of both',                    
                        '- optional autogeneration of get/set/clear adresses for registers (atomic bit manipulation)',                        
                        '- auto-splitting of registers wider than the bus data width',                    
                        '- option for multiple memory pages of registers, dependent on a selector register,',
                        '  quantity can be controlled via generic',
                        '- optional complete flow control by the outer (user generated) entity',
                        '- optional feedback control via ACK/ERR by the outer (user generated) entity',
                        '- auto feedback for successful or failed operations(accessing unmapped addresses or',
                        '  writing to read only / reading from write only registers)',
                        '- optional pulsed registers, reset to all 0 automatically after 1 cycle',
                        '- optional autogeneration of write enable (WE) flag for a register (e.g. easy fifo connection)',
                        '\n'
                        'Planned features / currently under development:\n'
                        '- named bit fields in registers',
                        '- automatic RAM block generation',                    
                        '\n',
                        '+%s+' % ("-" * 78),
                         '|                            Wishbone-Descriptor-XMLs                          |',
                        '+%s+\n' % ("-" * 78),                    
                        
                        'This sections covers the details of the XML syntax.\n',
                        'Supported tags:\n',
                        '<wbdevice             Supreme Tag introducing a new wishbone device with one ore more interfaces.',
                        '   <codegen>          Selects which outputs files should be built',
                        '   <generics>         Gives a list of generics to the device. Generic names can be used in interface',
                        '   <clockdomain>      Introduces a clockdomain. If no such tag is present, wbgenplus will automatically',
                        '                      generate the "sys" domain for the wb interface',                                       
                        '   <slaveinterface    Introduces a new Wishbone Slave interface to the device',
                        '       <sdb>          Parameters for Self Describing Bus (SDB) record of this slave interface',
                        '       <reg>          Introduces a new register to this slave interface interface',        
                        '       <ram>          Introduces a new memory block to this slave interface interface (not yet implemented)',
                        '   >',
                        '>',
                        
                        'Detailed Tag parameter descriptions. All parameters marked with an * are mandatory,',
                        'the rest is optional and does need to appear in the XML.',
                        'There are two exceptions, see below:',
                        '   1: Either read or write or both must be "yes"',
                        '   2: Only valid in a group: If pages is greater 0, exactly 1 register must have set selector="yes"',
                        '      and 1 or more registers must have set paged="yes"\n\n',
                        'Tag parameters:\n',
                        '<CLOCKDOMAIN>:\n',
                        '  *name:       Name of the clock domain. The first such tag is always treated as the Wishbone domain\n',
                        '   Example:',                      
                        '   <clockdomain name="wb"></clockdomain>\n',
                        '<WBDEVICE>:\n',                  
                        '  *unitname:   Name of the design unit of the wishbone top file.',
                        '               The inner core will be named "<unitname>_auto"\n',
                        '  *author:     Name of the author of this xml and all derived files\n',
                        '   email:      The email address of the author\n',
                        '   version:    version number of this device\n',
                        '   Example:',                      
                        '   <wbdevice unitname="my_cool_device" author="M. Kreider" email="m.kreider@gsi.de" version="0.0.1">\n',
                        '<SLAVEINTERFACE>:\n',                   
                        '  *name:       Name of the slave interface port\n',
                        '   data:       Bitwidth of the data lines. Default is 32\n',
                        '   type:       Type of flow control. Accepts "pipelined" or "classic", default is "pipelined"\n',
                        ' 2*pages:      Number <n> of memory pages to instantiate, default is 0.',
                        '               Accepts a generic (via const package, see above)',
                        '               All registers marked paged="yes" will be built as an array with n elements.',
                        '               If <n> is greater 0, one register must be marked as the page selector by issueing selector="yes"\n',
                        '   Example:',                      
                        '   <slaveinterface name="control" data="32" type="pipelined" pages="8">\n',
                        '<SDB>:\n',
                        '  *vendorID:   Vendor Identification code, 64 bit hex value. Also accepts known vendors like "GSI" or "CERN"\n',
                        '  *productID:  Product Identification code, 32 bit hex value\n',
                        '  *version:    Device version number, 1 to 3 digits\n',
                        '   date:       Date to be shown on sdb record. Default is "auto" (Today)\n',
                        '  *name:       Name to be shown on sdb record. 19 Characters max.\n', 
                        '   Example:',  
                        '   <sdb vendorID="GSI" productID="0x01234567" version="1" date="auto" name="my_ctrl_thingy"></sdb>\n',
                  
                        '<REG>:\n',
                        '  *name:       Main name of the register. Actual address and record names might be extended by suffices\n',
                        '  *read:       indicates if this register is readable from Wishbone. Default is "no"\n',
                        '  *write:      indicates if this register is writeable from Wishbone. Default is "no"\n',
                        '  *comment:    A (hopefully) descriptive comment for this register\n',                        
                        '   access:     Access mode for this register, "simple" or "atomic", default is "simple"',
                        '               Simple mode allows direct overwriting of register content.',
                        '               Atomic mode provides seperate get, set, and clear addresses for this register,\n'
                        '               allowing atomic single bit manipulation\n',
                        '   mask:       Bitmask for this register (currently only functions as width), default is the',
                        '               data(bus width) parameter of the slave interface tag',
                        '               If "mask" is wider than "data", wbgenplus will automatically generate multiple addresses',
                        '               to allow word access of the register. Accepts either hex or binary values as',
                        '               masks (0x ... or 0b ...) or decimal values as the register bitwidth\n',
                        '   address:    Manually sets the offset for this register, default is auto addressing.',
                        '               All follwing Registers will be enumerated from this address onward\n',
                        '   reset:      Defines the reset value for this register. Accepts "ones", "zeroes", binary, hex or decimal value.',
                        '               Currently only works for registers that can be written to from WB. Default is "zeroes".\n',                      
                        '   weflag      Write enable flag, default is "no". If set to "yes", a additional flag register will be created,',
                        '               going HI for 1 clock cycle every time the parent register is written to.',
                        '               The flag register does not discriminate which page, word, or subword is accessed.\n',
                        '   autostall:  If set to "yes", raises the stall line for 1 cycle after each access. Default is "no"',
                        '               The outer entity can, only raise a stall request 2 cycles AFTER the bus operation.',
                        '               Autostall bridges this gap by keeping the bus stalled until the outer entity can do flow control\n',
                        '   pulse:      If set to "yes", the register will reset to all 0 after 1 cycle. Default is "no"\n', 
                        '   paged:      When set to "yes", this register will be instantiated as an array with the number of elements',
                        '               in the pages parameter of the slave interface tag\n',
                        '   selector:   Selects the active memory page of all paged registers. Value is auto range checked on access.\n',
                        '   clock:      Clock domain this register shall be synchronized to. Default is no sync (WB clock domain)',
                        '               Needs a corresponding <clockdomain> tag.\n',
                        '   Example:',                    
                        '   <reg name="ACT" read="yes" write="yes" access="atomic" mask="0xff" comment="Triggers on/off"></reg>\n',
                        '<RAM>:\n',
                        '  not yet implemented\n'
                        ]
    
        self.versionText = ["\nwbgenplus - A Wishbone Slave Generator\n",
                   "Version: %s" % version,
                   "Created %s by %s" % (start, creator),
                   "Last updated %s\n" % update                 
                   ]                   
                   