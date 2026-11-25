// Read/transpile the existing frontend in memory. No output in the frontend repo.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const readline = require('node:readline');
const {createRequire} = require('node:module');
const root = path.resolve(process.argv[2] || path.join(__dirname, '../../frontend'));
const nativeRequire = createRequire(path.join(root, 'package.json'));
const ts = nativeRequire('typescript');
const cache = new Map();
function load(filename) {
  filename = path.resolve(filename);
  if (cache.has(filename)) return cache.get(filename).exports;
  const mod = {exports:{}};
  cache.set(filename, mod);
  const source = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    fileName:filename,
    compilerOptions:{module:ts.ModuleKind.CommonJS, target:ts.ScriptTarget.ES2020}
  }).outputText;
  const localRequire = name => {
    if (/\.(svg|png|jpe?g|gif)$/.test(name)) return name;
    if (!name.startsWith('.')) return nativeRequire(name);
    const base = path.resolve(path.dirname(filename), name);
    const found = [base, base+'.ts', base+'.js'].find(p=>fs.existsSync(p) && fs.statSync(p).isFile());
    if (!found) throw new Error('Cannot resolve '+name+' from '+filename);
    return load(found);
  };
  const wrapped = new vm.Script('(function(require,module,exports,console){'+source+'\n})', {filename});
  wrapped.runInThisContext()(localRequire, mod, mod.exports, {log(){},error(...args){process.stderr.write(args.join(' ')+'\n');},warn(){}});
  return mod.exports;
}
const util = load(path.join(root,'src/Utils/Utils.ts'));
const golf = load(path.join(root,'src/Utils/Simulation.ts'));
const arm = load(path.join(root,'src/Utils/ArmSimulation.ts'));
function seeded(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6D2B79F5) | 0;
    let t = Math.imul(state ^ state >>> 15, 1 | state);
    t ^= t + Math.imul(t ^ t >>> 7, 61 | t);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
async function calculate(m) {
  Math.random = seeded(m.seed);
  if (m.kind === 'metadata') return {nodeVersion:process.version,typescriptVersion:ts.version,rounds:util.RoundNames, architectures:arm.armArchitectures.map(a=>({name:a.architecture, components:a.components.map(c=>c.component)}))};
  if (m.kind === 'arm-experiment') return arm.runArmComponentSimulation(m.solver,m.component);
  if (m.kind === 'arm') {
    const s = m.solvers;
    const r = arm.runArmArchitectureSimulation(m.playerId,m.architecture,m.round,s[0],s[1],s[2],s[3],m.weight);
    const out = {playerId:m.playerId,architecture:m.architecture,round:m.round,weight:r.weight,cost:r.cost,score:r.score !== null ? Math.floor(r.score*100):null};
    s.forEach((v,i)=>out[['solverOne','solverTwo','solverThree','solverFour'][i]]=v);
    return out;
  }
  if (m.kind === 'free') {
    const functions = [golf.runPlayDrive,golf.runPlayLong,golf.runPlayFairway,golf.runPlayShort,golf.runPlayPutt];
    const r = m.module === 6 ? {...await golf.runSimEntireHole(m.solver,undefined,1),distance:700} : await functions[m.module-1](m.solver);
    return {playerId:m.playerId,shots:r.shots,distance:Math.floor(r.distance*100),solver:m.solver,module:m.module};
  }
  if (m.kind === 'golf') {
    const s=m.solvers;
    let r;
    if (m.architecture === 'h') r=await golf.runSimEntireHole(s[0]);
    else if (m.architecture === 'lp') r=await golf.runLP(s[0],s[1]);
    else if (m.architecture === 'ds') r=await golf.runDS(s[0],s[1]);
    else r=await golf.runDAP(s[0],s[1],s[2]);
    const score=util.scoreRound(m.round,r.shots,r.cost,m.weight);
    const out={playerId:m.playerId,round:m.round,architecture:m.architecture,shots:r.shots,cost:Math.floor(r.cost*100),score:score !== null ? Math.floor(score*100):null,customPerformanceWeight:m.weight?Math.floor(m.weight*100):null,reasoning:m.reasoning};
    s.forEach((v,i)=>out[['solverOne','solverTwo','solverThree'][i]]=v);
    return out;
  }
  throw new Error('Unknown calculation '+m.kind);
}
async function main() {
  const lines=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
  for await (const line of lines) {
    try {
      const result=await calculate(JSON.parse(line));
      const encoded=JSON.stringify(result,(_k,v)=>{if(typeof v==='number'&&!Number.isFinite(v))throw new Error('Non-finite simulation result');return v;});
      process.stdout.write(JSON.stringify({ok:true,result:JSON.parse(encoded)})+'\n');
    } catch(e) {process.stdout.write(JSON.stringify({ok:false,error:e.message})+'\n');}
  }
}
main().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
