# Air Touch VMC per Home Assistant

![Logo Utek](assets/utek-logo.png)

Integrazione personalizzata locale per VMC controllate dall'app **Air Touch**
(`com.codazzidev.airtouch`). Protocollo ricostruito dall'APK **1.1.1** e confrontato
con il manuale preliminare dell'app e con letture eseguite su una VMC reale.

**Versione 0.1.3 sperimentale.** L'utente ha installato l'integrazione in Home
Assistant e riferito che un cambio modalità sembra funzionare. La compatibilità
con altri modelli, tutte le modalità e la persistenza dei comandi dopo il riavvio
della VMC non sono ancora verificate. Home Assistant minimo dichiarato: **2025.3**,
da verificare prima di una release stabile. Non è un'integrazione ufficiale.

## Installazione e aggiornamento

1. Copia `custom_components/air_touch` in `/config/custom_components/air_touch`.
   Il manifest deve trovarsi in `/config/custom_components/air_touch/manifest.json`.
2. Riavvia Home Assistant.
3. In **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cerca
   **Air Touch VMC**.
4. Inserisci IP/hostname, porta **502** e Unit ID **1** (valori predefiniti).
   La configurazione verifica i registri con operazioni di sola lettura.

Per aggiornare, sovrascrivi l'intera cartella dell'integrazione e riavvia. Non
serve cancellare il dispositivo. Home Assistant conserva le entità già
disabilitate: sulla pagina del dispositivo apri le entità disabilitate e abilita
le temperature se avevi installato la 0.1.0.

Dopo la pubblicazione su GitHub sarà possibile aggiungere l'URL del repository
in HACS come repository personalizzato di tipo **Integrazione**. `hacs.json`
è incluso; l'installazione tramite HACS non è ancora stata collaudata.

## Funzioni implementate

| Funzione | Comportamento attuale |
|---|---|
| Temperature | E/R/X/I/W/D in °C, abilitate per impostazione predefinita |
| Modalità ventilazione | Spenta / Programmazione oraria / Manuale / Non riconosciuta |
| Ventilatori in funzione | Almeno uno dei registri velocità 87/88 diverso da zero |
| Stati | Bypass, antigelo, deumidificazione, controllo remoto e ingressi esterni |
| Allarmi | Aggregati 90/97, allarme filtri e ventilatori |
| Ore ventilatori | Contatore a 32 bit dai registri 95/96 |
| Diagnostica | Registri grezzi e download diagnostica con hostname/IP oscurato |
| Polling | 30 secondi; configurabile tra 10 e 3600 secondi |
| Controllo ventilazione | Spenta, Programmazione oraria, Sole (30), Aperitivo (65) |
| Altri controlli | Selettori stagione e modalità bypass |

I comandi compaiono dopo aver attivato **Abilita scritture sperimentali** nelle
opzioni. Aggiungi **Controllo ventilazione** a una scheda Entità della dashboard.
Per riaccendere scegli una modalità attiva.

Molti sensori grezzi sono inizialmente disabilitati e diagnostici: abilita quelli
utili e disponibili sul tuo modello. Velocità 87/88 restano senza unità, perché
la codifica sul dispositivo osservato non è ancora chiarita.

## Fonti e grado di verifica

Questa documentazione separa tre tipi di evidenza:

- **Manuale:** significato delle funzioni e schermate, senza specifica Modbus.
- **APK:** indirizzi, campi bit, conversioni e sequenze effettivamente usate
  dall'app 1.1.1; non garantiscono il supporto di ogni funzione su ogni macchina.
- **Impianto osservato:** letture confrontate con le selezioni dell'utente e
  riscontro di un comando, senza estendere i risultati a tutti i modelli.

Manuale esaminato: **APP_MANUALE PRELIMINARE.pdf**, titolo interno
“Manuale d'uso e programmazione”, 13 pagine PDF. Data/revisione non identificate
nel documento. Nel seguito i riferimenti usano le **pagine del PDF**, contando
copertina e indice, non la numerazione stampata.

SHA-256 del documento esaminato:

