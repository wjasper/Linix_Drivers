#! /usr/bin/python3
#
# Copyright (c) 2018 Warren J. Jasper <wjasper@ncsu.edu>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import bluetooth 
from struct import *
from mccBluetooth import *
from datetime import datetime

BTH1208LS_PID = 6883

class BTH_1208LS:
  """
    Settings memory map
  |===========================================================================================|
  |    Address    |        Value                                                              |
  |===========================================================================================|
  | 0x000         | DOut Bluetooth connection mode.  This determines the DOut value           |
  |               | when the Bluetooth connection status changes (not applicable in USB mode) |
  |               |    0 = no change                                                          |
  |               |    1 = apply specified values                                             |
  |-------------------------------------------------------------------------------------------|
  | 0x001         | DOut value when Bluetooth connected                                       |
  |-------------------------------------------------------------------------------------------|
  | 0x002         | DOut value when Bluetooth disconnected                                    |
  |-------------------------------------------------------------------------------------------|
  | 0x003         | AOut channel 0 Bluetooth connection mode.  This determines the AOut value |
  |               | when the Bluetooth connection status changes (not applicable in USB mode) |
  |               |    0 = no change                                                          |
  |               |    1 = apply specified values                                             |
  |-------------------------------------------------------------------------------------------|
  | 0x004 - 0x005 | AOut channel 0 value when Bluetooth connected                             |
  |-------------------------------------------------------------------------------------------|
  | 0x006 - 0x007 | AOut channel 0 value when Bluetooth disconnected                          |
  |-------------------------------------------------------------------------------------------|
  | 0x008         | AOut channel 1 Bluetooth connection mode.  This determines the AOut value |
  |               | when the Bluetooth connection status changes (not applicable in USB mode) |
  |               |    0 = no change                                                          |
  |               |    1 = apply specified values                                             |
  |-------------------------------------------------------------------------------------------|
  | 0x009 - 0x00A | AOut channel 1 value when Bluetooth connected                             |
  |-------------------------------------------------------------------------------------------|
  | 0x00B - 0x00C | AOut channel 1 value when Bluetooth disconnected                          |
  |-------------------------------------------------------------------------------------------|
  | 0x00C         | Auto shutdown timer value in minutes (0 = no auto shutdown).  When this   |
  |               | is used the device will automatically power down when powered by          |
  |               | batteries and no Bluetooth connection is present for this amount of time. |
;  |-------------------------------------------------------------------------------------------|
  | 0x00E         | Allow charging when Bluetooth connected                                   |
  |               |   0 = do not allow                                                        |
  |               |   1 = allow                                                               |
  |-------------------------------------------------------------------------------------------|
  | 0x00F - 0x3FF | Unused                                                                    |
  |===========================================================================================|
  """


  # Commands and Report ID for BTH-1208LS
  # Digital I/O
  DIN_R                = (0x00) # Read the current state of the DIO pins
  DOUT_R               = (0x02) # Read DIO latch value
  DOUT_W               = (0x03) # Write DIO latch value
  # Analog Input Commands
  AIN                    = (0x10) # Read analog input channel
  AIN_SCAN_START         = (0x11) # Start analog input scan
  AIN_SCAN_SEND_DATA     = (0x12) # Read data from the analog input scan FIFO
  AIN_SCAN_STOP          = (0x13) # Stop analog input scan
  AIN_CONFIG_R           = (0x14) # Read analog input configuration
  AIN_CONFIG_W           = (0x15) # Write analog input configuration
  AIN_SCAN_CLEAR_FIFO    = (0x16) # Clear the analog input scan FIFO
  AIN_SCAN_RESEND_DATA   = (0x18) # Resend data from the analog input scan
  # Analog Output Commands
  AOUT_R                 = (0x20) # Read analog output channel
  AOUT_W                 = (0x21) # Analog output channel
  #  Counter Commands
  COUNTER_R              = (0x30) # Read event counter
  COUNTER_W              = (0x31) # Reset event counter
  # Memory Commands
  CAL_MEMORY_R           = (0x40) # Read calibration memory
  USER_MEMORY_R          = (0x42) # Read user memory
  USER_MEMORY_W          = (0x43) # Write user memory
  SETTINGS_MEMORY_R      = (0x44) # Read settings memory
  SETTINGS_MEMORY_W      = (0x45) # Write settings memory
  # Miscellaneous Commands
  BLINK_LED              = (0x50) # Blink the LED
  RESET                  = (0x51) # Reset the device
  STATUS                 = (0x52) # Read device status
  SERIAL                 = (0x54) # Read serial number
  PING                   = (0x55) # Check device communications
  FIRMWARE_VERSION       = (0x56) # Read the firmware version
  RADIO_FIRMWARE_VERSION = (0x5A) # Read the radio firmware version
  BATTERY_VOLTAGE        = (0x58) # Read battery voltage

  NGAINS                 =  8     # max number of input gain levels (differential mode only)
  NCHAN_DE               =  4     # max number of A/D differential channels
  NCHAN_SE               =  8     # max number of A/D single-ended channels
  NCHAN_AOUT             =  2     # max number of D/A 12 bit 0-2.5V output channels

  # Aanalog Input
  SINGLE_ENDED    = 0
  DIFFERENTIAL    = 1

  # Analog Input Scan Options
  IMMEDIATE_TRANSFER_MODE = (0x1)
  BLOCK_TRANSFER_MODE     = (0x0)
  DIFFERENTIAL_MODE       = (0x2)
  SINGLE_ENDED_MODE       = (0x0)
  NO_TRIGGER              = (0x0)
  TRIG_EDGE_RISING        = (0x1 << 2)
  TRIG_EDGE_FALLING       = (0x2 << 2)
  TRIG_LEVEL_HIGH         = (0x3 << 2)
  TRIG_LEVEL_LOW          = (0x4 << 2)
  RETRIGGER_MODE          = (0x1 << 5)
  STALL_ON_OVERRUN        = (0x0)
  INHIBIT_STALL           = (0x1 << 7)

  # Ranges
  BP_20V   = 0x0      # +/- 20 V
  BP_10V   = 0x1      # +/- 10V
  BP_5V    = 0x2      # +/- 5V
  BP_4V    = 0x3      # +/- 4V
  BP_2_5V  = 0x4      # +/- 2.5V
  BP_2V    = 0x5      # +/- 2V
  BP_1_25V = 0x6      # +/- 1.25V
  BP_1V    = 0x7      # +/- 1V
  UP_2_5V  = 0x8      # 0-2.5V

  # Status bit values
  AIN_SCAN_RUNNING   = (0x1 << 1)
  AIN_SCAN_OVERRUN   = (0x1 << 2)
  NO_BATTERY         = (0x0)
  FAST_CHARGE        = (0x1 << 8)
  MAINTENANCE_CHARGE = (0x2 << 8)
  FAULT_CHARGING     = (0x3 << 8)
  DISABLE_CHARGING   = (0x4 << 8)

  voltage = 0
  status = 0

  def __init__(self, device):
    self.device = device        # inherit values from mccBluetoothDevice

    # Build a lookup table of calibration coefficients to translate values into voltages:
    # The calibration coefficients are stored in the onboard FLASH memory on the device in
    # IEEE-754 4-byte floating point values.
    #
    #   calibrated code = code*slope + intercept
    #
    #  table_AInDE[NCHAN_DE][NGAIN]
    self.table_AInDE  = [[table(), table(), table(), table(), table(), table(), table(), table()],\
                         [table(), table(), table(), table(), table(), table(), table(), table()],\
                         [table(), table(), table(), table(), table(), table(), table(), table()],\
                         [table(), table(), table(), table(), table(), table(), table(), table()]]

    #  table_AInSE = [NCHAN_SE]                         
    self.table_AInSE = [table(), table(), table(), table(), table(), table(), table(), table()]

    self.BuildGainTable_DE()
    self.BuildGainTable_SE()

  def BuildGainTable_DE(self):
    """
    Builds a lookup table of differential mode calibration
    coefficents to translate values into voltages: The calibration
    coefficients are stored in onboard FLASH memory on the device in
    IEEE-754 4-byte floating point values.

       calibrated code = code * slope + intercept
    """
    address = 0x0
    for gain in range(self.NGAINS):
      for chan in range(self.NCHAN_DE):
        self.table_AInDE[chan][gain].slope, = unpack('f', self.CalMemoryR(address, 4))
        address += 4
        self.table_AInDE[chan][gain].intercept, = unpack('f', self.CalMemoryR(address, 4))
        address += 4

  def BuildGainTable_SE(self):
    """
    Builds a lookup table of differential mode calibration
    coefficents to translate values into voltages: The calibration
    coefficients are stored in onboard FLASH memory on the device in
    IEEE-754 4-byte floating point values.

       calibrated code = code * slope + intercept
    """

    address = 0x100
    for chan in range(self.NCHAN_SE):
      self.table_AInSE[chan].slope, = unpack('f', self.CalMemoryR(address, 4))
      address += 4
      self.table_AInSE[chan].intercept, = unpack('f', self.CalMemoryR(address, 4))
      address += 4

  def CalDate(self):
    """
    get the manufacturers calibration data (timestamp) from the
    Calibration memory
    """

    # get the year (since 2000)
    address = 0x200
    data ,= unpack('B', self.CalMemoryR(address, 1))
    year  = 2000+data

    # get the month
    address = 0x201
    month ,= unpack('B', self.CalMemoryR(address, 1))

    # get the day
    address = 0x202
    day ,= unpack('B', self.CalMemoryR(address, 1))

    # get the hour
    address = 0x203
    hour ,= unpack('B', self.CalMemoryR(address, 1))
    
    # get the minute
    address = 0x204
    minute ,= unpack('B', self.CalMemoryR(address, 1))

    # get the second
    address = 0x205
    second ,= unpack('B', self.CalMemoryR(address, 1))

    mdate = datetime(year, month, day, hour, minute, second)
    return mdate

  def volts(self, value, gain):
    volt = 0.0
    if   (gain == self.BP_20V):
      volt = (value - 0x800)* 20.0/2048.
    elif (gain == self.BP_10V):
      volt = (value - 0x800)* 10.0/2048.
    if   (gain == self.BP_5V):
      volt = (value - 0x800)* 5.0/2048.
    elif (gain == self.BP_4V):
      volt = (value - 0x800)* 4.0/2048.
    if   (gain == self.BP_2_5V):
      volt = (value - 0x800)* 2.5/2048.
    elif (gain == self.BP_2V):
      volt = (value - 0x800)* 2.0/2048.
    if   (gain == self.BP_1_25V):
      volt = (value - 0x800)* 1.25/2048.
    elif (gain == self.BP_1V):
      volt = (value - 0x800)* 1.0/2048.
    elif (gain == self.UP_2_5V):
      volt = value*2.5/4096.             # analog output
    else:
      print("Unknown range.")

    return volt

  #############################################
  #        Digital I/O Commands               #
  #############################################

  def DIn(self):
    """
    This command reads the current state of the DIO pins.  A 0 in a
    bit position indicates the correspoing pin is reading a low
    state, and a 1 indicates a high state.
    """
    
    dataCount = 0
    replyCount = 1
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.DIN_R
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('DIn: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        data = r_buffer[MSG_INDEX_DATA]
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in DIn BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
      return -1

    return data

  def DOutR(self, value):
    """
    This command reads the DIO output latch value. The factory power
    on default is all 1 (pins are floating.) Writing a 0 to a bit
    drives it low, writing a 1 allows it to float.
    """

    dataCount = 0
    replyCount = 1
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.DOUT_R
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('DOutR: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        data = r_buffer[MSG_INDEX_DATA]

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in DOutR BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

      
  def DOut(self, value):
    """
    This command reads the DIO output latch value. The factory power
    on default is all 1 (pins are floating.) Writing a 0 to a bit
    drives it low, writing a 1 allows it to float.
    """

    dataCount = 1
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.DOUT_W
    s_buffer[MSG_DATA]                 = value
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('DOut: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in DOut BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
    
  #############################################
  #        Analog Input Commands              #
  #############################################

  #############################################
  #        Analog Output Commands             #
  #############################################

  def AOutR(self):
    """
     This command reads the value of the analog output channels

     value[0]   the current value for analog output channel 0
     value[1]   the current value for analog output channel 1
    """

    dataCount = 0
    replyCount = 4
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.AOUT_R
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('AOutR: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        data = unpack_from('H'*2, r_buffer, MSG_INDEX_DATA)
        value[0] = round(data[0]*self.table_AOut[0].slope + self.table_AOut[0].intercept)
        value[1] = round(data[1]*self.table_AOut[1].slope + self.table_AOut[1].intercept)

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in AOutR BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

  def AOut(self, channel, value):
    """
    This command writes the value of the analog output channels

      channel: the channel to write (0-1)
      value:   the value to write (0-4095)
    """

    dataCount = 3
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.AOUT_W
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_DATA]           = channel
    s_buffer[MSG_INDEX_DATA+1]         = value & 0xff          # low byte
    s_buffer[MSG_INDEX_DATA+2]         = (value>>8) & 0xff     # high byte
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('AOut: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in AOut BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))


  #############################################
  #           Counter Commands                #
  #############################################

  def Counter(self):
    """
    The command reads the event counter.
    """
    dataCount = 0
    replyCount = 4
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.COUNTER_R
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('Counter: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        value ,= unpack_from('I', r_buffer, MSG_INDEX_DATA)

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in Counter BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

    return value

  def ResetCounter(self):
    """
    This command resets the event counter.  On a write, the
    counter will be reset to 0.
    """
    
    dataCount = 0
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.COUNTER_W
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID
    self.device.frameID = (self.device.frameID + 1) % 256              # increment frame ID with every send
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] = 0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('ResetCounter: timeout error.')
      return
    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
           result = True
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in RestCounter_R E-1608.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
    

  #############################################
  #        Memory Commands                    #
  #############################################

  def CalMemoryR(self, address, count):
    """
    This command reads the nonvolatile calibration memory.  The cal
    memory is 768 bytes (address 0 - 0x2FF)
    """
 
    if (count > 255):
      print("CalMemoryR: count must be less than 256.")
      return False

    if (address > 0x2ff):
      print("CalMemoryR: address must be between 0x0-0x2FF.")
      return False

    dataCount = 3
    replyCount = count
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.CAL_MEMORY_R
    s_buffer[MSG_INDEX_DATA]           = address & 0xff        # low byte
    s_buffer[MSG_INDEX_DATA+1]         = (address >> 8) & 0xff # high byte    
    s_buffer[MSG_INDEX_DATA+2]         = count
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('CalMemoryR: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        data = r_buffer[MSG_INDEX_DATA:MSG_INDEX_DATA+replyCount]
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in CalMemoryR BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
      return -1

    return data


  def UserMemoryR(self, address, count):
    """
    This command reads the nonvolatile user memory.  The user
    memory is 256 bytes (address 0 - 0xFF)
    """

    if (count > 255):
      print("UserMemoryR: count must be less than 256.")
      return False

    if (address > 0xff):
      print("UserMemoryR: address must be between 0x0-0xFF.")
      return False

    dataCount = 3
    replyCount = count
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.USER_MEMORY_R
    s_buffer[MSG_INDEX_DATA]           = address & 0xff        # low byte
    s_buffer[MSG_INDEX_DATA+1]         = (address >> 8) & 0xff # high byte    
    s_buffer[MSG_INDEX_DATA+2]         = count
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('UserMemoryR: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        data = r_buffer[MSG_INDEX_DATA:MSG_INDEX_DATA+replyCount]
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in UserMemoryR BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
      return -1

    return data

  def UserMemoryW(self, address, count, data):
    """
    This command writes the nonvolatile user memory.  The user memory
    is 256 bytes (address 0 - 0xFF).  The amount of data to be
    written is inferred from the frame count - 2;
    """

    if (count > 255):
      print("UserMemoryW: count must be less than 256.")
      return False

    if (address > 0xff):
      print("UserMemoryW: address must be between 0x0-0xFF.")
      return False

    dataCount = count + 2
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.USER_MEMORY_W
    s_buffer[MSG_INDEX_DATA]           = address & 0xff       # low byte
    s_buffer[MSG_INDEX_DATA+1]         = (address >> 8)& 0xff # high byte
    for i in range(count):
      s_buffer[MSG_INDEX_DATA+2+i] = data[i]
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('UserMemoryW: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in UserMemoryW BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
    
  def SettingsMemoryR(self, address, count):
    """
    This command reads the nonvolatile settings memory.  The settings
    memory is 1024 bytes (address 0 - 0x3FF)

    """

    if (count > 255):
      print("SettingsMemoryR: count must be less than 256.")
      return False

    if (address > 0x3ff):
      print("SettingsMemoryR: address must be between 0x0-0x3FF.")
      return False

    dataCount = 3
    replyCount = count
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.SETTINGS_MEMORY_R
    s_buffer[MSG_INDEX_DATA]           = address & 0xff        # low byte
    s_buffer[MSG_INDEX_DATA+1]         = (address >> 8) & 0xff # high byte    
    s_buffer[MSG_INDEX_DATA+2]         = count
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('SettingsMemoryR: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
        data = r_buffer[MSG_INDEX_DATA:MSG_INDEX_DATA+replyCount]
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in SettingsMemoryR BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
      return -1

    return data

  def SettingsMemoryW(self, address, count, data):
    """
    This command writes the nonvolatile user memory.  The settings memory
    is 1024 bytes (address 0 - 0x3FF).  The amount of data to be
    written is inferred from the frame count - 2.  the
    settings will be implemented immediately.
    """

    if (count > 255):
      print("SettingsMemoryW: count must be less than 256.")
      return False

    if (address > 0x3ff):
      print("SettingsMemoryW: address must be between 0x0-0x3FF.")
      return False

    dataCount = count + 2
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.SETTINGS_MEMORY_W
    s_buffer[MSG_INDEX_DATA]           = address & 0xff       # low byte
    s_buffer[MSG_INDEX_DATA+1]         = (address >> 8)& 0xff # high byte
    for i in range(count):
      s_buffer[MSG_INDEX_DATA+2+i] = data[i]
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('SettingsMemoryW: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True
    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in SettingsMemoryW BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
    
                         
  #############################################
  #        Miscellaneous Commands             #
  #############################################

  def BlinkLED(self, count=1):
    """
    This comman will blink the device power LED "count" times.
    """

    dataCount = 1
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.BLINK_LED
    s_buffer[MSG_INDEX_DATA]           = count
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   # increment frame ID with every send
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('Blink: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in Blink BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

  def GetSerialNumber(self):
    """
    This commands reads the device serial number.  The serial number
    consists of 8 bytes, typically ASCII numeric or hexadecimal digits
    (i.e. "00000001").
    """
    
    dataCount = 0
    replyCount = 8
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.SERIAL
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('GetSerialNumber: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
      else:
        serial = unpack_from('8s',r_buffer,offset=MSG_INDEX_DATA)
        serial = serial[0].decode()
        return  serial
    except ResultError:
      print('Error in GetSerialNumber BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

  def Reset(self):
    """
    This command resets the device
    """
    dataCount = 0
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.RESET
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('Reset: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in Reset BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
      
  def Status(self):
    """
    This command reads the device status.

      status: bit 0:     Reserved
              bit 1:     1 = AIn scan running
              bit 2:     1 = AIn scan overrun
              bits 3-7:  Reserved
              bits 8-10: Charger status
                           0 = no battery
                           1 = fast charge
                           2 = maintenance charge
                           3 = fault (not charging)
	                   4 = disabled, operating on battery power
              bits 11-15:   Reserved
    """

    dataCount = 0
    replyCount = 2
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.STATUS
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('Status: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
      else:
        status = unpack_from('H',r_buffer,offset=MSG_INDEX_DATA)
        self.status = status[0]
        return  (status[0])
    except ResultError:
      print('Error in Status BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

  def Ping(self):
    """
    This command checks communications with the device. Note that
    repetetive use of this command is not recommended for maximum
    battery life.
    """

    dataCount = 0
    replyCount = 0
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.PING
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('Ping: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
    except ResultError:
      print('Error in Ping BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
    return result

  def FirmwareVersion(self):
    """
    This command reads the firmware version.  The version consistes of
    16 bits in hexadecimal BCD notation, i.e. version 2.15 would be
    0x0215.
    """

    dataCount = 0
    replyCount = 2
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.FIRMWARE_VERSION
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('FrimwareVersion: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
      else:
        version = unpack_from('H',r_buffer,offset=MSG_INDEX_DATA)
        return version[0]
    except ResultError:
      print('Error in FirmwareVersion BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

  def RadioFirmwareVersion(self):
    """
    This command reads the radio firmware version.  The version consistes of
    16 bits in hexadecimal BCD notation, i.e. version 6.15 would be
    0x0615.
    """
    
    dataCount = 0
    replyCount = 2
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.RADIO_FIRMWARE_VERSION
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('RadioFrimwareVersion: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
      else:
        version = unpack_from('H',r_buffer,offset=MSG_INDEX_DATA)
        return version[0]
    except ResultError:
      print('Error in RadioFirmwareVersion BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))

  def BatteryVoltage(self):
    """
    This command reads the battery voltage. The value is returned in millivolts.
    """

    dataCount = 0
    replyCount = 2
    result = False
    s_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+dataCount)  # send buffer
    r_buffer = bytearray(MSG_HEADER_SIZE+MSG_CHECKSUM_SIZE+replyCount) # reply buffer

    s_buffer[MSG_INDEX_COMMAND]        = self.BATTERY_VOLTAGE
    s_buffer[MSG_INDEX_START]          = MSG_START
    s_buffer[MSG_INDEX_FRAME]          = self.device.frameID   
    self.device.frameID = (self.device.frameID + 1) % 256      # increment frame ID with every send    
    s_buffer[MSG_INDEX_STATUS]         = 0
    s_buffer[MSG_INDEX_COUNT]          =  (dataCount & 0xff)
    s_buffer[MSG_INDEX_DATA+dataCount] =  0xff - self.device.calcChecksum(s_buffer, MSG_INDEX_DATA+dataCount)

    self.device.sendMessage(s_buffer)

    try:
      r_buffer = self.device.receiveMessage()
    except socket.timeout:
      raise TimeoutError('BatteryVoltage: timeout error.')
      return

    if len(r_buffer) == MSG_HEADER_SIZE + MSG_CHECKSUM_SIZE + replyCount:
      if r_buffer[MSG_INDEX_START] == s_buffer[0]                               and \
         r_buffer[MSG_INDEX_COMMAND] == s_buffer[MSG_INDEX_COMMAND] | MSG_REPLY and \
         r_buffer[MSG_INDEX_FRAME] == s_buffer[2]                               and \
         r_buffer[MSG_INDEX_STATUS] == MSG_SUCCESS                              and \
         r_buffer[MSG_INDEX_COUNT] == replyCount & 0xff                         and \
         r_buffer[MSG_INDEX_DATA+replyCount] + self.device.calcChecksum(r_buffer,(MSG_HEADER_SIZE+replyCount)) == 0xff :
        result = True

    try:
      if (result == False):
        raise ResultError
      else:
        voltage = unpack_from('H',r_buffer,offset=MSG_INDEX_DATA)
        self.voltage = voltage[0]
        return voltage[0]
    except ResultError:
      print('Error in BatteryVoltage BTH-1208LS.  Status =', hex(r_buffer[MSG_INDEX_STATUS]))
 
