import pandas as pd
import requests


def get_google_reviews(api_key, place_id):
    # Google Place Details API Endpoint
    url = "https://googleapis.com"

    # Define parameters (specifically requesting the 'reviews' and 'name' fields)
    params = {"place_id": place_id, "fields": "name,reviews", "key": api_key}

    # Execute request
    response = requests.get(url, params=params).json()

    # Check for successful API response status
    if response.get("status") != "OK":
        print(f"Error from API: {response.get('status')}")
        if "error_message" in response:
            print(response["error_message"])
        return

    result = response.get("result", {})
    business_name = result.get("name", "Unknown Business")
    reviews_data = result.get("reviews", [])

    if not reviews_data:
        print("No reviews found for this place.")
        return

    # Parse JSON fields into a clean list
    parsed_reviews = []
    for review in reviews_data:
        parsed_reviews.append(
            {
                "Business Name": business_name,
                "Author Name": review.get("author_name"),
                "Rating (Stars)": review.get("rating"),
                "Review Text": review.get("text"),
                "Relative Time": review.get("relative_time_description"),
                "Time Timestamp": review.get("time"),
            }
        )

    # Convert to a DataFrame and export to Excel
    df = pd.DataFrame(parsed_reviews)
    output_filename = "google_top_5_reviews.xlsx"
    df.to_excel(output_filename, index=False)

    print(
        f"Success! Exported {len(parsed_reviews)} reviews to {output_filename}"
    )


# --- CONFIGURATION ---
API_KEY = "YOUR_GOOGLE_API_KEY"
PLACE_ID = "ChIJnZEJnjT3OxARG6t6yggf15g"

# Execute
get_google_reviews(API_KEY, PLACE_ID)