```text
ed00a729f45f4760f3fa7a9abaae85ca9e097aedb30e969efe6da3163411521d
```

Il PDF originale non è incluso nel repository; qui sono documentate le
informazioni rilevanti in forma riassunta. Non è stata verificata una licenza
di redistribuzione del manuale o dell'APK.

## Informazioni del manuale

### Controlli e connessione supportati

Il sommario indica controlli **EVO-LIGHT-BMS** e **EVOD-PH-IP** (PDF p. 2).
Questo identifica l'ambito dell'app, non una certificazione di compatibilità
dell'integrazione con tutte le macchine che montano tali controlli.

Nella versione descritta dal manuale la connessione selezionabile è soltanto
Ethernet, anche se la schermata prevede una scelta del tipo di connessione.
L'indirizzo IP si trova sul touch panel in **Menu installatore → Comunicazione**
(PDF p. 8). L'APK contiene anche riferimenti Bluetooth, ma l'integrazione
implementa esclusivamente Modbus TCP: Ethernet/Wi-Fi indicano qui il trasporto
della rete locale, non un protocollo di controllo alternativo.

### Le sei modalità della schermata principale

Le icone sono mutuamente esclusive: una sola selezione di funzionamento può
essere attiva alla volta (PDF pp. 4–5, §1.1, figura 1.1).

| Icona | Nome nel manuale | Significato |
|---|---|---|
| Luna | Notte | Profilo notturno; l'APK lo collega alla velocità ridotta |
| Sole | Giorno | Velocità standard |
| Bicchieri | Party | Velocità massima; corrisponde al profilo chiamato Aperitivo nelle prove |
| Orologio | Timer | Usa la programmazione settimanale dei ventilatori |
| Accensione/spegnimento | Spegnimento | Arresta i ventilatori, non necessariamente l'alimentazione della macchina |
| AUTO | Auto | Regolazione automatica; disponibile solo con sensore di qualità dell'aria |

**Timer indica la programmazione settimanale**, non un boost con durata fissa.
**Giorno non significa estate:** profilo ventilazione e stagione sono parametri
distinti. La presenza di un valore nel registro 89 non basta a dimostrare che
il sensore richiesto per Auto sia installato: l'app verifica la configurazione.

Le velocità dei profili sono configurabili. I valori illustrativi 40/60/80%
nella figura 2.3 (PDF p. 9) sono un esempio, non costanti del protocollo.

### Temperature

La schermata principale mostra temperatura esterna **Te**, immissione **Ti**
e ripresa **Tr** (PDF p. 5, §1.2). La schermata stato mostra anche espulsione
e acqua batteria (PDF p. 10, figura 2.4).

Il confronto con la funzione 15111 dell'APK permette l'associazione:

| Sonda | Significato | ID app | Indirizzo Modbus |
|---|---|---:|---:|
| E / Te | Aria esterna | 81 | 80 |
| R / Tr | Aria di ripresa | 82 | 81 |
| X / Tx | Aria di espulsione | 83 | 82 |
| I / Ti | Aria di immissione | 84 | 83 |
| W / Tw | Acqua batteria | 85 | 84 |
| D | Non identificata nel manuale | 100 | 99 |

L'APK applica conversione con segno e divisione per 10 a E/R/X/I/W.
L'integrazione usa `int16 / 10` anche per D, coerentemente con il suo descrittore,
ma posizione/supporto della sonda D restano da verificare. Le temperature con
segno negativo non sono ancora state confrontate con una lettura reale.

Le entità attuali mantengono i nomi “Temperatura E/R/X/I/W/D”. `0x7fff` e
`0x8000` sono trattati come non disponibili per convenzione provvisoria;
il manuale non documenta sentinelle o sonde assenti. Un valore plausibile, come
20 °C, non prova che una sonda opzionale sia fisicamente presente.

### Allarmi e aggiornamento

Nella schermata principale l'app distingue allarme filtri arancione e allarme
generale rosso, quest'ultimo associato a un possibile fermo macchina (PDF p. 5,
§1.4, figura 1.2). La schermata allarmi è raggiungibile dalle icone oppure
dalle impostazioni; ogni voce permette di consultare una spiegazione (PDF p. 6).

