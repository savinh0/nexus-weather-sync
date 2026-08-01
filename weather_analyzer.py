import os
import json
import asyncio
import hashlib
import base64
import random
from datetime import datetime, timedelta
import httpx
from google import genai
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Runtime decryption core ---
_SALT = b"wx_station_v1_salt_2026"

def _dk(key_raw: str) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', key_raw.encode('utf-8'), _SALT, iterations=100_000)

def _dec(blob: str, key_bytes: bytes) -> str:
    raw   = base64.b64decode(blob)
    nonce = raw[:12]
    ct    = raw[12:]
    return AESGCM(key_bytes).decrypt(nonce, ct, None).decode('utf-8')

# --- Encrypted payload (AES-256-GCM) ---
_V = {
    "EP": "oVBuUYDv+5dUuXaqxx4iD1rozzkiWmJ2b4XhbaIe8al/YWYG6doNWFciz9agvNwFfddr3zQgyOVAcbsuvYstpTqsU7zVJdLiYxsNcZ3TSBT9KiNnr4LMEvrsRhbnCnZt6cgxoiefHJciryVTw9zoPc0j3p1MRG/7d9ZuGofN06m4SzappEDqkOKHZRwXcHf3ZFICSINCBKGaeVS6CieiQz5LFw==",
    "FU": "9QbgLBMkvk+xngIdTpXSK7lREsEavUZ1I1td9j3oiKB7Jc6NIMhIs9FCH9qPaU7RR3kLAr8BpDH+4oosNXekG6GKm0CMINI/yjATKzTK/GphbBihb97HE7k7m85EuL8wrn0yC+/cQn0=",
    "TA": "kRUg0JTqbjhg4134m958gWWopEJpa0UXY2xPUon7FGwT5kgFASeh8BfbWsB5kNuijswUsmIpIcDj6qVGiu5dDUZ9+49CAA==",
    "SK": "7aeThYub36I13FvswT7peDiXgZRapGXsEuiyM8vXJ5O6vfjbT3E=",
    "TK": "ohRm7FwQ8OBnmChCF4XwToLjFp51ZEj3eJJutiRNuAGx",
    "OK": "59MhnZhoDqgHHw4hYCHxCaRNfj7Y1+wqmQ3vrKuQAWjaQg==",
    "DK": "GGj4ztXi/BKixRgp7WVpSdf095QD/9VLw/PSG7NM+7EOV4e6fQ==",
    "PK": "L3bu8JgtYxhjaV0/iS4tt07LvAEPCAD1uXZmHZoTFqUqUk9RKdCW8yTw",
    "AK": "+JK8XzdpEQtAzQQs5TyiR1V+L3nyisXh3izKHHlIT51VlFNaCQnS6aHJIg==",
    "CK": "KzJqcUTSVsobXY46RprC+f8DAUtq7AWDC5DrwF3xTBVY3s+N3ihYXnGVkoI=",
    "NV": "MFTfAHku0vgMDx13cxovOUXXy5tJ6+qe5Ks413oHbA==",
    "BT": "9iZmYxHud3Z7FoCWvEVfma1CUZrjdavrurSuuahexY9ALg7hWEFzPk7q",
    "CP": "wttlVjKMmJ9v4XbdiciOZd8VKTD2vIfat5A/U4UIXw==",
    "P1": "BADoxvG/Qi0FVgIAaiCw8AhdYcQZ1Ll+A68OYS3vP5ygzZJGdTkk3t0i8zm4AGmTD7lrX+/fGu6TKryiDjuxHkwgfx1VcoQv64lc99Q/jX0H+P8OBRRSbNeNYqYKAuNLDECLdY/BT1q6C8zLGVYW3Sfa5JOue/eguHxXvxBuKKSqCN1g2lscy4hhOeXLkd3rN6y+sjpxNYO6eMCGv3i1LgXSfybux5IpE2VECkwsKW60UqI9gIG6H4qNH8MCTQJR8c6TItBjsqMt3Ssv7CGwnNUn4WAB1OETKMN1/ZYzFs6W9Mj468Guis7Zz4/WKyxrACQM+CTxswqA7PFn5Kd6/w7XuvGYv0ybpLN++0eyBZm5EBuPrVhukeCJ3XDbYi7wevy4HDMDfoyBnN+lvrZ+LvL3Q2OHsOGjrxJfqwjM6RQXyOEAbgwgJgs5J9aayWuCIKjVnxux+moFTnu0jP/GSsZL936aDj2jgXlLFt9FYjrCvExpZ5wv",
    "P2": "Vv+xdSsd0e58dYzOKFNObO5CAuyAOo9JucQLVQhRBnuuNNIHQIqfltsYVng75FMBnxaJ7sX3xsrfV2UzQlYcs41SgR33iBP+Sf4u3p5vjcOEToX8MfbaF4Goee0lPjw+Q318fvcQD6F5gT4eRixYV7OQO1FePInz7/OD1fjnv99hmy98EFGo0iVandpfMt7Ys6/xdJDHJiA+G8roAvQ8JOM6AffbwY1A8T+rTLCqsS6yEmGE1juaJPaRfozd+f1lUVKUIt7I/xBqQZSEyYF3xvmBNaXsrByR1E/NY6NtVQjpcNP9h5OiIScEJsZejGumCz9czP5qv4iBtCOZg5iRx/WtLvb2zMjOZ7a+u/XL7lWqfipmGQE79GM6Acx4cvvXUBUm8b2ydsfCacFAiKYHN5JOqssLvr+0sTddmXiNT3Mabtww5jgRrVaICxO1Zvk=",
    "FB": "NQb6ZNCTUAy7migLjpznZaJRAMqypPOVeW0VqNLDl7NKtabswlvH8faKVgSLjUfPcowoZpuYdufSv4rF098D18xpq8yqvTmX6dZFMxdFuzBNCpnRS5ZitTxKIvtluuzavOow2UAObSlJKjDp8pU1FFvbYU3zr5ll1dBOukRyG7YvTdbw+U35RUkdycepYzlVns5MtYoutjhnnHH8vdgj",
}

