import { existsSync, readFileSync, appendFileSync } from 'node:fs';
import { resolve } from 'node:path';

const apps = ['api', 'web'];
const requiredScripts = ['dev', 'lint', 'typecheck', 'test:ci', 'build'];
const strict = process.argv.includes('--strict') || process.env.REQUIRE_APP === 'true';
const output = (ready) => {
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `ready=${ready}\n`);
};

try {
  const present = apps.map((app) => existsSync(resolve('apps', app)));
  if (present.every((value) => !value)) {
    output(false);
    if (strict) throw new Error('App chưa có mã nguồn; publish yêu cầu cả apps/api và apps/web.');
    console.log('BOOTSTRAP: chỉ kiểm tra hạ tầng; chưa lint/test/build ứng dụng.');
    if (process.env.GITHUB_STEP_SUMMARY) {
      appendFileSync(process.env.GITHUB_STEP_SUMMARY, '### Bootstrap\nChưa có app; các job ứng dụng được bỏ qua. CI này chỉ kiểm tra cấu hình hạ tầng.\n');
    }
  } else {
    for (const app of apps) {
      const folder = resolve('apps', app);
      for (const file of ['package.json', 'package-lock.json']) {
        if (!existsSync(resolve(folder, file))) throw new Error(`apps/${app}/${file} còn thiếu.`);
      }
      const manifest = JSON.parse(readFileSync(resolve(folder, 'package.json'), 'utf8'));
      const lock = JSON.parse(readFileSync(resolve(folder, 'package-lock.json'), 'utf8'));
      if (!Number.isInteger(lock.lockfileVersion) || lock.lockfileVersion < 2) {
        throw new Error(`apps/${app}: cần npm lockfileVersion >= 2.`);
      }
      if (manifest.workspaces) throw new Error(`apps/${app}: template yêu cầu package độc lập, không workspaces.`);
      for (const script of requiredScripts) {
        if (typeof manifest.scripts?.[script] !== 'string' || !manifest.scripts[script].trim()) {
          throw new Error(`apps/${app}: thiếu script ${script}.`);
        }
      }
    }
    output(true);
    console.log('APP-READY: hai manifest/lockfile và scripts đã có; CI sẽ chạy quality gates thực tế.');
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
