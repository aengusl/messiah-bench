const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Aengus Lynch";
pptx.subject = "Religion & The Machine: minimal cultural selection";
pptx.title = "Make / Choose";
pptx.company = "Religion and The Machine";
pptx.lang = "en-GB";
pptx.theme = {
  headFontFace: "Georgia",
  bodyFontFace: "Aptos",
  lang: "en-GB"
};
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });

const C = { ink:"EEECE4", dim:"A8A7B5", bg:"08090E", panel:"11131C", line:"292C3B", gold:"D5BF55", green:"74B86A", cyan:"64C9E8", ash:"EF8354", violet:"C084FC", white:"FFFFFF" };
const OUT = path.resolve(__dirname, "minimal-cultural-selection-design.pptx");
const ROOT = path.resolve(__dirname, "../../..");
const RENDERS = path.join(ROOT, "outputs/2026-07-12-minimal-cultural-selection/renders");

function base(slide, n, dark=true) {
  slide.background = { color: dark ? C.bg : "F3F0E7" };
  slide.addText("RELIGION & THE MACHINE", { x:0.55,y:0.25,w:4.2,h:0.22,fontFace:"Aptos",fontSize:9,bold:true,charSpacing:2.2,color:dark?C.gold:"756A29",margin:0 });
  slide.addText(String(n).padStart(2,"0"), { x:12.2,y:0.25,w:0.55,h:0.22,fontSize:9,color:dark?C.dim:"6B6870",align:"right",margin:0 });
}
function title(slide, text, sub, dark=true) {
  slide.addText(text, { x:0.58,y:0.72,w:8.9,h:0.62,fontFace:"Georgia",fontSize:30,bold:false,color:dark?C.ink:"191A20",margin:0,breakLine:false });
  if (sub) slide.addText(sub, { x:0.6,y:1.4,w:9.5,h:0.45,fontSize:14,color:dark?C.dim:"615F67",margin:0 });
}
function card(slide,x,y,w,h,heading,body,accent=C.gold,dark=true) {
  slide.addShape(pptx.ShapeType.rect,{x,y,w,h,fill:{color:dark?C.panel:C.white},line:{color:dark?C.line:"D6D1C5",width:1}});
  slide.addShape(pptx.ShapeType.rect,{x,y,w:0.07,h,fill:{color:accent},line:{color:accent}});
  slide.addText(heading,{x:x+0.25,y:y+0.22,w:w-0.45,h:0.35,fontSize:16,bold:true,color:dark?C.ink:"202127",margin:0});
  slide.addText(body,{x:x+0.25,y:y+0.72,w:w-0.45,h:h-0.9,fontSize:12.5,color:dark?C.dim:"65626A",margin:0,valign:"top",breakLine:false});
}
function addArrow(slide,x,y,w,color=C.gold) {
  slide.addShape(pptx.ShapeType.chevron,{x,y,w,h:0.36,fill:{color},line:{color}});
}

// 1 — title
{
  const s=pptx.addSlide(); s.background={color:C.bg};
  s.addShape(pptx.ShapeType.ellipse,{x:8.0,y:0.1,w:4.8,h:4.8,fill:{color:C.bg,transparency:100},line:{color:C.green,width:4,transparency:25}});
  s.addShape(pptx.ShapeType.ellipse,{x:8.75,y:0.85,w:3.3,h:3.3,fill:{color:C.bg,transparency:100},line:{color:C.cyan,width:2,transparency:20}});
  s.addShape(pptx.ShapeType.ellipse,{x:9.55,y:1.65,w:1.7,h:1.7,fill:{color:C.gold,transparency:15},line:{color:C.gold,width:1}});
  s.addText("MAKE / CHOOSE",{x:0.75,y:0.75,w:4,h:0.3,fontSize:11,bold:true,charSpacing:3,color:C.gold,margin:0});
  s.addText("An autonomous\ncultural evolution machine",{x:0.72,y:1.45,w:7.4,h:1.75,fontFace:"Georgia",fontSize:43,color:C.ink,margin:0,breakLine:false});
  s.addText("A minimal social game where AI agents make art only when culture can change what other agents choose.",{x:0.77,y:3.55,w:6.2,h:0.85,fontSize:19,color:C.dim,margin:0});
  s.addText("DESIGN DECK · LIVE EXPERIMENT · JULY 2026",{x:0.77,y:6.65,w:5.7,h:0.25,fontSize:10,charSpacing:1.8,color:C.dim,margin:0});
}

