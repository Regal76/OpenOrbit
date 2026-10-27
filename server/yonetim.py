"""Panel owner channel for live, server-side actions.

This listener is intentionally separate from chat and the developer control
channel.  It binds only to loopback and accepts a fresh secret passed by the
Panel process when it starts the game server.
"""
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8098
MAX_AMOUNT = 2_000_000_000
HERE = os.path.dirname(os.path.abspath(__file__))
_KNOWN_LOOTS = None


def known_loots():
    """Loot IDs accepted by the server, built from its bundled item tables."""
    global _KNOWN_LOOTS
    if _KNOWN_LOOTS is None:
        data = json.load(open(os.path.join(HERE, 'data', 'istemci_esyalari.json'), encoding='utf8'))
        _KNOWN_LOOTS = {key for key in (data.get('esyalar') or {})
                        if not key.startswith(('shipId_', 'paymentItem_'))}
        server_items = json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))
        for section in ('lazerler', 'lazer_cephane', 'roketler', 'onarim_robotlari', 'hiz_jeneratorleri',
                        'kalkan_jeneratorleri', 'gemiler', 'dronlar', 'formasyonlar', 'dron_tasarimlari',
                        'boosterlar', 'ekstralar', 'savas_esyalari', 'odeme_paketleri'):
            _KNOWN_LOOTS.update(key for key in (server_items.get(section) or {}) if isinstance(key, str) and not key.startswith('_'))
    return _KNOWN_LOOTS


def players(game):
    """Return connected pilots only; offline profiles are never edited here."""
    out = []
    for session in list(getattr(game, 'OTURUMLAR', ())):
        profile = getattr(session, 'profil', None)
        if profile is None:
            continue
        pilot = profile.d.get('pilot', {})
        out.append({'id': str(getattr(profile, 'user_id', '')), 'ad': str(pilot.get('userName', ''))})
    return sorted(out, key=lambda row: row['ad'].casefold())


def _session(game, user_id):
    user_id = str(user_id)
    for session in list(getattr(game, 'OTURUMLAR', ())):
        profile = getattr(session, 'profil', None)
        if profile is not None and str(getattr(profile, 'user_id', '')) == user_id:
            return session
    return None


def grant(game, user_id, loot_id, amount):
    """Give a connected player one known loot entry and announce it globally."""
    loot_id = str(loot_id or '').strip()
    if not loot_id or len(loot_id) > 120:
        raise ValueError('Geçerli bir eşya seçin.')
    if loot_id not in known_loots():
        raise ValueError('Bilinmeyen eşya: %s' % loot_id)
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        raise ValueError('Adet sayı olmalı.')
    if not 1 <= amount <= MAX_AMOUNT:
        raise ValueError('Adet 1 ile %d arasında olmalı.' % MAX_AMOUNT)
    session = _session(game, user_id)
    if session is None:
        raise ValueError('Oyuncu artık bağlı değil.')
    if not getattr(session, 'magaza', None):
        raise RuntimeError('Oyuncu henüz hazır değil.')

    # reward() is the same server-side reward route used by missions and loot.
    messages = list(session.magaza.reward(loot_id, amount) or [])
    session.send(messages + list(session.magaza.money_msgs() or []), quiet=True)
    session.profil.save()
    name = session.profil.d.get('pilot', {}).get('userName', 'oyuncu')
    announcement = 'Sunucu sahibi %s oyuncusuna %s x%d verdi.' % (name, loot_id, amount)
    chat = getattr(game, 'SOHBET', None)
    if chat:
        chat.duyuru(announcement)
    return {'oyuncu': name, 'esya': loot_id, 'adet': amount, 'duyuru': announcement}


class _Handler(BaseHTTPRequestHandler):
    server_version = 'OpenOrbitOwner/1'

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body):
        data = json.dumps(body, ensure_ascii=False).encode('utf8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _allowed(self):
        secret = self.headers.get('X-OpenOrbit-Owner', '')
        return hmac.compare_digest(secret, self.server.owner_secret)

    def do_GET(self):
        if not self._allowed():
            return self._send(403, {'hata': 'yetki'})
        if self.path == '/oyuncular':
            return self._send(200, {'oyuncular': players(self.server.game)})
        return self._send(404, {'hata': 'yok'})

    def do_POST(self):
        if not self._allowed():
            return self._send(403, {'hata': 'yetki'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n).decode('utf8') or '{}')
            if not isinstance(body, dict):
                raise ValueError('JSON nesnesi gerekli.')
            if self.path != '/ver':
                return self._send(404, {'hata': 'yok'})
            return self._send(200, grant(self.server.game, body.get('oyuncu'), body.get('esya'), body.get('adet')))
        except (ValueError, RuntimeError) as exc:
            return self._send(400, {'hata': str(exc)})
        except Exception:
            self.server.game.log('yönetim: eşya verme hatası')
            return self._send(500, {'hata': 'Eşya verilemedi.'})


def start(game, secret, port=PORT):
    """Start the Panel-only management listener if the Panel supplied a secret."""
    if not secret:
        return None
    server = ThreadingHTTPServer(('127.0.0.1', port), _Handler)
    server.game, server.owner_secret = game, secret
    game.log('panel yönetim kanalı: 127.0.0.1:%d' % port)
    import threading
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
