import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import date
from dotenv import load_dotenv
import os

# === CONFIG ===
load_dotenv()

api_key = os.getenv("OPEN_API_KEY")  # Replace with your actual key
BASE_URL = "https://www.abc.net.au/news/"
KEYWORDS = ["trump", "economics", "tariffs", "tech", "asx", "ASX"]

# === SCRAPE HOMEPAGE ===
def get_article_links(base_url,todaydate):
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

# === EXTRACT ARTICLE TEXT ===
def extract_article_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text() for p in paragraphs)
    except Exception as e:
        print(f"Error reading {url}: {e}")
        return ""

# === FILTER ARTICLES ===
def contains_keywords(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

# === GPT ANALYSIS ===
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
    #return response["choices"][0]["message"]["content"].strip()

# === MAIN ===
def main():
    print("Scraping ABC News...")
    todayDate = str(date.today())


    article_links = get_article_links(BASE_URL, todayDate)
    #print(article_links)

    

    print(f"Found {len(article_links)} articles. Filtering...")

    for url in article_links[:10]:  # Limit to top 10 for quick testing
        print(f"\nAnalyzing {url}")
        article_text = extract_article_text(url)
        
        if any(keyword in article_text.lower() for keyword in KEYWORDS):
            #print(article_text)
        # if contains_keywords(article_text, KEYWORDS):
        #     print(article_text)
            print("Relevant keywords found. Analyzing with ChatGPT...")
            analysis = analyze_text_with_chatgpt(article_text[:3000])  # limit length for GPT
            print(analysis)
        else:
            print("No relevant keywords found.")

if __name__ == "__main__":
    main()
