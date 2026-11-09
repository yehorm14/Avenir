import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const web = path.join(root, 'apps/web');
const python = process.env.AVENIR_PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const production = process.argv.includes('--production') || process.argv.includes('--preview');
const port = process.env.AVENIR_PORT || '4175';
const host = process.env.AVENIR_HOST || '127.0.0.1';
if (!existsSync(python) || (!production && !existsSync(path.join(web, 'node_modules/vite')))) {
  console.error('Install the app first: see apps/web/README.md. Python 3.12+ and Node 20+ are required.');
  process.exit(1);
}
if (production && !existsSync(path.join(web, 'dist/index.html'))) {
  console.error('Build the frontend first: npm --prefix apps/web run build');
  process.exit(1);
}
const children = [];
let closing = false;
function stop(code = 0) {
  if (closing) return;
  closing = true;
  for (const child of children) child.kill('SIGTERM');
  process.exitCode = code;
}
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => stop());
const processes = production
  ? [[python, ['-m', 'uvicorn', 'api.application:app', '--host', host, '--port', port]]]
  : [
      [python, ['-m', 'uvicorn', 'api.application:app', '--host', '127.0.0.1', '--port', '8015']],
      [process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'dev']],
    ];
for (const [command, args] of processes) {
  const child = spawn(command, args, { cwd: web, stdio: 'inherit', shell: process.platform === 'win32' });
  children.push(child);
  child.on('error', error => { console.error(error.message); stop(1); });
  child.on('exit', code => { if (!closing) stop(code || 0); });
}
console.log(`Avenir: http://${host}:${production ? port : '4175'} (same-origin APIs). Ctrl+C stops the app.`);
