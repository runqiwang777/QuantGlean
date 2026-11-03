const texts={
en:['REPRODUCTION LAB','Take the next step: run the hypothesis.','Explore three actual saved synthetic experiments: time-series trend, cross-sectional factor and fixed-split model. Inspect their specs, costs, diagnostics and reports. Historical hypotheses remain untested.','Open the saved experiment →'],
zh:['复现实验室','让研究假设，走进可核验的实验。','查看三个实际运行的合成案例：时序趋势、横截面因子、固定切分模型。核对规格、费用、诊断与报告。真实历史假设仍未检验。','查看已保存的实验 →'],
ja:['再現実験室','仮説を、検証できる実験へ。','実行済みの3つの合成実験：時系列トレンド、横断面ファクター、固定分割モデル。仕様・費用・診断・レポートを確認できます。歴史的仮説は未検証です。','保存された実験を見る →'],
ko:['재현 실험실','가설을 검증 가능한 실험으로.','실행된 세 가지 합성 사례인 시계열 추세, 횡단면 팩터, 고정 분할 모델을 확인하세요. 사양·비용·진단·보고서를 제공합니다. 실제 역사적 가설은 미검증 상태입니다.','저장된 실험 보기 →']};
function update(){const lang=document.getElementById('language').value,t=texts[lang]||texts.en;['repro-eyebrow','repro-title','repro-body','repro-link'].forEach((id,i)=>document.getElementById(id).textContent=t[i]);document.getElementById('repro-link').href='reproduction.html?lang='+lang;}
document.getElementById('language').addEventListener('change',update);update();