# --- Runtime environment ---
_T1 = os.getenv("TELEGRAM_BOT_TOKEN", "")
_T2 = os.getenv("TELEGRAM_CHAT_ID", "")
_G1 = os.getenv("GEMINI_KEY_1", "")
_G2 = os.getenv("GEMINI_KEY_2", "")
_DK_RAW = os.getenv("DECRYPT_KEY", "")
_SF = "sensor_cache.dat"
_NS = "node_status.dat"

_ME = datetime(2026, 9, 16)
_PS = [_ME, _ME - timedelta(days=1), _ME + timedelta(days=1), _ME + timedelta(days=2)]

# ── State helpers ────────────────────────────────────────────────────────────

def _load_state() -> set:
    if os.path.exists(_SF):
        with open(_SF, "r") as f:
            try: return set(json.load(f))
            except: pass
    return set()

def _flush_state(s: set):
    with open(_SF, "w") as f:
        json.dump(list(s), f)

def _load_node() -> dict:
    default = {"consecutive_failures": 0, "blocked_until": None, "block_notified": False}
    if os.path.exists(_NS):
        with open(_NS, "r") as f:
            try: return {**default, **json.load(f)}
            except: pass
    return default

def _flush_node(n: dict):
    with open(_NS, "w") as f:
        json.dump(n, f)

def _chk(a: str, b: str, c: str) -> str:
    return hashlib.md5(f"{a}_{b}_{c}".encode()).hexdigest()

# ── Telegram direct send (sem bot lib) ──────────────────────────────────────

async def _tg_send(client: httpx.AsyncClient, kbytes: bytes, text: str):
    if not (_T1 and _T2):
        return
    try:
        tg = _dec(_V["TA"], kbytes).format(_T1)
        await client.post(tg, json={"chat_id": _T2, "text": text, "parse_mode": "HTML"})
    except Exception:
        pass

# ── AI agents ────────────────────────────────────────────────────────────────

def _synth(client, kbytes: bytes, data: dict, d: str, h: str, v: str) -> str:
    p = _dec(_V["P1"], kbytes).format(json.dumps(data, ensure_ascii=False), d, h, v)
    return client.models.generate_content(model='gemini-3.5-flash-lite', contents=p).text.strip()

def _audit(client, kbytes: bytes, data: dict, d: str, h: str, v: str, msg: str) -> bool:
    p = _dec(_V["P2"], kbytes).format(d, h, v, json.dumps(data, ensure_ascii=False), msg)
    return client.models.generate_content(model='gemini-3.5-flash-lite', contents=p).text.strip() == "1"

# ── Core fetch ───────────────────────────────────────────────────────────────

