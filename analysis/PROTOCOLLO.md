# Air Touch 1.1.1 — mappa Modbus estratta dall'APK

Analisi statica di assets/index.android.bundle, Hermes v96. Nessuna connessione all'impianto e nessuna scrittura eseguita.

## Trasporto verificato nel codice

TCP porta 502; Unit ID 1; protocol ID 0; FC03 holding registers; FC06 write single register. Parole a 16 bit big endian. Gli ID nell'app sono base 1: indirizzo sul filo = ID − 1.

Evidenze: funzioni 7661 (connessione), 7871 (richiesta lettura), 7872 (richiesta scrittura), 7712 (Unit ID della scrittura), 7739 (tabella registri), 7741/7744 (campi dei descrittori). Il disassemblato completo è in disassembly.txt; l'estrazione riproducibile è in disassemble.cjs.

## Comandi e interpretazioni

- Registro 20, bit 0–1: stagione; UI: 0 automatico, 1 inverno, 2 estate.
- Registro 20, bit 2–3: bypass; UI: 0 Auto, 1 OFF, 2 ON. Sono codici di configurazione, mentre lo stato effettivo è registro 86 bit 0.
- Per modificare un campo: nuovo = (vecchio & ~maschera) | ((valore << bit_iniziale) & maschera). Preservare gli altri bit. La lettura e scrittura separate non sono atomiche.
- Registro 51: setpoint velocità; la tabella rinvia al manuale. Codifica OFF/AUTO/velocità ancora da verificare nel flusso UI e sul modello reale. Non assumere che sia sempre una percentuale.
- Registro 52: OFF se <=48; 50–300 con scala 0,1 °C secondo il descrittore.
- Registro 54: velocità remota mandata bit 0–6, abilitazione bit 7; estrazione bit 8–14, abilitazione bit 15. Da verificare limiti e priorità sul modello reale.
- Registro 5: gestione controllo remoto, reset e persistenza. La funzione 7723 prepara bit 14/15 tramite updateRegisterBits per salvare dati; sequenza completa e necessità per ogni comando da verificare prima dell'uso.
- Ore ventilatori = registro 95 × 65536 + registro 96, confermato nel codice UI.

## Limiti e anomalie

La tabella è quella dell'app: non garantisce che il modello installato supporti ogni sensore. Le temperature sono descritte in decimi di grado; segno, sentinelle e associazione fisica delle sonde devono essere verificati. La tabella allarmi del registro 90 assegna sia DPSUPPLY_FAIL sia DPEXHAUST_FAIL al bit 14: possibile errore nell'app, non corretto per supposizione. I registri 87/88 rinviano al manuale per la codifica velocità.

## Lettura sull'impianto

read-vmc.cjs invia soltanto FC03 ai blocchi usati dall'app. Richiede Node.js, accetta l'IP come argomento e stampa JSON con valori grezzi e campi bit. Nessuna scansione di rete e nessuna scrittura. Non è stato eseguito sull'impianto.

## Blocchi letti dall'app

| ID iniziale | Indirizzo sul filo | Numero registri | Gruppo |
|---:|---:|---:|---|
| 1 | 0 | 5 | configuration |
| 14 | 13 | 1 | configuration |
| 20 | 19 | 1 | configuration |
| 24 | 23 | 4 | configuration |
| 51 | 50 | 6 | commands |
| 81 | 80 | 20 | unit_1_data |
| 1001 | 1000 | 3 | weekly_programming |
| 1017 | 1016 | 56 | weekly_programming |
| 8502 | 8501 | 2 | service_data |
| 8555 | 8554 | 3 | service_data |
| 8559 | 8558 | 1 | service_data |

## Tabella completa