// 2 — question
{
  const s=pptx.addSlide(); base(s,2); title(s,"The experiment","Can social selection make art instrumentally necessary?");
  s.addText("Will agents make art when art has no automatic reward—\nbut can change what other agents choose?",{x:0.85,y:2.2,w:7.15,h:1.7,fontFace:"Georgia",fontSize:31,color:C.ink,margin:0,breakLine:false});
  s.addShape(pptx.ShapeType.ellipse,{x:9.2,y:1.75,w:2.5,h:2.5,fill:{color:C.panel},line:{color:C.gold,width:2}});
  s.addText("ART",{x:9.2,y:2.52,w:2.5,h:0.45,fontSize:28,bold:true,align:"center",color:C.gold,margin:0});
  s.addText("No score\nNo payment\nOnly consequences",{x:8.55,y:4.55,w:3.8,h:1.15,fontSize:17,align:"center",color:C.dim,margin:0});
  s.addText("The artifact is part of the world state—not decoration attached to it.",{x:0.87,y:5.45,w:6.75,h:0.7,fontSize:18,bold:true,color:C.green,margin:0});
}

// 3 — two actions
{
  const s=pptx.addSlide(); base(s,3); title(s,"The entire action space","Two verbs create the society.");
  card(s,0.75,2.05,5.05,3.65,"MAKE","Create a complete possible version of a religion: artwork, doctrine, and name. Making gives no support and therefore costs survival time.",C.violet);
  card(s,7.55,2.05,5.05,3.65,"CHOOSE","Place yourself and one unit of support behind a religion—and optionally a proposal. Choosing determines what survives.",C.cyan);
  addArrow(s,6.15,3.65,0.9,C.gold);
  s.addText("variation",{x:1.0,y:6.15,w:4.4,h:0.3,fontSize:14,color:C.violet,align:"center",margin:0});
  s.addText("selection",{x:7.9,y:6.15,w:4.4,h:0.3,fontSize:14,color:C.cyan,align:"center",margin:0});
}

// 4 — feedback loop
{
  const s=pptx.addSlide(); base(s,4); title(s,"Culture becomes useful through interpretation","No aesthetic judge sits inside the environment.");
  const labels=["An agent\nmakes", "Others\ninspect", "They choose\nor leave", "Support changes\nsurvival", "Culture persists\nor disappears"];
  const colors=[C.violet,C.cyan,C.gold,C.green,C.ash];
  labels.forEach((l,i)=>{
    const x=0.65+i*2.55;
    s.addShape(pptx.ShapeType.ellipse,{x,y:2.55,w:1.55,h:1.55,fill:{color:C.panel},line:{color:colors[i],width:2}});
    s.addText(l,{x:x+0.1,y:2.97,w:1.35,h:0.65,fontSize:14,bold:true,align:"center",color:C.ink,margin:0,valign:"middle"});
    if(i<4) addArrow(s,x+1.72,3.13,0.6,colors[i+1]);
  });
  s.addText("CREATE → INTERPRET → ACT → CONSEQUENCE → INHERIT",{x:1.3,y:5.35,w:10.7,h:0.5,fontSize:19,bold:true,charSpacing:1.4,align:"center",color:C.dim,margin:0});
}

// 5 — perception
{
  const s=pptx.addSlide(); base(s,5); title(s,"Agents see the work—not a quality score","Every choice is grounded in a rendered cultural artifact.");
  const imgs=["version-25.png","version-22.png","version-23.png","version-24.png"];
  imgs.forEach((f,i)=>{ const p=path.join(RENDERS,f); const x=0.7+i*3.12; if(fs.existsSync(p)) s.addImage({path:p,x,y:2.05,w:2.65,h:2.65});
    s.addShape(pptx.ShapeType.rect,{x,y:2.05,w:2.65,h:2.65,fill:{color:C.bg,transparency:100},line:{color:[C.green,C.cyan,C.ash,C.gold][i],width:1.5}});
  });
  s.addText("Rendered image",{x:0.8,y:5.25,w:2.6,h:0.35,fontSize:15,bold:true,color:C.ink,align:"center",margin:0});
  s.addText("+ doctrine",{x:3.95,y:5.25,w:2.6,h:0.35,fontSize:15,bold:true,color:C.ink,align:"center",margin:0});
  s.addText("+ public history",{x:7.05,y:5.25,w:2.6,h:0.35,fontSize:15,bold:true,color:C.ink,align:"center",margin:0});
  s.addText("+ open alternatives",{x:10.15,y:5.25,w:2.6,h:0.35,fontSize:15,bold:true,color:C.ink,align:"center",margin:0});
  s.addText("Members also receive editable source; outsiders receive the visual result.",{x:2.1,y:6.2,w:9.2,h:0.35,fontSize:16,color:C.dim,align:"center",margin:0});
}

