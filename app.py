from flask import Flask, redirect, request, jsonify
import requests

app = Flask(__name__)

# Replace these with your actual app details
APP_ID = "1262689168372475"
APP_SECRET = "bd115fce01ea96818414440eb68bc8eb"
REDIRECT_URI = "https://graphapi-sl3z.onrender.com/callback"
FB_AUTH_URL = "https://www.facebook.com/v17.0/dialog/oauth"
TOKEN_URL = "https://graph.facebook.com/v17.0/oauth/access_token"


@app.route("/")
def home():
    """Step 1: Redirect user to Facebook Authorization URL"""
    auth_url = (
        f"{FB_AUTH_URL}?"
        f"client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope="
        "instagram_basic,instagram_manage_insights,instagram_manage_comments,"
        "pages_show_list,pages_read_engagement&response_type=code"
    )
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Step 2: Handle the callback and exchange code for a short-lived token"""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code not found."})

    # Exchange the authorization code for a short-lived access token
    token_params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "client_secret": APP_SECRET,
        "code": code,
    }
    response = requests.get(TOKEN_URL, params=token_params)

    if response.status_code != 200:
        return jsonify({"error": response.json()})

    short_lived_token = response.json().get("access_token")
    return jsonify({"short_lived_token": short_lived_token})


@app.route("/long_lived_token")
def get_long_lived_token():
    """Step 3: Exchange short-lived token for a long-lived token"""
    short_lived_token = request.args.get("token")  # Pass short-lived token as a query param
    if not short_lived_token:
        return jsonify({"error": "Short-lived token is required."})

    long_lived_params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_lived_token,
    }
    response = requests.get(TOKEN_URL, params=long_lived_params)

    if response.status_code != 200:
        return jsonify({"error": response.json()})

    long_lived_token = response.json().get("access_token")
    return jsonify({"long_lived_token": long_lived_token})


@app.route("/get_media_id")
def get_media_id():
    """Step 4: Fetch media ID of Instagram posts for the authenticated user"""
    long_lived_token = request.args.get("token")  # Pass long-lived token as a query param
    if not long_lived_token:
        return jsonify({"error": "Long-lived token is required."})

    # Get Instagram user ID from the authenticated user's account
    user_url = "https://graph.facebook.com/v17.0/me"
    user_params = {"fields": "id", "access_token": long_lived_token}
    response = requests.get(user_url, params=user_params)

    if response.status_code != 200:
        return jsonify({"error": response.json()})

    user_data = response.json()
    user_id = user_data["id"]

    # Get media (posts) for the Instagram user
    media_url = f"https://graph.facebook.com/v17.0/{user_id}/media"
    media_params = {"access_token": long_lived_token}
    media_response = requests.get(media_url, params=media_params)

    if media_response.status_code != 200:
        return jsonify({"error": media_response.json()})

    media_data = media_response.json()
    if media_data.get("data"):
        media_id = media_data["data"][0]["id"]  # Get the first media ID
        return jsonify({"media_id": media_id})
    else:
        return jsonify({"error": "No media found for the user."})


@app.route("/get_impressions")
def get_impressions():
    """Step 5: Get impressions for a specific media post"""
    media_id = request.args.get("media_id")  # Pass media ID as a query param
    long_lived_token = request.args.get("token")  # Pass long-lived token as a query param
    if not media_id or not long_lived_token:
        return jsonify({"error": "Media ID and long-lived token are required."})

    insights_url = f"https://graph.facebook.com/v17.0/{media_id}/insights"
    insights_params = {"metric": "impressions", "access_token": long_lived_token}
    response = requests.get(insights_url, params=insights_params)

    if response.status_code != 200:
        return jsonify({"error": response.json()})

    impressions_data = response.json()
    if impressions_data.get("data"):
        impressions = impressions_data["data"][0]["values"][0]["value"]
        return jsonify({"impressions": impressions})
    else:
        return jsonify({"error": "No insights data found for the media."})


if __name__ == "__main__":
    app.run(debug=True)
