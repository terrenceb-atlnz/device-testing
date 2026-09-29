#!/bin/bash
# T22651 (sensors), T22650 (system), T22652 (alarms): read-only cases, each with its own enable / teardown / config capture.
cd /tmp/ckmodbus
C="python3 ckcon.py /dev/u5 115200 /tmp/ckmodbus/console-u5.log"
POST=/home/terrenceb/claude/device-testing/IE520/modbus-2026-09-29/post-test-configs
enable()  { $C --stop-on-error "configure terminal" "scada modbus tcp server" "end" "show scada modbus tcp server | include MODBUS|Write|Port  " || exit 2; sleep 2; }
teardown(){ $C --stop-on-error "configure terminal" "no scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada"; python3 mb.py --log /tmp/ckmodbus/mb-$1.log probe; $C "show running-config" | sed 1d > $POST/$1.u5.show_running-config.txt; }

{ echo "### $(date) T22651 read Sensor information"; enable
M="python3 mb.py --log /tmp/ckmodbus/mb-22651.log"
$C "show system environment"
for u in 1 3 4; do
  echo "--- member $u"
  $M --slave $u read 0x1000 1 ENUM  "step1 #1 Sensor Type"
  $M --slave $u read 0x1001 2 FLOAT "step2 #1 Sensor Reading"
  $M --slave $u read 0x1003 1 ENUM  "step3 #1 Sensor Units"
  $M --slave $u read 0x1004 1 UINT  "step4 #1 Sensor Fault Status"
  $M --slave $u read 0x1005 1 ENUM  "step5 #2 Sensor Type"
  $M --slave $u read 0x1006 2 FLOAT "step5 #2 Sensor Reading"
  $M --slave $u read 0x1008 1 ENUM  "step5 #2 Sensor Units"
  $M --slave $u read 0x1009 1 UINT  "step5 #2 Sensor Fault Status"
  $M --slave $u read 0x1000 25 RAW  "sensors 1-5 whole block (5 x 5 words)"
  $M --slave $u read 0x1019 5 RAW   "past sensor 5"
done
$M --slave 0 read 0x1000 25 RAW "unit 0 sensor block"
$C "show system environment" "show scada modbus tcp server | include holding|illegal"
echo "### $(date) T22651 teardown"; teardown 22651; } 2>&1 | tee /tmp/ckmodbus/22651.out

{ echo "### $(date) T22650 read System information"; enable
M="python3 mb.py --log /tmp/ckmodbus/mb-22650.log"
echo "--- the case text addresses (older mapping) --- "
$M read 0x0000 1  UINT  "step1 Mapping Version"
$M read 0x0001 32 ASCII "step2 case: Board Name / DUT map 5: System Name"
$M read 0x0021 32 ASCII "step3 case: Serial Number / DUT map 5: Software Version"
$M read 0x0041 1  UINT  "step4 case: Number of Sensors"
$M read 0x0042 1  UINT  "step5 case: Number of Alarms"
$M read 0x0043 1  UINT  "step6 case: Number of Ports"
$M read 0x0044 1  UINT  "step7 case: Number of Faults"
$M read 0x0045 32 ASCII "step8 case: Software Version"
$M read 0x0065 32 ASCII "step9 case: System Name"
$M read 0x0085 3  HEX   "step10 case: HW Mac Address"
echo "--- the DUT mapping-5 addresses (ART library_1359 map) ---"
$M read 0x0041 3 HEX  "map5 HW MAC Address 0x0041-0x0043"
$M read 0x0044 1 HEX  "map5 Stack members bitmap"
$M read 0x0045 1 UINT "map5 Number of Ports"
$M read 0x0046 1 UINT "map5 Number of Faults"
$M read 0x0047 1 UINT "map5 Number of Sensors"
$M read 0x0048 1 UINT "map5 Number of Alarms (global)"
$M read 0x0049 1 UINT "map5 Number of Alarms (members)"
$M read 0x004a 3 RAW  "map5 0x004a-0x004c heartbeat"
$M read 0x0000 0x50 RAW "system block 0x0000-0x004f raw"
$M read 0x0050 0x30 RAW "system block 0x0050-0x007f raw"
for u in 1 3 4; do
  echo "--- member $u board block"
  $M --slave $u read 0x0120 5 RAW   "member system info: boards, ports, faults, sensors, alarms"
  $M --slave $u read 0x0200 1 ENUM  "board class"
  $M --slave $u read 0x0201 1 UINT  "board slot"
  $M --slave $u read 0x0202 32 ASCII "Board Name"
  $M --slave $u read 0x0222 32 ASCII "Serial Number"
  $M --slave $u read 0x0242 3 HEX   "board HW MAC"
done
$C "show system" "show system mac" "show running-config | include hostname" "show stack | include Ready" "show scada modbus tcp server | include holding|illegal"
echo "### $(date) T22650 teardown"; teardown 22650; } 2>&1 | tee /tmp/ckmodbus/22650.out

{ echo "### $(date) T22652 read alarm information"; enable
M="python3 mb.py --log /tmp/ckmodbus/mb-22652.log"
$C "show alarm facility settings" "show alarm facility status" "show system environment | include Power|Temp|Stack"
echo "--- the case text addresses ---"
$M --slave 1 read 0x3600 1 ENUM "step1 case: #1 Alarm Type @0x3600"
$M --slave 1 read 0x3601 1 HEX  "step2 case: #1 Alarm Configuration @0x3601"
$M --slave 1 read 0x3602 1 BOOL "step3 case: #1 Alarm Status @0x3602"
echo "--- the DUT mapping-5 block (6 words per alarm) ---"
for u in 1 3 4; do
  echo "--- member $u"
  $M --slave $u read 0x3000 1 ENUM "step1 #1 Alarm Type (External PSU 1)"
  $M --slave $u read 0x3001 1 HEX  "step2 #1 Alarm Configuration"
  $M --slave $u read 0x3005 1 BOOL "step3 #1 Alarm Status (word 5 of the entry)"
  $M --slave $u read 0x3002 3 RAW  "#1 words 2-4"
  $M --slave $u read 0x3006 6 RAW  "#2 External PSU 2 entry"
  $M --slave $u read 0x300c 6 RAW  "#3 Link down port$u.0.1"
  $M --slave $u read 0x3012 6 RAW  "#4 Link down port$u.0.2"
  $M --slave $u read 0x305a 6 RAW  "#31 Temperature entry"
done
$M --slave 0 read 0x3000 6 RAW "unit 0 #1 entry"
$C "show scada modbus tcp server | include holding|illegal"
echo "### $(date) T22652 teardown"; teardown 22652; } 2>&1 | tee /tmp/ckmodbus/22652.out
echo "### $(date) all done"