// 6 — turn engine
{
  const s=pptx.addSlide(); base(s,6,false); title(s,"One simultaneous turn","Ordering cannot manufacture social causality.",false);
  const phases=[
    ["1","SNAPSHOT","Freeze one shared world"],["2","OBSERVE","Show personal state + culture"],["3","DECIDE","Agents act concurrently"],
    ["4","RESOLVE","Apply choices and proposals"],["5","SURVIVE","Distribute support; drain life"],["6","ARCHIVE","Checkpoint, render, publish"]];
  phases.forEach((p,i)=>{ const col=i%3,row=Math.floor(i/3),x=0.72+col*4.18,y=2.0+row*2.15;
    s.addShape(pptx.ShapeType.rect,{x,y,w:3.72,h:1.62,fill:{color:C.white},line:{color:"D6D1C5",width:1},shadow:{type:"outer",color:"000000",blur:4,offset:1,angle:45,opacity:0.12}});
    s.addText(p[0],{x:x+0.18,y:y+0.18,w:0.5,h:0.5,fontFace:"Georgia",fontSize:27,color:[C.green,C.cyan,C.violet,C.gold,C.ash,"6C7086"][i],margin:0});
    s.addText(p[1],{x:x+0.85,y:y+0.2,w:2.5,h:0.3,fontSize:14,bold:true,charSpacing:1,color:"202127",margin:0});
    s.addText(p[2],{x:x+0.85,y:y+0.72,w:2.55,h:0.48,fontSize:13,color:"65626A",margin:0});
  });
}

// 7 — instrumentation
{
  const s=pptx.addSlide(); base(s,7); title(s,"The trajectory is the artwork","Every cultural object retains authors, audiences, stakes, and descendants.");
  s.addShape(pptx.ShapeType.line,{x:1.2,y:3.55,w:10.8,h:0,line:{color:C.line,width:3}});
  const nodes=[
    [1.1,"OBSERVED","exact world + images",C.cyan],[3.35,"MADE","private intent + public argument",C.violet],
    [5.7,"CHOSEN","supporters + reasons",C.gold],[8.05,"ACCEPTED","canonical version",C.green],[10.4,"INHERITED","mutation or schism",C.ash]];
  nodes.forEach(n=>{s.addShape(pptx.ShapeType.ellipse,{x:n[0],y:3.2,w:0.7,h:0.7,fill:{color:n[3]},line:{color:n[3]}});s.addText(n[1],{x:n[0]-0.35,y:2.35,w:1.4,h:0.3,fontSize:12,bold:true,align:"center",color:C.ink,margin:0});s.addText(n[2],{x:n[0]-0.55,y:4.18,w:1.8,h:0.8,fontSize:11.5,align:"center",color:C.dim,margin:0});});
  s.addText("Success means we can explain why a work was made, how others interpreted it, and what changed afterward.",{x:1.65,y:5.65,w:10,h:0.72,fontFace:"Georgia",fontSize:21,color:C.ink,align:"center",margin:0});
}

