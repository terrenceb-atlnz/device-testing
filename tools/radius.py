#!/usr/bin/env python3
"""RADIUS (RFC 2865 / 2866) packet library -- build, parse and verify, in pure Python.

The one home for the RADIUS wire format in this repo.  `radsend.py` (client),
`radsrv.py` (server) and `radwire.py` (pcap decoder) all import it, so the
encoding used to SEND a packet is the same code that DECODES it off the wire.

Nothing here needs root, scapy, or a RADIUS package on the box.

What it covers:
  * the header (code, id, length, 16-byte authenticator) and the attribute TLVs;
  * PAP User-Password hiding/unhiding (RFC 2865 s5.2);
  * the Request Authenticator of an Accounting-Request (RFC 2866 s3);
  * the Response Authenticator of a reply (RFC 2865 s3) -- the check that proves
    the responder holds the shared secret, which no `show` command can prove;
  * Message-Authenticator (RFC 3579 s3.2), HMAC-MD5, built and verified.

Running this file directly runs a self-test of the codec (no network).
"""
import hashlib
import hmac
import os
import struct

CODES = {1: "Access-Request", 2: "Access-Accept", 3: "Access-Reject",
         4: "Accounting-Request", 5: "Accounting-Response", 11: "Access-Challenge",
         12: "Status-Server", 13: "Status-Client", 40: "Disconnect-Request",
         41: "Disconnect-ACK", 42: "Disconnect-NAK", 43: "CoA-Request",
         44: "CoA-ACK", 45: "CoA-NAK"}

# Attribute types we name when printing.  Everything else prints as its number.
ATTRS = {1: "User-Name", 2: "User-Password", 3: "CHAP-Password", 4: "NAS-IP-Address",
         5: "NAS-Port", 6: "Service-Type", 7: "Framed-Protocol", 8: "Framed-IP-Address",
         11: "Filter-Id", 18: "Reply-Message", 24: "State", 25: "Class",
         26: "Vendor-Specific", 27: "Session-Timeout", 28: "Idle-Timeout",
         29: "Termination-Action", 30: "Called-Station-Id", 31: "Calling-Station-Id",
         32: "NAS-Identifier", 33: "Proxy-State", 40: "Acct-Status-Type",
         41: "Acct-Delay-Time", 42: "Acct-Input-Octets", 43: "Acct-Output-Octets",
         44: "Acct-Session-Id", 45: "Acct-Authentic", 46: "Acct-Session-Time",
         47: "Acct-Input-Packets", 48: "Acct-Output-Packets", 49: "Acct-Terminate-Cause",
         50: "Acct-Multi-Session-Id", 55: "Event-Timestamp", 61: "NAS-Port-Type",
         64: "Tunnel-Type", 65: "Tunnel-Medium-Type", 79: "EAP-Message",
         80: "Message-Authenticator", 81: "Tunnel-Private-Group-Id", 87: "NAS-Port-Id"}

STRING_ATTRS = {1, 11, 18, 25, 30, 31, 32, 33, 44, 50, 81, 87}
INT_ATTRS = {5, 6, 7, 27, 28, 29, 40, 41, 42, 43, 45, 46, 47, 48, 49, 55, 61, 64, 65}
IP_ATTRS = {4, 8}

SERVICE_TYPE = {1: "Login", 2: "Framed", 6: "Administrative", 7: "NAS-Prompt",
                8: "Authenticate-Only", 10: "Call-Check"}
ACCT_STATUS = {1: "Start", 2: "Stop", 3: "Interim-Update", 7: "Accounting-On",
               8: "Accounting-Off"}


# ------------------------------------------------------------------ attributes
def attr(typ, value):
    """One attribute TLV.  `value` is bytes, str, int or a dotted IPv4 string."""
    if isinstance(value, str):
        if typ in IP_ATTRS:
            value = bytes(int(x) for x in value.split("."))
        else:
            value = value.encode("utf-8")
    elif isinstance(value, int):
        value = struct.pack(">I", value)
    if len(value) > 253:
        raise ValueError("attribute %d too long (%d)" % (typ, len(value)))
    return bytes([typ, len(value) + 2]) + value


def pack_attrs(items):
    """items: a list of (type, value) pairs, in order."""
    return b"".join(attr(t, v) for t, v in items)


def parse_attrs(buf):
    """Return [(type, raw_value_bytes), ...].  Raises ValueError if malformed."""
    out, i = [], 0
    while i < len(buf):
        if i + 2 > len(buf):
            raise ValueError("truncated attribute header at %d" % i)
        t, ln = buf[i], buf[i + 1]
        if ln < 2 or i + ln > len(buf):
            raise ValueError("bad attribute length %d at %d" % (ln, i))
        out.append((t, buf[i + 2:i + ln]))
        i += ln
    return out


def attr_name(t):
    return ATTRS.get(t, "Attr-%d" % t)


def show_value(t, v):
    """A readable rendering of one attribute value, for logs and the pcap decoder."""
    if t in IP_ATTRS and len(v) == 4:
        return ".".join(str(b) for b in v)
    if t in INT_ATTRS and len(v) == 4:
        n = struct.unpack(">I", v)[0]
        if t == 6:
            return "%d(%s)" % (n, SERVICE_TYPE.get(n, "?"))
        if t == 40:
            return "%d(%s)" % (n, ACCT_STATUS.get(n, "?"))
        return str(n)
    if t in STRING_ATTRS:
        try:
            return repr(v.decode("utf-8"))
        except UnicodeDecodeError:
            pass
    return "0x" + v.hex()


