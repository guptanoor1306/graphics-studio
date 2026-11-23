// Static-ready decor: appends named layers into #decor (or body).
function zoDecor(o={}){
 const host=document.getElementById('decor')||document.body;
 const dark=!!o.dark, s=o.seed||1, r=(i)=>{const x=Math.sin(s*97+i*13.7)*1e4;return x-Math.floor(x)};
 const add=(name,html,css)=>{const d=document.createElement('div');d.setAttribute('data-name',name);d.style.position='absolute';d.innerHTML=html;Object.assign(d.style,css);host.appendChild(d)};
 const doodle=c=>`<svg width="150" height="90" viewBox="0 0 150 90"><path d="M6 40c18-26 26-36 18-34-8 2-12 34 6 34s20-24 12-22-6 26 12 26 18-22 12-20-4 26 14 26 18-18 12-16-2 22 18 30" fill="none" stroke="${c}" stroke-width="4" stroke-linecap="round"/></svg>`;
 const tri=(c,rot,sz)=>`<svg width="${sz}" height="${sz}" viewBox="0 0 40 40"><path d="M8 6 L36 20 L8 34 Z" fill="${c}" stroke="${c}" stroke-width="5" stroke-linejoin="round" transform="rotate(${rot} 20 20)"/></svg>`;
 const star=`<svg width="70" height="70" viewBox="0 0 40 40"><path d="M20 2 L24 16 L38 20 L24 24 L20 38 L16 24 L2 20 L16 16Z" fill="#CCCCCC" transform="rotate(20 20 20)"/></svg>`;
 const cols=['#A984FF','#4CAF52','#f07339','#FFC02E'];
 const c1=cols[Math.floor(r(1)*4)], c2=cols[(Math.floor(r(1)*4)+1+Math.floor(r(2)*3))%4];
 add('Triangle',tri(dark?'#f07339':c1,Math.floor(r(3)*360),dark?60:56),o.tri1||{right:'250px',top:'150px'});
 add('Triangle',tri(dark?'#A984FF':c2,Math.floor(r(4)*360),dark?64:80),o.tri2||{left:'230px',bottom:'170px'});
 if(!dark){
  if(o.star!==false) add('Sparkle',star,o.starAt||{right:'230px',bottom:'130px'});
  add('Dash','<div style="width:64px;height:10px;border-radius:10px;background:#f07339"></div>',o.dash1||{left:'180px',top:'46%'});
  add('Dash','<div style="width:58px;height:6px;border-radius:6px;background:#4CAF52"></div>',o.dash2||{right:'170px',top:'20%'});
 }
}
// Pie: zoPie(el,{size,pad,slices:[{v,color,label,stroke,text}]}) — SVG slices + HTML % and labels (exporter-safe).
function zoPie(el,o){const R=o.size/2,cx=R+o.pad,cy=R+o.pad,W=o.size+2*o.pad;let a=-90,svg='',lab='';
 const P=(ang,rr)=>[cx+rr*Math.cos(ang*Math.PI/180),cy+rr*Math.sin(ang*Math.PI/180)];
 const T=(x,y,txt,fs,col,anchor,name)=>{const tx=anchor==='start'?'0':anchor==='end'?'-100%':'-50%';
  return `<div data-name="${name}" style="position:absolute;left:${x}px;top:${y}px;transform:translate(${tx},-50%);white-space:nowrap"><div style="font-size:${fs}px;font-weight:500;color:${col}">${txt}</div></div>`};
 o.slices.forEach((s,i)=>{const sw=s.v*3.6,[x1,y1]=P(a,R),[x2,y2]=P(a+sw,R),m=a+sw/2;
  svg+=`<path d="M${cx} ${cy}L${x1} ${y1}A${R} ${R} 0 ${sw>180?1:0} 1 ${x2} ${y2}Z" fill="${s.color}" stroke="${s.stroke||'#fff'}" stroke-width="2"/>`;
  const big=s.v>=30,sm=s.v<8,[tx,ty]=P(m,R*(big?.55:sm?.8:.66));
  lab+=T(tx,ty,s.v+'%',big?110:sm?40:56,s.text||'#fff','middle','Value / '+(s.label||i+1));
  if(s.label){const[lx,ly]=P(m,R+50),c=Math.cos(m*Math.PI/180);lab+=T(lx,ly,s.label,44,'#222222',c>0.2?'start':c<-0.2?'end':'middle','Label / '+s.label)}
  a+=sw});
 el.style.width=W+'px';el.style.height=W+'px';
 el.innerHTML=`<svg data-name="Slices" style="position:absolute;left:0;top:0" width="${W}" height="${W}" viewBox="0 0 ${W} ${W}">${svg}</svg>`+lab}
