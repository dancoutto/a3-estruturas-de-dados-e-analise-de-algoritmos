const D=window.DATA;
const R=new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL"});
const $=id=>document.getElementById(id);
let N=10,modo="n2";
function cls(v){return v<0?"neg":"pos"}
function render(){
  const a=D.n2[N-1][5],b=D.n3[N-1][5],d=a-b;
  $("nv").value=N;$("nv").max=$("r").max;
  $("k").innerHTML=[["Ganho do Nível 2",R.format(a)],["Ganho real (Nível 3)",R.format(b)],
    [d>=0?"Superestimativa do Nível 2":"Nível 2 abaixo do real",R.format(Math.abs(d))+" ("+Math.round(100*Math.abs(d)/Math.max(1,Math.abs(a)))+"%)"],["Investimento",N+" × R$ 850 = "+R.format(N*D.custo)]]
    .map(x=>"<div class=kpi><small>"+x[0]+"</small><b>"+x[1]+"</b></div>").join("");
  const L=D[modo].slice(0,N);
  $("th").textContent="Fazendas escolhidas, em ordem de prioridade ("+(modo=="n2"?"Nível 2":"Nível 3")+")";
  $("g1").textContent=modo=="n2"?"Ganho líquido":"Ganho marginal";
  $("tb").innerHTML=L.map(r=>"<tr><td>"+r[0]+"</td><td>"+r[1]+"</td><td>"+r[2]+"</td><td>"+r[3].toLocaleString("pt-BR")+"</td><td class="+cls(r[4])+">"+R.format(r[4])+"</td><td>"+R.format(r[5])+"</td><td>"+(r[6]==r[7]?r[6]+" (sem mudança)":r[6]+" → "+r[7])+"</td></tr>").join("");
  const g={};L.forEach(r=>{if(r[6]!=r[7]){(g[r[2]]=g[r[2]]||{a:r[6],d:r[7],f:[]}).f.push(r[1])}});
  const ks=Object.keys(g);let rep=ks.some(k=>g[k].f.length>1);
  $("t").innerHTML=(ks.length?"<ul>"+ks.map(k=>"<li><b>"+k+"</b>: faixa "+g[k].a+" → "+g[k].d+"<br><small>por "+g[k].f.join(", ")+"</small></li>").join("")+"</ul>":"<p>Nenhum tanque muda de faixa.</p>")
    +(modo=="n2"&&rep?"<p class=warn>No Nível 2, fazendas do mesmo tanque contam a mesma subida de faixa mais de uma vez.</p>":"");
  chart();
}
function chart(){
  const K=+$("r").max,A=D.n2.slice(0,K),B=D.n3.slice(0,K),W=560,H=270,l=62,r=14,t=14,bm=34;
  const all=A.concat(B).map(p=>p[5]),hi=Math.max(0,...all)*1.05,lo=Math.min(0,...all)*1.05,sp=(hi-lo)||1;
  const x=n=>l+(n-1)/Math.max(1,K-1)*(W-l-r),y=v=>H-bm-(v-lo)/sp*(H-t-bm);
  const path=s=>s.map((p,i)=>(i?"L":"M")+x(i+1).toFixed(1)+","+y(p[5]).toFixed(1)).join("");
  let s="";
  for(let i=0;i<=4;i++){const v=lo+sp*i/4;s+="<line x1="+l+" x2="+(W-r)+" y1="+y(v)+" y2="+y(v)+" stroke=var(--bd) /><text x="+(l-6)+" y="+(y(v)+4)+" text-anchor=end font-size=11 fill=var(--mut)>"+Math.round(v/1000)+" mil</text>"}
  if(lo<0)s+="<line x1="+l+" x2="+(W-r)+" y1="+y(0)+" y2="+y(0)+" stroke=var(--mut) />";
  [1,K/4,K/2,3*K/4,K].map(Math.round).forEach(n=>s+="<text x="+x(n)+" y="+(H-bm+16)+" text-anchor=middle font-size=11 fill=var(--mut)>"+n+"</text>");
  s+="<text x="+((l+W-r)/2)+" y="+(H-4)+" text-anchor=middle font-size=11 fill=var(--mut)>treinamentos (N)</text>";
  s+="<path d=\""+path(A)+"\" fill=none stroke=var(--a) stroke-width=2.5 /><path d=\""+path(B)+"\" fill=none stroke=var(--b) stroke-width=2.5 />";
  s+="<line x1="+x(N)+" x2="+x(N)+" y1="+t+" y2="+(H-bm)+" stroke=var(--mut) stroke-dasharray=4 />";
  s+="<circle cx="+x(N)+" cy="+y(D.n2[N-1][5])+" r=5 fill=var(--a) /><circle cx="+x(N)+" cy="+y(D.n3[N-1][5])+" r=5 fill=var(--b) />";
  $("c").innerHTML=s;
}
$("r").addEventListener("input",e=>{N=+e.target.value;render()});
[["b2","n2"],["b3","n3"]].forEach(([id,m])=>$(id).addEventListener("click",()=>{modo=m;$("b2").setAttribute("aria-pressed",m=="n2");$("b3").setAttribute("aria-pressed",m=="n3");render()}));
render();

(function(){
  var els=document.querySelectorAll(".reveal");
  if("IntersectionObserver" in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("on");io.unobserve(e.target)}})},{threshold:.12});
    els.forEach(function(e){io.observe(e)});
  }else{els.forEach(function(e){e.classList.add("on")})}
  var bar=document.getElementById("bar");
  addEventListener("scroll",function(){var h=document.documentElement;bar.style.width=(100*h.scrollTop/Math.max(1,h.scrollHeight-h.clientHeight))+"%"},{passive:true});
})();

(function(){
  var r=document.documentElement,b=document.getElementById("tema"),mq=window.matchMedia("(prefers-color-scheme: dark)");
  function atual(){return r.getAttribute("data-theme")||(mq.matches?"dark":"light")}
  function rotulo(){b.textContent=atual()=="dark"?"☀ Tema claro":"☾ Tema escuro"}
  try{var s=localStorage.getItem("tema");if(s)r.setAttribute("data-theme",s)}catch(e){}
  rotulo();
  b.addEventListener("click",function(){var n=atual()=="dark"?"light":"dark";r.setAttribute("data-theme",n);try{localStorage.setItem("tema",n)}catch(e){}rotulo()});
  if(mq.addEventListener)mq.addEventListener("change",rotulo);
})();

(function(){
  function ampliar(on){var r=$("r");r.max=on?D.n2.length:40;$("ext").checked=on;if(N>+r.max){N=+r.max;r.value=N}}
  $("ext").addEventListener("change",function(e){ampliar(e.target.checked);render()});
  $("nv").addEventListener("input",function(e){var v=Math.round(+e.target.value);if(!v)return;
    if(v>40&&!$("ext").checked)ampliar(true);N=Math.min(Math.max(v,1),+$("r").max);$("r").value=N;render()});
})();