async def _fetch(target: datetime, c1, c2, kbytes: bytes, node: dict, http: httpx.AsyncClient) -> bool:
    """Retorna False se houver falha de rede/bloqueio, True caso contrário."""
    ud  = target.strftime("%Y-%m-%d")
    dd  = target.strftime("%d/%m/%Y")
    url = _dec(_V["EP"], kbytes).format(ud)

    try:
        resp = await http.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15.0)

        if resp.status_code in (403, 429, 503):
            return False  # sinaliza falha para contabilizar

        if resp.status_code != 200:
            return True  # outro erro, ignora sem contabilizar

        data     = resp.json()
        samples  = data.get(_dec(_V["SK"], kbytes), []) + data.get(_dec(_V["TK"], kbytes), [])
        states   = _load_state()
        modified = False

        for s in samples:
            try:
                raw_dt = s[_dec(_V["OK"], kbytes)][_dec(_V["DK"], kbytes)]
                dt_obj = datetime.fromisoformat(raw_dt)
                hm     = dt_obj.strftime("%H:%M")
                price  = f"{_dec(_V['CP'], kbytes)}{s[_dec(_V['PK'], kbytes)]:.2f}"
                seats  = s.get(_dec(_V["AK"], kbytes), _dec(_V["NV"], kbytes))
                cls    = s.get(_dec(_V["CK"], kbytes), "").strip(".")
                cid    = _chk(dd, hm, price)

                if cid not in states:
                    front   = _dec(_V["FU"], kbytes).format(ud)
                    msg_out = None

                    for _ in range(3):
                        ai = await asyncio.to_thread(_synth, c1, kbytes, s, dd, hm, price)
                        ok = await asyncio.to_thread(_audit, c2, kbytes, s, dd, hm, price, ai)
                        if ok:
                            lnk     = f"\n\n🔗 <a href='{front}'>{_dec(_V['BT'], kbytes)}</a>"
                            msg_out = ai + lnk
                            break

                    if not msg_out:
                        msg_out = _dec(_V["FB"], kbytes).format(dd, hm, cls, price, seats, front)

                    await _tg_send(http, kbytes, msg_out)
                    states.add(cid)
                    modified = True
            except Exception:
                pass

        if modified:
            _flush_state(states)

        return True  # sucesso

    except Exception:
        return False  # falha de rede

# ── Main ─────────────────────────────────────────────────────────────────────

async def _run():
    if not (_T1 and _G1 and _G2 and _DK_RAW):
        return

    kbytes = _dk(_DK_RAW)
    node   = _load_node()

    async with httpx.AsyncClient() as http:

        # ── Verificar se está em modo de bloqueio ──────────────────────────
        if node["blocked_until"]:
            blocked_until_dt = datetime.fromisoformat(node["blocked_until"])
            if datetime.utcnow() < blocked_until_dt:
                # Ainda bloqueado — notifica uma única vez
                if not node["block_notified"]:
                    resume_str = blocked_until_dt.strftime("%d/%m/%Y às %H:%Mh (UTC)")
                    msg = (
                        f"⛔ <b>Monitoramento suspenso temporariamente</b>\n"
                        f"O nó de diagnóstico detectou 3 falhas consecutivas de acesso.\n"
                        f"Retomada prevista: <b>{resume_str}</b>"
                    )
                    await _tg_send(http, kbytes, msg)
                    node["block_notified"] = True
                    _flush_node(node)
                return
            else:
                # Bloqueio expirou — reseta e notifica retomada
                node["consecutive_failures"] = 0
                node["blocked_until"] = None
                node["block_notified"] = False
                _flush_node(node)
                await _tg_send(http, kbytes,
                    "✅ <b>Monitoramento retomado</b>\nO período de pausa terminou. Voltando a operar normalmente.")

        # ── Execução normal ────────────────────────────────────────────────
        c1 = genai.Client(api_key=_G1)
        c2 = genai.Client(api_key=_G2)

        for dt in _PS:
            success = await _fetch(dt, c1, c2, kbytes, node, http)

            if not success:
                node["consecutive_failures"] += 1
                _flush_node(node)

                if node["consecutive_failures"] >= 3:
                    # Bloqueia por 2 horas
                    blocked_until = datetime.utcnow() + timedelta(hours=2)
                    node["blocked_until"] = blocked_until.isoformat()
                    node["block_notified"] = False
                    _flush_node(node)

                    resume_str = blocked_until.strftime("%d/%m/%Y às %H:%Mh (UTC)")
                    await _tg_send(http, kbytes,
                        f"⚠️ <b>3 falhas consecutivas detectadas!</b>\n"
                        f"O sistema entrou em modo de espera por 2 horas para evitar sobrecarga.\n"
                        f"Retomada prevista: <b>{resume_str}</b>"
                    )
                    return
            else:
                # Sucesso: reseta o contador de falhas
                if node["consecutive_failures"] > 0:
                    node["consecutive_failures"] = 0
                    _flush_node(node)

            await asyncio.sleep(2)

        # ── Data histórica aleatória ───────────────────────────────────────
        today    = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt   = _ME - timedelta(days=2)
        historic = []
        cur      = today
        while cur <= end_dt:
            historic.append(cur)
            cur += timedelta(days=1)

        if historic:
            await _fetch(random.choice(historic), c1, c2, kbytes, node, http)

if __name__ == "__main__":
    asyncio.run(_run())
