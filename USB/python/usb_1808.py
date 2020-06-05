#! /usr/bin/python3
#
# Copyright (c) 2020 Warren J. Jasper <wjasper@ncsu.edu>
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

import libusb1
import usb1
import time
import sys
from struct import *
from datetime import datetime
from mccUSB import *

class usb1808(mccUSB):

  # USB PIDs for family of devices
  USB_1808_PID  = 0x013d
  USB_1808X_PID = 0x013e

  # Counter Timer
  COUNTER0 = 0x0  # Counter 0
  COUNTER1 = 0x1  # Counter 1
  ENCODER0 = 0x2  # Counter 2
  ENCODER1 = 0x3  # Counter 3
  TIMER0   = 0x0  # Timer 0
  TIMER1   = 0x1  # Timer 1

  # Timer Control
  TIMER_ENABLE      = 0x1   # Enable timer
  TIMER_RUNNING     = 0x2   # Timer running
  TIMER_INVERTED    = 0x4   # Timer inverted output
  TIMER_OTRIG_BEGIN = 0x10  # Timer will begin output when the OTRIG pin has triggered
  TIMER_OTRIG       = 0x40  # Timer will continue to output on every OTRIG it receives

  # Counter Modes
  COUNTER_TOTALIZE   = 0x0   # Total Count (counts total number of pulses)
  COUNTER_PERIOD     = 0x1   # Counter returns Period [100us]
  COUNTER_PULSEWIDTH = 0x2   # Counter returns pulse width [100us]
  COUNTER_TIMING     = 0x3
  PERIOD_MODE_1X     = 0x0   # Period Mode x1
  PERIOD_MODE_10X    = 0x4   #  Period Mode x10
  PERIOD_MODE_100X   = 0x8   # Period Mode x100
  PERIOD_MODE_1000X  = 0xc   # Period Mode x1000
  TICK_SIZE_20NS     = 0x0   #  Tick size 20ns (fundamental unit of time in nano seconds)
  TICK_SIZE_200NS    = 0x10  # 200 ns
  TICK_SIZE_2000NS   = 0x20  # 2000 ns
  TICK_SIZE_20000NS  = 0x30  # 20000 ns

  # Counter Options
  CLEAR_ON_READ     = 0x1   # Clear on Read
  NO_RECYCLE        = 0x2   # No recycle mode
  COUNT_DOWN        = 0x4   # Count Down
  RANGE_LIMIT       = 0x8   # Range Limit (use max and min limits)
  FALLING_EDGE      = 0x10  # Count on the falling edge

  # Aanalog Input
  DIFFERENTIAL      = 0
  SINGLE_ENDED      = 1
  GROUNDED          = 3
  PACKET_SIZE       = 512    # max bulk transfer size in bytes
  CONTINUOUS        = 1      # continuous input mode
  EXTERNAL_TRIGGER  = 0x1    # 1 = use external trigger
  PATTERN_DETECTION = 0x2    # 1 = use Pattern Detection trigger
  RETRIGGER_MODE    = 0x4    # 1 = retrigger mode, 0 = normal trigger
  COUNTER_VALUE     = 0x8    # 1 = Maintain counter value on scan start,  0 = Clear counter value on scan start
  SINGLE_IO         = 0x10   # 1 = use SINGLE_IO data transfer,  0 = use BLOCK_IO transfer

  # Ananlog Output Scan Options
  AO_CHAN0       = 0x1   # Include Channel 0 in output scan
  AO_CHAN1       = 0x2   # Include Channel 1 in output scan
  AO_TRIG        = 0x10  # Use Trigger
  AO_RETRIG_MODE = 0x20  # Retrigger Mode
  
  # Ranges 
  BP_10V = 0x0      # +/- 10V
  BP_5V  = 0x1      # +/- 5V
  UP_10V = 0x2      # 0 - 10V
  UP_5V  = 0x3      # 0 - 5V
  
  # Status bit values
  AIN_SCAN_RUNNING   = (0x1 << 1)  # input pacer running
  AIN_SCAN_OVERRUN   = (0x1 << 2)  # input scan overrun
  AOUT_SCAN_RUNNING  = (0x1 << 3)  # output scan running
  AOUT_SCAN_UNDERRUN = (0x1 << 4)  # output scan overrun
  AIN_SCAN_DONE      = (0x1 << 5)  # input scan done
  AOUT_SCAN_DONE     = (0x1 << 6)  # output scan done
  FPGA_CONFIGURED    = (0x1 << 8)  # 1 = FPGA configured
  FPGA_CONFIG_MODE   = (0x1 << 9)  # 1 = FPGA config mode

  NCHAN               =   8  # max number of A/D channels in the device
  NGAIN               =   4  # max number of gain levels
  NCHAN_AO            =   2  # number of analog output channels
  MAX_PACKET_SIZE_HS  = 512  # max packet size for HS device
  MAX_PACKET_SIZE_FS  =  64  # max packet size for FS device

  # Commands and Codes for USB1608G
  # Digital I/O Commands
  DTRISTATE            = 0x00  # Read/write digital port tristate register
  DPORT                = 0x01  # Read digital port pins / write output latch register
  DLATCH               = 0x02  # Read/write digital port output latch register

  # Analog Input Commands
  AIN                  = 0x10  # Read analog input channel
  AIN_ADC_SETUP        = 0x11  # Read/write setup registers on the ADC
  AIN_SCAN_START       = 0x12  # Start analog input scan
  AIN_SCAN_STOP        = 0x13  # Stop analog input scan
  AIN_SCAN_CONFIG      = 0x14  # Read/Write analog input configuration
  AIN_SCAN_CLEAR_FIFO  = 0x15  # Clear the analog input scan FIFO
  AIN_BULK_FLUSH       = 0x16  # Flush the input Bulk pipe

  # Analog Output Commands
  AOUT                 = 0x18  # Read/write analog output channel
  AOUT_SCAN_START      = 0x1A  # Start analog output scan
  AOUT_SCAN_STOP       = 0x1B  # Stop analog output scan
  AOUT_SCAN_CLEAR_FIFO = 0x1C  # Clear the analog output scan FIFO

  # Counter Commands
  COUNTER              = 0x20  # Read/reset counter
  COUNTER_OPTIONS      = 0x21  # Read or set the counter's options
  COUNTER_LIMITS       = 0x22  # Read or set the counter's range limits
  COUNTER_MODE         = 0x23  # Read or set the counter's mode
  COUNTER_PARAMETERS   = 0x24  # Read or set the counter's mode and options

  # Timer Commandws
  TIMER_CONTROL        = 0x28  # Read/Write timer control register
  TIMER_PARAMETERS     = 0x2D  # Read/Write all timer parameters at once

  # Memory Commands
  MEMORY               = 0x30  # Read/Write EEPROM
  MEM_ADDRESS          = 0x31  # EEPROM read/write address value
  MEM_WRITE_ENABLE     = 0x32  # Enable writes to firmware area

  # Miscellaneous Commands
  STATUS               = 0x40  # Read device status
  BLINK_LED            = 0x41  # Causes the LED to blink
  RESET                = 0x42  # Reset the device
  TRIGGER_CONFIG       = 0x43  # External trigger configuration
  PATTERN_DETECT_CONF  = 0x44  # Pattern detection triger configuration
  SERIAL               = 0x48  # Read/Write USB Serial Number

  # FPGA Configuration Commands
  FPGA_CONFIG          = 0x50 # Start FPGA configuration
  FPGA_DATA            = 0x51 # Write FPGA configuration data
  FPGA_VERSION         = 0x52 # Read FPGA version

  HS_DELAY = 2000

  def __init__(self):
    self.status = 0                       # status of the device
    self.samplesToRead = -1               # number of bytes left to read from a scan
    self.scanList = bytearray(self.NCHAN) # depth of scan queue is 15
    self.lastElement = 0                  # last element of the scan list
    self.count = 0
    self.retrig_count = 0
    self.options = 0
    self.frequency = 0.0                  # frequency of scan (0 for external clock)
    self.packet_size = 512                # number of samples to return from FIFO
    self.mode = 0                         # mode bits:
                                          # bit 0:   0 = counting mode,  1 = CONTINUOUS_READOUT
                                          # bit 1:   1 = SINGLEIO
                                          # bit 2:   1 = use packet size in self.packet_size
    # Configure the FPGA
    if not (self.Status() & self.FPGA_CONFIGURED) :
      # load the FPGA data into memory
      from usb_1808_rbf import FPGA_data
      print("Configuring FPGA.  This may take a while ...")
      self.FPGAConfig()
      if self.Status() & self.FPGA_CONFIG_MODE:
        for i in range(0, len(FPGA_data) - len(FPGA_data)%64, 64) :
          self.FPGAData(FPGA_data[i:i+64])
        i += 64
        if len(FPGA_data) % 64 :
          self.FPGAData(FPGA_data[i:i+len(FPGA_V2_data)%64])
        if not self.Status() & self.FPGA_CONFIGURED:
          print("Error: FPGA for the USB-1808 is not configured.  status = ", hex(self.Status()))
          return
      else:
        print("Error: could not put USB-1808 into FPGA Config Mode.  status = ", hex(self.Status()))
        return
    else:
      print("USB-1808 FPGA configured.")

    if sys.platform.startswith('linux'):
      if self.udev.kernelDriverActive(0):
        self.udev.detachKernelDriver(0)
        self.udev.resetDevice()

    # claim all the needed interfaces for AInScan
    self.udev.claimInterface(0)

    # Find the maxPacketSize for bulk transfers
    self.wMaxPacketSize = self.getMaxPacketSize(libusb1.LIBUSB_ENDPOINT_IN | 0x6)  #EP IN 6

    # Set up the Timers
    # self.timerParameters = TimerParameters()

    # Build a lookup table of calibration coefficients to translate values into voltages:
    # The calibration coefficients are stored in the onboard FLASH memory on the device in
    # IEEE-754 4-byte floating point values.
    #
    #   calibrated code = code*slope + intercept
    #   self.table_AIn[channel][gain]  0 <= chan < 8,  0 <= gain < 4
    #
    self.table_AIn = [[table(), table(), table(), table()], \
                      [table(), table(), table(), table()], \
                      [table(), table(), table(), table()], \
                      [table(), table(), table(), table()], \
                      [table(), table(), table(), table()], \
                      [table(), table(), table(), table()], \
                      [table(), table(), table(), table()], \
                      [table(), table(), table(), table()]]

    address = 0x7000
    for chan in range(self.NCHAN):
      for gain in range(self.NGAIN):
        self.MemAddressW(address)
        self.table_AIn[chan][gain].slope, = unpack('f', self.MemoryR(4))
        address += 4
        self.MemAddressW(address)
        self.table_AIn[chan][gain].intercept, = unpack('f', self.MemoryR(4))
        address += 4

    # Read calibration table for analog out
    self.table_AOut = [table(), table()]
    address = 0x7100
    for chan in range(self.NCHAN_AO):
      self.MemAddressW(address)
      self.table_AOut[chan].slope, = unpack('f', self.MemoryR(4))
      address += 4
      self.MemAddressW(address)
      self.table_AOut[chan].intercept, = unpack('f', self.MemoryR(4))
      address += 4

  def CalDate(self):
    """
    get the manufacturers calibration data (timestamp) from the
    Calibration memory
    """

    # get the year (since 2000)
    address = 0x7110
    self.MemAddressW(address)
    data ,= unpack('B', self.MemoryR(1))
    year  = 2000+data

    # get the month
    address = 0x7111
    self.MemAddressW(address)
    month ,= unpack('B', self.MemoryR(1))

    # get the day
    address = 0x7112
    self.MemAddressW(address)
    day ,= unpack('B', self.MemoryR(1))

    # get the hour
    address = 0x7113
    self.MemAddressW(address)
    hour ,= unpack('B', self.MemoryR(1))
    
    # get the minute
    address = 0x7114
    self.MemAddressW(address)
    minute ,= unpack('B', self.MemoryR(1))

    # get the second
    address = 0x7115
    self.MemAddressW(address)
    second ,= unpack('B', self.MemoryR(1))

    mdate = datetime(year, month, day, hour, minute, second)
    return mdate
        
  ##############################################
  #           Digital I/O  Commands            #
  ##############################################
  # Read/Write digital port tristate register

  def DTristateR(self):
    """
    This command reads the digital port tristate register.  The
    tristate register determines if the latch register value is driven
    onto the port pin.  A '1' in the tristate register makes the
    corresponding pin an input, a '0' makes it an output.
    """

    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    value ,= self.udev.controlRead(request_type, self.DTRISTATE, wValue, wIndex, 2, self.HS_DELAY)
    return value

  def DTristateW(self, value):
    """
    This command writes the digital port tristate register.  The
    tristate register determines if the latch register value is driven
    onto the port pin.  A '1' in the tristate register makes the
    corresponding pin an input, a '0' makes it an output.
    """

    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.DTRISTATE
    wValue = value & 0xffff
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, [0x0], self.HS_DELAY)

  def DPort(self):
    """
    This command reads the current state of the digital pins.
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    value ,= self.udev.controlRead(request_type, self.DPORT, wValue, wIndex, 2, self.HS_DELAY)
    return value

  def DLatchR(self):
    """
    This command reads the digital port latch register
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    value ,= self.udev.controlRead(request_type, self.DLATCH, wValue, wIndex, 2, self.HS_DELAY)
    return value

  def DLatchW(self, value):
    """
    This command writes the digital port latch register
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.DLATCH
    wValue = value & 0xffff
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, [0x0], self.HS_DELAY)
        
  ##########################################
  #            Counter Commands            #
  ##########################################

    def CounterSet(self, counter, count):
    """
    This command reads or sets the value of the 64-bit counters.  Counter 0 and 1
    are event coutner, while Counter 2 and 3 are Encoder 0 and 1, respectively.

    counter: the counter to set (0-3)
    count:   the 32 bit value to set the counter
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.COUNTER
    wValue = 0x0
    wIndex = counter & 0xf

    if counter > self.NCOUNTER:
      raise ValueError('CounterSet: counter out of range.')
      return

    count = pack('I', count)
    self.udev.controlWrite(request_type, request, wValue, wIndex, count, self.HS_DELAY)

  def Counter(self, counter):
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = counter & 0xf

    if counter > self.NCOUNTER:
      raise ValueError('Counter: counter out of range.')
      return

    value = unpack('I',self.udev.controlRead(request_type, self.COUNTER, wValue, wIndex, 8, self.HS_DELAY))
    return value

  def CounterOptionsR(self, counter):
    """
    This command reads or sets the options of the counter.
    counter: the counter to set (0-3)

    options:    The options for this counter's mode and will differ depending on the coutner type.
      Counter:
          bit(0):   1 = Clear on Read,  0 = Read has no effect
          bit(1):   1 = No recycle mode (counter stops at 2^32 or 0, unless Range Limit is enabled)
                    0 = counter rolls over to a minimum (or maximum) and continues counting.
          bit(2):   1 = Count down,  0 = Count up
          bit(3):   1 = Range Limit on (use max and min limits) 0 = 64-bit counter (max = 2^32, min = 0)
          bit(4):   1 = Count on falling edge,  0 = Count on rising edge
          bit(5-7): Reserved

      Encoder:
         bit 0-1: Encoder Type:
                  0 = X1
                  1 = X2
                  2 = X4
         bit 2: Clear on Z: 1 = clear when Z goes high, 0 = do not clear when Z goes high
         bit 3: Latch on Z: 1 = Counter will be latched when Z goes high, 
                            0 = Counter will be latched when asynchronously read or on a pacer clock in a scan.
         bit 4: 1 = No recycle mode (counter stops at 2^32 or 0, unless Range Limit is enabled)
                0 = counter rolls over to minimum (or max) and continue counting.
         bit 5: 1 = Range Limit on (use max and min limits)
                0 = 32-bit counter (max = 2^32, 0 = min)
         bits 6-7: Reserved

    """
    
    if counter >= self.NCOUNTER:
      raise ValueError('CounterOptionsR: counter value too large.')
      return

    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = counter & 0xf
    options ,= unpack('B',self.udev.controlRead(request_type, self.COUNTER_OPTIONS, wValue, wIndex, 1, self.HS_DELAY))
    self.counterParameters[counter].counterOptions = options
    return options
    
  def CounterOptionsW(self, counter, options):
    if counter >= self.NCOUNTER:
      raise ValueError('CounterOptionsW: counter value too large.')
      return

    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.COUNTER_OPTIONS
    wValue = options
    wIndex = counter
    self.counterParameters[counter].counterOptions = options
    self.udev.controlWrite(request_type, request, wValue, wIndex, [0x0], self.HS_DELAY)


  ##########################################
  #           Memory Commands              #
  ##########################################

  def MemoryR(self, length):
    """
    This command reads or writes data from the EEPROM memory.  The
    read will begin at the current address, which may be set with
    MemAddress.  The address will automatically increment during a
    read or write but stay within the range allowed for the EEPROM.
    The amount of data to be written or read is specified in wLength.

    The range from 0x0000 to 0x3FFF is used for storing the
    microcontroller firmware and is write-protected during normal
    operation.
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    data = self.udev.controlRead(request_type, self.MEMORY, wValue, wIndex, length, self.HS_DELAY*length)
    return data

  def MemoryW(self, data):
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.MEMORY
    wValue = 0
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, data, self.HS_DELAY)

  def MemAddressR(self):
    """
    This command reads or writes the address used for memory accesses.
    The upper byte is used to denominate different memory areas.  The
    memory map for this device is

    Address                            Description
    =============               ============================
    0x0000-0x6FF7               Microcontroller firmware (write protected)
    0x6FF8-0x6FF8               Serial Number
    0x7000-0x7FFF               User data (Calibration Coefficients)

    The firmware area is protected by a separate command so is not typically
    write-enabled.  The calibration area is unlocked by writing the value 0xAA55
    to address 0x8000.  The area will remain unlocked until the device is reset
    or a value other than 0xAA55 is written to address 0x8000.
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    address = self.udev.controlRead(request_type, self.MEM_ADDRESS, wValue, wIndex, 2, self.HS_DELAY)
    return address[0] + (address[1] << 8)
    
  def MemAddressW(self, address):
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.MEM_ADDRESS
    wValue = 0
    wIndex = 0
    barray = [address & 0xff, (address >> 8) & 0xff]
    self.udev.controlWrite(request_type, request, wValue, wIndex, barray, self.HS_DELAY)

  def MemWriteEnable(self):
    """
    This command enables writes to the EEPROM memory in the range
    0x0000-0x6FFF.  This command is only to be used when updating the
    microcontroller firmware.
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.MEM_WRITE_ENABLE
    wValue = 0
    wIndex = 0
    unlock_code = 0xad
    self.udev.controlWrite(request_type, request, wValue, wIndex, [unlock_code], self.HS_DELAY)


  ##########################################
  #        Miscellaneous Commands          #
  ##########################################

  def Status(self):
    """
    This command retrieves the status of the device.
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    value ,= unpack('H',self.udev.controlRead(request_type, self.STATUS, wValue, wIndex, 2, self.HS_DELAY))
    return value

  def BlinkLED(self, count):
    """
    This command will blink the device LED "count" number of times
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.BLINK_LED
    wValue = 0
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, [count], self.HS_DELAY)

  def Reset(self):
    """
    This function causes the device to perform a reset.  The device
    disconnects from the USB bus and resets its microcontroller.
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.RESET
    wValue = 0
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, [0x0], self.HS_DELAY)

  def TriggerConfig(self, options):
    """
    This function configures the Scan trigger.  Once the trigger is
    received, the Scan will proceed as configured.  The "use
    trigger" option must be used in the ScanStart command to
    utilize this feature.

      options:     bit 0: trigger mode (0 = level,  1 = edge)
                   bit 1: trigger polarity (0 = low / falling, 1 = high / rising)
                   bits 2-7: reserved
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.TRIGGER_CONFIG
    wValue = 0x0
    wIndex = 0x0
    self.udev.controlWrite(request_type, request, wValue, wIndex, [options], self.HS_DELAY)

  def PatternDetectConfigR(self):
    """
    This function configures the Pattern Detection trigger.  Once the
    trigger is received, the Scan will proceed as configured.  The
    "use Patern Detection trigger" option must be used in the
    AInScanStart command to utilize this feature.

    value:   the pattern on which to trigger
    mask:    these bits will mask the inputs such taht only bits set to 1 here wil be compared to the pattern.
    options: bit field that controls various options
             bit 0:    Reserved
             bit 1-2:  00 = Equal to Pattern
                       01 = Not equal to Pattern
                       10 = Greater than Pattern's numeric value
                       11 = Less than Pattern's numeric value
             bits 3-7: eserved
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    value = unpack('BBB',self.udev.controlRead(request_type, self.PATTERN_DETECT_CONFIG, wValue, wIndex, 3, self.HS_DELAY))
    return (value[0], value[1], value[2])

  def PatternDetectConfigW(self, value, mask, options):
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    data = pack('BBB', value, mask, options)
    result = self.udev.controlWrite(request_type, self.PATTERN_DETECT_CONFIG, wValue, wIndex, data, self.HS_DELAY)

  def GetSerialNumber(self):

    """
    This commands reads the device USB serial number.  The serial
    number consists of 8 bytes, typically ASCII numeric or hexadecimal digits
    (i.e. "00000001").
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    value = self.udev.controlRead(request_type, self.SERIAL, wValue, wIndex, 8, self.HS_DELAY)
    return value.decode()

  def WriteSerialNumber(self, serial):
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.SERIAL
    wValue = 0
    wIndex = 0
    barray = bytearray(8)
    for i in range(8):
      barray[i] = ord(serial[i])
    self.udev.controlWrite(request_type, request, wValue, wIndex, barray, self.HS_DELAY)

  ##########################################
  #            FPGA Commands               #
  ##########################################
  
  def FPGAConfig(self):
    """
    This command puts the device into FPGA configuration update mode,
    which allows downloading the configuration for the FPGA.  The
    unlock code must be correct as a further safely device.  If the
    device is not in FPGA config mode, then the FPGAData command will
    result in a control pipe stall.

    Use the Status command to determine if the FPGA needs to be
    configured.  If so, use this command to enter configuration mode.
    Open the .rbf file containing the FPGA configuration and stream
    the data to the device using FPGAData.  After the FPGA is
    configured, then the DAQ commands will work.
    """
    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.FPGA_CONFIG
    unlock_code = 0xad
    wValue = 0
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, [unlock_code], self.HS_DELAY)

  def FPGAData(self, data):
    """
    This command writes the FPGA configuration data to the device.  This
    command is not accepted unless the device is in FPGA config mode.  The
    number of bytes to be written must be specified in wLength.

    data: max length is 64 bytes
    """
    if len(data) > 64:
      raise ValueError('FPGAData: max length is 64 bytes.')
      return

    request_type = (HOST_TO_DEVICE | VENDOR_TYPE | DEVICE_RECIPIENT)
    request = self.FPGA_DATA
    wValue = 0
    wIndex = 0
    self.udev.controlWrite(request_type, request, wValue, wIndex, data, self.HS_DELAY)

  def FPGAVersion(self):
    """
    This command reads the FPGA version.  The version is in
    hexadecimal BCD, i.e. 0x0102 is version 01.02.
    """
    request_type = (DEVICE_TO_HOST | VENDOR_TYPE | DEVICE_RECIPIENT)
    wValue = 0
    wIndex = 0
    version ,= unpack('H',self.udev.controlRead(request_type, self.FPGA_VERSION, wValue, wIndex, 2, self.HS_DELAY))
    return "{0:02x}.{1:02x}".format((version>>8)&0xff, version&0xff)

  def printStatus(self):
    status = self.Status()
    print('**** USB-1608G Status ****')
    if status & self.AIN_SCAN_RUNNING:
      print('  Analog Input scan running.')
    if status & self.AIN_SCAN_OVERRUN:
      print('  Analog Input scan overrun.')
    if status & self.AOUT_SCAN_RUNNING:
      print('  Analog Output scan running.')
    if status & self.AOUT_SCAN_UNDERRUN:
      print('  Analog Output scan underrun.')
    if status & self.AIN_SCAN_DONE:
      print(' Analog Input scan done.')
    if status & self.AOUT_SCAN_DONE:
      print(' Analog Outputt scan done.')
    if status & self.FPGA_CONFIGURED:
      print('  FPGA is configured.')
    if status & self.FPGA_CONFIG_MODE:
      print('  FPGA in configuration mode.')

  def volts(self, gain, value):
    # converts 18 bit unsigned int value to volts
    if gain == self.BP_10V:
      volt = (value - 131072) * 10. / 131072.
    elif gain == self.BP_5V:
      volt = (value - 131072) * 5. / 131072
    elif gain == self.UP_10V:
      volt = value * 10. / 262143.
    elif gain == self.UP_5V:
      volt = value * 5. / 262143.
    else:
      raise ValueError('volts: Unknown range.')
      return

    return volt

################################################################################################################

class usb_1808(usb1808):
  def __init__(self, serial=None):
    self.productID = self.USB_1808_PID   #usb-1808
    self.udev = self.openByVendorIDAndProductID(0x9db, self.productID, serial)
    if not self.udev:
      raise IOError("MCC USB-1808 not found")
      return
    usb1808.__init__(self)

class usb_1808X(usb1808):
  def __init__(self, serial=None):
    self.productID = self.USB_1808X_PID   #usb-1808X
    self.udev = self.openByVendorIDAndProductID(0x9db, self.productID, serial)
    if not self.udev:
      raise IOError("MCC USB-1808X not found")
      return
    usb1808.__init__(self)


