# hybrid_ai_voting_app/main.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import streamlit as st
import matplotlib.pyplot as plt
import re
from openai import OpenAI


# ====== API KEY CONFIGURATION ======
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ====== SYSTEM PROMPT ======
SYSTEM_PROMPT = """
You are an unbiased political and economic analyst. Your tasks:
1. Identify top political parties and their current campaign promises.
2. Evaluate their historical reliability.
3. Predict living conditions for an average citizen if each party wins.
4. Assign a satisfaction score (0–20) with source-based explanation.
"""

# ====== SCRAPER FUNCTION ======


def scrape_party_info(country):
    # Correct edge cases for country naming on Wikipedia
    country_map = {
        "United States": "the_United_States",
        "United Kingdom": "the_United_Kingdom",
        "Philippines": "the_Philippines"
    }
    wiki_country = country_map.get(country, country)
    url = f"https://en.wikipedia.org/wiki/List_of_political_parties_in_{wiki_country.replace(' ', '_')}"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    party_names = []
    for li in soup.select('ul li a'):
        if li.get('title') and 'party' in li.get('title').lower():
            party_names.append(li.get('title'))

    return party_names[:5]

# ====== LLM CALL FUNCTION ======
def evaluate_parties(parties, country):
    party_analysis = {}
    party_scores = {}

    for party in parties:
        prompt = f"""
        Analyze the political party '{party}' in {country}:
        - Current promises
        - Past performance
        - Predict living conditions impact (salary, cost of living, happiness index)
        - Give a score (0–20) and justify with real sources if available
        """

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content
        party_analysis[party] = content

        score_match = re.search(r"score.*?(\d{1,2})", content, re.IGNORECASE)
        if score_match:
            score = int(score_match.group(1))
            party_scores[party] = min(max(score, 0), 20)
        else:
            party_scores[party] = None

    return party_analysis, party_scores

# ====== STREAMLIT UI ======
import pycountry

flag_urls = {
    country.name: f"https://flagcdn.com/w320/{country.alpha_2.lower()}.png"
    for country in pycountry.countries
}

def main():
    st.image("images/image.png", use_container_width=True)
    st.title("🙋🏻‍♀️💡 Aware Citizen: Political Economy Analysis")
    st.markdown("Choose your country to analyze political party promises and predicted impacts on daily life.")
    st.markdown("💭 This system uses AI to evaluate political parties based on their promises and historical performance.")
    st.markdown("🚨 Disclaimer: This system is LLM-Based. Please note that the results may be incorrect due to the Open AI model's hallucinations! Thank you for your understanding! 🙏🏻") 
    st.markdown("❗️ Attention: Please enter the full name of the country with no space!")

    country = st.text_input("🔍 Enter Country Name:", "Canada")
    
    if country in flag_urls:
     st.image(flag_urls[country], width=100, caption=f"{country} Flag")
    else:
     st.warning("Flag not available for this country.")
     
    if st.button("Analyze"): 
        with st.spinner("Scraping party data..."):
            parties = scrape_party_info(country)

        st.success(f"Found {len(parties)} political parties.")
        st.write(parties)

        with st.spinner("Evaluating each party using AI..."):
            results, scores = evaluate_parties(parties, country)

        st.header("🔍 Results")
        for party, analysis in results.items():
            st.subheader(party)
            st.markdown(analysis)

        st.header("📊 Satisfaction Score Comparison")
        valid_scores = {k: v for k, v in scores.items() if v is not None}

            
        if valid_scores:
            fig, ax = plt.subplots()
            ax.bar(valid_scores.keys(), valid_scores.values())
            ax.set_ylim(0, 20)
            ax.set_ylabel("Satisfaction Score (0–20)")
            ax.set_title("Predicted Impact of Parties on Living Conditions")
            ax.set_xticklabels(valid_scores.keys(), rotation=45, ha="right")  # Rotate labels
            plt.tight_layout()  # Adjust layout to prevent label cutoff
            st.pyplot(fig)
        else:
            st.warning("No valid scores found to visualize.")

if __name__ == '__main__':
    main()