| ID app | Indirizzo Modbus | Nome | Scrivibile | Protetto / password | Formato |
|---:|---:|---|---|---|---|
| 1 | 0 | SW_PN_0 | no | no / no | SW TYPE 0 |
| 2 | 1 | SW_PN_1 | no | no / no | SW TYPE 1 |
| 3 | 2 | SW_PN_2 | no | no / no | SW VER 0 (AAMM) |
| 4 | 3 | SW_PN_3 | no | no / no | SW VER 1 (DDPP) |
| 5 | 4 | REMOTE_CONTROL | sì | no / no | campi bit sotto |
| 14 | 13 | SPEED_BALANCE | sì | no / no | 67-150 (%) |
| 20 | 19 | PARAMETER_FLAGS | sì | sì / no | campi bit sotto |
| 24 | 23 | UNIT_1_MAX_FILT_HOURS | sì | sì / no | 0-199 (500h) |
| 25 | 24 | UNIT_2_MAX_FILT_HOURS | sì | sì / no | 0-199 (500h) |
| 26 | 25 | UNIT_3_MAX_FILT_HOURS | sì | sì / no | 0-199 (500h) |
| 27 | 26 | UNIT_4_MAX_FILT_HOURS | sì | sì / no | 0-199 (500h) |
| 51 | 50 | SPEED_SET_POINT | sì | sì / no | [see register 51 on the manual] |
| 52 | 51 | TEMPERATURE_SET_POINT | sì | sì / no | OFF(<=48) or 50-300 (0,1 °C) |
| 53 | 52 | TIMER | sì | no / no | 0-14400 (sec.) |
| 54 | 53 | SPEEDS REMOTE CONTROL | sì | no / no | campi bit sotto |
| 55 | 54 | RHUMIDITY_SET_POINT | sì | sì / no | 0-100 (%) |
| 56 | 55 | TEMPERATURE_FREE_SET_POINT | sì | sì / no | 50-400 (0,1 °C) |
| 81 | 80 | TEMP_E | no | no / no | (0,1 °C) |
| 82 | 81 | TEMP_R | no | no / no | (0,1 °C) |
| 83 | 82 | TEMP_X | no | no / no | (0,1 °C) |
| 84 | 83 | TEMP_I | no | no / no | (0,1 °C) |
| 85 | 84 | TEMP_W | no | no / no | (0,1 °C) |
| 86 | 85 | STATUS_FLAGS | no | no / no | campi bit sotto |
| 87 | 86 | SPEED_C_VALUE | no | no / no | [see register 87 on the manual] |
| 88 | 87 | SPEED_D_VALUE | no | no / no | [see register 88 on the manual] |
| 89 | 88 | AUTO_INPUT_VALUE | no | no / no | (%) |
| 90 | 89 | ALARMS 1 | no | no / no | campi bit sotto |
| 91 | 90 | DP_SUPPLY | no | no / no | (Pa) |
| 92 | 91 | DP_EXHAUST | no | no / no | (Pa) |
| 93 | 92 | FLOW_SUPPLY | no | no / no | (m3/h) |
| 94 | 93 | FLOW_EXHAUST | no | no / no | (m3/h) |
| 95 | 94 | FAN_HOURS_H | no | no / no | (65536 h) |
| 96 | 95 | FAN_HOURS_L | no | no / no | (h) |
| 97 | 96 | ALARMS 2 | no | no / no | campi bit sotto |
| 98 | 97 | PRE_HEAT | no | no / no | (%) |
| 99 | 98 | POST_HEAT | no | no / no | (%) |
| 100 | 99 | TEMP_D | no | no / no | (0,1 °C) |
| 1001 | 1000 | TIME_TABLE_SPEED_0 | sì | sì / no | [see register 1001 on the manual] |
| 1002 | 1001 | TIME_TABLE_SPEED_1 | sì | sì / no | [see register 1002 on the manual] |
| 1003 | 1002 | TIME_TABLE_SPEED_2 | sì | sì / no | [see register 1003 on the manual] |
| 1017 | 1016 | MONDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1018 | 1017 | MONDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1019 | 1018 | MONDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1020 | 1019 | MONDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1021 | 1020 | MONDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1022 | 1021 | MONDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1023 | 1022 | MONDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1024 | 1023 | MONDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 1025 | 1024 | TUESDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1026 | 1025 | TUESDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1027 | 1026 | TUESDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1028 | 1027 | TUESDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1029 | 1028 | TUESDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1030 | 1029 | TUESDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1031 | 1030 | TUESDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1032 | 1031 | TUESDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 1033 | 1032 | WEDNESDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1034 | 1033 | WEDNESDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1035 | 1034 | WEDNESDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1036 | 1035 | WEDNESDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1037 | 1036 | WEDNESDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1038 | 1037 | WEDNESDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1039 | 1038 | WEDNESDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1040 | 1039 | WEDNESDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 1041 | 1040 | THURSDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1042 | 1041 | THURSDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1043 | 1042 | THURSDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1044 | 1043 | THURSDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1045 | 1044 | THURSDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1046 | 1045 | THURSDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1047 | 1046 | THURSDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1048 | 1047 | THURSDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 1049 | 1048 | FRIDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1050 | 1049 | FRIDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1051 | 1050 | FRIDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1052 | 1051 | FRIDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1053 | 1052 | FRIDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1054 | 1053 | FRIDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1055 | 1054 | FRIDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1056 | 1055 | FRIDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 1057 | 1056 | SATURDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1058 | 1057 | SATURDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1059 | 1058 | SATURDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1060 | 1059 | SATURDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1061 | 1060 | SATURDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1062 | 1061 | SATURDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1063 | 1062 | SATURDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1064 | 1063 | SATURDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 1065 | 1064 | SUNDAY-CHANGE-0 | sì | sì / no | campi bit sotto |
| 1066 | 1065 | SUNDAY-CHANGE-1 | sì | sì / no | campi bit sotto |
| 1067 | 1066 | SUNDAY-CHANGE-2 | sì | sì / no | campi bit sotto |
| 1068 | 1067 | SUNDAY-CHANGE-3 | sì | sì / no | campi bit sotto |
| 1069 | 1068 | SUNDAY-CHANGE-4 | sì | sì / no | campi bit sotto |
| 1070 | 1069 | SUNDAY-CHANGE-5 | sì | sì / no | campi bit sotto |
| 1071 | 1070 | SUNDAY-CHANGE-6 | sì | sì / no | campi bit sotto |
| 1072 | 1071 | SUNDAY-CHANGE-7 | sì | sì / no | campi bit sotto |
| 8502 | 8501 | BAUD RATE | sì | no / sì | (100 bit/s) |
| 8503 | 8502 | TIMEOUT | sì | no / sì | (sec.) |
| 8555 | 8554 | DAY | sì | sì / sì | 1(LUNEDÌ)-7(DOMENICA) |
| 8556 | 8555 | HOUR | sì | sì / sì | 1-24 |
| 8557 | 8556 | MINUTES | sì | sì / sì | 0-59 |
| 8559 | 8558 | PASSWORD | sì | no / no |  |

