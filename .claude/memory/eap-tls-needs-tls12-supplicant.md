---
name: eap-tls-needs-tls12-supplicant
description: "EAP-TLS from a testbox stalls on TLS 1.3, not on fragmentation; cap the supplicant at TLS 1.2 with a per-process OPENSSL_CONF (no root)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: e1b6a525-1ced-44a8-bded-4e12b6b39c08
  modified: 2026-10-27T22:33:59.313Z
---

An EAP-TLS exchange driven from a testbox with `wpa_supplicant` 2.6 **will not conclude** against
a correct AW+ authenticator. Measured on tb277 against an x960, 2026-10-28.

**The cause is TLS 1.3 alone.** `wpa_supplicant` 2.6 predates TLS 1.3 and RFC 9190, while
OpenSSL 1.1.1 beneath it negotiates TLS 1.3 anyway. The client marks the EAP method Done when it
sends its Finished, then **discards the authenticator's RFC 9190 commitment message**.

**The fix needs no root** — a per-process OpenSSL ceiling:

```bash
printf '[system_default_sect]\nMaxProtocol = TLSv1.2\n' >> /tmp/<run>/openssl-tls12.cnf
tools/tb sudotool <box> <run> wpasup --env OPENSSL_CONF=/tmp/<run>/openssl-tls12.cnf ...
```

`tools/wpasup.py --env` exists for this. **Do not** edit `/etc/ssl/openssl.cnf` — that is root
and hits every other user of the box.

🔴 **Two false leads, both measured and both wrong, so nobody repeats them:**
- **A leaf-only `client_cert` changes nothing.** The flight stays the same size *to the byte*,
  because **OpenSSL rebuilds the client chain from the `ca_cert` verify store**. The CA must
  leave the store too, and even then the exchange still stalls.
- **Fragmentation is not the cause.** The leg that succeeded carried a **two-fragment** client
  flight. Both ends fragment and reassemble correctly in both directions.

`wpa_supplicant` 2.6 has **no `tls_disable_tlsv1_3` network field** — it postdates 2.6, and
adding one breaks the config. EAP-TLS over TLS 1.3 is therefore not measurable with 2.6 at all;
that needs 2.10+, a root install.

Platform behaviour is in `platforms/x960.md` §7K.3. Related: [[scapy-for-traffic-tests]],
[[tb277-x960-auth-security-campaign-2026-10-23]].
