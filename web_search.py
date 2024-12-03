import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re
import time

class WebSearch:
    def __init__(self):
        self.search_cache = {}
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
    def clean_text(self, text):
        """Clean and format the search result text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove URLs, emails, and file paths
        text = re.sub(r'http\S+|www\.\S+|\S+@\S+|\S+\.(com|org|net|edu|gov)\b|\\+\S+', '', text)
        
        # Remove unwanted phrases
        unwanted_phrases = [
            r'cookies?\s+policy',
            r'privacy\s+policy',
            r'terms\s+of\s+service',
            r'accept\s+cookies',
            r'change\s+your\s+city',
            r'subscribe\s+to\s+our\s+newsletter',
            r'sign\s+up\s+for\s+our\s+newsletter',
            r'advertisement',
            r'we\s+serve\s+personalized\s+stories',
            r'based\s+on\s+the\s+selected\s+city',
            r'click\s+here',
            r'read\s+more'
        ]
        for phrase in unwanted_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        # Remove text within parentheses and brackets
        text = re.sub(r'\([^)]*\)|\[[^\]]*\]|{[^}]*}', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.,!?]', ' ', text)
        
        # Clean up sentences
        sentences = re.split(r'[.!?]+', text)
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Only keep meaningful sentences with proper structure
            if (len(sentence) > 20 and 
                not re.match(r'^\d+$', sentence) and  # Skip number-only sentences
                not re.match(r'^[a-zA-Z\s]{1,3}$', sentence) and  # Skip very short word-only sentences
                not sentence.lower().startswith(('click', 'subscribe', 'sign up', 'download'))):
                sentence = sentence[0].upper() + sentence[1:] if sentence else ''
                cleaned_sentences.append(sentence)
        
        return '. '.join(cleaned_sentences)

    def search_web(self, query, num_results=8):
        """Search the web using Google"""
        try:
            # Check cache first
            if query in self.search_cache:
                return self.search_cache[query]
            
            # Add specificity to certain queries
            if 'latest' in query.lower() and 'movie' in query.lower():
                query += ' ' + time.strftime('%Y')  # Add current year
            elif 'photosynthesis' in query.lower():
                query += ' process definition explanation'
            
            results = []
            headers = {'User-Agent': self.user_agent}
            
            for url in search(query, num_results=num_results):
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove unwanted elements
                        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                            element.decompose()
                        
                        # Get main content
                        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
                        if main_content:
                            soup = main_content
                        
                        # Get paragraphs with meaningful content
                        paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3'])
                        content = []
                        
                        for p in paragraphs:
                            text = p.get_text().strip()
                            if len(text) > 100:  # Only consider substantial paragraphs
                                cleaned_text = self.clean_text(text)
                                if cleaned_text and len(cleaned_text) > 50:
                                    content.append(cleaned_text)
                        
                        if content:
                            # Get the most relevant content
                            relevant_content = max(content, key=len)
                            if len(relevant_content) > 50:
                                results.append(relevant_content)
                                if len(results) >= 2:  # If we have enough good results
                                    break
                            
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
                    continue
            
            if results:
                # Combine and format the best results
                final_result = ' '.join(results[:2])
                if len(final_result) > 250:  # Keep response concise
                    final_result = final_result[:247] + "..."
                
                # Final cleanup
                final_result = self.clean_text(final_result)
                self.search_cache[query] = final_result
                return final_result
            
            return "I couldn't find specific information about that. Could you try rephrasing your question?"
            
        except Exception as e:
            print(f"Error searching web: {e}")
            return "I'm having trouble searching for that information right now. Please try again in a moment."

    def get_simple_definition(self, query):
        """Get a simple, direct definition or explanation"""
        # Customize search based on query type
        if query.lower() in ['photosynthesis', 'respiration', 'osmosis', 'diffusion']:
            search_query = f"{query} process definition for students simple explanation"
        else:
            search_query = f"{query} definition meaning simple explanation"
        
        try:
            headers = {'User-Agent': self.user_agent}
            results = []
            
            # Try to get definition-style content
            for url in search(search_query, num_results=8):
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove unwanted elements
                        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                            element.decompose()
                        
                        # Look for definition-style content
                        definition_markers = [
                            'is a process', 'is the process', 'is an', 'is a',
                            'refers to', 'defined as', 'describes', 'means'
                        ]
                        
                        # First try to find direct definition paragraphs
                        paragraphs = soup.find_all(['p', 'div'])
                        for p in paragraphs:
                            text = p.get_text().strip()
                            text = re.sub(r'\s+', ' ', text)
                            
                            # Look for definition-style sentences
                            lower_text = text.lower()
                            
                            # Check if this paragraph contains a definition
                            if any(f"{query.lower()} {marker}" in lower_text for marker in definition_markers):
                                # Extract the definition sentence and potentially the follow-up
                                sentences = re.split(r'[.!?]+', text)
                                for i, sentence in enumerate(sentences):
                                    lower_sentence = sentence.lower().strip()
                                    # Check if this sentence contains the definition
                                    if any(f"{query.lower()} {marker}" in lower_sentence for marker in definition_markers):
                                        # Clean the current sentence
                                        clean_sentence = re.sub(r'[^a-zA-Z0-9\s.,]', '', sentence).strip()
                                        
                                        # For processes, try to include the next sentence if it adds value
                                        if query.lower() in ['photosynthesis', 'respiration', 'osmosis', 'diffusion']:
                                            if i + 1 < len(sentences):
                                                next_sentence = sentences[i + 1].strip()
                                                if len(next_sentence) > 20 and any(word in next_sentence.lower() for word in ['this', 'which', 'during', 'through', 'using']):
                                                    next_clean = re.sub(r'[^a-zA-Z0-9\s.,]', '', next_sentence).strip()
                                                    clean_sentence = f"{clean_sentence}. {next_clean}"
                                        
                                        if len(clean_sentence) > 50:
                                            results.append(clean_sentence)
                                            break
                            
                            if results:
                                break
                                
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
                    continue
                
                if results:
                    break
            
            if results:
                # Filter and select the best definition
                definitions = [d for d in results if len(d) >= 50 and len(d) <= 250]  # Allow longer definitions
                if definitions:
                    # Sort by length and quality
                    scored_definitions = []
                    for d in definitions:
                        score = 0
                        # Prefer definitions with key explanation words
                        score += sum(2 for word in ['process', 'which', 'where', 'through', 'using'] if word in d.lower())
                        # Prefer definitions with proper length
                        if 100 <= len(d) <= 200:
                            score += 3
                        scored_definitions.append((score, d))
                    
                    # Get the definition with the highest score
                    best_definition = max(scored_definitions, key=lambda x: (x[0], -len(x[1])))[1]
                    # Ensure the first letter is capitalized
                    return best_definition[0].upper() + best_definition[1:]
            
            # Fallback to regular search if no definition found
            return self.search_web(query)
            
        except Exception as e:
            print(f"Error in get_simple_definition: {e}")
            return self.search_web(query)

    def get_product_info(self, query):
        """Get specific product information"""
        # Add current year to get latest info
        product_type = ""
        if 'iphone' in query.lower():
            product_type = "iPhone"
            search_query = f"latest Apple {product_type} model {time.strftime('%Y')}"
        elif 'samsung' in query.lower():
            product_type = "Samsung"
            search_query = f"latest {product_type} Galaxy phone model {time.strftime('%Y')}"
        else:
            search_query = f"{query} {time.strftime('%Y')} latest model"
        
        try:
            headers = {'User-Agent': self.user_agent}
            results = []
            
            for url in search(search_query, num_results=8):
                try:
                    # Skip irrelevant sites for product searches
                    if any(site in url.lower() for site in [
                        'amazon', 'ebay', 'walmart', 'shopping', 
                        'store', 'buy', 'shop', 'cart', 'price'
                    ]):
                        continue
                        
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove unwanted elements
                        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                            element.decompose()
                        
                        # Remove marketing and shopping content
                        unwanted_phrases = [
                            r'buy now', r'add to cart', r'shop now', r'price',
                            r'payment', r'shipping', r'delivery', r'warranty',
                            r'EMI', r'credit card', r'debit card', r'UPI',
                            r'available', r'stock', r'order', r'purchase'
                        ]
                        
                        paragraphs = soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3'])
                        for p in paragraphs:
                            text = p.get_text().strip()
                            text = re.sub(r'\s+', ' ', text)
                            
                            # Skip marketing content
                            if any(re.search(phrase, text, re.IGNORECASE) for phrase in unwanted_phrases):
                                continue
                                
                            # Product-specific patterns
                            if product_type == "iPhone":
                                iphone_patterns = [
                                    r'iPhone\s+(?:1[0-9]|[0-9])\s*(?:Pro\s*(?:Max)?|Plus|mini)?',
                                    r'latest\s+iPhone.*?(?:1[0-9]|[0-9])\s*(?:Pro\s*(?:Max)?|Plus|mini)?',
                                    r'newest\s+iPhone.*?(?:1[0-9]|[0-9])\s*(?:Pro\s*(?:Max)?|Plus|mini)?'
                                ]
                                for pattern in iphone_patterns:
                                    matches = re.finditer(pattern, text, re.IGNORECASE)
                                    for match in matches:
                                        model = match.group(0).strip()
                                        if model and len(model) > 6:  # Ensure it's a complete model name
                                            results.append(model)
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
                    continue
            
            # Process results outside the URL loop
            if results:
                # Count occurrences of each model
                model_counts = {}
                for model in results:
                    model_clean = re.sub(r'\s+', ' ', model).strip()
                    model_counts[model_clean] = model_counts.get(model_clean, 0) + 1
                
                # Get the most frequently mentioned model
                if model_counts:
                    latest_model = max(model_counts.items(), key=lambda x: x[1])[0]
                    
                    # Format the response based on query type
                    if product_type == "iPhone":
                        return f"The latest iPhone model is the {latest_model}"
                    elif product_type == "Samsung":
                        return f"The latest Samsung phone is the {latest_model}"
                    else:
                        return f"The latest model is the {latest_model}"
            
            return f"I couldn't find specific information about the latest {product_type if product_type else 'model'}. Please try asking in a different way."
            
        except Exception as e:
            print(f"Error in get_product_info: {e}")
            return "I'm having trouble finding that product information right now."

    def get_information(self, query):
        """Get information from web search"""
        # Clean the query
        query = re.sub(r'[^\w\s]', ' ', query).strip()
        
        # Check if it's a product query
        if any(word in query.lower() for word in ['latest', 'newest', 'recent']) and \
           any(word in query.lower() for word in ['model', 'version', 'phone', 'iphone', 'samsung', 'device']):
            result = self.get_product_info(query)
        elif any(phrase in query.lower() for phrase in ['what is', 'what are', 'define', 'tell me about']):
            topic = re.sub(r'what\s+(?:is|are)\s+|define\s+|tell\s+me\s+about\s+', '', query.lower()).strip()
            result = self.get_simple_definition(topic)
        else:
            result = self.search_web(query)
        
        # Format the response
        if result and not result.startswith(("I couldn't", "I'm having")):
            return result
        return result
