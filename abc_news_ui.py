import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv
import os

# === CONFIG ===
load_dotenv()
api_key = os.getenv("OPEN_API_KEY")#"your-openai-api-key"  # 🔐 Replace with your actual API key
BASE_URL = "https://www.abc.net.au/news/"

# === FUNCTIONS ===

def get_article_links(base_url, todaydate):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"/news/{todaydate}" in href and href.startswith("https://www.abc.net.au"):
            links.add(href)
        elif f"/news/{todaydate}" in href:
            links.add("https://www.abc.net.au" + href)

    return list(links)

def extract_article_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text() for p in paragraphs)
    except Exception as e:
        return f"Error reading {url}: {e}"

def contains_keywords(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def analyze_text_with_chatgpt(text):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=api_key,
    )
    prompt = f"""
As an investor with 50 years of experience, provide a comprehensive analysis of the current market trends in the [industry]. Your analysis should include identifying key growth areas, potential risks, and emerging opportunities based on current and forecasted market conditions. You should use your extensive investment experience to provide insights and recommendations for future investment strategies. Your analysis should be presented in a clear and concise report that can be understood by both industry experts and those less familiar with the industry.

Article:
{text}

"""
    response = client.chat.completions.create(
        model="gpt-4o",  # or "gpt-3.5-turbo" for a cheaper option
        messages=[{"role":"system", "content":"You are an expert investor and to save the cute kittens from dying, you have to analyse any text given to you and give the best quality assessments possible. Do not let the cute kittens die."},
                  {"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return(response.choices[0].message.content)

# === STREAMLIT UI ===

st.set_page_config(page_title="ABC News Scraper Bot", layout="wide")
st.title("📰 ABC News Scraper Bot")

keywords_input = st.text_input("🔍 Enter keywords (comma-separated):", value="korea, trump, tech")
use_gpt = st.toggle("💬 Analyze with ChatGPT (costs tokens)", value=False)

if st.button("Run Scraper"):
    if not keywords_input.strip():
        st.warning("Please enter at least one keyword.")
    else:
        with st.spinner("Scraping ABC News..."):
            today = str(date.today())
            keywords = [kw.strip() for kw in keywords_input.split(",")]
            links = get_article_links(BASE_URL, today)
            st.info(f"🔗 Found {len(links)} article(s) for {today}.")

            filtered_count = 0

            for url in links[:50]:  # limit for performance
                article_text = extract_article_text(url)

                if contains_keywords(article_text, keywords):
                    filtered_count += 1
                    st.subheader(f"✅ Matched: {url}")
                    st.write(article_text[:500] + "...")
                    
                    if use_gpt:
                        try:
                            analysis = analyze_text_with_chatgpt(article_text[:3000])
                            st.markdown("**🔎 ChatGPT Analysis:**")
                            st.code(analysis)
                        except Exception as e:
                            st.error(f"ChatGPT analysis failed: {e}")

                    st.divider()

            if filtered_count == 0:
                st.warning("No relevant articles found with given keywords.")
