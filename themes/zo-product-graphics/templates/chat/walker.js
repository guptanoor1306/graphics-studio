(() => {
const R = v => Math.round(v*100)/100;
const visBox = cs => {
  const bg = cs.backgroundColor, hasBg = bg && !/rgba\(.*, 0\)$/.test(bg) && bg!=='transparent';
  const hasImg = cs.backgroundImage && cs.backgroundImage!=='none';
  const bw = ['Top','Right','Bottom','Left'].some(s=>parseFloat(cs['border'+s+'Width'])>0 && cs['border'+s+'Style']!=='none');
  const sh = cs.boxShadow && cs.boxShadow!=='none';
  return hasBg||hasImg||bw||sh;
};
const opa = el => { let o=1; for(let e=el;e&&e!==document.documentElement;e=e.parentElement){o*=parseFloat(getComputedStyle(e).opacity)} return R(o); };
const boxLeaf = (el,name) => {
  const cs=getComputedStyle(el), r=el.getBoundingClientRect();
  const sides=['Top','Right','Bottom','Left'];
  const bw=sides.some(s=>parseFloat(cs['border'+s+'Width'])>0&&cs['border'+s+'Style']!=='none');
  return {type:'box',name,x:R(r.left),y:R(r.top),w:R(r.width),h:R(r.height),bg:cs.backgroundColor,
    bgimg:cs.backgroundImage,bgsize:cs.backgroundImage!=='none'?cs.backgroundSize:'',bgpos:cs.backgroundPosition,bgrepeat:cs.backgroundRepeat,
    radius:(()=>{const c=[cs.borderTopLeftRadius,cs.borderTopRightRadius,cs.borderBottomRightRadius,cs.borderBottomLeftRadius].map(v=>v.split(' '));
      const h=c.map(v=>v[0]),v=c.map(v=>v[1]||v[0]); return h.join(' ')===v.join(' ')?h.join(' '):h.join(' ')+' / '+v.join(' ');})(),
    border:bw?sides.map(s=>`${cs['border'+s+'Width']} ${cs['border'+s+'Style']} ${cs['border'+s+'Color']}`):null,
    shadow:cs.boxShadow==='none'?'':cs.boxShadow,opacity:opa(el)};
};
const textLeaves = (node) => {
  const el=node.parentElement, cs=getComputedStyle(el), out=[];
  const s=node.textContent; const re=/\S+/g; let m; const words=[];
  while((m=re.exec(s))){const rg=document.createRange();rg.setStart(node,m.index);rg.setEnd(node,m.index+m[0].length);
    const rs=[...rg.getClientRects()].filter(q=>q.width>0); if(!rs.length) continue;
    const q=rs[0]; words.push({t:m[0],l:q.left,t0:q.top,r:Math.max(...rs.map(z=>z.right)),b:q.bottom});}
  const lines=[]; for(const w of words){const L=lines.find(l=>Math.abs(l.t0-w.t0)<3); if(L){L.ws.push(w)} else lines.push({t0:w.t0,ws:[w]})}
  for(const L of lines){ let txt=L.ws.map(w=>w.t).join(' '); if(cs.textTransform==='uppercase') txt=txt.toUpperCase();
    const l=Math.min(...L.ws.map(w=>w.l)), r=Math.max(...L.ws.map(w=>w.r)), t=Math.min(...L.ws.map(w=>w.t0)), b=Math.max(...L.ws.map(w=>w.b));
    out.push({type:'text',name:txt,text:txt,x:R(l),y:R(t),w:R(r-l+2),h:R(b-t),mono:false,size:R(parseFloat(cs.fontSize)),weight:cs.fontWeight,
      style:'normal',color:cs.color,ls:cs.letterSpacing==='normal'?0:R(parseFloat(cs.letterSpacing)),tt:'none',deco:'',
      shadow:cs.textShadow==='none'?'':cs.textShadow,stroke:'',opacity:opa(el)});}
  return out;
};
const warn=[];
const walk = (el, defName) => {
  // returns list of nodes (a group if named, else flattened children)
  const cs=getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden') return [];
  const name=el.getAttribute('data-name');
  if(el.tagName.toLowerCase()==='svg'){
    if(el.querySelector('text')) warn.push('svg text in '+(name||'svg'));
    const r=el.getBoundingClientRect(); const c=el.cloneNode(true);
    if(!c.getAttribute('viewBox')) c.setAttribute('viewBox',`0 0 ${r.width} ${r.height}`);
    ['class','style','data-name','width','height'].forEach(a=>c.removeAttribute(a));
    c.setAttribute('width','100%');c.setAttribute('height','100%');c.setAttribute('preserveAspectRatio','none');
    return [{type:'svg',name:name||'Shapes',x:R(r.left),y:R(r.top),w:R(r.width),h:R(r.height),opacity:opa(el),svg:c.outerHTML}];
  }
  if(el.tagName==='IMG'){const r=el.getBoundingClientRect();
    return [{type:'img',name:name||'Image',x:R(r.left),y:R(r.top),w:R(r.width),h:R(r.height),src:el.getAttribute('src'),fit:cs.objectFit||'fill',opacity:opa(el)}];}
  const kids=[];
  if(visBox(cs)) kids.push(boxLeaf(el, name && !hasContent(el) ? name : 'Background'));
  for(const ch of el.childNodes){
    if(ch.nodeType===3){ if(ch.textContent.trim()) kids.push(...textLeaves(ch)); }
    else if(ch.nodeType===1 && !['SCRIPT','STYLE','DEFS'].includes(ch.tagName)) kids.push(...walk(ch));
  }
  if(name && !(kids.length===1 && kids[0].type==='box' && kids[0].name===name)) {
    if(!kids.length) return [];
    if(kids.length===1 && kids[0].type!=='group' && !name.includes('/')) { if(kids[0].type!=='text') kids[0].name=name; return [kids[0]]; }
    return [{type:'group',name,children:kids}];
  }
  return kids;
};
function hasContent(el){return el.textContent.trim().length>0 || el.querySelector('svg,div,span,img')}
const top=[];
for(const ch of document.body.children){ if(ch.tagName!=='SCRIPT') top.push(...walk(ch)); }
return {tree:top,warn};
})()
