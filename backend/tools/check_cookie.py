"""
Cek apakah cookie li_at masih valid.
Jalankan: python tools/check_cookie.py
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from playwright.sync_api import sync_playwright

def main():
    li_at = os.getenv("LINKEDIN_LI_AT", "").strip()
    if not li_at:
        print("[FAIL] LINKEDIN_LI_AT tidak ada di .env")
        return

    print(f"Cookie li_at ditemukan, panjang: {len(li_at)} karakter")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
        )
        context.add_cookies([{
            "name": "li_at", "value": li_at,
            "domain": ".linkedin.com", "path": "/",
            "httpOnly": True, "secure": True,
        }])
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        redirects = []
        page.on("response", lambda r: redirects.append((r.status, r.url[:100])))

        print("\nMembuka https://www.linkedin.com/feed/ ...")
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20_000)
            page.wait_for_timeout(2000)
            final_url = page.url
            html_len  = len(page.content())

            print(f"Final URL    : {final_url}")
            print(f"HTML length  : {html_len}")
            print(f"Redirects    : {len(redirects)}")

            if "feed" in final_url and html_len > 5000:
                print("\n[OK] Cookie VALID — LinkedIn feed terbuka!")
            elif "login" in final_url or "authwall" in final_url:
                print("\n[FAIL] Cookie EXPIRED — redirect ke login page")
                print("       Ambil li_at baru dari browser Chrome yang sudah login")
            elif len(redirects) > 5 and all(s == 302 for s, _ in redirects):
                print("\n[FAIL] Cookie EXPIRED — redirect loop terdeteksi")
            else:
                print(f"\n[?] Tidak pasti. Final URL: {final_url}")
                print("    Cek manual apakah LinkedIn feed terbuka normal")

        except Exception as e:
            if "ERR_TOO_MANY_REDIRECTS" in str(e):
                print("\n[FAIL] Cookie EXPIRED — redirect loop (ERR_TOO_MANY_REDIRECTS)")
                print("       Ambil li_at baru dari browser Chrome yang sudah login")
            else:
                print(f"\n[ERROR] {e}")

        browser.close()

if __name__ == "__main__":
    main()