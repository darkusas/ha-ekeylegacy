# Structure of a data packet with the rare protocol

The rare protocol can only be used in ekey home systems. This protocol has the following structure:

|Position| Data set   |Data type |Values and meaning|
|-|-----------|-------------------------------|-----------------------------|
|1| nVersion  | Long | 3 |
|2| nCmd | Long | Decimal 1.. Open door with finger; Decimal 19.. Wrong or unrecognized finger |
|3| nTerminalID | Long | Address of the finger scanner.  |
|4| strTerminalSerial | Char[14] | Terminal Serial number as a string |
|5| nRelayID | Char[1] | 0.. Relay 1; 1.. Relay 2; 2.. Relay 3; 15.. Double relay |
|6| nReserved | Char[1] | Empty |
|7| nUserID | Long | User number according to ekey home control panel: 1.. User 1; 2.. User 2; 3.. User 3; ..; 99.. User 99; 0.. Unrecognized user |
|8| nFinger | Long | Finger number according to ekey home control panel: 0.. Finger 1; 1.. Finger 2; 2.. Finger 3; ..; 8.. Finger 9; 9.. Finger 0; 13.. RFID |
|9| strEvent | Char[16] | Event string |
|10| sTime | Char[16] | Time string |
|11| strName | Unsigned short | 0 |
|12| strPersonalID | Unsigned short | 0 |
