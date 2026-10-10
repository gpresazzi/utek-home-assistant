// Lettura soltanto: nessuna funzione Modbus di scrittura.
const net = require('node:net');
const fs = require('node:fs');
const host = process.argv[2];
if (!host) { console.error('Uso: node analysis/read-vmc.cjs IP_VMC'); process.exit(1); }
const map = JSON.parse(fs.readFileSync(__dirname + '/registers.json'));
let transaction = 0;
function read(start, count) {
  return new Promise((resolve, reject) => {
    const id = ++transaction, request = Buffer.alloc(12);
    request.writeUInt16BE(id, 0); request.writeUInt16BE(6, 4);
    request[6] = 1; request[7] = 3;
    request.writeUInt16BE(start - 1, 8); request.writeUInt16BE(count, 10);
    let data = Buffer.alloc(0), settled = false;
    const socket = net.createConnection({host, port: 502}, () => socket.write(request));
    const finish = (error, result) => { if (settled) return; settled = true; socket.destroy(); error ? reject(error) : resolve(result); };
    socket.setTimeout(3000, () => finish(new Error('Timeout')));
    socket.on('error', e => finish(e));
    socket.on('end', () => { if (!settled) finish(new Error('Risposta incompleta')); });
    socket.on('data', chunk => {
      data = Buffer.concat([data, chunk]);
      if (data.length < 7) return;
      const length = data.readUInt16BE(4);
      if (length < 3 || length > 254) return finish(new Error('Lunghezza MBAP non valida'));
      if (data.length < 6 + length) return;
      if (data.readUInt16BE(0) !== id || data.readUInt16BE(2) !== 0 || data[6] !== 1) return finish(new Error('Header inatteso'));
      if (data[7] & 128) return finish(new Error('Eccezione Modbus ' + data[8]));
      if (data[7] !== 3 || data[8] !== count * 2 || length !== count * 2 + 3) return finish(new Error('Formato risposta inatteso'));
      const values = Array.from({length: count}, (_, i) => data.readUInt16BE(9 + i * 2));
      finish(null, values);
    });
  });
}
(async () => {
  const output = {};
  for (const range of map.ranges) {
    const values = await read(range.start, range.length);
    for (let i = 0; i < values.length; i++) {
      const id = range.start + i, raw = values[i], reg = map.registers.find(r => r.id === id);
      const item = {address: id - 1, name: reg?.name, raw};
      if (reg?.isMultiple) item.bits = Object.values(reg.dataFormat).map(f => ({name: f.name, value: (raw >>> f.startingBit) & ((1 << f.length) - 1)}));
      output[id] = item;
    }
  }
  console.log(JSON.stringify(output, null, 2));
})().catch(e => { console.error(e.message); process.exitCode = 1; });