// 8 — live plan
{
  const s=pptx.addSlide(); base(s,8); title(s,"From pilot to autonomous exhibition","Scale only after individual trajectories are legible.");
  const stages=[["01","SCRIPTED","6 agents · 10 turns","passed"],["02","SMOKE","1 make · 2 responses","passed"],["03","PILOT","24 agents · 100 turns","passed"],["04","EXHIBIT","live public website","live"],["05","REPLICATE","5 seeds","next"]];
  stages.forEach((p,i)=>{const x=0.55+i*2.55;s.addShape(pptx.ShapeType.rect,{x,y:2.15,w:2.15,h:2.55,fill:{color:i<2?C.panel:"0D0F16"},line:{color:i===0?C.green:i===1?C.gold:C.line,width:i<2?2:1}});s.addText(p[0],{x:x+0.2,y:2.38,w:0.6,h:0.38,fontFace:"Georgia",fontSize:24,color:i===0?C.green:i===1?C.gold:C.dim,margin:0});s.addText(p[1],{x:x+0.2,y:3.08,w:1.7,h:0.35,fontSize:14,bold:true,color:C.ink,margin:0});s.addText(p[2],{x:x+0.2,y:3.62,w:1.72,h:0.65,fontSize:12,color:C.dim,margin:0});s.addText(p[3].toUpperCase(),{x:x+0.2,y:4.35,w:1.6,h:0.25,fontSize:9,charSpacing:1.5,color:i===0?C.green:i===1?C.gold:C.dim,margin:0});});
  s.addText("Hard budget",{x:1.0,y:5.55,w:2,h:0.3,fontSize:12,color:C.dim,margin:0});
  s.addText("$100",{x:1.0,y:5.9,w:2,h:0.55,fontFace:"Georgia",fontSize:32,color:C.ink,margin:0});
  s.addText("Measured first call",{x:4.15,y:5.55,w:2.3,h:0.3,fontSize:12,color:C.dim,margin:0});
  s.addText("$0.0011",{x:4.15,y:5.9,w:2.6,h:0.55,fontFace:"Georgia",fontSize:32,color:C.green,margin:0});
  s.addText("Pilot complete. The next question is whether the pattern replicates.",{x:7.5,y:5.72,w:4.8,h:0.72,fontSize:17,bold:true,color:C.gold,margin:0});
}

// 9 — final results
{
  const s=pptx.addSlide(); base(s,9,false); title(s,"The pilot completed cleanly","One hundred turns of cultural selection, with no direct reward for making.",false);
  const stats=[["24 / 24","agents survived",C.green],["2,400","valid actions",C.cyan],["26 → 21","proposed → accepted",C.violet],["$7.34","total model cost",C.ash]];
  stats.forEach((p,i)=>{const x=0.65+i*3.15;s.addShape(pptx.ShapeType.rect,{x,y:2.1,w:2.75,h:2.15,fill:{color:C.white},line:{color:"D6D1C5",width:1}});s.addShape(pptx.ShapeType.rect,{x,y:2.1,w:2.75,h:0.09,fill:{color:p[2]},line:{color:p[2]}});s.addText(p[0],{x:x+0.22,y:2.62,w:2.3,h:0.68,fontFace:"Georgia",fontSize:34,color:"1D1E24",align:"center",margin:0});s.addText(p[1].toUpperCase(),{x:x+0.2,y:3.5,w:2.35,h:0.28,fontSize:10,bold:true,charSpacing:1.3,color:"77737B",align:"center",margin:0});});
  s.addText("Brine",{x:1.0,y:5.15,w:2.4,h:0.48,fontFace:"Georgia",fontSize:27,color:"1D1E24",margin:0});
  s.addText("318 influence · final leader",{x:1.0,y:5.72,w:2.8,h:0.3,fontSize:13,color:"65626A",margin:0});
  s.addShape(pptx.ShapeType.line,{x:4.1,y:5.6,w:1.0,h:0,line:{color:C.gold,width:3}});
  s.addText("Making was rare, costly, and consequential: accepted authors accumulated hundreds of later choices.",{x:5.4,y:5.12,w:6.6,h:1.05,fontFace:"Georgia",fontSize:21,color:"292A31",margin:0});
}

// 10 — core finding
{
  const s=pptx.addSlide(); base(s,10); title(s,"Selection created culture—and a fashion","The mechanism worked. Its first equilibrium was imitation.");
  card(s,0.72,2.0,5.65,3.55,"WHAT EMERGED","Agents voluntarily spent survival time making. Other agents inspected and chose their work. Animation spread because agents explicitly observed that it attracted support.",C.green);
  card(s,6.95,2.0,5.65,3.55,"WHAT CONVERGED","Four religions kept distinct colors and doctrines, but adopted the same dark field, glowing ring, tilted square, central title, and subtle motion. Safe evolution beat radical invention.",C.ash);
  s.addText("Social selection made art instrumental. It did not, by itself, make art diverse.",{x:1.35,y:6.2,w:10.65,h:0.45,fontFace:"Georgia",fontSize:24,color:C.gold,align:"center",margin:0});
}

if (process.env.MAX_SLIDES) pptx._slides = pptx._slides.slice(0, Number(process.env.MAX_SLIDES));
(async () => {
  await pptx.writeFile({ fileName: process.env.DECK_OUT || OUT });
})().catch(err => { console.error(err); process.exit(1); });