Gli allarmi sono letti ciclicamente. Senza allarmi attivi il pulsante verde
permette una lettura generale immediata senza attendere il ciclo successivo.
Il manuale non fornisce la mappa dei bit: quella usata dal progetto deriva
dall'APK. L'integrazione non riproduce ancora tutte le spiegazioni o la
classificazione cromatica dell'app.

### Impostazioni dell'app e della macchina

Le impostazioni sono raggiungibili dall'icona con gli ingranaggi (PDF pp. 5, 7).
Lingua e tema inizialmente seguono il dispositivo; se la lingua non è disponibile
l'app usa l'inglese. Entrambe le scelte sono modificabili. Sono configurabili
frequenza di aggiornamento, connessione e IP, ed è visibile lo stato della
connessione (PDF pp. 7–8). Queste preferenze dell'app non vengono sincronizzate
da Home Assistant; il polling dell'integrazione è indipendente.

Le impostazioni dell'unità dipendono dalla configurazione della macchina
(PDF pp. 8–9, §2.2). La schermata esemplificativa mostra setpoint temperatura,
stagione, velocità ridotta, standard e massima. Il setpoint termico è modificabile
solo quando è presente il post-trattamento dell'aria.

Data e ora del controllo macchina sono modificabili dall'app (PDF p. 9, §2.3).
Il manuale non descrive una sincronizzazione automatica, il fuso orario o il
cambio ora legale. L'integrazione attuale non imposta l'orologio della VMC.

### Stato macchina

La schermata stato espone valori di funzionamento in sola lettura; il simbolo
“i” apre una spiegazione del parametro (PDF pp. 9–10, §2.4, figura 2.4).
La figura elenca temperature esterna/ripresa/espulsione/immissione/acqua,
antigelo acqua e scambiatore, velocità dei ventilatori di immissione ed
estrazione, ore di funzionamento, bypass, post-trattamento e qualità dell'aria.

Nell'esempio le velocità sono indicate in percentuale. Sul dispositivo provato
sono stati letti 1319, 2877 e 3033, e l'utente ha riferito che l'app li etichetta
con `%`. Questo non chiarisce la codifica: non vengono convertiti in percentuali
o RPM per supposizione. Bypass configurato e bypass effettivo sono distinti.

### Programmazione settimanale

Il manuale descrive copie, modifiche, aggiunte ed eliminazioni di fasce
(PDF pp. 10–13, §2.5, figure 2.5–2.7).

- Ogni fascia ha un orario d'inizio e continua fino alla fascia successiva.
  Gli inizi devono seguire l'ordine cronologico; non c'è un orario finale
  indipendente da impostare per ogni fascia.
- Per copiare, si seleziona l'icona verde del giorno sorgente, si sceglie
  il giorno destinazione e si conferma.
- Aprendo un giorno si possono scorrere le fasce e aprire la modifica
  dall'icona o dai campi del riquadro. L'orario d'inizio digitato deve essere
  confermato tramite spunta; i menu a tendina non richiedono quella conferma.
- Sono selezionabili velocità dei ventilatori ed eventuale post-trattamento.
  Al termine va confermato il salvataggio della fascia.
- Il pulsante `+` aggiunge una fascia con inizio e tipo di funzionamento.
- Per un vincolo del pannello è eliminabile soltanto l'ultima fascia,
  previa conferma; non una fascia intermedia.

L'APK descrive **8 record al giorno** nei registri 1017–1072:
minuti nei bit 0–10, selezione velocità nei bit 11–13 e abilitazione regolazione
temperatura nei bit 14–15. Il numero di record e questi campi derivano dall'APK,
non dal testo del manuale. L'integrazione può selezionare il funzionamento
orario già configurato, ma non legge/modifica ancora il calendario completo.

## Protocollo Modbus ricostruito dall'APK

