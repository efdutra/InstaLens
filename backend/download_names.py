"""
Script to download IBGE names and create local cache.
Run ONCE to generate names_cache.json.

Usage:
    python download_names.py
"""

import httpx
import json
from pathlib import Path
import time

API_BASE_URL = "https://servicodados.ibge.gov.br/api/v3/nomes/2022/localidade/0/ranking/nome"
OUTPUT_FILE_MALE = Path(__file__).parent / "names_cache_male.json"
OUTPUT_FILE_FEMALE = Path(__file__).parent / "names_cache_female.json"


def download_names_by_gender(sexo: str) -> dict[str, str]:
    """
    Download all names from a specific gender.
    
    Args:
        sexo: 'm' for male, 'f' for female
    
    Returns:
        Dict with {name: gender}
    """
    names = {}
    page = 1
    total_pages = None
    
    print(f"\n{'='*60}")
    print(f"📥 Downloading {'MALE' if sexo == 'm' else 'FEMALE'} names...")
    print(f"{'='*60}\n")
    
    while True:
        try:
            # Request to IBGE API
            url = f"{API_BASE_URL}?page={page}&sexo={sexo}"
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            
            # First page: discover total
            if total_pages is None:
                total_pages = data.get('totalPages', 0)
                print(f"📊 Total pages: {total_pages}")
                print(f"📊 Total names: {data.get('count', 0)}\n")
            
            # Extract names from current page
            items = data.get('items', [])
            for item in items:
                nome = item['nome'].lower().strip()
                names[nome] = sexo.upper()
            
            # Progress
            print(f"✅ Page {page}/{total_pages} processed ({len(names)} names so far)")
            
            # Next page
            next_page = data.get('nextPage')
            if not next_page or next_page == 0:
                break
            
            page = next_page
            
            # Delay to not overload API
            time.sleep(0.1)
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error on page {page}: {e}")
            break
        except Exception as e:
            print(f"❌ Error on page {page}: {e}")
            break
    
    print(f"\n✅ {len(names)} {'MALE' if sexo == 'm' else 'FEMALE'} names downloaded!\n")
    return names


def main():
    """Main function."""
    print("\n" + "="*60)
    print("🇧🇷 IBGE Names Downloader")
    print("="*60)
    print("\nThis script will download ALL names from IBGE (may take ~5-10 minutes)")
    
    input("\nPress ENTER to start... ")
    
    start_time = time.time()
    
    # Download male and female names
    male_names = download_names_by_gender('m')
    female_names = download_names_by_gender('f')
    
    # Save in 2 separate JSON files
    print("="*60)
    print("💾 Saving caches...")
    print("="*60)
    
    # Save males
    with open(OUTPUT_FILE_MALE, 'w', encoding='utf-8') as f:
        json.dump(male_names, f, ensure_ascii=False, indent=2)
    print(f"✅ Males saved: {OUTPUT_FILE_MALE}")
    
    # Save females
    with open(OUTPUT_FILE_FEMALE, 'w', encoding='utf-8') as f:
        json.dump(female_names, f, ensure_ascii=False, indent=2)
    print(f"✅ Females saved: {OUTPUT_FILE_FEMALE}")
    
    elapsed_time = time.time() - start_time
    
    # Resumo
    print("\n" + "="*60)
    print("✅ CONCLUÍDO!")
    print("="*60)
    print(f"\n📊 Statistics:")
    print(f"   • Males: {len(male_names)}")
    print(f"   • Females: {len(female_names)}")
    print(f"   • Total: {len(male_names) + len(female_names)}")
    print(f"   • Elapsed time: {elapsed_time:.1f}s")
    print(f"   • Saved files:")
    print(f"      - {OUTPUT_FILE_MALE} ({OUTPUT_FILE_MALE.stat().st_size / 1024:.1f} KB)")
    print(f"      - {OUTPUT_FILE_FEMALE} ({OUTPUT_FILE_FEMALE.stat().st_size / 1024:.1f} KB)")
    
    # Preview males
    print(f"\n📝 Preview MALES (first 5):")
    for i, (nome, sexo) in enumerate(list(male_names.items())[:5], 1):
        print(f"   {i}. {nome.capitalize()} → ♂️  {sexo}")
    
    # Preview females
    print(f"\n📝 Preview FEMALES (first 5):")
    for i, (nome, sexo) in enumerate(list(female_names.items())[:5], 1):
        print(f"   {i}. {nome.capitalize()} → ♀️  {sexo}")
    
    print("\n" + "="*60)
    print("🎉 Caches ready for use in scraper!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