def find(attrs, typ):
    """First value of `typ`, or None."""
    for t, v in attrs:
        if t == typ:
            return v
    return None


# ------------------------------------------------------------------ crypto
def pap_hide(password, secret, authenticator):
    """RFC 2865 s5.2 -- the User-Password attribute value."""
    pw = password.encode("utf-8")
    pw += b"\x00" * ((16 - len(pw) % 16) % 16) if len(pw) % 16 else b""
    if not pw:
        pw = b"\x00" * 16
    out, last = b"", authenticator
    for off in range(0, len(pw), 16):
        b = hashlib.md5(secret.encode("utf-8") + last).digest()
        c = bytes(x ^ y for x, y in zip(pw[off:off + 16], b))
        out += c
        last = c
    return out


def pap_unhide(hidden, secret, authenticator):
    """The inverse: recover the plaintext password a client hid with the same secret."""
    out, last = b"", authenticator
    for off in range(0, len(hidden), 16):
        c = hidden[off:off + 16]
        b = hashlib.md5(secret.encode("utf-8") + last).digest()
        out += bytes(x ^ y for x, y in zip(c, b))
        last = c
    return out.rstrip(b"\x00").decode("utf-8", "replace")


def response_authenticator(code, ident, body, request_auth, secret):
    """RFC 2865 s3 -- MD5(Code+ID+Length+RequestAuth+Attributes+Secret)."""
    ln = 20 + len(body)
    return hashlib.md5(struct.pack(">BBH", code, ident, ln) + request_auth
                       + body + secret.encode("utf-8")).digest()


def acct_request_authenticator(ident, body, secret):
    """RFC 2866 s3 -- the Request Authenticator of an Accounting-Request."""
    ln = 20 + len(body)
    return hashlib.md5(struct.pack(">BBH", 4, ident, ln) + b"\x00" * 16
                       + body + secret.encode("utf-8")).digest()


def message_authenticator(code, ident, auth, body, secret):
    """RFC 3579 s3.2 -- HMAC-MD5 over the packet with the M-A value zeroed."""
    ln = 20 + len(body)
    return hmac.new(secret.encode("utf-8"),
                    struct.pack(">BBH", code, ident, ln) + auth + body,
                    hashlib.md5).digest()


# ------------------------------------------------------------------ packets
def build(code, ident, authenticator, attrs):
    body = pack_attrs(attrs) if not isinstance(attrs, (bytes, bytearray)) else bytes(attrs)
    return struct.pack(">BBH", code, ident, 20 + len(body)) + authenticator + body


def parse(data):
    """Return (code, id, authenticator, body_bytes).  Raises ValueError if malformed."""
    if len(data) < 20:
        raise ValueError("short RADIUS packet (%d bytes)" % len(data))
    code, ident, ln = struct.unpack(">BBH", data[:4])
    if ln < 20 or ln > len(data):
        raise ValueError("declared length %d, have %d" % (ln, len(data)))
    return code, ident, data[4:20], data[20:ln]


def code_name(c):
    return CODES.get(c, "Code-%d" % c)


def new_authenticator():
    return os.urandom(16)


def add_message_authenticator(code, ident, auth, attrs, secret):
    """Append a correct Message-Authenticator(80) to a list of (type, value) pairs."""
    with_zero = list(attrs) + [(80, b"\x00" * 16)]
    body = pack_attrs(with_zero)
    mac = message_authenticator(code, ident, auth, body, secret)
    return list(attrs) + [(80, mac)]


# ------------------------------------------------------------------ self-test
def _selftest():
    secret, auth = "testing123", bytes(range(16))
    hidden = pap_hide("s3cret-password-longer-than-16", secret, auth)
    assert pap_unhide(hidden, secret, auth) == "s3cret-password-longer-than-16"
    assert pap_unhide(pap_hide("", secret, auth), secret, auth) == ""
    assert pap_unhide(pap_hide("abc", secret, auth), secret, auth) == "abc"
    a = [(1, "bob"), (4, "10.0.0.1"), (6, 1), (2, hidden)]
    pkt = build(1, 7, auth, a)
    code, ident, ra, body = parse(pkt)
    assert (code, ident, ra) == (1, 7, auth)
    got = parse_attrs(body)
    assert find(got, 1) == b"bob" and find(got, 4) == bytes([10, 0, 0, 1])
    assert show_value(6, find(got, 6)) == "1(Login)"
    rbody = pack_attrs([(18, "ok")])
    ra2 = response_authenticator(2, 7, rbody, auth, secret)
    assert len(ra2) == 16
    assert response_authenticator(2, 7, rbody, auth, "wrong") != ra2
    aa = acct_request_authenticator(9, pack_attrs([(40, 1)]), secret)
    assert len(aa) == 16
    ma = add_message_authenticator(1, 7, auth, [(1, "bob")], secret)
    assert ma[-1][0] == 80 and len(ma[-1][1]) == 16
    print("radius.py self-test: OK")


if __name__ == "__main__":
    _selftest()
