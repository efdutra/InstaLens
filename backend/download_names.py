"""
Script para baixar nomes do IBGE e criar cache local.
Executa UMA VEZ para gerar names_cache.json.

Uso:
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
    Baixa todos os nomes de um sexo específico.
    
    Args:
        sexo: 'm' para masculino, 'f' para feminino
    
    Returns:
        Dict com {nome: sexo}
    """
    names = {}
    page = 1
    total_pages = None
    
    print(f"\n{'='*60}")
    print(f"📥 Baixando nomes {'MASCULINOS' if sexo == 'm' else 'FEMININOS'}...")
    print(f"{'='*60}\n")
    
    while True:
        try:
            # Request para API do IBGE
            url = f"{API_BASE_URL}?page={page}&sexo={sexo}"
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            
            # Primeira página: descobre total
            if total_pages is None:
                total_pages = data.get('totalPages', 0)
                print(f"📊 Total de páginas: {total_pages}")
                print(f"📊 Total de nomes: {data.get('count', 0)}\n")
            
            # Extrai nomes da página atual
            items = data.get('items', [])
            for item in items:
                nome = item['nome'].lower().strip()
                names[nome] = sexo.upper()
            
            # Progresso
            print(f"✅ Página {page}/{total_pages} processada ({len(names)} nomes até agora)")
            
            # Próxima página
            next_page = data.get('nextPage')
            if not next_page or next_page == 0:
                break
            
            page = next_page
            
            # Delay para não sobrecarregar API
            time.sleep(0.1)
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Erro HTTP na página {page}: {e}")
            break
        except Exception as e:
            print(f"❌ Erro na página {page}: {e}")
            break
    
    print(f"\n✅ {len(names)} nomes {'MASCULINOS' if sexo == 'm' else 'FEMININOS'} baixados!\n")
    return names


def main():
    """Função principal."""
    print("\n" + "="*60)
    print("🇧🇷 IBGE Names Downloader")
    print("="*60)
    print("\nEste script baixará TODOS os nomes do IBGE (pode demorar ~5-10 minutos)")
    
    input("\nPressione ENTER para iniciar... ")
    
    start_time = time.time()
    
    # Baixa nomes masculinos e femininos
    male_names = download_names_by_gender('m')
    female_names = download_names_by_gender('f')
    
    # Salva em 2 arquivos JSON separados
    print("="*60)
    print("💾 Salvando caches...")
    print("="*60)
    
    # Salva masculinos
    with open(OUTPUT_FILE_MALE, 'w', encoding='utf-8') as f:
        json.dump(male_names, f, ensure_ascii=False, indent=2)
    print(f"✅ Masculinos salvos: {OUTPUT_FILE_MALE}")
    
    # Salva femininos
    with open(OUTPUT_FILE_FEMALE, 'w', encoding='utf-8') as f:
        json.dump(female_names, f, ensure_ascii=False, indent=2)
    print(f"✅ Femininos salvos: {OUTPUT_FILE_FEMALE}")
    
    elapsed_time = time.time() - start_time
    
    # Resumo
    print("\n" + "="*60)
    print("✅ CONCLUÍDO!")
    print("="*60)
    print(f"\n📊 Estatísticas:")
    print(f"   • Masculinos: {len(male_names)}")
    print(f"   • Femininos: {len(female_names)}")
    print(f"   • Total: {len(male_names) + len(female_names)}")
    print(f"   • Tempo decorrido: {elapsed_time:.1f}s")
    print(f"   • Arquivos salvos:")
    print(f"      - {OUTPUT_FILE_MALE} ({OUTPUT_FILE_MALE.stat().st_size / 1024:.1f} KB)")
    print(f"      - {OUTPUT_FILE_FEMALE} ({OUTPUT_FILE_FEMALE.stat().st_size / 1024:.1f} KB)")
    
    # Preview masculinos
    print(f"\n📝 Preview MASCULINOS (primeiros 5):")
    for i, (nome, sexo) in enumerate(list(male_names.items())[:5], 1):
        print(f"   {i}. {nome.capitalize()} → ♂️  {sexo}")
    
    # Preview femininos
    print(f"\n📝 Preview FEMININOS (primeiros 5):")
    for i, (nome, sexo) in enumerate(list(female_names.items())[:5], 1):
        print(f"   {i}. {nome.capitalize()} → ♀️  {sexo}")
    
    print("\n" + "="*60)
    print("🎉 Caches prontos para uso no scraper!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