### 5 — REMOTE_CONTROL

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 1 | R/W DEVICE_RESET | sì |
| 1 | 1 | R TERMINAL_ACTIVE | no |
| 2 | 1 | R TERM_RS485_ACTIVE | no |
| 4 | 1 | R/W CONNECTION_LOST | sì |
| 13 | 1 | R/W CMD DEVICE RESET | sì |
| 14 | 1 | R/W WR_APP_CONF | sì |
| 15 | 1 | R/W WR_SP | sì |

### 20 — PARAMETER_FLAGS

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 2 | R/W SEASON | sì |
| 2 | 2 | R/W BYPASS | sì |
| 4 | 1 | DEHUMIDIFIER SWITCH OFF | no |
| 5 | 1 | SPEED SWITCH OFF | no |
| 6 | 1 | POST TEMPERATURE MANAGING SWITCH OFF | no |

### 54 — SPEEDS REMOTE CONTROL

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 7 | REMOTE_SUPPLY_SPEED | sì |
| 7 | 1 | SUPPLY_SPEED_REMOTE_CONTROL | sì |
| 8 | 7 | REMOTE_EXHAUST_SPEED | sì |
| 15 | 1 | EXHAUST_SPEED_REMOTE_CONTROL | sì |

### 86 — STATUS_FLAGS

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 1 | BYPASS | no |
| 1 | 1 | SUPPLY_SPEED_REM_CONT_ACTIVE | no |
| 2 | 1 | EXHAUST_SPEED_REM_CONT_ACTIVE | no |
| 3 | 1 | DEHUM_ON | no |
| 4 | 1 | NOFROST_ACTIVE | no |
| 5 | 1 | EXT_DI_HUMIDITY | no |
| 6 | 1 | EXT_DI_PIR_MIN | no |
| 7 | 1 | EXT_DI_REMOTE_OFF | no |
| 8 | 1 | HEAT/COOL_1 | no |
| 9 | 1 | HEAT_2 | no |
| 10 | 1 | TEMP_WATER_LOW | no |
| 11 | 1 | EXT_DI_SUMMER | no |
| 12 | 1 | EXT_DI_FIRE | no |
| 13 | 1 | EXT_DI_WATER_NOFROST | no |
| 14 | 1 | EXT_DI_AUTO_COMPARE | no |