Trasporto TCP, porta 502, Unit ID 1, protocol ID 0. FC03 per holding registers,
FC06 per singolo registro, parole a 16 bit big endian. Gli ID app sono
**base 1**: indirizzo sul filo = **ID app − 1**.

La [mappa completa](analysis/PROTOCOLLO.md) e i
[descrittori dei 102 registri](analysis/registers.json) conservano i nomi e
i campi originali. Tabella essenziale:

| ID app | Indirizzo | Funzione |
|---:|---:|---|
| 5 | 4 | Controllo remoto, reset e salvataggio |
| 14 | 13 | Bilanciamento velocità |
| 20 | 19 | Stagione, modalità bypass e flag di disabilitazione |
| 24–27 | 23–26 | Soglie ore filtri per unità |
| 51 | 50 | Selezione/setpoint ventilazione |
| 52 | 51 | Setpoint termico, decimi di °C; descrittore OFF se ≤48 |
| 53 | 52 | Timer in secondi; non confonderlo con l'icona Timer |
| 54 | 53 | Velocità remote e bit di abilitazione ventilatori |
| 55 | 54 | Setpoint umidità |
| 56 | 55 | Setpoint temperatura free |
| 81–85 | 80–84 | Temperature E/R/X/I/W |
| 86 | 85 | Stati effettivi |
| 87–88 | 86–87 | Velocità mandata/estrazione, codifica da chiarire |
| 89 | 88 | Ingresso automatico / valore qualità aria nell'app |
| 90, 97 | 89, 96 | Allarmi |
| 91–94 | 90–93 | Pressioni e portate |
| 95–96 | 94–95 | Ore: registro 95 × 65536 + registro 96 |
| 98–99 | 97–98 | Uscite preriscaldo e postriscaldo |
| 100 | 99 | Temperatura D |
| 1001–1003 | 1000–1002 | Velocità dei profili Notte/Giorno/Party |
| 1017–1072 | 1016–1071 | Record settimanali, 8 per giorno |
| 8502–8503 | 8501–8502 | Baud rate e timeout del controllo |
| 8555–8557 | 8554–8556 | Giorno settimana, ora e minuti |
| 8559 | 8558 | Password |

I tre blocchi letti dall'integrazione sono **20**, **51–56**, **81–100**.
Registri password e configurazione bus non vengono interrogati o scritti.

### Profili configurabili e varianti a tre velocità

La funzione 13195 confronta il registro 51 con 1001/1002/1003 per individuare
Notte/Giorno/Party. La funzione 13198 usa quei valori per i pulsanti: i profili
sono setpoint configurabili, non codici universali 30 e 65.

La funzione 13194 distingue tramite `isThreeSpeed`:

| Variante nell'app | Timer / programmazione | Auto |
|---|---:|---:|
| Regolazione continua | 101 | 102 |
| Tre velocità | 4 | 5 |

Questi codici sono verificati nel codice dell'app, ma Auto e la variante a tre
velocità non sono stati provati sul dispositivo. **La versione attuale usa 101
per programmazione e i setpoint osservati 30/65: non supporta automaticamente
la variante a tre velocità**, non identifica ancora i profili leggendo 1001–1003
e non espone Auto o Notte come comandi.

### Comandi implementati e verifica

| Selettore | Campo | Valori attuali |
|---|---|---|
| Controllo ventilazione | Registro 51 | Spenta 0, Programmazione 101, Sole 30, Aperitivo 65 |
| Stagione | Registro 20 bit 0–1 | auto 0, winter 1, summer 2 |
| Modalità bypass | Registro 20 bit 2–3 | auto 0, off 1, on 2 secondo l'UI dell'APK |

“Sole (30)” va letto come **Giorno a setpoint 30** e “Aperitivo (65)” come
**Party a setpoint 65** sul dispositivo provato. Le etichette attuali sono
conservate nell'integrazione; il manuale chiarisce i nomi, non impone i valori.

Per ventilazione, l'APK accoda la scrittura di 51 (funzione 13204), poi
`saveWrittenData` imposta WR_APP_CONF e WR_SP (funzione 7723). Il client esegue:

1. FC06 sul registro 51.
2. Lettura del registro 5.
3. FC06 su 5 con valore precedente OR `0xC000`, preservando gli altri bit.
4. Rilettura di 51 per verificare la selezione.

Non viene scritto il bit SPEED SWITCH OFF di 20, indicato dall'APK come sola
lettura. Tutta la sequenza è serializzata. Nessuna scrittura viene ritentata
automaticamente: se una fase fallisce, la VMC può aver già accettato parte del
comando. Il readback conferma il parametro, non la persistenza dopo riavvio
né il raggiungimento immediato della velocità richiesta.

Stagione e bypass usano lettura/modifica/scrittura del solo campo in 20;
non applicano ancora la richiesta di salvataggio in 5. Accettazione e persistenza
di questi due selettori restano da verificare. La protezione dalle operazioni
concorrenti riguarda il nostro client; un altro client può modificare 20 fra
lettura e scrittura.

## Osservazioni sulla VMC provata

| Selezione app | 51 | 20 | Bit SPEED SWITCH OFF | Velocità 87 / 88 |
|---|---:|---:|---:|---|
| Programmazione oraria | 101 | 70 | 0 | 1319 / 1319 |
| Aperitivo / Party | 65 | 70 | 0 | 2877 / 3033 |
| Spenta | 0 | 102 | 1 | 0 / 0 |
| Sole / Giorno | 30 | 70 | 0 | 1276 / 1300 |

Ulteriori riscontri:

- Letture riuscite dal client Python sugli stessi blocchi dell'integrazione.
- Temperatura E circa 19 °C, R circa 21,6 °C; conversione in decimi coerente
  con i valori plausibili e con il codice dell'app.
- Ore ventilatori 2625; allarmi 90/97 entrambi zero nei campioni.
- Regolazione termica spenta (52 = 0), timer 53 = 0 e controllo remoto 54 = 0.
- Stagione configurata estate (20 bit 0–1 = 2).
- Bypass effettivo 86 bit 0 = 1, confermato ON nell'app, anche da spento.
- Modalità bypass 20 bit 2–3 = 1, interpretata OFF nell'UI estratta, mentre
  lo stato effettivo era ON: differenza ancora da chiarire.
- Pressioni e portate lette a zero: non è verificato se i sensori siano presenti.
- L'utente riferisce che un cambio modalità da Home Assistant sembra funzionare;
  non è una verifica di tutte le opzioni o della persistenza.

La modalità del sensore Home Assistant è la selezione richiesta; “Ventilatori
in funzione” usa invece le velocità misurate. Allarmi assenti, bypass attivo
o mancanza di controllo remoto non dimostrano da soli che la VMC sia in Auto.

## Connessioni brevi e convivenza con l'app

Il client della 0.1.3 chiude la connessione dopo ogni poll completo, dopo ogni
comando con verifica finale e anche su errore/cancellazione. Il poll successivo
apre una nuova sessione; il refresh dopo un comando è una sessione distinta.

L'utente ha segnalato che l'app non si collegava dopo l'installazione. Una sola
connessione TCP ammessa dalla VMC è un'ipotesi, non un limite documentato nel
manuale. Le sessioni brevi evitano l'occupazione permanente, ma app e polling
possono sovrapporsi, oppure l'app può occupare stabilmente l'unica connessione.
Se necessario aumenta il polling, per esempio a 60 secondi. La convivenza
dopo l'aggiornamento resta da verificare.

## Prova Python senza Home Assistant

Richiede Python **3.11+**; nessun pacchetto aggiuntivo. Lo script importa
direttamente il client dell'integrazione e usa soltanto letture.

```sh
uv run --python 3.13 scripts/read_air_touch.py IP_VMC
uv run --python 3.13 scripts/read_air_touch.py IP_VMC --register 51 --count 6
uv run --python 3.13 scripts/read_air_touch.py IP_VMC --register 1001 --count 3
```

Sostituisci `IP_VMC` con il tuo indirizzo. `--register` usa l'ID app base 1;
il client sottrae uno. Sono disponibili `--port`, `--unit-id` e `--timeout`.
L'output include valori grezzi, esadecimali e campi bit. La terza lettura
permette di conoscere i setpoint configurati dei tre profili senza modificarli.

