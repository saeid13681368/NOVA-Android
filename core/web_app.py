import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

from core.ai.gateway import AIGateway
from core.ai.team_engine import NOVATeamEngine
from core.ai.multimodel import run as run_multimodel
from memory.store import load, remember, forget

gateway = AIGateway()
team_engine = NOVATeamEngine()

PAGE = r"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0c1220">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="NOVA">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon-192.png">
<link rel="apple-touch-icon" href="/icon-192.png">
<title>NOVA AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0c1220;color:#e9efff;font-family:Tahoma,Arial,sans-serif}
header{padding:18px;background:#131e32;border-bottom:1px solid #263653}
.logo{font-size:25px;font-weight:bold;color:#75baff}
.sub{font-size:12px;color:#9eacc4;margin-top:7px}
main{max-width:900px;margin:auto;padding:15px}
.status{background:#14243a;border:1px solid #294260;border-radius:13px;padding:13px;margin-bottom:15px}
.green{color:#66e3a3}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
button{border:0;border-radius:10px;padding:12px 15px;background:#245c9e;color:white;font-size:14px;cursor:pointer}
.tab{background:#1b2a41}
.tab.active{background:#286bb4}
.panel{background:#121d30;border:1px solid #263953;border-radius:15px;padding:15px}
#chat{height:48vh;min-height:260px;overflow:auto;padding:5px}
.msg{padding:12px;margin:9px 0;border-radius:12px;white-space:pre-wrap;line-height:1.9;overflow-wrap:anywhere}
.user{background:#21456b;margin-right:35px}
.bot{background:#202d43;margin-left:15px}
.inputrow{display:flex;gap:8px;margin-top:12px}
input{min-width:0;flex:1;background:#0d1727;color:white;border:1px solid #354b68;border-radius:10px;padding:13px;font-size:15px}
.small{font-size:12px;color:#9eacc4;line-height:1.9}
.item{padding:12px;border-bottom:1px solid #293b55;line-height:1.8}
.hidden{display:none}
h3{margin-top:5px}
footer{text-align:center;color:#8293ad;font-size:11px;padding:22px}
#installBtn{background:#167b65}

.codebox{background:#080f1c;border:1px solid #36516f;border-radius:11px;margin:12px 0;overflow:hidden;direction:ltr}
.codehead{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#192b42;color:#a9c8ed;font-size:12px}
.copybtn{padding:7px 13px;background:#286bb4;border-radius:7px;font-size:12px}
.codebox pre{margin:0;padding:14px;overflow-x:auto;white-space:pre;direction:ltr;text-align:left;color:#d9edff;font-size:13px;line-height:1.7}

.trace-label{font-weight:bold;color:#83c5ff;margin-bottom:7px;font-size:13px}
.voice-controls{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.voice-controls button{flex:1;min-width:90px}
#voiceStatus{margin-top:7px}
</style>
</head>
<body>
<header>
 <div class="logo">✦ NOVA</div>
 <div class="sub">دستیار هوش مصنوعی شخصی شما | نسخه 0.5 PWA</div>
 <button id="installBtn" class="hidden" style="margin-top:12px">نصب NOVA</button>
 <div class="small">در iPhone از منوی Share مرورگر، گزینه Add to Home Screen را انتخاب کنید.</div>
</header>
<main>
 <div class="status">
 وضعیت سرور: <span class="green" id="status">در حال بررسی...</span>
 <div class="small" id="providerStatus">وضعیت درگاه هوش مصنوعی: در حال بررسی...</div>
 <div class="small" id="modelStatus">وضعیت مدل: در حال بررسی...</div>
</div>
 <div class="tabs">
  <button class="tab active" onclick="showTab('chatTab',this)">گفت‌وگو</button>
  <button class="tab" onclick="showTab('memoryTab',this)">حافظه</button>
  <button class="tab" onclick="showTab('teamTab',this)">تیم هوش</button>
 </div>
 <section id="chatTab" class="panel">
  <h3>گفت‌وگو با NOVA</h3>
  <div id="chat"><div class="msg bot">سلام! من NOVA هستم. چطور می‌توانم کمک کنم؟</div></div>
  <div class="inputrow">
   <input id="question" placeholder="پیام خود را بنویس..." onkeydown="if(event.key==='Enter')send()">
   <button onclick="send()">ارسال</button>
  </div>
  <div class="voice-controls">
   <button id="voiceToggle" onclick="toggleVoice()">فعال‌سازی صدا</button>
   <button id="micBtn" onclick="startListening()">🎙 صحبت</button>
   <button id="stopVoiceBtn" onclick="stopVoice()">قطع صدا</button>
  </div>
  <div id="voiceStatus" class="small">قابلیت صوتی آماده بررسی است.</div>
  <p class="small">پاسخ‌ها از طریق مدل هوش مصنوعی متصل‌شده تولید می‌شوند.</p>
 </section>
 <section id="memoryTab" class="panel hidden">
  <h3>حافظه بلندمدت NOVA</h3>
  <div class="inputrow">
   <input id="note" placeholder="یادداشت جدید...">
   <button onclick="saveNote()">ذخیره</button>
  </div>
  <div id="notes" class="small" style="margin-top:15px">در حال بارگذاری...</div>
  <button onclick="loadMemory()" style="margin-top:12px">تازه‌سازی حافظه</button>
 </section>
 <section id="teamTab" class="panel hidden">
  <h3>معماری تیم هوش NOVA</h3>
  <div class="item">۱. معمار مسئله — تقسیم مسئله به بخش‌ها</div>
  <div class="item">۲. پژوهشگر — یافتن اطلاعات</div>
  <div class="item">۳. متخصص — بررسی تخصصی موضوع</div>
  <div class="item">۴. استدلال‌گر — تحلیل و نتیجه‌گیری</div>
  <div class="item">۵. منتقد مستقل — یافتن ایرادها</div>
  <div class="item">۶. داور شواهد — ارزیابی اعتبار اطلاعات</div>
  <div class="item">۷. تصمیم‌گیرنده — جمع‌بندی نهایی</div>
  <p class="small">این بخش فعلاً نمایش معماری تیم است؛ عامل‌های مستقل هنوز پیاده‌سازی نشده‌اند.</p>
 </section>
</main>
<footer>NOVA — Truth, Intelligence, Evolution</footer>
<script>
function showTab(id,btn){
 document.querySelectorAll('main section').forEach(x=>x.classList.add('hidden'));
 document.getElementById(id).classList.remove('hidden');
 document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
 btn.classList.add('active');
 if(id==='memoryTab')loadMemory();
}
function addMessage(text,kind){
 const box=document.getElementById('chat');
 const div=document.createElement('div');
 div.className='msg '+kind;div.textContent=text;
 box.appendChild(div);box.scrollTop=box.scrollHeight;
}

function renderBotMessage(target,text){
 target.textContent='';
 const pattern=/```([^\n`]*)\n([\s\S]*?)```/g;
 let last=0,match;
 function prose(value){
  if(!value)return;
  const d=document.createElement('div');
  d.textContent=value;
  target.appendChild(d);
 }
 while((match=pattern.exec(text))!==null){
  prose(text.slice(last,match.index));
  const box=document.createElement('div');
  box.className='codebox';
  const head=document.createElement('div');
  head.className='codehead';
  const lang=document.createElement('span');
  lang.textContent=match[1].trim()||'CODE';
  const copy=document.createElement('button');
  copy.className='copybtn';
  copy.textContent='کپی کد';
  const pre=document.createElement('pre');
  const code=document.createElement('code');
  code.textContent=match[2].replace(/\n$/,'');
  pre.appendChild(code);
  copy.onclick=async()=>{
   try{
    await navigator.clipboard.writeText(code.textContent);
   }catch(e){
    const area=document.createElement('textarea');
    area.value=code.textContent;
    document.body.appendChild(area);
    area.select();
    document.execCommand('copy');
    area.remove();
   }
   copy.textContent='کپی شد ✓';
   setTimeout(()=>copy.textContent='کپی کد',1600);
  };
  head.append(lang,copy);
  box.append(head,pre);
  target.appendChild(box);
  last=pattern.lastIndex;
 }
 prose(text.slice(last));
 target.scrollIntoView({block:'nearest'});
}

async function send(){
 const input=document.getElementById('question');
 const q=input.value.trim();if(!q)return;
 input.value='';addMessage(q,'user');
 const wait=document.createElement('div');
 wait.className='msg bot';wait.textContent='NOVA در حال فکر کردن است...';
 document.getElementById('chat').appendChild(wait);
 try{
  const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:q})});
  const d=await r.json();
  if(d.success){
   wait.remove();
   const answerCard=document.createElement('div');
   answerCard.className='msg bot';
   const answerLabel=document.createElement('div');
   answerLabel.className='trace-label';
   answerLabel.textContent='NOVA | پاسخ نهایی';
   const answerBody=document.createElement('div');
   answerCard.append(answerLabel,answerBody);
   document.getElementById('chat').appendChild(answerCard);
   renderBotMessage(answerBody,d.answer||'پاسخ اصلی از سرور دریافت نشد.');
    if(voiceEnabled) speakAnswer(d.answer||'پاسخ دریافت نشد.');
   if(d.runtime_identity){
    const info=d.runtime_identity;
    const identityCard=document.createElement('div');
    identityCard.className='msg bot';
    const identityLabel=document.createElement('div');
    identityLabel.className='trace-label';
    identityLabel.textContent='NOVA | هویت فنی اتصال';
    const identityBody=document.createElement('div');
    identityBody.style.whiteSpace='pre-wrap';
    identityBody.textContent=
     'ارائه‌دهنده: '+(info.provider||'نامشخص')+'\\n'+
     'مدل تنظیم‌شده: '+(info.configured_model||'نامشخص')+'\\n'+
     'مدل گزارش‌شده توسط سرویس: '+(info.reported_model||'دریافت نشده')+'\\n'+
     'وضعیت شناسه: '+(info.model_status||'نامشخص');
    identityCard.append(identityLabel,identityBody);
    document.getElementById('chat').appendChild(identityCard);
   }


   (d.trace||[]).forEach(item=>{
    const card=document.createElement('div');
    card.className='msg bot';
    const label=document.createElement('div');
    label.className='trace-label';
    label.textContent=item.speaker;
    const body=document.createElement('div');
    card.append(label,body);
    document.getElementById('chat').appendChild(card);
    renderBotMessage(body,item.text||'');
   });
  }else wait.textContent='خطا: '+(d.message||'پاسخی دریافت نشد');
 }catch(e){wait.textContent='ارتباط با سرور NOVA برقرار نیست.'}
}

let voiceEnabled=false;
let recognition=null;
let listening=false;

const voiceToggle=document.getElementById('voiceToggle');
const micBtn=document.getElementById('micBtn');
const voiceStatus=document.getElementById('voiceStatus');
const SpeechRecognitionAPI=window.SpeechRecognition||window.webkitSpeechRecognition;

function setVoiceStatus(message){
 if(voiceStatus) voiceStatus.textContent=message;
}

function toggleVoice(){
 voiceEnabled=!voiceEnabled;
 if(voiceToggle) voiceToggle.textContent=voiceEnabled?'صدای پاسخ روشن است':'فعال‌سازی صدا';
 if(!voiceEnabled){
  if('speechSynthesis' in window) window.speechSynthesis.cancel();
  setVoiceStatus('پخش خودکار پاسخ خاموش شد.');
 }else{
  setVoiceStatus('صدای پاسخ فعال شد. برای صحبت، دکمه میکروفون را بزن.');
 }
}

function stopVoice(){
 if('speechSynthesis' in window) window.speechSynthesis.cancel();
 if(recognition && listening){
  try{recognition.stop();}catch(e){}
 }
 setVoiceStatus('پخش صدا متوقف شد.');
}

function speakAnswer(text){
 if(!voiceEnabled || !('speechSynthesis' in window)) return;

 const clean=String(text||'')
  .replace(/```[\s\S]*?```/g,' بخش کد ')
  .replace(/\[([^\]]+)\]\([^)]+\)/g,'$1')
  .replace(/https?:\/\/\S+/g,'')
  .replace(/[*_#>`~]/g,'')
  .trim();

 if(!clean) return;

 window.speechSynthesis.cancel();
 const utterance=new SpeechSynthesisUtterance(clean);
 utterance.lang='fa-IR';
 utterance.rate=0.96;
 utterance.pitch=0.95;
 utterance.volume=1;

 const voices=window.speechSynthesis.getVoices();
 const persianVoice=voices.find(v=>/^fa(-|$)/i.test(v.lang));
 if(persianVoice) utterance.voice=persianVoice;

 utterance.onstart=()=>setVoiceStatus('نوا در حال صحبت است...');
 utterance.onend=()=>setVoiceStatus('پاسخ صوتی تمام شد.');
 utterance.onerror=()=>setVoiceStatus('پخش صدا با مشکل روبه‌رو شد.');

 window.speechSynthesis.speak(utterance);
}

function startListening(){
 if(!SpeechRecognitionAPI){
  setVoiceStatus('مرورگر فعلی از تشخیص گفتار پشتیبانی نمی‌کند.');
  return;
 }

 if(listening){
  try{recognition.stop();}catch(e){}
  return;
 }

 voiceEnabled=true;
 if(voiceToggle) voiceToggle.textContent='صدای پاسخ روشن است';

 recognition=new SpeechRecognitionAPI();
 recognition.lang='fa-IR';
 recognition.continuous=false;
 recognition.interimResults=false;
 recognition.maxAlternatives=1;

 recognition.onstart=()=>{
  listening=true;
  if(micBtn) micBtn.textContent='در حال شنیدن...';
  setVoiceStatus('نوا گوش می‌دهد. صحبت کن.');
 };

 recognition.onresult=(event)=>{
  const transcript=event.results[0][0].transcript.trim();
  if(!transcript){
   setVoiceStatus('گفتار تشخیص داده نشد. دوباره تلاش کن.');
   return;
  }
  document.getElementById('question').value=transcript;
  setVoiceStatus('گفتار دریافت شد؛ نوا در حال آماده‌سازی پاسخ است.');
  send();
 };

 recognition.onerror=(event)=>{
  setVoiceStatus('خطای میکروفون یا تشخیص گفتار: '+event.error);
 };

 recognition.onend=()=>{
  listening=false;
  if(micBtn) micBtn.textContent='🎙 صحبت';
 };

 try{
  recognition.start();
 }catch(e){
  listening=false;
  setVoiceStatus('شروع میکروفون ممکن نشد. دوباره امتحان کن.');
 }
}

if(!SpeechRecognitionAPI){
 micBtn.disabled=true;
 micBtn.title='تشخیص گفتار در این مرورگر پشتیبانی نمی‌شود';
 setVoiceStatus('تشخیص گفتار در این مرورگر در دسترس نیست؛ پخش صدا ممکن است کار کند.');
}else{
 setVoiceStatus('میکروفون آماده است؛ برای شروع صحبت دکمه را بزن.');
}

async function loadMemory(){
 const box=document.getElementById('notes');
 try{
  const r=await fetch('/api/memory');const d=await r.json();
  box.innerHTML='';
  const notes=d.user_notes||[];
  if(!notes.length){box.textContent='هنوز یادداشتی ذخیره نشده است.';return}
  notes.forEach(n=>{
   const row=document.createElement('div');row.className='item';
   const t=document.createElement('span');t.textContent=n+' ';
   const b=document.createElement('button');b.textContent='حذف';
   b.onclick=()=>deleteNote(n);row.append(t,b);box.appendChild(row);
  });
 }catch(e){box.textContent='خطا در خواندن حافظه'}
}
async function saveNote(){
 const input=document.getElementById('note');const n=input.value.trim();
 if(!n)return;
 try{
  await fetch('/api/remember',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note:n})});
  input.value='';loadMemory();
 }catch(e){alert('ارتباط با NOVA برقرار نیست')}
}
async function deleteNote(n){
 await fetch('/api/forget',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note:n})});
 loadMemory();
}
fetch('/api/status').then(r=>r.json()).then(d=>{
  document.getElementById('status').textContent =
   d.server_online ? 'روشن' : 'خاموش';

  document.getElementById('providerStatus').textContent =
   d.provider_configured
    ? 'درگاه OpenRouter پیکربندی شده؛ اتصال زنده هنوز آزمایش نشده'
    : 'تنظیمات درگاه یا کلید API کامل نیست';

  document.getElementById('modelStatus').textContent =
   'مدل: '+(d.model || 'نامشخص')+' | اتصال واقعی: آزمایش نشده';
 }).catch(()=>{
  document.getElementById('status').textContent='نامشخص';
  document.getElementById('providerStatus').textContent='وضعیت درگاه قابل دریافت نیست';
  document.getElementById('modelStatus').textContent='وضعیت مدل قابل دریافت نیست';
 });

let installPrompt;
const installBtn=document.getElementById('installBtn');
window.addEventListener('beforeinstallprompt',e=>{
 e.preventDefault();installPrompt=e;installBtn.classList.remove('hidden');
});
installBtn.addEventListener('click',async()=>{
 if(!installPrompt)return;
 installPrompt.prompt();await installPrompt.userChoice;
 installPrompt=null;installBtn.classList.add('hidden');
});
if('serviceWorker' in navigator){
 window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def send_data(self, data, content_type="application/json; charset=utf-8"):
        if isinstance(data, bytes):
            raw = data
        elif isinstance(data, str):
            raw = data.encode("utf-8")
        else:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(raw)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            print("NOVA: مرورگر پیش از دریافت پاسخ، ارتباط را قطع کرد.")


    def read_data(self):
        size = int(self.headers.get("Content-Length", 0))
        if size > 100000:
            raise ValueError("درخواست بیش از حد بزرگ است")
        return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self):
        if self.path == "/":
            self.send_data(PAGE, "text/html; charset=utf-8")
        elif self.path == "/manifest.webmanifest":
            self.send_data(MANIFEST, "application/manifest+json; charset=utf-8")
        elif self.path == "/sw.js":
            self.send_data(SERVICE_WORKER, "application/javascript; charset=utf-8")
        elif self.path in ("/icon-192.png", "/icon-512.png"):
            size = 192 if "192" in self.path else 512
            self.send_data((WEB / f"icon-{size}.png").read_bytes(), "image/png")
        elif self.path == "/api/memory":
            self.send_data(load())
        elif self.path == "/api/status":
            from core.ai.config import AI_CONFIG
            from core.ai.multimodel import PRIMARY_MODEL

            key_configured = bool(str(AI_CONFIG.get("api_key") or "").strip())
            url_configured = bool(str(AI_CONFIG.get("openrouter_url") or "").strip())

            self.send_data({
                "online": True,
                "server_online": True,
                "name": "NOVA",
                "provider": "OpenRouter",
                "provider_configured": key_configured and url_configured,
                "model": PRIMARY_MODEL or "openrouter/free",
                "model_verified": False,
                "model_status": "not_tested"
            })
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            data = self.read_data()
            if not isinstance(data, dict):
                raise ValueError("ساختار درخواست نامعتبر است")
            if self.path == "/api/chat":
                prompt = str(data.get("prompt", "")).strip()
                if not prompt:
                    return self.send_data({"success": False, "message": "پیام خالی است"})
                if len(prompt) > 8000:
                    return self.send_data({"success": False, "message": "پیام بیش از حد طولانی است"})
                nova_request = team_engine.build_team_prompt(prompt)
                result = run_multimodel(nova_request, gateway=gateway)
                self.send_data(result)
            elif self.path == "/api/remember":
                note = str(data.get("note", "")).strip()
                if not note:
                    return self.send_data({"success": False, "message": "یادداشت خالی است"})
                if len(note) > 2000:
                    return self.send_data({"success": False, "message": "یادداشت بیش از حد طولانی است"})
                remember(note)
                self.send_data({"success": True})
            elif self.path == "/api/forget":
                note = str(data.get("note", "")).strip()
                self.send_data({"success": forget(note)})
            else:
                self.send_error(404)
        except Exception:
            self.send_data({"success": False, "message": "در پردازش درخواست خطایی رخ داد"})

    def log_message(self, format, *args):
        pass

WEB = __import__("pathlib").Path(__file__).resolve().parent.parent / "web"

MANIFEST = {
    "id": "/",
    "name": "NOVA AI",
    "short_name": "NOVA",
    "description": "دستیار هوش مصنوعی NOVA",
    "lang": "fa",
    "dir": "rtl",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "background_color": "#0c1220",
    "theme_color": "#0c1220",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
    ]
}

SERVICE_WORKER = """
const CACHE = 'nova-pwa-v1';
const ASSETS = ['/', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png'];
self.addEventListener('install', event => {
 event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
 self.skipWaiting();
});
self.addEventListener('activate', event => {
 event.waitUntil(caches.keys().then(keys =>
  Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
 ));
 self.clients.claim();
});
self.addEventListener('fetch', event => {
 const url = new URL(event.request.url);
 if (url.origin !== self.location.origin) return;
 if (url.pathname.startsWith('/api/')) return;
 event.respondWith(fetch(event.request).catch(() =>
  caches.match(event.request).then(r => r || caches.match('/'))
 ));
});
"""

_http_server = None
_server_thread = None
_server_lock = threading.Lock()

def start_server():
    global _http_server, _server_thread
    with _server_lock:
        if _server_thread is not None and _server_thread.is_alive():
            return
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
        except OSError:
            import urllib.request
            try:
                with urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=2) as response:
                    status = json.loads(response.read().decode("utf-8"))
                    if status.get("name") == "NOVA" and status.get("server_online"):
                        return
            except Exception:
                pass
            raise
        server.daemon_threads = True
        thread = threading.Thread(
            target=server.serve_forever,
            name="NOVA-HTTP",
            daemon=True
        )
        _http_server = server
        _server_thread = thread
        thread.start()

def stop_server():
    global _http_server, _server_thread
    with _server_lock:
        server = _http_server
        thread = _server_thread
        if server is None:
            return
        server.shutdown()
        if thread is not None:
            thread.join(timeout=3)
        server.server_close()
        _http_server = None
        _server_thread = None

if __name__ == "__main__":
    import threading
    start_server()
    print("NOVA PWA starting...")
    print("Open: http://127.0.0.1:8765")
    try:
        _server_thread.join()
    except KeyboardInterrupt:
        stop_server()
