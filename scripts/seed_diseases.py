import os
import json
import time
from app import create_app, db
from app.models import Disease

app = create_app()

def determine_pathogen_type(cause):
    cause_lower = cause.lower()
    if 'fung' in cause_lower: return 'Fungal Pathogen'
    if 'bacter' in cause_lower: return 'Bacterial Infection'
    if 'vir' in cause_lower: return 'Viral Infection'
    if 'mite' in cause_lower or 'insect' in cause_lower or 'pest' in cause_lower: return 'Parasitic Infestation'
    return 'Environmental / Unknown'

def seed_legacy_diseases():
    with open(app.config["PLANT_DISEASE_JSON"], "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for item in data:
        name = item.get("name")
        # Skip if already exists
        if Disease.query.filter_by(name=name).first():
            continue
            
        parts = name.split('___')
        crop = parts[0].replace('_', ' ') if len(parts) > 1 else 'Unknown'
        disease_title = parts[1].replace('_', ' ') if len(parts) > 1 else name.replace('_', ' ')
        
        disease = Disease(
            name=name,
            crop=crop,
            disease_name=disease_title,
            cause=item.get("cause", ""),
            cure=item.get("cure", ""),
            pathogen_type=determine_pathogen_type(item.get("cause", "")),
            image_url=item.get("image_url", ""),
            region="Global"
        )
        db.session.add(disease)
    db.session.commit()
    print("Seeded legacy diseases successfully.")

def seed_indian_diseases():
    indian_crops = [
        {"crop": "Rice", "disease": "Leaf Blast"},
        {"crop": "Rice", "disease": "Brown Spot"},
        {"crop": "Wheat", "disease": "Yellow Rust"},
        {"crop": "Sugarcane", "disease": "Red Rot"},
        {"crop": "Cotton", "disease": "Leaf Curl Virus"},
        {"crop": "Cotton", "disease": "Bollworm Infestation"},
        {"crop": "Mango", "disease": "Malformation"},
        {"crop": "Mango", "disease": "Anthracnose"},
        {"crop": "Banana", "disease": "Panama Disease"},
        {"crop": "Banana", "disease": "Bunchy Top Virus"},
        {"crop": "Tea", "disease": "Blister Blight"},
        {"crop": "Chickpea", "disease": "Ascochyta Blight"}
    ]
    
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    
    for item in indian_crops:
        name = f"{item['crop']}___{item['disease'].replace(' ', '_')}"
        if Disease.query.filter_by(name=name).first():
            continue
            
        print(f"Generating data for {item['crop']} {item['disease']}...")
        prompt = f"""You are an expert Indian agronomist and plant pathologist. 
        Provide data for the disease '{item['disease']}' affecting the crop '{item['crop']}'.
        Return ONLY a JSON object with exactly these keys:
        - 'cause': 2-3 sentences explaining the biological cause.
        - 'cure': 2-3 sentences explaining the actionable treatment or prevention.
        - 'image_keyword': A 2-3 word keyword to search for an image on Unsplash (e.g., 'rice leaf blight').
        Ensure the response is strictly valid JSON."""
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text.strip()
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: text = match.group(0)
            data = json.loads(text)
            
            # Use unsplash source for placeholder image
            keyword = data.get("image_keyword", f"{item['crop']} {item['disease']}").replace(' ', ',')
            image_url = f"https://source.unsplash.com/800x600/?{keyword},plant,leaf"
            
            disease = Disease(
                name=name,
                crop=item['crop'],
                disease_name=item['disease'],
                cause=data.get("cause", ""),
                cure=data.get("cure", ""),
                pathogen_type=determine_pathogen_type(data.get("cause", "")),
                image_url=image_url,
                region="India"
            )
            db.session.add(disease)
            db.session.commit()
            print(f"Added {name} to database.")
            time.sleep(2) # Prevent rate limiting
        except Exception as e:
            print(f"Failed to generate for {name}: {e}")

if __name__ == "__main__":
    with app.app_context():
        # First drop and recreate DB
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        
        print("Seeding legacy data...")
        seed_legacy_diseases()
        
        print("Seeding new Indian crop data via Gemini API...")
        seed_indian_diseases()
        
        print("Database seed complete.")