### 90 — ALARMS 1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 1 | COMM_X540_FAIL | no |
| 1 | 1 | TE_FAIL | no |
| 2 | 1 | TR_FAIL | no |
| 3 | 1 | TX_FAIL | no |
| 4 | 1 | FILTERS_FAIL | no |
| 5 | 1 | FANS_FAIL | no |
| 6 | 1 | AUTO1_FAIL | no |
| 7 | 1 | TI_FAIL | no |
| 8 | 1 | COMM_X531_FAIL | no |
| 9 | 1 | TW_FAIL | no |
| 10 | 1 | TW_LOW | no |
| 11 | 1 | AUTO1_TO_FAIL | no |
| 12 | 1 | COMM_X570_DPS_FAIL | no |
| 13 | 1 | COMM_X570_DPE_FAIL | no |
| 14 | 1 | DPSUPPLY_FAIL | no |
| 14 | 1 | DPEXHAUST_FAIL | no |

### 97 — ALARMS 2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 1 | CONFIGURATION_FAIL | no |
| 1 | 1 | ANTI_ICE_FAIL | no |
| 2 | 1 | EXT_AI2_FAIL | no |
| 3 | 1 | TD_FAIL | no |
| 4 | 1 | COMM_X570_EDPS_FAIL | no |
| 5 | 1 | COMM_X570_EDPE_FAIL | no |
| 6 | 1 | EDPS_FAIL | no |
| 7 | 1 | EDPE_FAIL | no |
| 8 | 1 | AUTO2_TO_FAIL | no |
| 9 | 1 | MIN_SPEED | no |

### 1017 — MONDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1018 — MONDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1019 — MONDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1020 — MONDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1021 — MONDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1022 — MONDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1023 — MONDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1024 — MONDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1025 — TUESDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1026 — TUESDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1027 — TUESDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1028 — TUESDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1029 — TUESDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1030 — TUESDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1031 — TUESDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1032 — TUESDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1033 — WEDNESDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1034 — WEDNESDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1035 — WEDNESDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1036 — WEDNESDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1037 — WEDNESDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1038 — WEDNESDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1039 — WEDNESDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1040 — WEDNESDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1041 — THURSDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1042 — THURSDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1043 — THURSDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1044 — THURSDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1045 — THURSDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1046 — THURSDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1047 — THURSDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1048 — THURSDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1049 — FRIDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1050 — FRIDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1051 — FRIDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1052 — FRIDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1053 — FRIDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1054 — FRIDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1055 — FRIDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1056 — FRIDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1057 — SATURDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1058 — SATURDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1059 — SATURDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1060 — SATURDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1061 — SATURDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1062 — SATURDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1063 — SATURDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1064 — SATURDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1065 — SUNDAY-CHANGE-0

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1066 — SUNDAY-CHANGE-1

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1067 — SUNDAY-CHANGE-2

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1068 — SUNDAY-CHANGE-3

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1069 — SUNDAY-CHANGE-4

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1070 — SUNDAY-CHANGE-5

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1071 — SUNDAY-CHANGE-6

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |

### 1072 — SUNDAY-CHANGE-7

| Bit iniziale | Lunghezza | Nome | Scrivibile |
|---:|---:|---|---|
| 0 | 11 | TIME - MINUTES | sì |
| 11 | 3 | SPEED SELECTION | sì |
| 14 | 2 | TEMPERATURE REG. ENABLE | sì |
