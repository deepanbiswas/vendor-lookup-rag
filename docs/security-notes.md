# Security Overview: CVEs and Resolutions

This document outlines recent critical security vulnerabilities associated with the project's third-party dependencies and the required version baselines to mitigate them.

## 1. Pydantic AI
* **Vulnerability:** **CVE-2026-25580** (High/Critical) – A Server-Side Request Forgery (SSRF) vulnerability existed in Pydantic AI's URL download functionality. When applications accept message history from untrusted sources, attackers can include malicious URLs that cause the server to make HTTP requests to internal network resources, potentially exposing internal services or cloud credentials. 
* **Resolution:** Ensure the project uses **version 1.56.0 or higher**. This release introduces comprehensive SSRF protection, blocking private IP ranges and cloud metadata endpoints by default.

## 2. Streamlit
* **Vulnerability:** **CVE-2026-33682** (Medium/High) – Streamlit Open Source versions prior to 1.54.0 running on Windows hosts have an unauthenticated SSRF vulnerability arising from improper validation of attacker-supplied filesystem paths. Supplying a malicious UNC path can cause the Streamlit server to initiate outbound SMB connections, potentially leaking NTLMv2 credentials. 
* **Resolution:** Ensure the project uses **version 1.54.0 or higher**, which patches this specific vulnerability. Additionally, avoid storing sensitive user data or session tokens in process-wide environment variables to prevent leakage between concurrent users.

## 3. Qdrant
* **Vulnerability:** **CVE-2026-25628** (High) – A path traversal vulnerability existed in the `/logger` endpoint. It allowed attackers with minimal read-only access to append arbitrary content to files on the target system by exploiting an attacker-controlled log file path parameter, potentially leading to configuration tampering or persistence mechanisms. 
* **Resolution:** Ensure the project uses **version 1.16.0 or higher**. The patch implements proper access control and restricts the ability to specify log file paths to the configuration file, preventing runtime manipulation through the API.

## 4. Vendor HTTP API (FastAPI)

* **Surface:** The chat UI talks to a **FastAPI** application (`vendor-api` / `python -m vendor_lookup_rag.api`) over JSON REST (`/v1/chat`, `/v1/health`, `/v1/status`). The dependency stack pins **FastAPI** in [`pyproject.toml`](../pyproject.toml); keep it current with your security process.
* **Deployment posture:** Defaults bind the API to **127.0.0.1** for local development (`VENDOR_LOOKUP_API_HOST` overrides this, e.g. `0.0.0.0` in Docker). There is **no authentication** on these endpoints in the reference setup—they are intended for trusted local or private networks. If you expose the API beyond localhost, add network controls (reverse proxy, mTLS, or application auth) appropriate to your threat model.
* **Related:** Streamlit’s own CVE discussion above applies to the UI process; the API process does not serve Streamlit’s file APIs.
