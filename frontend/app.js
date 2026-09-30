/* Aegis premium live visualizer.
   UI-only changes: all telemetry and answer data still comes from the backend. */
const $ = (id) => document.getElementById(id);
const SESSION = "demo_" + Math.random().toString(36).slice(2, 8);
const SCRIPTS = {
  fresh: "I need a venue in Pune for 30 people and I want to know the cancellation policy and the catering options",
  refine: "Actually make that 60 people instead",
  suppress: "Make the expense submission deadline and approval chain shorter",
  gauntlet: "What is the parental leave policy and how many weeks are paid?"
};

let ws = null, corpus = {}, lastResult = null;
let streamBuffer = "", liveTextSent = "", liveActive = false, liveStartedAt = 0, liveFlushTimer = null;
let firstTokenClientMs = null, eventCount = 0, lastTurnHadAnswer = false;
let clockTimer = null;

const NARRATION = {
  provisional_retrieve: (e) => `Speculative search fired${e.timestamp_s != null ? ` at ${Number(e.timestamp_s).toFixed(2)}s` : ""} — Aegis is searching before the sentence ends.`,
  retrieve: (e) => `Utterance complete${e.timestamp_s != null ? ` at ${Number(e.timestamp_s).toFixed(2)}s` : ""} — dispatching the final searches in parallel.`,
  suppress: () => "This is a presentation/refinement action — Aegis can reuse existing evidence instead of searching again.",
};

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/${SESSION}`);
  ws.onopen = () => setConn(true, "connected");
  ws.onclose = () => { setConn(false, "reconnecting…"); setTimeout(connect, 2000); };
  ws.onerror = () => setConn(false, "connection error");
  ws.onmessage = (ev) => { try { handle(JSON.parse(ev.data)); } catch {} };
}
function setConn(ok, text) {
  $("conn-dot").className = "dot " + (ok ? "ok" : "bad");
  $("conn-text").textContent = text;
}
function setProcessing(active, label="Thinking live…") {
  document.body.classList.toggle("processing", active);
  $("activity-stage").classList.toggle("active", active);
  $("live-state").classList.toggle("active", active);
  $("live-state").innerHTML = `<i></i> ${active ? escapeHtml(label) : "Ready"}`;
  $("stage-badge").classList.toggle("active", active);
  if (active) $("stage-badge").textContent = "LIVE";
}
function updateClock() {
  if (!liveStartedAt) { $("stream-clock").textContent = "0.0s"; return; }
  $("stream-clock").textContent = ((performance.now() - liveStartedAt) / 1000).toFixed(1) + "s";
}
function startClock() { clearInterval(clockTimer); clockTimer = setInterval(updateClock, 80); updateClock(); }
function stopClock() { clearInterval(clockTimer); clockTimer = null; updateClock(); }

function handle(msg) {
  const ev = msg.event;
  if (msg.status === "ok" && msg.chunks_indexed !== undefined) {
    const label = `${msg.chunks_indexed} chunks · ${msg.documents} docs · ${msg.embedding_backend} · llm:${msg.llm_provider}`;
    setConn(true, label); $("footer-status").textContent = `${msg.chunks_indexed} chunks · ${msg.documents} docs`;
    return;
  }
  switch (ev) {
    case "controller_decision":
      if (msg.decision === "provisional_retrieve" || msg.decision === "retrieve" || msg.decision === "suppress") {
        addTick(msg); narrate(msg);
        if (msg.decision === "provisional_retrieve") markSpeculative(msg.timestamp_s);
        if (msg.decision === "retrieve") markRetrieve(msg.timestamp_s);
      }
      break;
    case "retrieval_started":
      if (msg.trigger === "provisional" && msg.speculative_sub_queries) addSubQueries(msg.speculative_sub_queries, true);
      if (msg.trigger !== "provisional") markRetrieve(msg.timestamp_s);
      break;
    case "sub_query_dispatched":
      addSubQueries(msg.sub_queries, false);
      setStage("Retrieval dispatched", `${msg.sub_queries?.length || 0} focused sub-queries are now searching the corpus.`, "SEARCH");
      break;
    case "retrieval_suppressed":
      narrate({decision:"suppress"}); addTick({decision:"suppress", timestamp_s:msg.timestamp_s, reason:msg.reason});
      setStage("Reusing existing evidence", "No new retrieval needed for this turn.", "REUSE");
      break;
    case "token":
      if (firstTokenClientMs === null && liveStartedAt) {
        firstTokenClientMs = performance.now() - liveStartedAt;
        $("token-time").textContent = firstTokenClientMs.toFixed(0) + "ms";
        $("token-item").classList.add("live");
      }
      streamBuffer += msg.text;
      $("answer").innerHTML = `<p class="claim"><span class="stream-cursor"></span>${escapeHtml(streamBuffer)}</p>`;
      setStage("Answer streaming", "Grounded claims are arriving token by token.", "STREAM");
      break;
    case "turn_result":
      renderResult(msg.result); stopClock(); liveActive = false; setProcessing(false); lastTurnHadAnswer = true; break;
    case "session_reset": clearAll(); break;
    case "error":
      setStage("Something went wrong", msg.detail || "The backend returned an error.", "ERROR");
      setProcessing(false); stopClock(); break;
  }
  if (ev && ev.startsWith("answer_v")) $("version").textContent = "v" + msg.answer_version;
}

function setStage(title, detail, badge="LIVE") {
  $("stage-title").textContent = title;
  $("stage-detail").textContent = detail;
  $("stage-badge").textContent = badge;
}
function narrate(e) {
  const fn = NARRATION[e.decision];
  if (fn) { $("live-help").textContent = fn(e); $("live-help").style.color = e.decision === "provisional_retrieve" ? "#a88b58" : ""; }
}
function markSpeculative(t) {
  $("spec-time").textContent = t == null ? "LIVE" : Number(t).toFixed(2) + "s";
  $("spec-item").classList.add("live");
  $("spec-detail").textContent = "Search began before the utterance ended";
  setStage("Speculative retrieval", `Aegis started searching while you were still speaking${t != null ? ` · ${Number(t).toFixed(2)}s` : ""}.`, "SPECULATE");
}
function markRetrieve(t) {
  if (t != null) $("retrieve-time").textContent = Number(t).toFixed(2) + "s";
  $("retrieve-item").classList.add("live");
  $("retrieve-detail").textContent = "Final parallel retrieval dispatched";
  setStage("Final retrieval", `The complete utterance is locked${t != null ? ` · ${Number(t).toFixed(2)}s` : ""}.`, "RETRIEVE");
}
function addTick(e) {
  eventCount++;
  $("timeline-count").textContent = `${eventCount} event${eventCount === 1 ? "" : "s"}`;
  const cls = {provisional_retrieve:"prov",retrieve:"retr",suppress:"supp"}[e.decision] || "wait";
  const short = {provisional_retrieve:"speculate",retrieve:"retrieve",suppress:"reuse"}[e.decision] || e.decision;
  const el = document.createElement("div"); el.className = "tick " + cls;
  el.innerHTML = `<div class="pip"></div><div class="t">${Number(e.timestamp_s || 0).toFixed(2)}s</div><div class="d">${short}</div>`;
  el.title = e.reason || ""; $("timeline").appendChild(el); $("timeline").scrollLeft = $("timeline").scrollWidth;
}
function addSubQueries(list, speculative) {
  if (!list) return;
  const box = $("subqueries"); if (!speculative) box.innerHTML = "";
  list.forEach((q,i)=>{ const el=document.createElement("span"); el.className="sq"+(speculative?" spec":""); el.textContent=q; el.title=speculative?"Speculative — fired before utterance end":"Dispatched after utterance end"; el.style.animationDelay=(i*70)+"ms"; box.appendChild(el); });
  $("query-count").textContent = box.children.length;
}
function renderResult(res) {
  lastResult = res;
  const box=$("answer"); box.innerHTML="";
  if (!res.claims || !res.claims.length) box.innerHTML=`<p class="placeholder">${escapeHtml(res.answer || "No grounded answer could be produced.")}</p>`;
  else res.claims.forEach(c=>{
    const p=document.createElement("p"); const added=/added_in_v/.test(c.status||""); const mod=/modified_in_v/.test(c.status||"");
    p.className="claim"+(added?" added":"")+(mod?" modified":"")+(c.is_uncertain?" uncertain":"");
    const conf=c.confidence||0, col=conf>.66?"var(--green)":conf>.33?"var(--amber)":"var(--red)";
    p.innerHTML=`<span class="ring" style="background:${col}" title="confidence ${conf.toFixed(2)}"></span>${escapeHtml(c.text)}`;
    (c.citations||[]).forEach((cit,i)=>{ const b=document.createElement("span"); b.className="cite"; b.textContent=cit; b.onclick=()=>inspect(c.chunk_ids?.[i]||c.chunk_ids?.[0],cit); p.appendChild(b); });
    if(added||mod||(res.version > 1 && !added && !mod)){
      const t=document.createElement("span");
      t.className = "status-tag " + (added ? "new-tag" : (mod ? "patched-tag" : "reused-tag"));
      t.textContent = added ? "NEW" : (mod ? "PATCHED" : "REUSED");
      p.appendChild(t);
    }
    box.appendChild(p);
  });
  const u=$("uncertainty"); if(res.uncertainty){u.classList.remove("hidden");u.innerHTML=`<b>Grounding boundary</b>${escapeHtml(res.uncertainty)}`}else u.classList.add("hidden");
  $("version").textContent="v"+(res.answer_version||0);
  const m=res.metrics||{}; $("m-ttft").textContent=(m.ttft_ms??0).toFixed(1)+"ms"; $("m-calls").textContent=m.retrieval_calls??0; $("m-tokens").textContent=m.total_tokens??0; $("m-cost").textContent="$"+(m.estimated_cost_usd??0).toFixed(6);
  if(m.ttft_ms!=null){$("token-time").textContent=Number(m.ttft_ms).toFixed(0)+"ms";$("token-item").classList.add("live")}
  if(!res.retrieval_required){setStage("Evidence reused","Presentation-only turn — zero new retrieval calls.","REUSE")}
  else if(m.is_refine_turn){const patched=(res.claims||[]).filter(c=>/modified_in_v/.test(c.status||"")).length;setStage("Answer refined",`Aegis patched ${patched||"the affected"} claim${patched===1?"":"s"} without restarting the whole turn.`,"REFINE")}
  else setStage("Grounded answer ready",`${(res.claims||[]).length} grounded claim${(res.claims||[]).length===1?"":"s"} returned with source citations.`,"READY");
  const dl=$("decisions"); dl.innerHTML="";
  (res.retrieval_events||[]).forEach(e=>{const d=document.createElement("div");d.className="dec";d.innerHTML=`<span class="dt">${Number(e.timestamp_s||0).toFixed(2)}s</span><span class="dd ${e.trigger==="provisional"?"provisional_retrieve":"retrieve"}">${escapeHtml(e.trigger||"search")}</span><span class="dr" title="${escapeHtml(e.query||"")}">${escapeHtml(e.query||"")}</span>`;dl.appendChild(d)});
}
function inspect(chunkId,citation){const box=$("inspector"),c=corpus[chunkId];if(!c){box.innerHTML=`<p class="placeholder">Chunk ${escapeHtml(chunkId||citation)} not found in the loaded corpus.</p>`;return}box.innerHTML=`<div class="cid">${escapeHtml(c.chunk_id)} · ${escapeHtml(c.citation)} · ${escapeHtml(c.section)}</div><div class="ctext">${escapeHtml(c.text)}</div>`}

function clearAll(){
  $("timeline").innerHTML="";$("subqueries").innerHTML="";$("decisions").innerHTML="";$("uncertainty").classList.add("hidden");
  $("answer").innerHTML='<div class="answer-empty"><div class="empty-orb"></div><p>Your grounded answer will appear here.</p></div>';
  $("inspector").innerHTML='<p class="placeholder">No citation selected.</p>';
  $("version").textContent="v0";$("timeline-count").textContent="0 events";$("query-count").textContent="0";
  $("spec-time").textContent="—";$("retrieve-time").textContent="—";$("token-time").textContent="—";
  ["spec-item","retrieve-item","token-item"].forEach(id=>$(id).classList.remove("live"));
  $("live-help").textContent="Aegis can begin speculative retrieval before you finish speaking.";
  $("stage-title").textContent="Ready for your question";$("stage-detail").textContent="Speak or type a compound request. Aegis will surface retrieval decisions as they happen.";$("stage-badge").textContent="IDLE";
  $("stage-badge").classList.remove("active");eventCount=0;streamBuffer="";firstTokenClientMs=null;lastTurnHadAnswer=false;stopClock();setProcessing(false);
}
function wsReady(){return ws&&ws.readyState===WebSocket.OPEN}
function sendLiveDelta(value,force=false){if(!wsReady())return;const text=String(value??"");if(!liveActive&&text.length){clearAll();liveActive=true;liveStartedAt=performance.now();liveTextSent="";setProcessing(true,"Listening live…");startClock();document.body.classList.add("listening")}if(!liveActive)return;const t=(performance.now()-liveStartedAt)/1000;if(force||text!==liveTextSent){ws.send(JSON.stringify({type:"replace",text,t}));liveTextSent=text}}
function scheduleLiveInput(){if(liveFlushTimer)clearTimeout(liveFlushTimer);liveFlushTimer=setTimeout(()=>{liveFlushTimer=null;sendLiveDelta($("utterance").value)},300)}
function finishLiveTurn(text){if(!wsReady()||!text.trim())return;if(!liveActive){clearAll();liveActive=true;liveStartedAt=performance.now();liveTextSent="";setProcessing(true,"Thinking live…");startClock()}if(liveFlushTimer){clearTimeout(liveFlushTimer);liveFlushTimer=null}sendLiveDelta(text,true);ws.send(JSON.stringify({type:"end"}));document.body.classList.remove("listening");setStage("Processing final request","Waiting for the final retrieval and grounded synthesis.","WORKING");liveTextSent="";liveActive=false}

$("send").onclick=()=>{const text=$("utterance").value.trim();if(!text)return;finishLiveTurn(text);$("utterance").value=""};
$("utterance").addEventListener("input",scheduleLiveInput);$("utterance").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();$("send").click()}});
document.querySelectorAll("[data-script]").forEach(b=>b.onclick=()=>{const value=SCRIPTS[b.dataset.script];$("utterance").value=value;finishLiveTurn(value);$("utterance").value=""});
$("reset").onclick=()=>ws&&ws.send(JSON.stringify({type:"reset"}));

const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SR){const rec=new SR();rec.continuous=false;rec.interimResults=true;rec.lang="en-US";let speaking=false;$("mic").onclick=()=>{if(speaking){rec.stop();return}try{rec.start();speaking=true;$("mic").classList.add("live");document.body.classList.add("listening");$("live-state").classList.add("active");$("live-state").innerHTML="<i></i> Listening…"}catch{}};rec.onresult=e=>{const t=Array.from(e.results).map(r=>r[0].transcript).join("");$("utterance").value=t;sendLiveDelta(t,true);if(e.results[e.results.length-1].isFinal)finishLiveTurn(t)};rec.onend=()=>{speaking=false;$("mic").classList.remove("live");document.body.classList.remove("listening")};rec.onerror=()=>{speaking=false;$("mic").classList.remove("live");document.body.classList.remove("listening")}}else{$("mic").disabled=true;$("mic").title="Voice input is unavailable in this browser"}

function escapeHtml(s){return String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}
fetch("/api/corpus").then(r=>r.json()).then(d=>(d.chunks||[]).forEach(c=>{corpus[c.chunk_id]=c})).catch(()=>{});
connect();
