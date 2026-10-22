/* Varsity scene helpers. Include with <script src="../templates/components.js"></script>
   then call the helpers from an inline script at the end of <body>.

   V.person({x,y,h,color,hair,hat,moustache,bindi,facing,item,name,nameDir})
       doodle stick-figure in the house style: round head, triangle dress, stick legs, white shoes
   V.decor({theme:'blue'|'warm', clouds:true, wires:true, papers:true})
       FSS dressing: thin wire curves with blue square nodes, paper-note doodles, clouds
   V.anchorDecor({side:'right'|'left', wires:true, papers:true})
       OSA dressing over the anchor: wire curve + paper doodles in the outer margin only
   V.asset(src,{x,y,w,h,flip,z})  absolutely positioned <img>; z defaults to 6 (above .z content at 5).
       Pass z:4 to tuck a prop behind a card.
   V.person(...) also accepts z.
*/
(function(){
const NS='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e}
function place(node,x,y,z){node.style.position='absolute';node.style.left=x+'px';node.style.top=y+'px';node.style.zIndex=(z==null?6:z);document.body.appendChild(node);return node}

const V={};
V.asset=(src,o={})=>{const i=document.createElement('img');i.src=src;if(o.w)i.style.width=o.w+'px';if(o.h)i.style.height=o.h+'px';
  if(o.flip)i.style.transform='scaleX(-1)';const node=place(i,o.x||0,o.y||0,o.z);
  if(o.specIdx!=null){
    node.dataset.specIdx=String(o.specIdx);
    node.classList.add('studio-editable');
    if(o.layerType)node.dataset.layerType=o.layerType;
    if(o.layerLabel)node.dataset.layerLabel=o.layerLabel;
  }return node;
};

/* doodle person, drawn in a 200x400 box and scaled to height h */
V.person=(o={})=>{
  const h=o.h||380, s=h/400, col=o.color||'#F2B233', f=o.facing==='left'?-1:1;
  const svg=el('svg',{width:200*s,height:400*s,viewBox:'0 0 200 400',overflow:'visible'});
  const g=el('g',{transform:f<0?'translate(200,0) scale(-1,1)':''},svg);
  const k={stroke:'#111','stroke-width':4,'stroke-linecap':'round','stroke-linejoin':'round'};
  // legs + shoes
  el('path',{d:'M84 300 L80 372',fill:'none',...k},g); el('path',{d:'M118 300 L122 372',fill:'none',...k},g);
  el('path',{d:'M58 380 q16 -14 32 -6 l2 10 h-34z',fill:'#fff',...k,'stroke-width':3.5},g);
  el('path',{d:'M110 380 q16 -14 32 -6 l2 10 h-34z',fill:'#fff',...k,'stroke-width':3.5},g);
  // dress (wide triangle) + darker side fold
  el('path',{d:'M100 132 L34 308 L166 308 Z',fill:col,...k},g);
  el('path',{d:'M100 132 L124 308 L166 308 Z',fill:'#000',opacity:.13},g);
  // arms (curled hands like the house characters)
  el('path',{d:'M78 168 Q46 210 34 246 q-8 6 -2 12',fill:'none',...k},g);
  el('path',{d:'M122 168 Q156 205 166 236 q8 6 2 12',fill:'none',...k},g);
  // head (big, about 1/3 of the figure)
  el('circle',{cx:100,cy:76,r:58,fill:'#fff',...k},g);
  if(o.hair!=='none'){
    if(o.hair==='long') el('path',{d:'M42 72 Q40 8 100 8 Q160 8 158 74 L162 150 Q146 124 142 84 Q126 46 82 50 Q60 64 58 112 L44 150Z',fill:'#2b2b2b',...k,'stroke-width':3},g);
    else el('path',{d:'M40 74 L42 30 L60 40 L68 6 L88 24 L102 0 L118 22 L138 6 L144 36 L162 30 L160 74 Q132 50 100 52 Q68 50 40 74Z',fill:'#1b1b1b',...k,'stroke-width':3},g);
  }
  if(o.hat){el('path',{d:'M38 40 L162 40 L150 32 Q146 -6 100 -6 Q54 -6 50 32Z',fill:'#444',...k,'stroke-width':3},g);}
  // eyes + mouth
  el('circle',{cx:82,cy:74,r:12,fill:'#fff',...k,'stroke-width':3.5},g);el('circle',{cx:116,cy:72,r:12,fill:'#fff',...k,'stroke-width':3.5},g);
  el('circle',{cx:85,cy:76,r:5,fill:'#111'},g);el('circle',{cx:119,cy:74,r:5,fill:'#111'},g);
  if(o.moustache) el('path',{d:'M78 104 q11 -14 22 -3 q11 -11 22 3 q-11 10 -22 3 q-11 8 -22 -3z',fill:'#444',...k,'stroke-width':2.5},g);
  else el('path',{d:'M88 106 q12 10 24 0',fill:'none',...k,'stroke-width':3.5},g);
  if(o.bindi) el('circle',{cx:100,cy:54,r:4,fill:'#D33'},g);
  const wrap=document.createElement('div');wrap.appendChild(svg);
  if(o.name){const n=document.createElement('div');n.className=o.nameClass||'name';n.textContent=o.name;
    n.style.cssText='position:absolute;white-space:nowrap;top:-10px;left:'+(100*s)+'px;transform:translate(-50%,-100%)';wrap.appendChild(n)}
  wrap.style.width=200*s+'px';wrap.style.height=400*s+'px';
  const node=place(wrap,o.x||0,o.y||0,o.z);
  if(o.specIdx!=null){
    node.dataset.specIdx=String(o.specIdx);
    node.classList.add('studio-editable');
    if(o.layerType)node.dataset.layerType=o.layerType;
    if(o.layerLabel)node.dataset.layerLabel=o.layerLabel;
  }return node;
};

/* wire curve with square nodes (both FSS and anchor-side dressing) */
function wire(svg,d,color){el('path',{d,fill:'none',stroke:color,'stroke-width':2,opacity:.8},svg);}
function node(svg,x,y,color){el('rect',{x:x-8,y:y-8,width:16,height:16,fill:color,transform:`rotate(15 ${x} ${y})`},svg)}
function paper(svg,x,y,r){const g=el('g',{transform:`translate(${x} ${y}) rotate(${r})`},svg);
  el('path',{d:'M0 0 h80 v56 h-52 l-16 16 v-16 h-12z',fill:'#fff',stroke:'#222','stroke-width':2.5},g);
  [14,26,38].forEach((yy,i)=>el('line',{x1:12,y1:yy,x2:i==2?50:68,y2:yy,stroke:'#555','stroke-width':3},g));}
function cloud(svg,x,y,s,fill){const g=el('g',{transform:`translate(${x} ${y}) scale(${s})`},svg);
  el('path',{d:'M0 40 q0 -22 26 -22 q8 -22 34 -18 q20 -14 40 4 q24 -2 26 22 q14 4 12 14 z',fill,stroke:'#6FA9E8','stroke-width':2.5},g);}

V.decor=(o={})=>{
  const warm=o.theme==='warm', c='#248EF7';
  const svg=el('svg',{width:1920,height:1080,style:'position:absolute;left:0;top:0;z-index:1'});
  if(o.wires!==false){wire(svg,'M-20 300 Q60 60 150 0',c);node(svg,108,248,c);
    wire(svg,'M1920 720 Q1700 820 1690 640 Q1700 470 1860 420',c);node(svg,1820,280,c);node(svg,1640,560,c);}
  if(o.papers!==false){paper(svg,40,520,-14);paper(svg,1700,160,30);}
  if(o.clouds!==false){cloud(svg,1580,90,1.1,warm?'#FFF6DD':'#D9E9FF');cloud(svg,210,110,.8,warm?'#FFF6DD':'#D9E9FF');}
  document.body.appendChild(svg);return svg;
};
V.anchorDecor=(o={})=>{
  // dressing stays in the outer 120px margin of the graphics side + far corner, never in the content zone
  const c='#248EF7', right=o.side!=='left';
  const svg=el('svg',{width:1920,height:1080,style:'position:absolute;left:0;top:0;z-index:1'});
  if(right){if(o.wires!==false){wire(svg,'M30 0 Q90 90 62 190',c);node(svg,62,190,c);}
    if(o.papers!==false){paper(svg,18,760,-18);paper(svg,1740,70,40);}}
  else{if(o.wires!==false){wire(svg,'M1890 0 Q1830 90 1858 190',c);node(svg,1858,190,c);}
    if(o.papers!==false){paper(svg,1820,760,18);paper(svg,100,70,-30);}}
  document.body.appendChild(svg);return svg;
};
window.V=V;
})();
