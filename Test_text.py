import requests
import getpass

BASE_URL = "http://localhost:8000"


def manual_login():
    print("=== Manual Login ===")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    r = requests.post(
        f"{BASE_URL}/login",
        json={"username": username, "password": password},
        timeout=15,
    )

    if r.status_code != 200:
        print(f"\n❌ Login failed ({r.status_code})")
        print(r.text)
        return None

    token = r.json()["access_token"]
    print("\n✅ Login successful.")
    return token


def ask_agent(token: str, query: str, user_id: str):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": query, "user_id": user_id}

    r = requests.post(
        f"{BASE_URL}/query",
        json=payload,
        headers=headers,
        timeout=120,
    )
    return r


def main():
    token = manual_login()
    if not token:
        return

    print("\n=== Banking Agent Interactive Mode ===")
    print("Type any banking question.")
    print("Type 'q' to quit.\n")

    while True:
        query = input("Query: ").strip()
        if not query:
            continue
        if query.lower() in {"q", "quit", "exit"}:
            break

        # user_id here maps to your session, not auth
        r = ask_agent(token, query, user_id="user123")

        print(f"\nStatus: {r.status_code}")
        try:
            data = r.json()
            print("\nAgent response:\n" + data.get("response", str(data)))
        except Exception:
            print(r.text)


if __name__ == "__main__":
    main()
