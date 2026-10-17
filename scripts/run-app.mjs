import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const web = path.join(root, 'apps/web');
const python = process.env.AVENIR_PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
if (!existsSync(python) || !existsSync(path.join(web, 'node_modules/vite'))) {
  console.error('Install the app first: see apps/web/README.md. Python 3.12+ is required.');
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
for (const [command, args] of [
  [python, ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8015']],
  [process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', process.argv.includes('--preview') ? 'preview' : 'dev']],
]) {
  const child = spawn(command, args, { cwd: web, stdio: 'inherit', shell: process.platform === 'win32' });
  children.push(child);
  child.on('error', error => { console.error(error.message); stop(1); });
  child.on('exit', code => { if (!closing) stop(code || 0); });
}
console.log('Aventier: http://127.0.0.1:4175 (API: http://127.0.0.1:8015). Ctrl+C stops both.');
