"""Baixar Swagger HTML"""
import httpx

cert_path = r"d:\leitor pdf e geração de notas\certificados\cert.pem"
key_path = r"d:\leitor pdf e geração de notas\certificados\key.pem"

client = httpx.Client(cert=(cert_path, key_path), verify=False)
r = client.get('https://adn.producaorestrita.nfse.gov.br/contribuintes/docs/index.html')

with open('swagger.html', 'w', encoding='utf-8') as f:
    f.write(r.text)

print(f"✅ Swagger salvo em swagger.html ({len(r.text)} bytes)")

# Procurar por paths
import re
paths = re.findall(r'"(/[^"]+)"[^>]*>\s*(GET|POST|PUT|DELETE|PATCH)', r.text)
if paths:
    print("\n📍 Endpoints encontrados:")
    for path, method in sorted(set(paths)):
        if 'contribuintes' in path or 'nfse' in path or 'dps' in path:
            print(f"   {method:6} {path}")
