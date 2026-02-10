# LAN Access Troubleshooting

When another device on the same Wi‑Fi cannot reach the server at `http://10.10.11.145:8000/`, work through these checks.

---

## 1. Server bound to all interfaces (0.0.0.0)

**Issue:** If the server is started with `--host 127.0.0.1`, it only accepts connections from this PC. Other devices get "connection refused" or timeouts.

**Check:** On the host machine, in PowerShell:
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, OwningProcess
```
- `LocalAddress` should be **0.0.0.0** (or **::** for IPv6). If it shows **127.0.0.1**, the server is not listening on the LAN.

**Fix:** Restart the server with:
```powershell
cd c:\Dev\polish_art
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## 2. Windows Firewall blocking inbound port 8000

**Issue:** Windows Defender Firewall (or another firewall) often blocks **inbound** connections to new applications. The server works on the host (localhost) but other devices cannot connect.

**Check:** In PowerShell **as Administrator**:
```powershell
Get-NetFirewallRule -DisplayName "*8000*" -ErrorAction SilentlyContinue | Format-Table DisplayName, Enabled, Direction, Action
```
If there is no rule allowing **Inbound** TCP 8000, add one.

**Fix:** Run the project script **as Administrator** (Right‑click PowerShell → "Run as administrator"):
```powershell
cd c:\Dev\polish_art
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\allow_firewall_port_8000.ps1
```
Or add the rule manually:
```powershell
New-NetFirewallRule -DisplayName "Polish Art Server (TCP 8000)" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

---

## 3. Wrong or changing IP address

**Issue:** The host’s IP may change (DHCP). The other user might be using an old or wrong address.

**Check:** On the host, run:
```powershell
ipconfig
```
Under **Wireless LAN adapter Wi‑Fi**, note **IPv4 Address** (e.g. 10.10.11.145). The other device must use **http://THAT_IP:8000/** (e.g. `http://10.10.11.145:8000/`).

---

## 4. Router / access point isolation

**Issue:** Some routers have **AP isolation**, **client isolation**, or **guest network** so that Wi‑Fi clients cannot reach each other. Then even with firewall open and server on 0.0.0.0, other devices still cannot connect.

**Check:** In the router’s admin UI, look for options like:
- "AP Isolation" / "Client Isolation" / "Wireless Isolation"
- "Allow wireless clients to communicate" / "Inter-client communication"

**Fix:** Disable AP/client isolation (or use a network where it’s disabled). If the other user is on a **guest** network, try the **main** Wi‑Fi (or vice versa) to see if the router treats them differently.

---

## 5. Server not running

**Issue:** The server process may have stopped.

**Check:** On the host:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
```
If this fails, the server is not running. Start it (see step 1).

---

## 6. Antivirus or third‑party security software

**Issue:** Security suites (e.g. Norton, McAfee, Kaspersky) can block incoming connections or "server" behavior.

**Check:** Temporarily disable the firewall/network part of the AV or add an exception for Python / port 8000. If LAN access works after that, add a permanent exception.

---

## 7. Other device using wrong URL or cached error

**Issue:** Typo, wrong port, or browser cache showing an old error page.

**Check:** On the other device:
- Use exactly: **http://10.10.11.145:8000/** (replace with the host’s current IPv4 if different).
- Try another browser or private/incognito window.
- Try from the other device’s command line if possible, e.g.:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://10.10.11.145:8000/health
  ```
  A **200** response means the server is reachable.

---

## Quick checklist (host machine)

| Step | Action |
|------|--------|
| 1 | Start server: `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000` |
| 2 | Confirm listening on 0.0.0.0: `Get-NetTCPConnection -LocalPort 8000 -State Listen` |
| 3 | Add firewall rule: run `scripts\allow_firewall_port_8000.ps1` as Administrator |
| 4 | Note IPv4 from `ipconfig` (e.g. 10.10.11.145) |
| 5 | On another device, open **http://YOUR_IPv4:8000/** |

If the host can open `http://10.10.11.145:8000/` in a browser but the other user still cannot, the problem is usually **firewall** (step 3) or **router isolation** (section 4).
