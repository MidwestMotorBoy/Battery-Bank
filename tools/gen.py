import csv
# (ref, part, value, package, status, [(pin, pin_name, net), ...])
C = "confirmed from TI datasheet"; A = "assumed, verify"; T = "to be selected"
parts = [
("U1","TPS25751D","USB-C PD controller","WQFN-38 4x6mm",C,[
 (1,"LDO_3V3","PD_3V3"),(2,"ADCIN1","ADCIN1"),(3,"ADCIN2","ADCIN2"),(4,"LDO_1V5","PD_1V5"),
 (5,"GPIO0","GND"),(6,"GPIO1","GND"),(7,"GPIO2","GND"),(8,"I2Ct_SDA","HOST_SDA"),(9,"I2Ct_SCL","HOST_SCL"),(10,"I2Ct_IRQ","HOST_IRQ"),
 (11,"GND","GND"),(12,"GND","GND"),(13,"GPIO11","GND"),(14,"GND","GND"),(15,"DRAIN","PD_DRAIN"),
 (16,"I2Cc_SDA","CHG_SDA"),(17,"I2Cc_SCL","CHG_SCL"),(18,"I2Cc_IRQ","CHG_INT"),(19,"GPIO3","GND"),
 (20,"PPHV","PPHV"),(21,"PPHV","PPHV"),(22,"PPHV","PPHV"),(23,"VBUS_IN","VBUS1"),(24,"VBUS_IN","VBUS1"),(25,"VBUS_IN","VBUS1"),
 (26,"GPIO4/USB_P","P1_DP"),(27,"GPIO5/USB_N","P1_DN"),(28,"CC1","P1_CC1"),(29,"CC2","P1_CC2"),(30,"DRAIN","PD_DRAIN"),(31,"GND","GND"),
 (32,"VBUS","VBUS1"),(33,"VBUS","VBUS1"),(34,"PP5V","5V"),(35,"PP5V","5V"),(36,"GPIO7","GND"),(37,"GPIO6","GND"),(38,"VIN_3V3","3V3"),
 ("EP1","GND pad","GND"),("EP2","DRAIN pad","PD_DRAIN")]),
("U2","BQ25756","Buck-boost charge controller","VQFN-36 5x6mm",C,[
 (1,"SCL","CHG_SCL"),(2,"SDA","CHG_SDA"),(3,"INT","CHG_INT"),(4,"STAT1","CHG_STAT1"),(5,"STAT2","CHG_STAT2"),(6,"PG","CHG_PG"),
 (7,"CE","CHG_CE_N"),(8,"TS","CHG_TS"),(9,"ICHG","CHG_ICHG"),(10,"ILIM_HIZ","CHG_ILIM"),(11,"FBG","CHG_FBG"),(12,"FB","CHG_FB"),
 (13,"SRN","VBAT_SYS"),(14,"SRP","BAT_SNS_P"),(15,"NC",""),(16,"NC",""),(17,"PGND","GND"),(18,"SW2","SW2"),(19,"HIDRV2","HG2"),
 (20,"BTST2","BTST2"),(21,"LODRV2","LG2"),(22,"PGND","GND"),(23,"DRV_SUP","REGN"),(24,"REGN","REGN"),(25,"LODRV1","LG1"),
 (26,"BTST1","BTST1"),(27,"HIDRV1","HG1"),(28,"SW1","SW1"),(29,"ACN","AC_SNS_N"),(30,"ACP","PPHV"),(31,"NC",""),
 (32,"VAC","CHG_VAC"),(33,"VAC","CHG_VAC"),(34,"ACUV","CHG_ACUV"),(35,"ACOV","CHG_ACOV"),(36,"FSW_SYNC","CHG_FSW"),("EP","Thermal pad","GND")]),
("Q1","N-FET 40V <=6mOhm logic-level","Buck high side","3.3x3.3mm",T,[("D","drain","AC_SNS_N"),("G","gate","HG1"),("S","source","SW1")]),
("Q2","N-FET 40V <=6mOhm logic-level","Buck low side","3.3x3.3mm",T,[("D","drain","SW1"),("G","gate","LG1"),("S","source","GND")]),
("Q3","N-FET 40V <=6mOhm logic-level","Boost low side","3.3x3.3mm",T,[("D","drain","SW2"),("G","gate","LG2"),("S","source","GND")]),
("Q4","N-FET 40V <=6mOhm logic-level","Boost high side","3.3x3.3mm",T,[("D","drain","BAT_SNS_P"),("G","gate","HG2"),("S","source","SW2")]),
("L1","Inductor","4.7uH, Isat>=12A, <=5mm tall","about 10x10mm",T,[(1,"","SW1"),(2,"","SW2")]),
("R1","Sense resistor","5mOhm 1% 1W","2512 or 1206 wide",A,[(1,"","PPHV"),(2,"","AC_SNS_N")]),
("R2","Sense resistor","5mOhm 1% 1W","2512 or 1206 wide",C,[(1,"","BAT_SNS_P"),(2,"","VBAT_SYS")]),
("C1","Bootstrap cap","100nF 25V","0402",A,[(1,"","BTST1"),(2,"","SW1")]),
("C2","Bootstrap cap","100nF 25V","0402",A,[(1,"","BTST2"),(2,"","SW2")]),
("C3","REGN cap","4.7uF 10V","0603",C,[(1,"","REGN"),(2,"","GND")]),
("C4","DRV_SUP cap","4.7uF 10V","0603",C,[(1,"","REGN"),(2,"","GND")]),
("C5","VAC cap","1uF 35V","0603",C,[(1,"","CHG_VAC"),(2,"","GND")]),
("R3","VAC feed","10 Ohm","0402",A,[(1,"","PPHV"),(2,"","CHG_VAC")]),
("C6-C9","Input bulk (port side)","4x 22uF 35V X7R, plus C10","1210",A,[(1,"","AC_SNS_N"),(2,"","GND")]),
("C10","Input bulk polymer","68uF 25V, <=5mm tall","D case",A,[(1,"","PPHV"),(2,"","GND")]),
("C11-C14","Output bulk (battery side)","4x 22uF 25V X7R, plus C15","1210",A,[(1,"","BAT_SNS_P"),(2,"","GND")]),
("C15","Battery bulk polymer","68uF 25V, <=5mm tall","D case",A,[(1,"","VBAT_SYS"),(2,"","GND")]),
("R4","FB top","243k 0.1%","0402",A,[(1,"","VBAT_SYS"),(2,"","CHG_FB")]),
("R5","FB bottom","24.9k 0.1%","0402",A,[(1,"","CHG_FB"),(2,"","CHG_FBG")]),
("R6","ICHG set","16.9k 1% (2.96A)","0402",C,[(1,"","CHG_ICHG"),(2,"","GND")]),
("R7","ILIM set","4.02k 1% (about 5A with 5mOhm R1)","0402",A,[(1,"","CHG_ILIM"),(2,"","GND")]),
("R8","FSW set","66.5k 1% (400kHz)","0402",C,[(1,"","CHG_FSW"),(2,"","GND")]),
("R9","TS upper","5.23k 1%","0402",C,[(1,"","REGN"),(2,"","CHG_TS")]),
("R10","TS lower","30.1k 1%","0402",C,[(1,"","CHG_TS"),(2,"","GND")]),
("RT1","NTC on cell","10k 103AT, on leads","wired",C,[(1,"","CHG_TS"),(2,"","GND")]),
("R11","ACUV/ACOV divider top","value from datasheet section 6.3","0402",T,[(1,"","CHG_VAC"),(2,"","CHG_ACOV")]),
("R12","ACUV/ACOV divider mid","value from datasheet section 6.3","0402",T,[(1,"","CHG_ACOV"),(2,"","CHG_ACUV")]),
("R13","ACUV/ACOV divider bottom","value from datasheet section 6.3","0402",T,[(1,"","CHG_ACUV"),(2,"","GND")]),
("R14","CE pull-down","10k","0402",A,[(1,"","CHG_CE_N"),(2,"","GND")]),
("R15","INT pull-up","10k","0402",C,[(1,"","CHG_INT"),(2,"","PD_3V3")]),
("R16","I2Cc SDA pull-up","3.3k","0402",C,[(1,"","CHG_SDA"),(2,"","PD_3V3")]),
("R17","I2Cc SCL pull-up","3.3k","0402",C,[(1,"","CHG_SCL"),(2,"","PD_3V3")]),
("R18","I2Ct SDA pull-up","4.7k","0402",C,[(1,"","HOST_SDA"),(2,"","3V3")]),
("R19","I2Ct SCL pull-up","4.7k","0402",C,[(1,"","HOST_SCL"),(2,"","3V3")]),
("R20","Host IRQ pull-up","10k","0402",A,[(1,"","HOST_IRQ"),(2,"","3V3")]),
("R21-R23","STAT1/STAT2/PG pull-ups","3x 100k","0402",A,[(1,"","CHG_STAT1 / CHG_STAT2 / CHG_PG"),(2,"","3V3")]),
("C16","LDO_3V3 cap","10uF 6.3V","0603",C,[(1,"","PD_3V3"),(2,"","GND")]),
("C17","LDO_1V5 cap","10uF 6.3V","0603",C,[(1,"","PD_1V5"),(2,"","GND")]),
("C18","VIN_3V3 cap","10uF 6.3V","0603",C,[(1,"","3V3"),(2,"","GND")]),
("C19","VBUS cap","4.7uF 35V","0805",C,[(1,"","VBUS1"),(2,"","GND")]),
("C20","PP5V cap","22uF 10V","0805",C,[(1,"","5V"),(2,"","GND")]),
("C21","CC1 cap","330pF","0402",C,[(1,"","P1_CC1"),(2,"","GND")]),
("C22","CC2 cap","330pF","0402",C,[(1,"","P1_CC2"),(2,"","GND")]),
("R24,R25","ADCIN1 strap divider","level chosen in TI GUI","0402",T,[(1,"","PD_3V3 / GND"),(2,"","ADCIN1")]),
("R26,R27","ADCIN2 strap divider","level chosen in TI GUI","0402",T,[(1,"","PD_3V3 / GND"),(2,"","ADCIN2")]),
("U3","I2C EEPROM","size and address per TPS25751 datasheet","SOT-23-5 or UDFN",T,[("SDA","","CHG_SDA"),("SCL","","CHG_SCL"),("VCC","","PD_3V3"),("GND","","GND")]),
("D1","VBUS TVS","TVS2200 or equivalent","SON",C,[(1,"","VBUS1"),(2,"","GND")]),
("D2","CC/D+/D- ESD array","4-channel, 24V-tolerant on CC","SOT/DFN",T,[("IO","","P1_CC1, P1_CC2, P1_DP, P1_DN"),("GND","","GND")]),
("J1","Amphenol 12402082E512A","Port 1 USB-C","vertical SMT",A,[("VBUS","A4/A9/B4/B9","VBUS1"),("GND","A1/A12/B1/B12/shell","GND"),("CC1","A5","P1_CC1"),("CC2","B5","P1_CC2"),("D+","A6/B6","P1_DP"),("D-","A7/B7","P1_DN")]),
]
blocks_pending = [("Protector","BQ77915 + 2 FETs + 5mOhm sense + 15A fuse","between cell stack and VBAT_SYS","pinout not yet pulled"),
 ("3.3V rail","TPS709 LDO","VBAT_SYS -> 3V3","pinout not yet pulled"),
 ("5V rail and port 2","TPS62933 buck, J2, 4.7k CC pull-ups","VBAT_SYS -> 5V, 5V -> VBUS2 through a load switch","pinout not yet pulled"),
 ("Bluetooth","Ebyte E104-BT5005A","HOST_SDA, HOST_SCL, HOST_IRQ, CHG_STAT1/2, CHG_PG, LEDs, SWD pads","pinout not yet pulled")]
with open("monolith_port1_netlist.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["ref","part","value_or_role","pin","pin_name","net","status"])
    for ref,part,val,pkg,st,pins in parts:
        for p,n,net in pins: w.writerow([ref,part,val,p,n,net if net else "no connect",st])
with open("monolith_port1_bom.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["ref","part","value_or_role","package","status","JLC_part_number"])
    for ref,part,val,pkg,st,pins in parts: w.writerow([ref,part,val,pkg,st,""])
    for b in blocks_pending: w.writerow(["(block)",b[1],b[0]+": "+b[2],"",b[3],""])
nets={}
for ref,part,val,pkg,st,pins in parts:
    for p,n,net in pins:
        if net: nets.setdefault(net,[]).append(f"{ref}.{p}")
single=[k for k,v in nets.items() if len(v)<2]
print(len(parts),"lines,",len(nets),"nets; single-node nets:",single)
print("FB:",1.536*(1+243/24.9), 1.566*(1+243/24.9), "ICHG:",50/16.9, "FSW R:",1/(10*400e3*5e-12-500e-9))
