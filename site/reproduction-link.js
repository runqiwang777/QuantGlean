const texts={
en:['REPRODUCTION LAB','Take the next step: run the hypothesis.','Inspect an actual saved synthetic experiment: frozen specification, lagged positions, itemized costs and a traceable report. The historical hypothesis remains untested.','Open the saved experiment →'],
zh:['复现实验室','让研究假设，走进可核验的实验。','查看实际运行的合成数据案例：冻结规格、滞后仓位、费用分项与可追溯报告。真实历史假设仍未检验。','查看已保存的实验 →'],
ja:['再現実験室','仮説を、検証できる実験へ。','実際に実行した合成データ実験を確認：固定仕様、遅延ポジション、費用内訳、追跡可能なレポート。歴史的仮説は未検証です。','保存された実験を見る →'],
ko:['재현 실험실','가설을 검증 가능한 실험으로.','실제로 실행한 합성 데이터 사례를 확인하세요. 고정 사양, 시차 포지션, 비용 내역과 추적 가능한 보고서를 제공합니다. 실제 역사적 가설은 미검증 상태입니다.','저장된 실험 보기 →']};
function update(){const lang=document.getElementById('language').value,t=texts[lang]||texts.en;['repro-eyebrow','repro-title','repro-body','repro-link'].forEach((id,i)=>document.getElementById(id).textContent=t[i]);document.getElementById('repro-link').href='reproduction.html?lang='+lang;}
document.getElementById('language').addEventListener('change',update);update();
