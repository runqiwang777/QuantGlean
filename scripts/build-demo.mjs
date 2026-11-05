import {cp,mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=new URL('../',import.meta.url);
await mkdir(new URL('_site/assets/',root),{recursive:true});
await cp(new URL('site/',root),new URL('_site/',root),{recursive:true});
await cp(new URL('assets/QuantGlean.png',root),new URL('_site/assets/QuantGlean.png',root));
await writeFile(new URL('_site/.nojekyll',root),'');
console.log('Built demo:',fileURLToPath(new URL('_site/',root)));