## Test e limiti noti

**24 test superati con Python 3.13** nella verifica della 0.1.3, con risposte
simulate e senza collegarsi alla VMC. Sintassi Python, metadata JSON e chiavi
delle traduzioni italiana/inglese verificati.

```sh
python -m compileall -q custom_components tests scripts
python -m unittest discover -s tests -v
python tests/validate_metadata.py
```

I test coprono indirizzi, framing, byte count, MBAP, eccezioni, echo di scrittura,
readback, campi bit preservati, serializzazione, timeout, cancellazione, chiusura
e riconnessione. La CI in `.github/workflows/checks.yml` esegue i controlli.
Non sono test completi di config flow, lifecycle o frontend Home Assistant.

Altri limiti:

- Modello e firmware della VMC provata non ancora annotati.
- `ALARMS 1` assegna nell'APK sia DPSUPPLY_FAIL sia DPEXHAUST_FAIL al bit 14;
  possibile errore della tabella, non corretto per supposizione.
- Unità delle velocità 87/88, sentinelle e presenza delle sonde opzionali
  restano da verificare.
- Nessun controllo di Auto, Notte, timer temporizzato, umidità o setpoint termici.
- Nessuna modifica di calendario settimanale o data/ora della macchina.
- Profili, varianti a tre velocità e capacità non vengono ancora rilevati
  automaticamente. Usare i comandi solo dopo aver verificato la configurazione.
- Stato bypass e modalità bypass configurata non sono intercambiabili.

## Passi successivi documentati

Leggere 1001–1003 e la configurazione macchina per usare profili dinamici;
aggiungere Notte e Auto solo sulle macchine compatibili; distinguere programmazione
101/4 e Auto 102/5; assegnare nomi descrittivi alle sonde; verificare le unità
velocità; completare salvataggio dei selettori stagione/bypass; collaudare
connessioni brevi, errori e persistenza sul dispositivo. Per il calendario,
rispettare i vincoli di ordine e cancellazione descritti nel manuale.

## Struttura e pubblicazione GitHub

- `custom_components/air_touch/`: integrazione, client e traduzioni.
- `scripts/read_air_touch.py`: prova autonoma in sola lettura.
- `tests/`: verifiche del protocollo, dello stato e dei metadata.
- `analysis/PROTOCOLLO.md` e `analysis/registers.json`: evidenze Modbus.
- `.github/workflows/checks.yml`: verifica automatica.
- `hacs.json`: metadata per repository personalizzato HACS.

Repository: [gpresazzi/utek-home-assistant](https://github.com/gpresazzi/utek-home-assistant).
Il manifest include autore, documentazione e issue tracker del repository.
Prima di una release stabile verifica supporto Home Assistant e installazione HACS.
`.gitignore` esclude APK, bytecode, disassemblato e strumenti scaricati; il
manuale originale non è stato copiato nel progetto. Controlla i file del commit.
La licenza MIT copre il codice originale, non APK, manuale, codice proprietario
o logo Utek. Il logo fornito dall'utente è conservato in assets/utek-logo.png
e usato nel README per identificare il marchio; il progetto resta non ufficiale.

L'architettura segue
[config flow](https://developers.home-assistant.io/docs/core/integration/config_flow/)
e [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data/).

## Cronologia

- **0.1.0:** integrazione locale, configurazione UI, sensori e allarmi;
  temperature inizialmente disabilitate.
- **0.1.1:** temperature abilitate e sensori modalità/ventilatori in funzione.
- **0.1.2:** selettore ventilazione con valori osservati e salvataggio come nell'APK.
- **0.1.3:** connessione rilasciata dopo poll/comando, anche su errore/cancellazione.
- **Documentazione del 10 ottobre 2026:** manuale confrontato con APK e campioni;
  chiariti nomi delle icone, sonde, profili configurabili e varianti. Nessun
  cambiamento funzionale dell'integrazione in questo aggiornamento del README.
