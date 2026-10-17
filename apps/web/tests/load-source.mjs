import { readFile } from 'node:fs/promises';
import ts from 'typescript';

export async function loadSource(name) {
  const source = await readFile(new URL(`../src/${name}.ts`, import.meta.url), 'utf8');
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ES2022, target: ts.ScriptTarget.ES2021 },
  });
  return import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
}
